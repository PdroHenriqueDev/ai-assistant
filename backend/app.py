from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import socketio
import uvicorn
import json
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, List, Optional, Any


from backend.brokers.broker_system import BrokerSystem
from backend.database.mongodb import get_database, save_message, get_messages
from backend.database.redis_client import redis_client

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await redis_client.connect()
    except Exception as e:
        print(f"Warning: Redis connection failed: {e}. Continuing without Redis.")
    yield
    try:
        await redis_client.disconnect()
    except Exception:
        pass

app = FastAPI(title="Knowledge & Math Assistant API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

broker_system = BrokerSystem()

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True
)

@app.get("/health")
async def health_check():
    redis_stats = await redis_client.get_system_stats()
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "redis": redis_stats
    }

@app.get("/socket-test")
async def socket_test():
    return {
        "socketio_server": str(type(sio)),
        "socketio_async_mode": sio.async_mode,
        "socketio_status": "initialized"
    }

@app.get("/api/messages")
async def get_chat_messages(session_id: str = "default", limit: int = 50):
    try:
        messages = await broker_system.get_conversation_history(session_id, limit)
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/messages")
async def send_message(message: Dict[str, Any]):
    try:
        session_id = message.get("session_id", "default")
        response = await broker_system.process_message(message, session_id)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@sio.event
async def connect(sid, environ):
    print(f"Client {sid} connected")
    await sio.emit('connected', {'status': 'Connected to server'}, room=sid)

@sio.event
async def disconnect(sid):
    print(f"Client {sid} disconnected")

@sio.event
async def chat_message(sid, data):
    try:
        session_id = data.get("session_id", sid)
        response = await broker_system.process_message(data, session_id)
        await sio.emit('chat_response', response, room=sid)
    except Exception as e:
        error_response = {
            "text": "Sorry, I encountered an error processing your request.",
            "type": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
        await sio.emit('chat_error', error_response, room=sid)

socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))

    uvicorn.run(socket_app, host="0.0.0.0", port=port, reload=False)