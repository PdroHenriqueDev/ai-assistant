import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "weather_chatbot")

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

async def get_database():
    return db

async def save_message(message: Dict[str, Any], sender: str) -> Dict[str, Any]:
    if "timestamp" not in message:
        message["timestamp"] = datetime.now().isoformat()
    
    message["sender"] = sender
    
    result = await db.messages.insert_one(message)
    
    message["_id"] = str(result.inserted_id)
    return message

async def get_messages(limit: int = 50) -> List[Dict[str, Any]]:
    cursor = db.messages.find().sort("timestamp", -1).limit(limit)
    messages = []
    
    async for document in cursor:
        document["_id"] = str(document["_id"])
        messages.append(document)
    
    return list(reversed(messages))

async def delete_messages():
    await db.messages.delete_many({})
    return {"deleted": True}