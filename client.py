"""
Fellow Buffalo - OpenEnv Client
Allows users to install and use the environment as a Python package.
"""

import httpx
from typing import Optional
from models import FellowBuffaloAction, FellowBuffaloObservation, FellowBuffaloState


class FellowBuffaloEnvClient:
    """
    HTTP client for Fellow Buffalo OpenEnv environment.
    
    Usage:
        # Connect to remote HF Space
        client = FellowBuffaloEnvClient(
            base_url="https://sufi-sufi-fellow-buffalo-env.hf.space"
        )
        
        # Or run locally
        client = FellowBuffaloEnvClient(
            base_url="http://localhost:7860"
        )
        
        obs = client.reset(task_id=1)
        obs, reward, done = client.step(action)
    """
    
    def __init__(self, base_url: str = "https://sufi-sufi-fellow-buffalo-env.hf.space"):
        self.base_url = base_url.rstrip('/')
        self.http = httpx.Client(timeout=60.0)
    
    def reset(self, task_id: int = 1) -> FellowBuffaloObservation:
        response = self.http.post(
            f"{self.base_url}/reset",
            json={"task_id": task_id}
        )
        response.raise_for_status()
        return FellowBuffaloObservation(**response.json())
    
    def step(self, action: FellowBuffaloAction):
        response = self.http.post(
            f"{self.base_url}/step",
            json={"action": action.model_dump()}
        )
        response.raise_for_status()
        data = response.json()
        obs = FellowBuffaloObservation(**data['observation'])
        reward = data['reward']
        done = data['done']
        return obs, reward, done
    
    def state(self) -> FellowBuffaloState:
        response = self.http.get(f"{self.base_url}/state")
        response.raise_for_status()
        return FellowBuffaloState(**response.json())
    
    def health(self):
        response = self.http.get(f"{self.base_url}/health")
        return response.json()
    
    def close(self):
        self.http.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()