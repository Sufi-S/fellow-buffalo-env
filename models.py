"""
Fellow Buffalo - OpenEnv Models
Defines the Action, Observation, and State classes for the environment.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class FellowBuffaloAction(BaseModel):
    """What the AI agent can do"""
    task_id: int  # 1, 2, 3, 4, or 5
    tab: Optional[str] = None  # Jobs, Internships, News, Sports, Events, Finance, General
    color: Optional[str] = None  # green, orange, red
    deadline: Optional[str] = None  # ISO format datetime or null
    confidence: Optional[int] = None  # 0-100 confidence score
    account: Optional[str] = None  # "primary" or "archive"
    summary: Optional[str] = None  # AI-generated summary
    tag_cloud: Optional[str] = None  # Pipe-separated keywords
    reply: Optional[str] = None  # Task 4 - Email reply
    email_ranking: Optional[List[str]] = None  # NEW: Task 5 - List of email IDs in priority order
    lifecycle_decisions: Optional[List[Dict[str, Any]]] = None  # For Task 3


class FellowBuffaloObservation(BaseModel):
    """What the AI agent sees"""
    task_id: int
    step: int
    email_subject: str
    email_body: str
    attachment_texts: Dict[str, str]
    current_colors: Optional[Dict[str, str]] = None
    deadline: Optional[str] = None
    done: bool = False
    reward: Optional[float] = None
    metadata: Dict[str, Any] = {}
    episode_history: Optional[List[Dict]] = []  # last 3 steps
    hint: Optional[str] = None  # hint for next step if last step was wrong
    difficulty: Optional[int] = 1  # 1=easy, 2=medium, 3=hard


class FellowBuffaloState(BaseModel):
    """Episode state information"""
    task_id: int
    task_name: str
    step_count: int
    max_steps: int
    done: bool
    score: Optional[float] = None