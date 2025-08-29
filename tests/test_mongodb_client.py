import pytest
import os
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from backend.database.mongodb import (
    get_database,
    save_message,
    get_messages,
    delete_messages,
    client,
    db
)


class TestMongoDBClient:
    
    def setup_method(self):
        # Mock the database and collection
        self.mock_db = Mock()
        self.mock_collection = Mock()
        self.mock_db.messages = self.mock_collection
        
    @pytest.mark.asyncio
    async def test_get_database(self):
        result = await get_database()
        assert result is not None
        # Should return the same db instance
        assert result == db
    
    @pytest.mark.asyncio
    async def test_save_message_with_timestamp(self):
        with patch('backend.database.mongodb.db', self.mock_db):
            # Mock insert_one result
            mock_result = Mock()
            mock_result.inserted_id = "507f1f77bcf86cd799439011"
            self.mock_collection.insert_one = AsyncMock(return_value=mock_result)
            
            message = {
                "text": "Test message",
                "timestamp": "2024-01-15T10:30:00"
            }
            sender = "user"
            
            result = await save_message(message, sender)
            
            # Verify the message was modified correctly
            assert result["text"] == "Test message"
            assert result["timestamp"] == "2024-01-15T10:30:00"
            assert result["sender"] == "user"
            assert result["_id"] == "507f1f77bcf86cd799439011"
            
            # Verify insert_one was called
            self.mock_collection.insert_one.assert_called_once()
            call_args = self.mock_collection.insert_one.call_args[0][0]
            assert call_args["sender"] == "user"
    
    @pytest.mark.asyncio
    async def test_save_message_without_timestamp(self):
        with patch('backend.database.mongodb.db', self.mock_db):
            # Mock insert_one result
            mock_result = Mock()
            mock_result.inserted_id = "507f1f77bcf86cd799439012"
            self.mock_collection.insert_one = AsyncMock(return_value=mock_result)
            
            message = {"text": "Test message without timestamp"}
            sender = "assistant"
            
            with patch('backend.database.mongodb.datetime') as mock_datetime:
                mock_now = Mock()
                mock_now.isoformat.return_value = "2024-01-15T11:00:00"
                mock_datetime.now.return_value = mock_now
                
                result = await save_message(message, sender)
                
                # Verify timestamp was added
                assert result["timestamp"] == "2024-01-15T11:00:00"
                assert result["sender"] == "assistant"
                assert result["_id"] == "507f1f77bcf86cd799439012"
                
                # Verify datetime.now was called
                mock_datetime.now.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_message_modifies_original(self):
        with patch('backend.database.mongodb.db', self.mock_db):
            mock_result = Mock()
            mock_result.inserted_id = "507f1f77bcf86cd799439013"
            self.mock_collection.insert_one = AsyncMock(return_value=mock_result)
            
            original_message = {"text": "Original message"}
            sender = "user"
            
            result = await save_message(original_message, sender)
            
            # Both original and result should have the same modifications
            assert original_message["sender"] == "user"
            assert original_message["_id"] == "507f1f77bcf86cd799439013"
            assert "timestamp" in original_message
            assert result is original_message  # Should be the same object
    
    @pytest.mark.asyncio
    async def test_get_messages_default_limit(self):
        with patch('backend.database.mongodb.db', self.mock_db):
            # Mock cursor and documents
            mock_doc1 = {"_id": "id1", "text": "Message 1", "timestamp": "2024-01-15T10:00:00"}
            mock_doc2 = {"_id": "id2", "text": "Message 2", "timestamp": "2024-01-15T11:00:00"}
            
            # Create async iterator mock
            class AsyncIterator:
                def __init__(self, items):
                    self.items = items
                    self.index = 0
                
                def __aiter__(self):
                    return self
                
                async def __anext__(self):
                    if self.index >= len(self.items):
                        raise StopAsyncIteration
                    item = self.items[self.index]
                    self.index += 1
                    return item
            
            mock_cursor = Mock()
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.limit.return_value = mock_cursor
            mock_cursor.__aiter__ = lambda self: AsyncIterator([mock_doc1, mock_doc2])
            
            self.mock_collection.find.return_value = mock_cursor
            
            result = await get_messages()
            
            # Verify the query was constructed correctly
            self.mock_collection.find.assert_called_once_with()
            mock_cursor.sort.assert_called_once_with("timestamp", -1)
            mock_cursor.limit.assert_called_once_with(50)  # Default limit
            
            # Verify results are reversed and _id is converted to string
            assert len(result) == 2
            assert result[0]["_id"] == "id2"  # Should be reversed order
            assert result[1]["_id"] == "id1"
            assert result[0]["text"] == "Message 2"
            assert result[1]["text"] == "Message 1"
    
    @pytest.mark.asyncio
    async def test_get_messages_custom_limit(self):
        with patch('backend.database.mongodb.db', self.mock_db):
            # Create empty async iterator
            class AsyncIterator:
                def __aiter__(self):
                    return self
                
                async def __anext__(self):
                    raise StopAsyncIteration
            
            mock_cursor = Mock()
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.limit.return_value = mock_cursor
            mock_cursor.__aiter__ = lambda self: AsyncIterator()
            
            self.mock_collection.find.return_value = mock_cursor
            
            result = await get_messages(limit=10)
            
            # Verify custom limit was used
            mock_cursor.limit.assert_called_once_with(10)
            assert result == []
    
    @pytest.mark.asyncio
    async def test_get_messages_empty_result(self):
        with patch('backend.database.mongodb.db', self.mock_db):
            # Create empty async iterator
            class AsyncIterator:
                def __aiter__(self):
                    return self
                
                async def __anext__(self):
                    raise StopAsyncIteration
            
            mock_cursor = Mock()
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.limit.return_value = mock_cursor
            mock_cursor.__aiter__ = lambda self: AsyncIterator()
            
            self.mock_collection.find.return_value = mock_cursor
            
            result = await get_messages()
            
            assert result == []
    
    @pytest.mark.asyncio
    async def test_get_messages_single_message(self):
        with patch('backend.database.mongodb.db', self.mock_db):
            mock_doc = {"_id": "single_id", "text": "Single message"}
            
            # Create async iterator with single document
            class AsyncIterator:
                def __init__(self, items):
                    self.items = items
                    self.index = 0
                
                def __aiter__(self):
                    return self
                
                async def __anext__(self):
                    if self.index >= len(self.items):
                        raise StopAsyncIteration
                    item = self.items[self.index]
                    self.index += 1
                    return item
            
            mock_cursor = Mock()
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.limit.return_value = mock_cursor
            mock_cursor.__aiter__ = lambda self: AsyncIterator([mock_doc])
            
            self.mock_collection.find.return_value = mock_cursor
            
            result = await get_messages()
            
            assert len(result) == 1
            assert result[0]["_id"] == "single_id"
            assert result[0]["text"] == "Single message"
    
    @pytest.mark.asyncio
    async def test_get_messages_order_reversal(self):
        with patch('backend.database.mongodb.db', self.mock_db):
            # Messages in descending order (newest first from DB)
            mock_doc1 = {"_id": "newest", "text": "Newest message", "timestamp": "2024-01-15T12:00:00"}
            mock_doc2 = {"_id": "middle", "text": "Middle message", "timestamp": "2024-01-15T11:00:00"}
            mock_doc3 = {"_id": "oldest", "text": "Oldest message", "timestamp": "2024-01-15T10:00:00"}
            
            # Create async iterator with multiple documents
            class AsyncIterator:
                def __init__(self, items):
                    self.items = items
                    self.index = 0
                
                def __aiter__(self):
                    return self
                
                async def __anext__(self):
                    if self.index >= len(self.items):
                        raise StopAsyncIteration
                    item = self.items[self.index]
                    self.index += 1
                    return item
            
            mock_cursor = Mock()
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.limit.return_value = mock_cursor
            mock_cursor.__aiter__ = lambda self: AsyncIterator([mock_doc1, mock_doc2, mock_doc3])
            
            self.mock_collection.find.return_value = mock_cursor
            
            result = await get_messages()
            
            # Should be reversed to chronological order (oldest first)
            assert len(result) == 3
            assert result[0]["_id"] == "oldest"
            assert result[1]["_id"] == "middle"
            assert result[2]["_id"] == "newest"
    
    @pytest.mark.asyncio
    async def test_delete_messages_success(self):
        with patch('backend.database.mongodb.db', self.mock_db):
            # Mock delete_many result
            mock_result = Mock()
            mock_result.deleted_count = 5
            self.mock_collection.delete_many = AsyncMock(return_value=mock_result)
            
            result = await delete_messages()
            
            # Verify delete_many was called with empty filter (delete all)
            self.mock_collection.delete_many.assert_called_once_with({})
            
            # Verify return value
            assert result == {"deleted": True}
    
    @pytest.mark.asyncio
    async def test_delete_messages_no_documents(self):
        with patch('backend.database.mongodb.db', self.mock_db):
            mock_result = Mock()
            mock_result.deleted_count = 0
            self.mock_collection.delete_many = AsyncMock(return_value=mock_result)
            
            result = await delete_messages()
            
            self.mock_collection.delete_many.assert_called_once_with({})
            assert result == {"deleted": True}
    
    def test_module_level_variables(self):
        # Test that client and db are initialized
        assert client is not None
        assert db is not None
        
        # Test environment variable defaults
        with patch.dict(os.environ, {}, clear=True):
            # Re-import to test defaults
            import importlib
            import backend.database.mongodb as mongodb_module
            importlib.reload(mongodb_module)
            
            # Should use default values when env vars are not set
            # Note: In Docker environment, it might be mongodb://mongo:27017
            assert "mongodb://" in str(mongodb_module.MONGO_URI)
            assert "27017" in str(mongodb_module.MONGO_URI)
            # Check if it's the default value (could be weather_chatbot or knowledge_math_chatbot)
            assert mongodb_module.DB_NAME in ["weather_chatbot", "knowledge_math_chatbot"]
    
    def test_environment_variable_loading(self):
        with patch.dict(os.environ, {
            'MONGO_URI': 'mongodb://test:27017',
            'DB_NAME': 'test_database'
        }):
            # Re-import to test custom env vars
            import importlib
            import backend.database.mongodb as mongodb_module
            importlib.reload(mongodb_module)
            
            assert mongodb_module.MONGO_URI == 'mongodb://test:27017'
            assert mongodb_module.DB_NAME == 'test_database'