import os
import logging
import uuid
from typing import Dict, List, Optional
from datetime import datetime

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Import services
from services.speech_to_text.whisper_service import WhisperService
from services.ai_processing.gemini_service import GeminiService
from services.notification.sns_service import SNSService
from models.database import init_db, get_db, SessionLocal
from models.schemas import Session, Response, Transcript

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="AI Meeting Assistant")

# Mount static files
app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="../frontend/templates")

# Initialize services
whisper_service = WhisperService()
gemini_service = GeminiService()
sns_service = SNSService()

# Active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

# Active sessions
active_sessions: Dict[str, Dict] = {}


# Models
class Settings(BaseModel):
    phoneNumber: str
    aiResponseFrequency: int
    sendMobileNotifications: bool


# Initialize database
@app.on_event("startup")
async def startup_event():
    init_db()


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    # Close any active connections
    pass


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
                
                # Store session in database
                db = SessionLocal()
                try:
                    db_session = Session(
                        id=session_id,
                        created_at=datetime.now(),
                        is_active=True
                    )
                    db.add(db_session)
                    db.commit()
                finally:
                    db.close()
                
                # Send session ID back to client
                await websocket.send_json({
                    "type": "session_created",
                    "sessionId": session_id
                })
                
            elif message_type == "reconnect_session":
                # Reconnect to existing session
                session_id = data.get("sessionId")
                if session_id in active_sessions:
                    active_connections[session_id] = websocket
                    await websocket.send_json({
                        "type": "session_reconnected",
                        "sessionId": session_id
                    })
                else:
                    # Session not found, create new one
                    session_id = str(uuid.uuid4())
                    active_connections[session_id] = websocket
                    active_sessions[session_id] = {
                        "created_at": datetime.now(),
                        "settings": None,
                        "is_capturing": False,
                    }
                    
                    # Store session in database
                    db = SessionLocal()
                    try:
                        db_session = Session(
                            id=session_id,
                            created_at=datetime.now(),
                            is_active=True
                        )
                        db.add(db_session)
                        db.commit()
                    finally:
                        db.close()
                    
                    await websocket.send_json({
                        "type": "session_created",
                        "sessionId": session_id
                    })
            
            elif message_type == "update_settings":
                # Update session settings
                if not session_id:
                    session_id = data.get("sessionId")
                
                if session_id in active_sessions:
                    settings = data.get("settings")
                    active_sessions[session_id]["settings"] = settings
                    
                    # Update phone number for SNS if needed
                    if settings.get("sendMobileNotifications") and settings.get("phoneNumber"):
                        sns_service.register_phone_number(settings["phoneNumber"])
                
            elif message_type == "capture_started":
                # Mark session as capturing
                if not session_id:
                    session_id = data.get("sessionId")
                
                if session_id in active_sessions:
                    active_sessions[session_id]["is_capturing"] = True
            
            elif message_type == "capture_stopped":
                # Mark session as not capturing
                if not session_id:
                    session_id = data.get("sessionId")
                
                if session_id in active_sessions:
                    active_sessions[session_id]["is_capturing"] = False
            
            elif message_type == "audio_data":
                # Process audio data
                if not session_id:
                    session_id = data.get("sessionId")
                
                if session_id in active_sessions and active_sessions[session_id]["is_capturing"]:
                    audio_data = data.get("data")
                    sample_rate = data.get("sampleRate", 44100)
                    
                    # Process audio with Whisper
                    transcript = await whisper_service.process_audio(audio_data, sample_rate)
                    
                    if transcript:
                        # Store transcript in database
                        db = SessionLocal()
                        try:
                            db_transcript = Transcript(
                                session_id=session_id,
                                text=transcript,
                                timestamp=datetime.now()
                            )
                            db.add(db_transcript)
                            db.commit()
                            
                            # Get transcript ID
                            transcript_id = db_transcript.id
                        finally:
                            db.close()
                        
                        # Generate AI response
                        ai_response = await gemini_service.generate_response(transcript)
                        
                        if ai_response:
                            # Store response in database
                            db = SessionLocal()
                            try:
                                db_response = Response(
                                    session_id=session_id,
                                    transcript_id=transcript_id,
                                    text=ai_response,
                                    timestamp=datetime.now()
                                )
                                db.add(db_response)
                                db.commit()
                            finally:
                                db.close()
                            
                            # Send response to client
                            await websocket.send_json({
                                "type": "ai_response",
                                "response": ai_response,
                                "timestamp": datetime.now().isoformat()
                            })
                            
                            # Send notification if enabled
                            settings = active_sessions[session_id].get("settings")
                            if settings and settings.get("sendMobileNotifications") and settings.get("phoneNumber"):
                                sns_service.send_notification(
                                    phone_number=settings["phoneNumber"],
                                    message=f"Meeting Assistant: {ai_response}"
                                )
            
            elif message_type == "screen_capture":
                # Process screen capture data
                # This is a placeholder - in a real implementation, you might
                # want to save screenshots or process them for visual context
                pass
            
            else:
                # Unknown message type
                await websocket.send_json({
                    "type": "error",
                    "error": f"Unknown message type: {message_type}"
                })
    
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
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)