# AI Meeting Assistant

An end-to-end application that captures screen sharing and audio from video calls, generates helpful responses based on the conversation, and sends these to users' mobile phones.

## Features

- Screen and audio capture from video calls (Teams, Google Meet)
- Real-time speech-to-text conversion
- AI-powered response generation using Google's Gemini API
- Web interface for viewing responses
- Mobile notifications via Amazon SNS
- Secure data handling and storage

## Technology Stack

- **Frontend**: HTML/CSS/JavaScript with WebRTC for screen/audio capture
- **Backend**: Python with FastAPI
- **Speech-to-Text**: Whisper AI (open source)
- **AI Integration**: Google's Gemini API
- **Mobile Notifications**: Amazon SNS (Simple Notification Service)
- **Database**: MongoDB for storing transcripts and responses
- **Message Queue**: RabbitMQ for task management
- **Containerization**: Docker for all components

## Getting Started

### Prerequisites

- Docker and Docker Compose
- AWS account for SNS
- Google API key for Gemini

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ai-meeting-assistant.git
   cd ai-meeting-assistant
   ```

2. Configure environment variables in `.env` file:
   ```
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Start the application:
   ```
   docker-compose up -d
   ```

4. Access the web interface at `http://localhost:8000`

## Architecture

The application follows a microservices architecture with the following components:

1. **Web Interface**: Provides UI for starting/stopping capture and viewing responses
2. **Capture Service**: Handles screen and audio capture using WebRTC
3. **Speech-to-Text Service**: Converts audio to text using Whisper AI
4. **AI Processing Service**: Generates responses using Gemini API
5. **Notification Service**: Sends responses to mobile devices using Amazon SNS
6. **Storage Service**: Stores transcripts and responses in MongoDB

## License

MIT