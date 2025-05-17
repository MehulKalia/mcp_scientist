from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from typing import Dict, List
import uuid
import logging
from api.agent import ProteinDiscoveryAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections and their agents
active_connections: Dict[str, WebSocket] = {}
active_agents: Dict[str, ProteinDiscoveryAgent] = {}
user_requests: Dict[str, str] = {}  # Store user requests by request_id

@app.post("/api/chat/request")
async def submit_request(request: dict):
    logger.info(f"Received new chat request: {request}")
    request_id = str(uuid.uuid4())
    logger.info(f"Generated request ID: {request_id}")
    
    # Store the user's request
    user_requests[request_id] = request.get("task", "")
    
    return {"requestId": request_id, "status": "pending"}

@app.websocket("/api/chat/stream/{request_id}")
async def stream_updates(websocket: WebSocket, request_id: str):
    logger.info(f"New WebSocket connection request for request_id: {request_id}")
    await websocket.accept()
    logger.info(f"WebSocket connection accepted for request_id: {request_id}")
    
    active_connections[request_id] = websocket
    active_agents[request_id] = ProteinDiscoveryAgent()
    logger.info(f"Active connections count: {len(active_connections)}")
    
    try:
        # Get the agent for this request
        agent = active_agents[request_id]
        
        # Get the user's request
        user_request = user_requests.get(request_id, "")
        logger.info(f"Processing request: {user_request}")
        
        # Process the request and stream updates
        async for update in agent.process_request(user_request):
            logger.info(f"Sending update for request_id: {request_id}")
            logger.info(f"Update content: {update}")
            await websocket.send_json(update)
            
    except Exception as e:
        logger.error(f"Error in WebSocket connection for request_id {request_id}: {str(e)}")
    finally:
        if request_id in active_connections:
            logger.info(f"Cleaning up WebSocket connection for request_id: {request_id}")
            del active_connections[request_id]
            del active_agents[request_id]
            if request_id in user_requests:
                del user_requests[request_id]
            logger.info(f"Remaining active connections: {len(active_connections)}")
        await websocket.close()
        logger.info(f"WebSocket connection closed for request_id: {request_id}")

@app.get("/api/protein/{request_id}")
async def get_protein_data(request_id: str):
    logger.info(f"Received request for protein data with request_id: {request_id}")
    
    # Get the agent for this request
    agent = active_agents.get(request_id)
    if not agent:
        # If no agent exists (e.g., request completed), create a new one
        agent = ProteinDiscoveryAgent()
    
    protein_data = agent.generate_protein_data()
    logger.info(f"Returning protein data for request_id: {request_id}")
    return protein_data

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000) 