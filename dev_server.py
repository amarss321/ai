import os
import sys
import uuid
import json
import logging
from datetime import datetime
from typing import Dict

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="AI Meeting Assistant (Development)")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="frontend/templates")

# Active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

# Active sessions
active_sessions: Dict[str, Dict] = {}

# Routes
@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = None
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message_type = data.get("type")
            logger.info(f"Received message: {message_type}")
            
            # Handle different message types
            if message_type == "create_session":
                # Create new session
                session_id = str(uuid.uuid4())
                active_connections[session_id] = websocket
                active_sessions[session_id] = {
                    "created_at": datetime.now(),
                    "settings": None,
                    "is_capturing": False,
                }
                
                # Send session ID back to client
                await websocket.send_json({
                    "type": "session_created",
                    "sessionId": session_id
                })
                logger.info(f"Created session: {session_id}")
                
            elif message_type == "reconnect_session":
                # Reconnect to existing session
                session_id = data.get("sessionId")
                if session_id in active_sessions:
                    active_connections[session_id] = websocket
                    await websocket.send_json({
                        "type": "session_reconnected",
                        "sessionId": session_id
                    })
                    logger.info(f"Reconnected to session: {session_id}")
                else:
                    # Session not found, create new one
                    session_id = str(uuid.uuid4())
                    active_connections[session_id] = websocket
                    active_sessions[session_id] = {
                        "created_at": datetime.now(),
                        "settings": None,
                        "is_capturing": False,
                    }
                    
                    await websocket.send_json({
                        "type": "session_created",
                        "sessionId": session_id
                    })
                    logger.info(f"Created new session (reconnect failed): {session_id}")
            
            elif message_type == "update_settings":
                # Update session settings
                if not session_id:
                    session_id = data.get("sessionId")
                
                if session_id in active_sessions:
                    settings = data.get("settings")
                    active_sessions[session_id]["settings"] = settings
                    logger.info(f"Updated settings for session: {session_id}")
                
            elif message_type == "capture_started":
                # Mark session as capturing
                if not session_id:
                    session_id = data.get("sessionId")
                
                if session_id in active_sessions:
                    active_sessions[session_id]["is_capturing"] = True
                    logger.info(f"Capture started for session: {session_id}")
            
            elif message_type == "capture_stopped":
                # Mark session as not capturing
                if not session_id:
                    session_id = data.get("sessionId")
                
                if session_id in active_sessions:
                    active_sessions[session_id]["is_capturing"] = False
                    logger.info(f"Capture stopped for session: {session_id}")
            
            elif message_type == "audio_data":
                # Process audio data (mock implementation)
                if not session_id:
                    session_id = data.get("sessionId")
                
                if session_id in active_sessions and active_sessions[session_id]["is_capturing"]:
                    # In development mode, we'll just send a mock AI response
                    await websocket.send_json({
                        "type": "ai_response",
                        "response": "This is a mock AI response for development. In production, this would be generated by Gemini API based on the audio transcript.",
                        "timestamp": datetime.now().isoformat()
                    })
                    logger.info(f"Sent mock AI response for session: {session_id}")
            
            elif message_type == "screen_capture":
                # Process screen capture data (mock implementation)
                logger.info("Received screen capture data (not processed in development mode)")
            
            else:
                # Unknown message type
                await websocket.send_json({
                    "type": "error",
                    "error": f"Unknown message type: {message_type}"
                })
                logger.warning(f"Unknown message type: {message_type}")
    
    except WebSocketDisconnect:
        # Handle disconnection
        if session_id and session_id in active_connections:
            del active_connections[session_id]
            logger.info(f"Client disconnected: {session_id}")
    
    except Exception as e:
        # Handle other exceptions
        logger.error(f"WebSocket error: {str(e)}")
        if session_id and session_id in active_connections:
            del active_connections[session_id]

# Run the application
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 12000))  # Use the port from RUNTIME_INFORMATION
    uvicorn.run("dev_server:app", host="0.0.0.0", port=port, reload=True)