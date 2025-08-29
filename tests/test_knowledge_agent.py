import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import aiohttp
from backend.agents.knowledge_agent import KnowledgeAgent


class TestKnowledgeAgent:
    def setup_method(self):
        self.knowledge_agent = KnowledgeAgent()
    
    @pytest.mark.asyncio
    async def test_successful_rag_api_response(self):
        mock_response_data = {
            "answer": "InfinitePay is a payment processing company.",
            "sources": [
                {"title": "About InfinitePay", "url": "https://example.com/about"},
                {"title": "Company Info", "url": "https://example.com/info"}
            ]
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_response_data
            
            mock_post.return_value.__aenter__.return_value = mock_response
            
            message = {"text": "What is InfinitePay?"}
            result = await self.knowledge_agent.process_query(message)
            
            assert result["text"] == "InfinitePay is a payment processing company."
            assert result["type"] == "knowledge"
            assert result["source"] == "infinitepay_knowledge_base"
            assert "timestamp" in result
            assert "execution_time" in result
            assert result["metadata"]["query"] == "What is InfinitePay?"
            assert result["metadata"]["num_sources"] == 2
            assert len(result["metadata"]["sources"]) == 2
    
    @pytest.mark.asyncio
    async def test_rag_api_no_answer(self):
        mock_response_data = {
            "sources": []
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_response_data
            
            mock_post.return_value.__aenter__.return_value = mock_response
            
            message = {"text": "Unknown question"}
            result = await self.knowledge_agent.process_query(message)
            
            assert result["text"] == "I do not know the answer."
            assert result["type"] == "knowledge"
            assert result["metadata"]["num_sources"] == 0
    
    @pytest.mark.asyncio
    async def test_rag_api_no_sources(self):
        mock_response_data = {
            "answer": "This is an answer without sources."
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_response_data
            
            mock_post.return_value.__aenter__.return_value = mock_response
            
            message = {"text": "Test question"}
            result = await self.knowledge_agent.process_query(message)
            
            assert result["text"] == "This is an answer without sources."
            assert result["metadata"]["sources"] == []
            assert result["metadata"]["num_sources"] == 0
    
    @pytest.mark.asyncio
    async def test_rag_api_error_status(self):
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 500
            
            mock_post.return_value.__aenter__.return_value = mock_response
            
            message = {"text": "Test question"}
            result = await self.knowledge_agent.process_query(message)
            
            assert result["type"] == "error"
            assert result["source"] == "knowledge_agent_error"
            assert "Desculpe, encontrei um erro" in result["text"]
            assert "error_details" in result
            assert "RAG API returned status 500" in result["error_details"]
    
    @pytest.mark.asyncio
    async def test_network_connection_error(self):
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.side_effect = aiohttp.ClientError("Connection failed")
            
            message = {"text": "Test question"}
            result = await self.knowledge_agent.process_query(message)
            
            assert result["type"] == "error"
            assert result["source"] == "knowledge_agent_error"
            assert "Desculpe, encontrei um erro" in result["text"]
            assert "error_details" in result
    
    @pytest.mark.asyncio
    async def test_json_decode_error(self):
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            
            mock_post.return_value.__aenter__.return_value = mock_response
            
            message = {"text": "Test question"}
            result = await self.knowledge_agent.process_query(message)
            
            assert result["type"] == "error"
            assert result["source"] == "knowledge_agent_error"
            assert "error_details" in result
    
    @pytest.mark.asyncio
    async def test_empty_query(self):
        mock_response_data = {
            "answer": "Please provide a question.",
            "sources": []
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_response_data
            
            mock_post.return_value.__aenter__.return_value = mock_response
            
            message = {"text": ""}
            result = await self.knowledge_agent.process_query(message)
            
            assert result["type"] == "knowledge"
            assert result["metadata"]["query"] == ""
    
    @pytest.mark.asyncio
    async def test_message_without_text_field(self):
        mock_response_data = {
            "answer": "No question provided.",
            "sources": []
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_response_data
            
            mock_post.return_value.__aenter__.return_value = mock_response
            
            message = {"other_field": "value"}
            result = await self.knowledge_agent.process_query(message)
            
            assert result["type"] == "knowledge"
            assert result["metadata"]["query"] == ""
    
    def test_initialization_default_url(self):
        with patch.dict('os.environ', {}, clear=True):
            agent = KnowledgeAgent()
            assert agent.rag_api_url == "http://rag-api:8001/ask"
    
    def test_initialization_custom_url(self):
        custom_url = "http://custom-rag:9000/query"
        with patch.dict('os.environ', {'RAG_API_URL': custom_url}):
            agent = KnowledgeAgent()
            assert agent.rag_api_url == custom_url
    
    @pytest.mark.asyncio
    async def test_execution_time_measurement(self):
        mock_response_data = {
            "answer": "Test answer",
            "sources": []
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_response_data
            
            mock_post.return_value.__aenter__.return_value = mock_response
            
            message = {"text": "Test question"}
            result = await self.knowledge_agent.process_query(message)
            
            assert "execution_time" in result
            assert isinstance(result["execution_time"], float)
            assert result["execution_time"] >= 0
    
    @pytest.mark.asyncio
    async def test_request_payload_format(self):
        mock_response_data = {
            "answer": "Test answer",
            "sources": []
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_response_data
            
            mock_post.return_value.__aenter__.return_value = mock_response
            
            message = {"text": "What is the payment process?"}
            await self.knowledge_agent.process_query(message)
            
            # Verify the request was made with correct parameters
            mock_post.assert_called_once_with(
                "http://rag-api:8001/ask",
                json={"question": "What is the payment process?"},
                headers={"Content-Type": "application/json"}
            )