# Docker Configuration

This directory contains Docker configuration files for containerizing the AI Meeting Assistant application.

## Structure

- `frontend/`: Docker configuration for the frontend service
- `backend/`: Docker configuration for the backend service
- `mongodb/`: Docker configuration for the MongoDB service
- `rabbitmq/`: Docker configuration for the RabbitMQ service

## Usage

To build and run the application using Docker Compose:

```bash
docker-compose up -d
```

This will start all services defined in the `docker-compose.yml` file.