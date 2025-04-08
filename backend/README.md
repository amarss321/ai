# Backend

This directory contains the backend code for the AI Meeting Assistant application.

## Structure

- `api/`: API endpoints
- `models/`: Database models and schemas
- `services/`: Service modules for different functionalities
  - `speech_to_text/`: Speech-to-text conversion using Whisper AI
  - `ai_processing/`: AI response generation using Gemini API
  - `notification/`: Mobile notification using Amazon SNS
- `utils/`: Utility functions and helpers

## Technologies

- Python with FastAPI
- WebSockets for real-time communication
- MongoDB for data storage
- RabbitMQ for task management