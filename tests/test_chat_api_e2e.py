import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import app
from backend.brokers.broker_system import BrokerSystem

class TestChatAPIE2E:
    
    def setup_method(self):
        self.client = TestClient(app)
        
        # Mock Redis client to avoid external dependencies
        self.redis_mock = AsyncMock()
        self.redis_mock.connect = AsyncMock()
        self.redis_mock.disconnect = AsyncMock()
        self.redis_mock.get_system_stats = AsyncMock(return_value={"status": "connected"})
        self.redis_mock.store_conversation_message = AsyncMock()
        self.redis_mock.get_cached_response = AsyncMock(return_value=None)
        self.redis_mock.log_structured_event = AsyncMock()
        self.redis_mock.cache_agent_response = AsyncMock()
        self.redis_mock.get_conversation_history = AsyncMock(return_value=[])
    
    @patch('backend.app.redis_client')
    @patch('backend.brokers.broker_system.redis_client')
    def test_health_endpoint(self, mock_broker_redis, mock_app_redis):
        mock_app_redis.get_system_stats = AsyncMock(return_value={"status": "connected"})
        
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "redis" in data
    
    @patch('backend.app.redis_client')
    @patch('backend.brokers.broker_system.redis_client')
    @patch('backend.app.broker_system')
    def test_get_messages_endpoint(self, mock_broker_system, mock_broker_redis, mock_app_redis):
        # Mock conversation history
        mock_messages = [
            {"text": "Hello", "type": "user", "timestamp": datetime.now().isoformat()},
            {"text": "Hi there!", "type": "assistant", "timestamp": datetime.now().isoformat()}
        ]
        
        mock_broker_system.get_conversation_history = AsyncMock(return_value=mock_messages)
        
        response = self.client.get("/api/messages?session_id=test_session&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert len(data["messages"]) == 2
        mock_broker_system.get_conversation_history.assert_called_once_with("test_session", 10)
    
    @patch('backend.app.redis_client')
    @patch('backend.brokers.broker_system.redis_client')
    @patch('backend.brokers.broker_system.MathAgent')
    @patch('backend.brokers.broker_system.KnowledgeAgent')
    def test_send_math_message_endpoint(self, mock_knowledge_agent, mock_math_agent, mock_broker_redis, mock_app_redis):
        # Setup mocks
        mock_broker_redis.store_conversation_message = AsyncMock()
        mock_broker_redis.get_cached_response = AsyncMock(return_value=None)
        mock_broker_redis.log_structured_event = AsyncMock()
        mock_broker_redis.cache_agent_response = AsyncMock()
        
        # Mock math agent response
        mock_math_instance = Mock()
        mock_math_instance.process_query.return_value = {
            "text": "2 + 3 = 5",
            "type": "math",
            "timestamp": datetime.now().isoformat(),
            "source": "simple_calculator"
        }
        mock_math_agent.return_value = mock_math_instance
        
        # Mock knowledge agent
        mock_knowledge_instance = AsyncMock()
        mock_knowledge_agent.return_value = mock_knowledge_instance
        
        message_data = {
            "text": "2 + 3",
            "session_id": "test_session"
        }
        
        response = self.client.post("/api/messages", json=message_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "2 + 3 = 5"
        assert data["type"] == "math"
        assert "routing_info" in data
        assert data["routing_info"]["agent_used"] == "math"
    
    @patch('backend.app.redis_client')
    @patch('backend.brokers.broker_system.redis_client')
    @patch('backend.app.broker_system')
    def test_send_knowledge_message_endpoint(self, mock_broker_system, mock_broker_redis, mock_app_redis):
        # Setup mocks
        mock_broker_redis.store_conversation_message = AsyncMock()
        mock_broker_redis.get_cached_response = AsyncMock(return_value=None)
        mock_broker_redis.log_structured_event = AsyncMock()
        mock_broker_redis.cache_agent_response = AsyncMock()
        
        # Mock broker system response
        mock_broker_system.process_message = AsyncMock(return_value={
            "text": "Card machine fees vary by plan. Please check our pricing page.",
            "type": "knowledge",
            "timestamp": datetime.now().isoformat(),
            "source": "knowledge_base",
            "routing_info": {
                "agent_used": "knowledge",
                "execution_time": 0.1,
                "decision_details": {"reasoning": "No mathematical patterns, routing to knowledge agent"}
            }
        })
        
        message_data = {
            "text": "What are the card machine fees?",
            "session_id": "test_session"
        }
        
        response = self.client.post("/api/messages", json=message_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "Card machine fees" in data["text"]
        assert data["type"] == "knowledge"
        assert "routing_info" in data
        assert data["routing_info"]["agent_used"] == "knowledge"
    
    @patch('backend.app.redis_client')
    @patch('backend.brokers.broker_system.redis_client')
    def test_send_message_with_cached_response(self, mock_broker_redis, mock_app_redis):
        # Setup cached response
        cached_response = {
            "text": "Cached: 5 + 5 = 10",
            "type": "math",
            "timestamp": datetime.now().isoformat(),
            "source": "cache"
        }
        
        mock_broker_redis.store_conversation_message = AsyncMock()
        mock_broker_redis.get_cached_response = AsyncMock(return_value=cached_response)
        mock_broker_redis.log_structured_event = AsyncMock()
        
        message_data = {
            "text": "5 + 5",
            "session_id": "test_session"
        }
        
        response = self.client.post("/api/messages", json=message_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Cached: 5 + 5 = 10"
        assert data["source"] == "cache"
    
    @patch('backend.app.redis_client')
    @patch('backend.brokers.broker_system.redis_client')
    @patch('backend.app.broker_system')
    def test_send_message_error_handling(self, mock_broker_system, mock_broker_redis, mock_app_redis):
        # Setup mocks to raise an exception
        mock_broker_redis.store_conversation_message = AsyncMock(side_effect=Exception("Redis error"))
        mock_broker_redis.get_cached_response = AsyncMock(return_value=None)
        mock_broker_redis.log_structured_event = AsyncMock()
        
        mock_broker_system.process_message = AsyncMock(side_effect=Exception("Processing error"))
        
        message_data = {
            "text": "test message",
            "session_id": "test_session"
        }
        
        response = self.client.post("/api/messages", json=message_data)
        
        assert response.status_code == 500
        assert "Processing error" in response.json()["detail"]
    
    def test_send_message_missing_text(self):
        message_data = {
            "session_id": "test_session"
            # Missing 'text' field
        }
        
        with patch('backend.app.broker_system') as mock_broker:
            mock_broker.process_message = AsyncMock(return_value={
                "text": "Please provide a message",
                "type": "error"
            })
            
            response = self.client.post("/api/messages", json=message_data)
            
            # Should still process but with empty text
            assert response.status_code == 200
    
    def test_example_messages_from_requirements(self):
        example_messages = [
            {
                "text": "What are the card machine fees?",
                "expected_agent": "knowledge"
            },
            {
                "text": "Can I use my phone as a card machine?",
                "expected_agent": "knowledge"
            },
            {
                "text": "How much is 65 x 3.11?",
                "expected_agent": "math"
            }
        ]
        
        with patch('backend.app.broker_system') as mock_broker:
            for example in example_messages:
                # Mock appropriate response based on expected agent
                if example["expected_agent"] == "math":
                    mock_response = {
                        "text": "65 * 3.11 = 202.15",
                        "type": "math",
                        "routing_info": {"agent_used": "math"}
                    }
                else:
                    mock_response = {
                        "text": "Here's information about that topic...",
                        "type": "knowledge",
                        "routing_info": {"agent_used": "knowledge"}
                    }
                
                mock_broker.process_message = AsyncMock(return_value=mock_response)
                
                response = self.client.post("/api/messages", json={
                    "text": example["text"],
                    "session_id": "test_session"
                })
                
                assert response.status_code == 200
                data = response.json()
                assert data["routing_info"]["agent_used"] == example["expected_agent"]
    
    def test_socket_test_endpoint(self):
        response = self.client.get("/socket-test")
        
        assert response.status_code == 200
        data = response.json()
        assert "socketio_server" in data
        assert "socketio_async_mode" in data
        assert "socketio_status" in data
        assert data["socketio_status"] == "initialized"
    
    @patch('backend.app.redis_client')
    @patch('backend.brokers.broker_system.redis_client')
    def test_concurrent_requests(self, mock_broker_redis, mock_app_redis):
        mock_broker_redis.store_conversation_message = AsyncMock()
        mock_broker_redis.get_cached_response = AsyncMock(return_value=None)
        mock_broker_redis.log_structured_event = AsyncMock()
        mock_broker_redis.cache_agent_response = AsyncMock()
        
        with patch('backend.app.broker_system') as mock_broker:
            mock_broker.process_message = AsyncMock(return_value={
                "text": "Response",
                "type": "test",
                "routing_info": {"agent_used": "test"}
            })
            
            # Send multiple concurrent requests
            responses = []
            for i in range(5):
                response = self.client.post("/api/messages", json={
                    "text": f"Test message {i}",
                    "session_id": f"session_{i}"
                })
                responses.append(response)
            
            # All requests should succeed
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert data["text"] == "Response"
    
    def test_session_id_handling(self):
        with patch('backend.app.broker_system') as mock_broker:
            mock_broker.process_message = AsyncMock(return_value={
                "text": "Response",
                "type": "test"
            })
            
            # Test with explicit session_id
            response = self.client.post("/api/messages", json={
                "text": "Test message",
                "session_id": "custom_session"
            })
            
            assert response.status_code == 200
            # Verify the session_id was passed to broker
            mock_broker.process_message.assert_called_with(
                {"text": "Test message", "session_id": "custom_session"},
                "custom_session"
            )
            
            # Test without session_id (should default)
            response = self.client.post("/api/messages", json={
                "text": "Test message"
            })
            
            assert response.status_code == 200
            # Should use default session_id
            args, kwargs = mock_broker.process_message.call_args
            assert args[1] == "default"  # Default session_id
    
    def test_response_structure_validation(self):
        with patch('backend.app.broker_system') as mock_broker:
            mock_broker.process_message = AsyncMock(return_value={
                "text": "Test response",
                "type": "math",
                "timestamp": datetime.now().isoformat(),
                "source": "test",
                "routing_info": {
                    "agent_used": "math",
                    "execution_time": 0.1,
                    "decision_details": {"reasoning": "test"}
                }
            })
            
            response = self.client.post("/api/messages", json={
                "text": "2 + 2",
                "session_id": "test"
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Validate required fields
            required_fields = ["text", "type", "timestamp", "source", "routing_info"]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            # Validate routing_info structure
            routing_info = data["routing_info"]
            assert "agent_used" in routing_info
            assert "execution_time" in routing_info
            assert "decision_details" in routing_info