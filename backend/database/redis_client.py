import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import redis.asyncio as redis
from redis.asyncio import Redis
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis: Optional[Redis] = None
        
    async def connect(self):
        try:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise
    
    async def disconnect(self):
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis")
    
    async def store_conversation_message(self, session_id: str, message: Dict[str, Any]):
        try:
            key = f"conversation:{session_id}"
            message_data = {
                **message,
                "timestamp": datetime.now().isoformat()
            }
            await self.redis.lpush(key, json.dumps(message_data))
            await self.redis.ltrim(key, 0, 99)
            await self.redis.expire(key, 604800)
        except Exception as e:
            logger.error(f"Failed to store conversation message: {str(e)}")
    
    async def get_conversation_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        try:
            key = f"conversation:{session_id}"
            messages = await self.redis.lrange(key, 0, limit - 1)
            return [json.loads(msg) for msg in reversed(messages)]
        except Exception as e:
            logger.error(f"Failed to get conversation history: {str(e)}")
            return []
    
    async def cache_agent_response(self, query_hash: str, response: Dict[str, Any], ttl: int = 3600):
        try:
            key = f"cache:response:{query_hash}"
            await self.redis.setex(key, ttl, json.dumps(response))
        except Exception as e:
            logger.error(f"Failed to cache agent response: {str(e)}")
    
    async def get_cached_response(self, query_hash: str) -> Optional[Dict[str, Any]]:
        try:
            key = f"cache:response:{query_hash}"
            cached = await self.redis.get(key)
            return json.loads(cached) if cached else None
        except Exception as e:
            logger.error(f"Failed to get cached response: {str(e)}")
            return None
    
    async def log_structured_event(self, event_type: str, data: Dict[str, Any]):
        try:
            stream_key = f"logs:{event_type}"
            event_data = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                **data
            }
            await self.redis.xadd(stream_key, event_data)
            await self.redis.xtrim(stream_key, maxlen=1000)
        except Exception as e:
            logger.error(f"Failed to log structured event: {str(e)}")
    
    async def get_system_stats(self) -> Dict[str, Any]:
        try:
            info = await self.redis.info()
            return {
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "total_commands_processed": info.get("total_commands_processed")
            }
        except Exception as e:
            logger.error(f"Failed to get system stats: {str(e)}")
            return {}

redis_client = RedisClient()