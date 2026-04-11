# api_server.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn

from environment import FellowBuffaloEnv
from models import FellowBuffaloAction

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global environment instance
env = FellowBuffaloEnv()

class ResetRequest(BaseModel):
    task_id: int
    seed: Optional[int] = None

class StepRequest(BaseModel):
    action: Dict[str, Any]

@app.post("/reset")
async def reset_endpoint(request: ResetRequest):
    """Reset environment and return observation"""
    observation = env.reset(task_id=request.task_id, seed=request.seed)
    return observation.model_dump()

@app.post("/step")
async def step_endpoint(request: StepRequest):
    """Take an action and return next observation, reward, done"""
    action = FellowBuffaloAction(**request.action)
    observation, reward, done = env.step(action)
    return {
        "observation": observation.model_dump(),
        "reward": reward,
        "done": done
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("Starting Fellow Buffalo API server on http://localhost:7860")
    uvicorn.run(app, host="0.0.0.0", port=7860)