import os
import json
import logging
import aiohttp
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class KnowledgeAgent:
    def __init__(self):
        # Use Docker service name for internal communication
        self.rag_api_url = os.getenv("RAG_API_URL", "http://rag-api:8001/ask")
    

    
    async def process_query(self, message: Dict[str, Any]) -> Dict[str, Any]:
        start_time = datetime.now()
        
        try:
            query = message.get("text", "")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.rag_api_url,
                    json={"question": query},
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        answer = result.get("answer", "I do not know the answer.")
                        sources = result.get("sources", [])
                        
                        execution_time = (datetime.now() - start_time).total_seconds()
                        
                        return {
                            "text": answer,
                            "type": "knowledge",
                            "timestamp": datetime.now().isoformat(),
                            "source": "infinitepay_knowledge_base",
                            "execution_time": execution_time,
                            "metadata": {
                                "query": query,
                                "sources": sources,
                                "num_sources": len(sources)
                            }
                        }
                    else:
                        raise Exception(f"RAG API returned status {response.status}")
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error in knowledge agent: {str(e)}")
            
            return {
                "text": "Desculpe, encontrei um erro ao buscar informações. Tente reformular sua pergunta.",
                "type": "error",
                "timestamp": datetime.now().isoformat(),
                "source": "knowledge_agent_error",
                "execution_time": execution_time,
                "error_details": str(e)
            }