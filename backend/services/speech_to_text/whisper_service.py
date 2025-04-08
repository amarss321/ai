import os
import logging
import numpy as np
import tempfile
import asyncio
from typing import List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhisperService:
    """
    Service for speech-to-text conversion using OpenAI's Whisper model.
    """
    
    def __init__(self):
        """
        Initialize the Whisper service.
        """
        self.model = None
        self.initialized = False
        self.lock = asyncio.Lock()
    
    async def initialize(self):
        """
        Initialize the Whisper model.
        """
        if self.initialized:
            return
        
        async with self.lock:
            if self.initialized:
                return
            
            try:
                import whisper
                # Load the model (choose size based on your needs: tiny, base, small, medium, large)
                model_size = os.environ.get("WHISPER_MODEL_SIZE", "base")
                logger.info(f"Loading Whisper model: {model_size}")
                self.model = whisper.load_model(model_size)
                self.initialized = True
                logger.info("Whisper model loaded successfully")
            except Exception as e:
                logger.error(f"Error initializing Whisper model: {str(e)}")
                raise
    
    async def process_audio(self, audio_data: List[int], sample_rate: int = 44100) -> Optional[str]:
        """
        Process audio data and convert to text.
        
        Args:
            audio_data: List of audio samples (16-bit PCM)
            sample_rate: Sample rate of the audio
            
        Returns:
            Transcribed text or None if transcription failed
        """
        try:
            # Initialize model if not already done
            if not self.initialized:
                await self.initialize()
            
            # Convert audio data to numpy array
            audio_np = np.array(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as temp_file:
                import soundfile as sf
                sf.write(temp_file.name, audio_np, sample_rate)
                
                # Run transcription in a separate thread to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, 
                    lambda: self.model.transcribe(temp_file.name)
                )
                
                # Extract text from result
                transcription = result["text"].strip()
                
                if transcription:
                    logger.info(f"Transcription successful: {transcription[:50]}...")
                    return transcription
                else:
                    logger.warning("Transcription returned empty result")
                    return None
                
        except Exception as e:
            logger.error(f"Error in speech-to-text processing: {str(e)}")
            return None
    
    def __del__(self):
        """
        Clean up resources when the service is destroyed.
        """
        # No specific cleanup needed for Whisper
        pass