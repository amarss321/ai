import os
import logging
import asyncio
import json
from typing import Optional
import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiService:
    """
    Service for generating AI responses using Google's Gemini API.
    """
    
    def __init__(self):
        """
        Initialize the Gemini service.
        """
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        self.session = None
        self.lock = asyncio.Lock()
        
        # Check if API key is available
        if not self.api_key:
            logger.warning("GEMINI_API_KEY environment variable not set. Gemini service will not work.")
    
    async def initialize(self):
        """
        Initialize the aiohttp session.
        """
        if self.session is None:
            self.session = aiohttp.ClientSession()
    
    async def generate_response(self, transcript: str) -> Optional[str]:
        """
        Generate an AI response based on meeting transcript.
        
        Args:
            transcript: The meeting transcript text
            
        Returns:
            AI-generated response or None if generation failed
        """
        if not self.api_key:
            logger.error("Cannot generate response: GEMINI_API_KEY not set")
            return None
        
        try:
            # Initialize session if not already done
            await self.initialize()
            
            # Prepare prompt for Gemini
            prompt = self._create_prompt(transcript)
            
            # Prepare request payload
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 1024,
                }
            }
            
            # Make API request
            url = f"{self.api_url}?key={self.api_key}"
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Extract response text
                    try:
                        response_text = result["candidates"][0]["content"]["parts"][0]["text"]
                        logger.info(f"Generated AI response: {response_text[:50]}...")
                        return response_text
                    except (KeyError, IndexError) as e:
                        logger.error(f"Error extracting response from Gemini API result: {str(e)}")
                        return None
                else:
                    error_text = await response.text()
                    logger.error(f"Gemini API error (status {response.status}): {error_text}")
                    return None
                
        except Exception as e:
            logger.error(f"Error in AI response generation: {str(e)}")
            return None
    
    def _create_prompt(self, transcript: str) -> str:
        """
        Create an effective prompt for Gemini based on the meeting transcript.
        
        Args:
            transcript: The meeting transcript text
            
        Returns:
            Formatted prompt for Gemini
        """
        return f"""
You are an AI Meeting Assistant that helps participants by providing helpful insights, summaries, and action items during meetings.

Below is a transcript from a portion of an ongoing meeting. Based on this transcript, provide:
1. A brief summary of the key points discussed (if applicable)
2. Any important questions that were raised
3. Action items that participants should follow up on
4. Any helpful resources or information related to the topics discussed

Keep your response concise, professional, and focused on the most valuable information.

Meeting Transcript:
{transcript}

Your response:
"""
    
    async def close(self):
        """
        Close the aiohttp session.
        """
        if self.session:
            await self.session.close()
            self.session = None
    
    def __del__(self):
        """
        Clean up resources when the service is destroyed.
        """
        if self.session:
            asyncio.create_task(self.close())