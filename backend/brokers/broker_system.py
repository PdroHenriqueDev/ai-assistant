import re
import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from backend.agents.knowledge_agent import KnowledgeAgent
from backend.agents.math_agent import MathAgent
from backend.database.redis_client import redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BrokerSystem:
    def __init__(self):
        self.agents = {}
        
        try:
            self.agents["math"] = MathAgent()
        except Exception as e:
            pass
            
        try:
            self.agents["knowledge"] = KnowledgeAgent()
        except Exception as e:
            self.agents["knowledge"] = None
    
    async def process_message(self, message: Dict[str, Any], session_id: str = "default") -> Dict[str, Any]:
        start_time = datetime.now()
        
        try:
            message_text = message.get("text", message.get("message", ""))
            
            try:
                await redis_client.store_conversation_message(session_id, {
                    "text": message_text,
                    "type": "user",
                    "sender": "user"
                })
            except Exception as e:
                pass
            
            query_hash = hashlib.md5(message_text.encode()).hexdigest()
            cached_response = None
            try:
                cached_response = await redis_client.get_cached_response(query_hash)
            except Exception as e:
                pass
            
            if cached_response:
                try:
                    await redis_client.log_structured_event("cache_hit", {
                        "query_hash": query_hash,
                        "session_id": session_id
                    })
                except Exception as e:
                    pass
                
                try:
                    await redis_client.store_conversation_message(session_id, cached_response)
                except Exception as e:
                    pass
                
                return cached_response

            try:
                agent_type, decision_details = self._determine_agent(message_text)
            except Exception as e:
                raise
            
            normalized_message = {"text": message_text, "message": message_text}
            
            if agent_type == "math":
                if "math" in self.agents and self.agents["math"]:
                    response = self.agents["math"].process_query(normalized_message)
                else:
                    response = {
                        "text": "Math agent is not available at the moment.",
                        "type": "error",
                        "timestamp": datetime.now().isoformat(),
                        "source": "system_error"
                    }
            else:
                if "knowledge" in self.agents and self.agents["knowledge"]:
                    response = await self.agents["knowledge"].process_query(normalized_message)
                else:
                    response = {
                         "text": "Knowledge agent is not available at the moment. Please try again later.",
                         "type": "error",
                         "timestamp": datetime.now().isoformat(),
                         "source": "system_error"
                     }
            

            
            execution_time = (datetime.now() - start_time).total_seconds()

            log_entry = {
                "session_id": session_id,
                "message": message_text,
                "agent_selected": agent_type,
                "decision_details": decision_details,
                "execution_time_seconds": execution_time,
                "response_type": response.get("type", "unknown")
            }
            
            try:
                await redis_client.log_structured_event("message_processed", log_entry)
            except Exception as e:
                pass
            
            logger.info(f"Router Decision: {json.dumps(log_entry)}")
            
            response["routing_info"] = {
                "agent_used": agent_type,
                "execution_time": execution_time,
                "decision_details": decision_details
            }
            
            try:
                await redis_client.cache_agent_response(query_hash, response)
            except Exception as e:
                pass

            try:
                await redis_client.store_conversation_message(session_id, response)
            except Exception as e:
                pass
            
            return response
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            message_text = message.get("text", message.get("message", ""))
            
            error_log = {
                "session_id": session_id,
                "message": message_text,
                "error": str(e),
                "execution_time_seconds": execution_time
            }
            
            try:
                await redis_client.log_structured_event("processing_error", error_log)
            except Exception as redis_error:
                pass
            
            logger.error(f"Router Error: {json.dumps(error_log)}")
            
            error_response = {
                "text": "Sorry, I encountered an error processing your request.",
                "type": "error",
                "timestamp": datetime.now().isoformat(),
                "sender": "agent",
                "routing_info": {
                    "agent_used": "none",
                    "execution_time": execution_time,
                    "error": str(e)
                }
            }

            try:
                await redis_client.store_conversation_message(session_id, error_response)
            except Exception as redis_error:
                pass
            
            return error_response
    
    def _determine_agent(self, message: str) -> tuple[str, Dict[str, Any]]:
        math_patterns = [
            r'\d+\s*[+\-*/×÷]\s*\d+', 
            r'\b(calculate|compute|solve|what is|what\'s|how much|how many)\b.*\d',
            r'\b(square root|sqrt|power|exponent)\b',
            r'\b(sin|cos|tan|log|ln)\b',
            r'\d+\s*[%^]',
            r'\([^)]*\d[^)]*\)',
            r'\d+\s*[x×*]\s*\d+',
        ]
        
        decision_details = {
            "patterns_checked": len(math_patterns),
            "matches_found": []
        }
        
        for pattern in math_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                decision_details["matches_found"].append(pattern)
        
        if decision_details["matches_found"]:
            decision_details["reasoning"] = "Mathematical patterns detected"
            return "math", decision_details
        else:
            decision_details["reasoning"] = "No mathematical patterns, routing to knowledge agent"
            return "knowledge", decision_details
    
    async def get_conversation_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        return await redis_client.get_conversation_history(session_id, limit)