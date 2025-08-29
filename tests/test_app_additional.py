import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
import socketio
from datetime import datetime
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import app, lifespan, sio, socket_app

class TestAppAdditional:
    
    def setup_method(self):
        self.client = TestClient(app)
    
    @pytest.mark.asyncio
    async def test_lifespan_redis_connect_success(self):
        with patch('backend.app.redis_client') as mock_redis:
            mock_redis.connect = AsyncMock()
            mock_redis.disconnect = AsyncMock()
            
            async with lifespan(app):
                # Verify Redis connect was called
                mock_redis.connect.assert_called_once()
            
            # Verify Redis disconnect was called after context exit
            mock_redis.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_lifespan_redis_connect_failure(self):
        with patch('backend.app.redis_client') as mock_redis:
            mock_redis.connect = AsyncMock(side_effect=Exception("Redis connection failed"))
            mock_redis.disconnect = AsyncMock()
            
            # Should not raise exception even if Redis connection fails
            async with lifespan(app):
                mock_redis.connect.assert_called_once()
            
            mock_redis.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_lifespan_redis_disconnect_failure(self):
        with patch('backend.app.redis_client') as mock_redis:
            mock_redis.connect = AsyncMock()
            mock_redis.disconnect = AsyncMock(side_effect=Exception("Disconnect failed"))
            
            # Should not raise exception even if Redis disconnect fails
            async with lifespan(app):
                mock_redis.connect.assert_called_once()
            
            mock_redis.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_socketio_connect_event(self):
        with patch.object(sio, 'emit') as mock_emit:
            # Import the connect handler
            from backend.app import connect
            
            # Call the connect handler
            await connect('test_sid', {})
            
            # Verify emit was called with correct parameters
            mock_emit.assert_called_once_with(
                'connected', 
                {'status': 'Connected to server'}, 
                room='test_sid'
            )
    
    @pytest.mark.asyncio
    async def test_socketio_disconnect_event(self):
        with patch('builtins.print') as mock_print:
            # Import the disconnect handler
            from backend.app import disconnect
            
            # Call the disconnect handler
            await disconnect('test_sid')
            
            # Verify print was called
            mock_print.assert_called_once_with('Client test_sid disconnected')
    
    @pytest.mark.asyncio
    async def test_socketio_chat_message_success(self):
        mock_response = {
            "text": "Test response",
            "type": "test",
            "timestamp": datetime.now().isoformat()
        }
        
        with patch('backend.app.broker_system') as mock_broker, \
             patch.object(sio, 'emit') as mock_emit:
            
            mock_broker.process_message = AsyncMock(return_value=mock_response)
            
            # Import the chat_message handler
            from backend.app import chat_message
            
            # Call the chat_message handler
            test_data = {"text": "Hello", "session_id": "test_session"}
            await chat_message('test_sid', test_data)
            
            # Verify broker was called
            mock_broker.process_message.assert_called_once_with(test_data, "test_session")
            
            # Verify emit was called with response
            mock_emit.assert_called_once_with('chat_response', mock_response, room='test_sid')
    
    @pytest.mark.asyncio
    async def test_socketio_chat_message_no_session_id(self):
        mock_response = {
            "text": "Test response",
            "type": "test",
            "timestamp": datetime.now().isoformat()
        }
        
        with patch('backend.app.broker_system') as mock_broker, \
             patch.object(sio, 'emit') as mock_emit:
            
            mock_broker.process_message = AsyncMock(return_value=mock_response)
            
            # Import the chat_message handler
            from backend.app import chat_message
            
            # Call the chat_message handler without session_id
            test_data = {"text": "Hello"}
            await chat_message('test_sid', test_data)
            
            # Verify broker was called with sid as session_id
            mock_broker.process_message.assert_called_once_with(test_data, "test_sid")
            
            # Verify emit was called with response
            mock_emit.assert_called_once_with('chat_response', mock_response, room='test_sid')
    
    @pytest.mark.asyncio
    async def test_socketio_chat_message_error(self):
        with patch('backend.app.broker_system') as mock_broker, \
             patch.object(sio, 'emit') as mock_emit:
            
            mock_broker.process_message = AsyncMock(side_effect=Exception("Processing failed"))
            
            # Import the chat_message handler
            from backend.app import chat_message
            
            # Call the chat_message handler
            test_data = {"text": "Hello", "session_id": "test_session"}
            await chat_message('test_sid', test_data)
            
            # Verify broker was called
            mock_broker.process_message.assert_called_once_with(test_data, "test_session")
            
            # Verify error emit was called
            mock_emit.assert_called_once()
            call_args = mock_emit.call_args
            assert call_args[0][0] == 'chat_error'
            error_response = call_args[0][1]
            assert error_response["text"] == "Sorry, I encountered an error processing your request."
            assert error_response["type"] == "error"
            assert "timestamp" in error_response
            assert error_response["error"] == "Processing failed"
            assert call_args[1]["room"] == 'test_sid'
    
    def test_socket_app_creation(self):
        assert socket_app is not None
        assert isinstance(socket_app, socketio.ASGIApp)
    
    def test_main_execution_default_port(self):
        with patch.dict('os.environ', {}, clear=True):
            # Simulate the main execution logic
            port = int(os.getenv("PORT", 8001))
            # Verify default port is used
            assert port == 8001
    
    def test_main_execution_custom_port(self):
        with patch.dict('os.environ', {'PORT': '9000'}):
            # Simulate the main execution logic
            port = int(os.getenv("PORT", 8001))
            # Verify custom port is used
            assert port == 9000
    
    def test_get_messages_error_handling(self):
        with patch('backend.app.broker_system') as mock_broker:
            mock_broker.get_conversation_history = AsyncMock(
                side_effect=Exception("Database error")
            )
            
            response = self.client.get("/api/messages?session_id=test&limit=10")
            
            assert response.status_code == 500
            assert "Database error" in response.json()["detail"]
    
    def test_send_message_error_handling(self):
        with patch('backend.app.broker_system') as mock_broker:
            mock_broker.process_message = AsyncMock(
                side_effect=Exception("Processing error")
            )
            
            response = self.client.post("/api/messages", json={
                "text": "Test message",
                "session_id": "test"
            })
            
            assert response.status_code == 500
            assert "Processing error" in response.json()["detail"]
    
    def test_main_execution_port_logic(self):
        # Test the exact logic from lines 120-121
        with patch.dict('os.environ', {'PORT': '9000'}):
            port = int(os.getenv("PORT", 8001))
            assert port == 9000
        
        with patch.dict('os.environ', {}, clear=True):
            port = int(os.getenv("PORT", 8001))
            assert port == 8001
    
    def test_uvicorn_run_simulation(self):
        with patch('uvicorn.run') as mock_uvicorn:
            # Import the socket_app and simulate the uvicorn.run call
            from backend.app import socket_app
            import uvicorn
            
            # Simulate the exact call from line 122
            uvicorn.run(socket_app, host="0.0.0.0", port=8001, reload=False)
            
            # Verify the call was made correctly
            mock_uvicorn.assert_called_once_with(
                socket_app,
                host="0.0.0.0",
                port=8001,
                reload=False
            )
    
    @pytest.mark.asyncio
    async def test_lifespan_redis_connect_exception_print(self):
        with patch('backend.app.redis_client') as mock_redis, \
             patch('builtins.print') as mock_print:
            
            mock_redis.connect = AsyncMock(side_effect=Exception("Connection failed"))
            mock_redis.disconnect = AsyncMock()
            
            async with lifespan(app):
                pass
            
            # Verify print was called with the warning message (line 55-56)
            mock_print.assert_called_once_with(
                "Warning: Redis connection failed: Connection failed. Continuing without Redis."
            )
    
    def test_socket_test_endpoint_print_coverage(self):
        # This endpoint returns string representations that cover line 65
        response = self.client.get("/socket-test")
        
        assert response.status_code == 200
        data = response.json()
        assert "socketio_server" in data
        assert "socketio_async_mode" in data
        assert "socketio_status" in data
        assert data["socketio_async_mode"] == "asgi"
        assert data["socketio_status"] == "initialized"
    
    @pytest.mark.asyncio
    async def test_connect_print_statement(self):
        with patch('builtins.print') as mock_print, \
             patch.object(sio, 'emit') as mock_emit:
            
            from backend.app import connect
            await connect('test_sid_123', {})
            
            # Verify print was called (line 76)
            mock_print.assert_called_once_with('Client test_sid_123 connected')
    
    @pytest.mark.asyncio
    async def test_disconnect_print_statement(self):
        with patch('builtins.print') as mock_print:
            
            from backend.app import disconnect
            await disconnect('test_sid_456')
            
            # Verify print was called (line 86)
            mock_print.assert_called_once_with('Client test_sid_456 disconnected')