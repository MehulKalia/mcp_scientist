# Protein Discovery API

This is the backend API for the Protein Discovery application. It provides real-time communication with the frontend using WebSocket and handles protein analysis requests.

## Setup

1. Create a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the API

Start the server:

```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### POST /api/chat/request

Submit a new protein analysis request.

### WebSocket /api/chat/stream/{request_id}

Stream real-time updates from the agent.

### GET /api/protein/{request_id}

Get protein visualization data.

## Development

The API is built with:

- FastAPI
- WebSocket for real-time communication
- CORS enabled for frontend communication
