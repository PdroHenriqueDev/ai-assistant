import pytest
import sys
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
import json
import hashlib

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.brokers.broker_system import BrokerSystem

class TestBrokerSystemFull:
    
    def setup_method(self):
        # Create persistent mocks that will be used across test methods
        self.mock_math_agent = Mock()
        self.mock_knowledge_agent = Mock()
        self.mock_redis = Mock()
        
        # Setup mock redis client methods
        self.mock_redis.store_conversation_message = AsyncMock()
        self.mock_redis.get_cached_response = AsyncMock(return_value=None)
        self.mock_redis.log_structured_event = AsyncMock()
        self.mock_redis.cache_agent_response = AsyncMock()
        self.mock_redis.get_conversation_history = AsyncMock(return_value=[])
        
        # Apply patches that will persist for the test method
        self.math_agent_patcher = patch('backend.brokers.broker_system.MathAgent')
        self.knowledge_agent_patcher = patch('backend.brokers.broker_system.KnowledgeAgent')
        self.redis_patcher = patch('backend.brokers.broker_system.redis_client', self.mock_redis)
        
        mock_math_agent_class = self.math_agent_patcher.start()
        mock_knowledge_agent_class = self.knowledge_agent_patcher.start()
        self.redis_patcher.start()
        
        mock_math_agent_class.return_value = self.mock_math_agent
        mock_knowledge_agent_class.return_value = self.mock_knowledge_agent
        
        self.broker = BrokerSystem()
    
    def teardown_method(self):
        self.math_agent_patcher.stop()
        self.knowledge_agent_patcher.stop()
        self.redis_patcher.stop()
    
    def test_initialization_success(self):
        with patch('backend.brokers.broker_system.MathAgent') as mock_math_agent, \
             patch('backend.brokers.broker_system.KnowledgeAgent') as mock_knowledge_agent:
            
            mock_math_agent.return_value = Mock()
            mock_knowledge_agent.return_value = Mock()
            
            broker = BrokerSystem()
            
            assert "math" in broker.agents
            assert "knowledge" in broker.agents
            assert broker.agents["math"] is not None
            assert broker.agents["knowledge"] is not None
    
    def test_initialization_math_agent_failure(self):
        with patch('builtins.print') as mock_print:
            with patch('backend.brokers.broker_system.MathAgent', side_effect=Exception("Math agent init failed")):
                broker = BrokerSystem()
                
                # Verify the debug print statement was called (line 62)
                mock_print.assert_any_call("DEBUG: Failed to initialize math agent: Math agent init failed")
                
                # Also verify the success print for knowledge agent (line 65)
                mock_print.assert_any_call("DEBUG: Knowledge agent initialized successfully")
    
    def test_initialization_knowledge_agent_failure(self):
        with patch('backend.brokers.broker_system.MathAgent') as mock_math_agent, \
             patch('backend.brokers.broker_system.KnowledgeAgent') as mock_knowledge_agent, \
             patch('builtins.print') as mock_print:
            
            mock_math_agent.return_value = Mock()
            mock_knowledge_agent.side_effect = Exception("Knowledge agent init failed")
            
            broker = BrokerSystem()
            
            assert "math" in broker.agents
            assert broker.agents["math"] is not None
            assert "knowledge" in broker.agents
            assert broker.agents["knowledge"] is None
            
            # Verify debug print statements were called (covers lines 66-67)
            mock_print.assert_any_call("DEBUG: Math agent initialized successfully")
            mock_print.assert_any_call("DEBUG: Failed to initialize knowledge agent: Knowledge agent init failed")
    
    @pytest.mark.asyncio
    async def test_process_message_math_agent_success(self):
        # Setup mock response from math agent
        mock_response = {
            "text": "The answer is 5",
            "type": "math",
            "timestamp": datetime.now().isoformat()
        }
        self.mock_math_agent.process_query.return_value = mock_response
        
        message = {"text": "2 + 3"}
        result = await self.broker.process_message(message, "test_session")
        
        # Verify the response structure
        assert result["text"] == "The answer is 5"
        assert result["type"] == "math"
        assert "routing_info" in result
        assert result["routing_info"]["agent_used"] == "math"
        assert "execution_time" in result["routing_info"]
        
        # Verify Redis operations were called
        self.mock_redis.store_conversation_message.assert_called()
        self.mock_redis.log_structured_event.assert_called()
        self.mock_redis.cache_agent_response.assert_called()
    
    @pytest.mark.asyncio
    async def test_process_message_redis_warning_prints(self):
        # Setup Redis to fail on store operations to trigger warning prints
        self.mock_redis.store_conversation_message.side_effect = Exception("Redis store failed")
        self.mock_redis.get_cached_response.side_effect = Exception("Redis get failed")
        self.mock_redis.log_structured_event.side_effect = Exception("Redis log failed")
        
        mock_response = {
            "text": "The answer is 5",
            "type": "math",
            "timestamp": datetime.now().isoformat()
        }
        self.mock_math_agent.process_query.return_value = mock_response
        
        with patch('builtins.print') as mock_print:
            message = {"text": "2 + 3"}
            result = await self.broker.process_message(message, "test_session")
            
            # Verify warning print statements were called (covers lines 76-78, 156-157)
            mock_print.assert_any_call("Warning: Failed to store user message in Redis: Redis store failed")
            mock_print.assert_any_call("Warning: Failed to get cached response: Redis get failed")
            mock_print.assert_any_call("Warning: Failed to log to Redis streams: Redis log failed")
    
    @pytest.mark.asyncio
    async def test_process_message_knowledge_agent_success(self):
        # Setup mock response from knowledge agent
        mock_response = {
            "text": "Here's information about card fees",
            "type": "knowledge",
            "timestamp": datetime.now().isoformat()
        }
        self.mock_knowledge_agent.process_query = AsyncMock(return_value=mock_response)
        
        message = {"text": "What are the card machine fees?"}
        result = await self.broker.process_message(message, "test_session")
        
        # Verify the response structure
        assert result["text"] == "Here's information about card fees"
        assert result["type"] == "knowledge"
        assert "routing_info" in result
        assert result["routing_info"]["agent_used"] == "knowledge"
        assert "execution_time" in result["routing_info"]
        
        # Verify Redis operations were called
        self.mock_redis.store_conversation_message.assert_called()
        self.mock_redis.log_structured_event.assert_called()
        self.mock_redis.cache_agent_response.assert_called()
    
    @pytest.mark.asyncio
    async def test_process_message_cached_response(self):
        cached_response = {
            "text": "Cached answer: 5",
            "type": "math",
            "timestamp": datetime.now().isoformat()
        }
        self.mock_redis.get_cached_response = AsyncMock(return_value=cached_response)
        
        message = {"text": "2 + 3"}
        result = await self.broker.process_message(message, "test_session")
        
        # Should return cached response without calling agents
        assert result == cached_response
        
        # Verify cache hit was logged
        expected_hash = hashlib.md5("2 + 3".encode()).hexdigest()
        self.mock_redis.log_structured_event.assert_any_call("cache_hit", {
            "query_hash": expected_hash,
            "session_id": "test_session"
        })
        
        # Agents should not be called
        self.mock_math_agent.process_query.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_message_math_agent_unavailable(self):
        # Set math agent to None
        self.broker.agents["math"] = None
        
        message = {"text": "2 + 3"}
        result = await self.broker.process_message(message, "test_session")
        
        # Should return error response
        assert result["text"] == "Math agent is not available at the moment."
        assert result["type"] == "error"
        assert result["source"] == "system_error"
        assert "routing_info" in result
        assert result["routing_info"]["agent_used"] == "math"
    
    @pytest.mark.asyncio
    async def test_process_message_knowledge_agent_unavailable(self):
        # Set knowledge agent to None
        self.broker.agents["knowledge"] = None
        
        message = {"text": "What are the fees?"}
        result = await self.broker.process_message(message, "test_session")
        
        # Should return error response
        assert result["text"] == "Knowledge agent is not available at the moment. Please try again later."
        assert result["type"] == "error"
        assert result["source"] == "system_error"
        assert "routing_info" in result
        assert result["routing_info"]["agent_used"] == "knowledge"
    
    @pytest.mark.asyncio
    async def test_process_message_agent_exception(self):
        # Setup math agent to raise exception
        self.mock_math_agent.process_query.side_effect = Exception("Agent processing failed")
        
        message = {"text": "2 + 3"}
        result = await self.broker.process_message(message, "test_session")
        
        # Should return error response
        assert result["text"] == "Sorry, I encountered an error processing your request."
        assert result["type"] == "error"
        assert "routing_info" in result
        assert result["routing_info"]["agent_used"] == "none"
        assert "error" in result["routing_info"]
        
        # Error should be logged
        self.mock_redis.log_structured_event.assert_any_call("processing_error", {
            "session_id": "test_session",
            "message": "2 + 3",
            "error": "Agent processing failed",
            "execution_time_seconds": pytest.approx(0, abs=1)
        })
    
    @pytest.mark.asyncio
    async def test_process_message_redis_failures(self):
        # Setup Redis operations to fail
        self.mock_redis.store_conversation_message.side_effect = Exception("Redis store failed")
        self.mock_redis.get_cached_response.side_effect = Exception("Redis get failed")
        self.mock_redis.log_structured_event.side_effect = Exception("Redis log failed")
        self.mock_redis.cache_agent_response.side_effect = Exception("Redis cache failed")
        
        # Setup successful agent response
        mock_response = {
            "text": "The answer is 5",
            "type": "math",
            "timestamp": datetime.now().isoformat()
        }
        self.mock_math_agent.process_query.return_value = mock_response
        
        message = {"text": "2 + 3"}
        result = await self.broker.process_message(message, "test_session")
        
        # Should still return successful response despite Redis failures
        assert result["text"] == "The answer is 5"
        assert result["type"] == "math"
        assert "routing_info" in result
    
    @pytest.mark.asyncio
    async def test_process_message_different_message_formats(self):
        mock_response = {
            "text": "Response",
            "type": "math",
            "timestamp": datetime.now().isoformat()
        }
        self.mock_math_agent.process_query.return_value = mock_response
        
        # Test with 'text' field
        message1 = {"text": "2 + 3"}
        result1 = await self.broker.process_message(message1, "test_session")
        assert result1["text"] == "Response"
        
        # Test with 'message' field
        message2 = {"message": "2 + 3"}
        result2 = await self.broker.process_message(message2, "test_session")
        assert result2["text"] == "Response"
        
        # Test with both fields (should prefer 'text')
        message3 = {"text": "2 + 3", "message": "different"}
        result3 = await self.broker.process_message(message3, "test_session")
        assert result3["text"] == "Response"
        
        # Test with empty message
        message4 = {}
        result4 = await self.broker.process_message(message4, "test_session")
        # Should still process (empty string routes to knowledge agent)
        assert "routing_info" in result4
    
    @pytest.mark.asyncio
    async def test_get_conversation_history(self):
        expected_history = [
            {"text": "Hello", "type": "user", "timestamp": "2024-01-01T10:00:00"},
            {"text": "Hi there!", "type": "assistant", "timestamp": "2024-01-01T10:00:01"}
        ]
        self.mock_redis.get_conversation_history.return_value = expected_history
        
        result = await self.broker.get_conversation_history("test_session", 10)
        
        assert result == expected_history
        self.mock_redis.get_conversation_history.assert_called_once_with("test_session", 10)
    
    @pytest.mark.asyncio
    async def test_get_conversation_history_default_limit(self):
        expected_history = []
        self.mock_redis.get_conversation_history.return_value = expected_history
        
        result = await self.broker.get_conversation_history("test_session")
        
        assert result == expected_history
        self.mock_redis.get_conversation_history.assert_called_once_with("test_session", 20)
    
    def test_determine_agent_math_patterns(self):
        math_cases = [
            "2 + 3",
            "calculate 5 * 6",
            "what is 10 - 4",
            "square root of 16",
            "sin 30",
            "15%",
            "2^3",
            "(5 + 3) * 2"
        ]
        
        for case in math_cases:
            agent_type, details = self.broker._determine_agent(case)
            assert agent_type == "math", f"Failed for case: {case}"
            assert len(details["matches_found"]) > 0
            assert details["reasoning"] == "Mathematical patterns detected"
    
    def test_determine_agent_knowledge_patterns(self):
        knowledge_cases = [
            "What are the card machine fees?",
            "How do I set up my account?",
            "Tell me about your services",
            "I need help with payment processing",
            "Contact information please"
        ]
        
        for case in knowledge_cases:
            agent_type, details = self.broker._determine_agent(case)
            assert agent_type == "knowledge", f"Failed for case: {case}"
            assert len(details["matches_found"]) == 0
            assert details["reasoning"] == "No mathematical patterns, routing to knowledge agent"
    
    def test_determine_agent_decision_details_structure(self):
        agent_type, details = self.broker._determine_agent("test message")
        
        # Check required fields
        assert "patterns_checked" in details
        assert "matches_found" in details
        assert "reasoning" in details
        
        # Check data types
        assert isinstance(details["patterns_checked"], int)
        assert isinstance(details["matches_found"], list)
        assert isinstance(details["reasoning"], str)
        
        # Check values
        assert details["patterns_checked"] == 7  # Number of patterns in the code
        assert agent_type in ["math", "knowledge"]
    
    def test_initialization_print_statements(self):
        with patch('backend.brokers.broker_system.MathAgent') as mock_math_agent, \
             patch('backend.brokers.broker_system.KnowledgeAgent') as mock_knowledge_agent, \
             patch('builtins.print') as mock_print:
            
            mock_math_agent.return_value = Mock()
            mock_knowledge_agent.return_value = Mock()
            
            broker = BrokerSystem()
            
            # Verify print statements were called (lines 61-62, 66-67)
            mock_print.assert_any_call("DEBUG: Math agent initialized successfully")
            mock_print.assert_any_call("DEBUG: Knowledge agent initialized successfully")
    
    def test_initialization_math_agent_failure_debug_prints(self):
        with patch('backend.brokers.broker_system.MathAgent') as mock_math_agent, \
             patch('backend.brokers.broker_system.KnowledgeAgent') as mock_knowledge_agent, \
             patch('builtins.print') as mock_print:
            
            # Make MathAgent initialization fail
            mock_math_agent.side_effect = Exception("Math agent init failed")
            mock_knowledge_agent.return_value = Mock()
            
            broker = BrokerSystem()
            
            # Verify debug print statements were called (lines 61-62)
            mock_print.assert_any_call("DEBUG: Failed to initialize math agent: Math agent init failed")
            mock_print.assert_any_call("DEBUG: Knowledge agent initialized successfully")
    
    def test_initialization_knowledge_agent_failure_debug_prints(self):
        with patch('backend.brokers.broker_system.MathAgent') as mock_math_agent, \
             patch('backend.brokers.broker_system.KnowledgeAgent') as mock_knowledge_agent, \
             patch('builtins.print') as mock_print:
            
            # Make KnowledgeAgent initialization fail
            mock_math_agent.return_value = Mock()
            mock_knowledge_agent.side_effect = Exception("Knowledge agent init failed")
            
            broker = BrokerSystem()
            
            # Verify debug print statements were called (lines 66-67)
            mock_print.assert_any_call("DEBUG: Math agent initialized successfully")
            mock_print.assert_any_call("DEBUG: Failed to initialize knowledge agent: Knowledge agent init failed")
            
            # Verify knowledge agent is set to None
            assert broker.agents["knowledge"] is None
    
    @pytest.mark.asyncio
    async def test_redis_log_structured_event_failure(self):
        # Setup Redis log_structured_event to fail
        self.mock_redis.log_structured_event.side_effect = Exception("Redis log failed")
        
        # Setup successful agent response
        mock_response = {
            "text": "The answer is 5",
            "type": "math",
            "timestamp": datetime.now().isoformat()
        }
        self.mock_math_agent.process_query.return_value = mock_response
        
        with patch('builtins.print') as mock_print:
            message = {"text": "2 + 3"}
            result = await self.broker.process_message(message, "test_session")
            
            # Should still return successful response
            assert result["text"] == "The answer is 5"
            
            # Verify warning print was called (line 156-157)
            mock_print.assert_any_call("Warning: Failed to log to Redis streams: Redis log failed")
    
    @pytest.mark.asyncio
    async def test_redis_store_error_response_failure(self):
        # Setup agent to raise exception
        self.mock_math_agent.process_query.side_effect = Exception("Agent processing failed")
        
        # Setup Redis store_conversation_message to fail only for error response
        call_count = 0
        def store_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:  # Second call (error response storage)
                raise Exception("Redis store failed")
            return None
        
        self.mock_redis.store_conversation_message.side_effect = store_side_effect
        
        with patch('builtins.print') as mock_print:
            message = {"text": "2 + 3"}
            result = await self.broker.process_message(message, "test_session")
            
            # Should return error response
            assert result["text"] == "Sorry, I encountered an error processing your request."
            assert result["type"] == "error"
            
            # Verify warning print was called (line 175-176)
            mock_print.assert_any_call("Warning: Failed to store error response: Redis store failed")
    
    @pytest.mark.asyncio
    async def test_process_message_redis_warning_prints(self):
        # Setup Redis operations to fail for specific warnings
        self.mock_redis.store_conversation_message.side_effect = Exception("Redis store failed")
        self.mock_redis.get_cached_response.side_effect = Exception("Redis get failed")
        
        # Setup successful agent response
        mock_response = {
            "text": "The answer is 5",
            "type": "math",
            "timestamp": datetime.now().isoformat()
        }
        self.mock_math_agent.process_query.return_value = mock_response
        
        with patch('builtins.print') as mock_print:
            message = {"text": "2 + 3"}
            result = await self.broker.process_message(message, "test_session")
            
            # Should still return successful response despite Redis failures
            assert result["text"] == "The answer is 5"
            
            # Verify warning print statements were called (lines 76-78)
            mock_print.assert_any_call("Warning: Failed to store user message in Redis: Redis store failed")
            mock_print.assert_any_call("Warning: Failed to get cached response: Redis get failed")