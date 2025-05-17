from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import json
import uuid
import logging
import sys
from datetime import datetime
from agent import ProteinDesignAgent, APIKeyError, PredictionError

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'api_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

# Log startup
logger.info("Initializing FastAPI application...")

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("CORS middleware configured")

# Store active WebSocket connections and their agents
active_connections: Dict[str, WebSocket] = {}
active_agents: Dict[str, ProteinDesignAgent] = {}
user_requests: Dict[str, str] = {}  # Store user requests by request_id

# Store active agents and their configurations
agent_configs: Dict[str, Dict[str, Any]] = {}

logger.info("Global state initialized")

class ChatRequest(BaseModel):
    task: str
    config: Optional[Dict[str, Any]] = None

class AgentConfig(BaseModel):
    maxIterations: int

@app.post("/api/chat/request")
async def submit_request(request: ChatRequest):
    """Submit a new protein design request"""
    try:
        logger.info(f"Received new chat request: {request}")
        request_id = str(uuid.uuid4())
        logger.info(f"Generated request ID: {request_id}")
        
        # Initialize agent with provided config or default
        logger.debug("Initializing new ProteinDesignAgent")
        agent = ProteinDesignAgent()
        active_agents[request_id] = agent
        
        # Set configuration
        config = request.config or {"maxIterations": 3}
        logger.debug(f"Setting agent configuration: {config}")
        agent_configs[request_id] = config
        agent.max_iterations = config["maxIterations"]
        
        # Store the user's request
        user_requests[request_id] = request.task
        logger.info(f"Request stored successfully. Active agents: {len(active_agents)}")
        
        return {"requestId": request_id, "status": "pending"}
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/configure")
async def configure_agent(config: AgentConfig):
    logger.info(f"Received configuration update: {config}")
    if not active_agents:
        logger.warning("Configuration update attempted with no active agents")
        raise HTTPException(status_code=400, detail="No active agent found")
    
    # Update configuration for all active agents
    for request_id in active_agents:
        logger.debug(f"Updating configuration for agent {request_id}")
        agent_configs[request_id] = {
            "maxIterations": config.maxIterations
        }
        active_agents[request_id].max_iterations = config.maxIterations
    
    logger.info("Configuration updated successfully")
    return {"status": "success", "config": config}

@app.post("/api/chat/stop/{request_id}")
async def stop_agent(request_id: str):
    logger.info(f"Received stop request for agent {request_id}")
    if request_id not in active_agents:
        logger.warning(f"Stop request for non-existent agent {request_id}")
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = active_agents[request_id]
    agent.should_stop = True
    logger.info(f"Stop flag set for agent {request_id}")
    
    return {"status": "stopping"}

@app.websocket("/api/chat/stream/{request_id}")
async def stream_updates(websocket: WebSocket, request_id: str):
    """Handle WebSocket connection for streaming updates"""
    try:
        logger.info(f"New WebSocket connection request for request_id: {request_id}")
        await websocket.accept()
        logger.info(f"WebSocket connection accepted for request_id: {request_id}")
        
        # Store connection
        active_connections[request_id] = websocket
        logger.debug(f"Active connections: {len(active_connections)}")
        
        # Get or create agent
        if request_id not in active_agents:
            logger.debug(f"Creating new agent for request_id: {request_id}")
            agent = ProteinDesignAgent()
            active_agents[request_id] = agent
            # Apply configuration if it exists
            if request_id in agent_configs:
                config = agent_configs[request_id]
                logger.debug(f"Applying existing configuration: {config}")
                agent.max_iterations = config["maxIterations"]
        
        agent = active_agents[request_id]
        user_request = user_requests.get(request_id)
        
        if not user_request:
            logger.warning(f"No request found for request_id: {request_id}")
            await websocket.send_json({
                "role": "error",
                "content": "No request found for this ID"
            })
            return
        
        logger.info(f"Processing request: {user_request}")
        
        # Get the current configuration
        config = agent_configs.get(request_id, {"maxIterations": 3})
        logger.debug(f"Using configuration: {config}")
        
        # Process the request and stream updates
        async for update in agent.process_request(config):
            logger.debug(f"Sending update for request_id: {request_id}")
            logger.debug(f"Update content: {update}")
            await websocket.send_json(update)
            
    except APIKeyError as e:
        logger.error(f"API Key error: {str(e)}", exc_info=True)
        try:
            await websocket.send_json({
                "role": "error",
                "content": str(e)
            })
        except:
            logger.error("Failed to send error message to client", exc_info=True)
    except PredictionError as e:
        logger.error(f"Prediction error: {str(e)}", exc_info=True)
        try:
            await websocket.send_json({
                "role": "error",
                "content": str(e)
            })
        except:
            logger.error("Failed to send error message to client", exc_info=True)
    except Exception as e:
        logger.error(f"Error in WebSocket connection for request_id {request_id}: {str(e)}", exc_info=True)
        try:
            await websocket.send_json({
                "role": "error",
                "content": f"An unexpected error occurred: {str(e)}"
            })
        except:
            logger.error("Failed to send error message to client", exc_info=True)
    finally:
        # Cleanup
        if request_id in active_connections:
            logger.info(f"Cleaning up WebSocket connection for request_id: {request_id}")
            del active_connections[request_id]
            del active_agents[request_id]
            if request_id in user_requests:
                del user_requests[request_id]
            logger.info(f"Remaining active connections: {len(active_connections)}")
        try:
            await websocket.close()
        except:
            logger.error("Failed to close WebSocket connection", exc_info=True)
        logger.info(f"WebSocket connection closed for request_id: {request_id}")

@app.get("/api/protein/{request_id}")
async def get_protein_data(request_id: str):
    """Get protein data for a completed request"""
    try:
        logger.info(f"Received request for protein data with request_id: {request_id}")
        
        # Get the agent for this request
        agent = active_agents.get(request_id)
        if not agent:
            logger.warning(f"No agent found for request_id: {request_id}")
            raise HTTPException(status_code=404, detail="Request not found")
        
        # Get the best sequence and score
        protein_data = {
            "sequence": agent.best_sequence,
            "binding_score": agent.best_score,
            "session_id": agent.session_id
        }
        
        logger.info(f"Returning protein data for request_id: {request_id}")
        logger.debug(f"Protein data: {protein_data}")
        return protein_data
        
    except Exception as e:
        logger.error(f"Error getting protein data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000) 