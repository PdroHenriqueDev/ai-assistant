import pytest
import json
import os
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from backend.database.redis_client import RedisClient


class TestRedisClient:
    
    def setup_method(self):
        self.redis_client = RedisClient("redis://test:6379")
        
    @pytest.mark.asyncio
    async def test_init_with_custom_url(self):
        client = RedisClient("redis://custom:1234")
        assert client.redis_url == "redis://custom:1234"
        assert client.redis is None
        
    @pytest.mark.asyncio
    async def test_init_with_env_url(self):
        with patch.dict('os.environ', {'REDIS_URL': 'redis://env:5678'}):
            client = RedisClient()
            assert client.redis_url == "redis://env:5678"
            
    @pytest.mark.asyncio
    async def test_init_with_default_url(self):
        with patch.dict('os.environ', {}, clear=True):
            client = RedisClient()
            assert client.redis_url == "redis://localhost:6379"
    
    @pytest.mark.asyncio
    async def test_connect_success(self):
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        
        with patch('backend.database.redis_client.redis.from_url', return_value=mock_redis):
            await self.redis_client.connect()
            
            assert self.redis_client.redis == mock_redis
            mock_redis.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_failure(self):
        with patch('backend.database.redis_client.redis.from_url', side_effect=Exception("Connection failed")):
            with pytest.raises(Exception, match="Connection failed"):
                await self.redis_client.connect()
    
    @pytest.mark.asyncio
    async def test_disconnect_with_connection(self):
        mock_redis = AsyncMock()
        self.redis_client.redis = mock_redis
        
        await self.redis_client.disconnect()
        
        mock_redis.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disconnect_without_connection(self):
        self.redis_client.redis = None
        
        # Should not raise any exception
        await self.redis_client.disconnect()
    
    @pytest.mark.asyncio
    async def test_store_conversation_message_success(self):
        mock_redis = AsyncMock()
        self.redis_client.redis = mock_redis
        
        message = {"text": "Hello", "type": "user"}
        session_id = "test_session"
        
        await self.redis_client.store_conversation_message(session_id, message)
        
        # Verify Redis operations were called
        mock_redis.lpush.assert_called_once()
        mock_redis.ltrim.assert_called_once_with("conversation:test_session", 0, 99)
        mock_redis.expire.assert_called_once_with("conversation:test_session", 604800)
        
        # Check that message data includes timestamp
        call_args = mock_redis.lpush.call_args[0]
        assert call_args[0] == "conversation:test_session"
        stored_data = json.loads(call_args[1])
        assert stored_data["text"] == "Hello"
        assert stored_data["type"] == "user"
        assert "timestamp" in stored_data
    
    @pytest.mark.asyncio
    async def test_store_conversation_message_failure(self):
        mock_redis = AsyncMock()
        mock_redis.lpush.side_effect = Exception("Redis error")
        self.redis_client.redis = mock_redis
        
        message = {"text": "Hello", "type": "user"}
        session_id = "test_session"
        
        # Should not raise exception, just log error
        await self.redis_client.store_conversation_message(session_id, message)
    
    @pytest.mark.asyncio
    async def test_get_conversation_history_success(self):
        mock_redis = AsyncMock()
        stored_messages = [
            json.dumps({"text": "Hello", "type": "user", "timestamp": "2023-01-01T00:00:00"}),
            json.dumps({"text": "Hi there", "type": "assistant", "timestamp": "2023-01-01T00:01:00"})
        ]
        mock_redis.lrange.return_value = stored_messages
        self.redis_client.redis = mock_redis
        
        result = await self.redis_client.get_conversation_history("test_session", 10)
        
        mock_redis.lrange.assert_called_once_with("conversation:test_session", 0, 9)
        assert len(result) == 2
        # Messages should be reversed (oldest first)
        assert result[0]["text"] == "Hi there"
        assert result[1]["text"] == "Hello"
    
    @pytest.mark.asyncio
    async def test_get_conversation_history_default_limit(self):
        mock_redis = AsyncMock()
        mock_redis.lrange.return_value = []
        self.redis_client.redis = mock_redis
        
        await self.redis_client.get_conversation_history("test_session")
        
        mock_redis.lrange.assert_called_once_with("conversation:test_session", 0, 19)
    
    @pytest.mark.asyncio
    async def test_get_conversation_history_failure(self):
        mock_redis = AsyncMock()
        mock_redis.lrange.side_effect = Exception("Redis error")
        self.redis_client.redis = mock_redis
        
        result = await self.redis_client.get_conversation_history("test_session")
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_cache_agent_response_success(self):
        mock_redis = AsyncMock()
        self.redis_client.redis = mock_redis
        
        response = {"text": "Answer", "type": "math"}
        query_hash = "abc123"
        
        await self.redis_client.cache_agent_response(query_hash, response, 7200)
        
        mock_redis.setex.assert_called_once_with(
            "cache:response:abc123", 
            7200, 
            json.dumps(response)
        )
    
    @pytest.mark.asyncio
    async def test_cache_agent_response_default_ttl(self):
        mock_redis = AsyncMock()
        self.redis_client.redis = mock_redis
        
        response = {"text": "Answer", "type": "math"}
        query_hash = "abc123"
        
        await self.redis_client.cache_agent_response(query_hash, response)
        
        mock_redis.setex.assert_called_once_with(
            "cache:response:abc123", 
            3600,  # default TTL
            json.dumps(response)
        )
    
    @pytest.mark.asyncio
    async def test_cache_agent_response_failure(self):
        mock_redis = AsyncMock()
        mock_redis.setex.side_effect = Exception("Redis error")
        self.redis_client.redis = mock_redis
        
        response = {"text": "Answer", "type": "math"}
        query_hash = "abc123"
        
        # Should not raise exception, just log error
        await self.redis_client.cache_agent_response(query_hash, response)
    
    @pytest.mark.asyncio
    async def test_get_cached_response_success(self):
        mock_redis = AsyncMock()
        cached_data = json.dumps({"text": "Cached answer", "type": "math"})
        mock_redis.get.return_value = cached_data
        self.redis_client.redis = mock_redis
        
        result = await self.redis_client.get_cached_response("abc123")
        
        mock_redis.get.assert_called_once_with("cache:response:abc123")
        assert result["text"] == "Cached answer"
        assert result["type"] == "math"
    
    @pytest.mark.asyncio
    async def test_get_cached_response_not_found(self):
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        self.redis_client.redis = mock_redis
        
        result = await self.redis_client.get_cached_response("abc123")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_cached_response_failure(self):
        mock_redis = AsyncMock()
        mock_redis.get.side_effect = Exception("Redis error")
        self.redis_client.redis = mock_redis
        
        result = await self.redis_client.get_cached_response("abc123")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_log_structured_event_success(self):
        mock_redis = AsyncMock()
        self.redis_client.redis = mock_redis
        
        event_data = {"user_id": "123", "action": "login"}
        
        await self.redis_client.log_structured_event("user_activity", event_data)
        
        # Verify xadd was called with correct parameters
        mock_redis.xadd.assert_called_once()
        call_args = mock_redis.xadd.call_args[0]
        assert call_args[0] == "logs:user_activity"
        
        logged_data = call_args[1]
        assert logged_data["event_type"] == "user_activity"
        assert logged_data["user_id"] == "123"
        assert logged_data["action"] == "login"
        assert "timestamp" in logged_data
        
        # Verify xtrim was called
        mock_redis.xtrim.assert_called_once_with("logs:user_activity", maxlen=1000)
    
    @pytest.mark.asyncio
    async def test_log_structured_event_failure(self):
        mock_redis = AsyncMock()
        mock_redis.xadd.side_effect = Exception("Redis error")
        self.redis_client.redis = mock_redis
        
        event_data = {"user_id": "123", "action": "login"}
        
        # Should not raise exception, just log error
        await self.redis_client.log_structured_event("user_activity", event_data)
    
    @pytest.mark.asyncio
    async def test_get_system_stats_success(self):
        mock_redis = AsyncMock()
        mock_info = {
            "redis_version": "7.0.0",
            "connected_clients": 5,
            "used_memory_human": "1.2M",
            "total_commands_processed": 1000
        }
        mock_redis.info.return_value = mock_info
        self.redis_client.redis = mock_redis
        
        result = await self.redis_client.get_system_stats()
        
        mock_redis.info.assert_called_once()
        assert result["redis_version"] == "7.0.0"
        assert result["connected_clients"] == 5
        assert result["used_memory_human"] == "1.2M"
        assert result["total_commands_processed"] == 1000
    
    @pytest.mark.asyncio
    async def test_get_system_stats_failure(self):
        mock_redis = AsyncMock()
        mock_redis.info.side_effect = Exception("Redis error")
        self.redis_client.redis = mock_redis
        
        result = await self.redis_client.get_system_stats()
        
        assert result == {}
    
    @pytest.mark.asyncio
    async def test_get_system_stats_partial_info(self):
        mock_redis = AsyncMock()
        mock_info = {
            "redis_version": "7.0.0",
            # Missing some expected keys
        }
        mock_redis.info.return_value = mock_info
        self.redis_client.redis = mock_redis
        
        result = await self.redis_client.get_system_stats()
        
        assert result["redis_version"] == "7.0.0"
        assert result["connected_clients"] is None
        assert result["used_memory_human"] is None
        assert result["total_commands_processed"] is None