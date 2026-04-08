"""
Fellow Buffalo - OpenEnv Server
FastAPI server exposing the required endpoints for the hackathon.
"""

import os
import sys
import json
import re
from datetime import datetime
from typing import Optional, Dict, Any, List

# Load .env file manually (handles Windows BOM) - looks in current or parent dir
def load_env_file():
    """Load .env from current dir or parent dir"""
    for filepath in ['.env', '../.env']:
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                content = f.read()
            if content.startswith(b'\xef\xbb\xbf'):
                content = content[3:]
            text = content.decode('utf-8')
            for line in text.splitlines():
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
            return True
    return False

# Load environment variables
load_env_file()

# Now import other modules
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from openai import OpenAI

# ADD THIS: Import Gradio
import gradio as gr
from gradio_app import demo as gradio_interface

from environment import FellowBuffaloEnv
from models import FellowBuffaloAction, FellowBuffaloObservation, FellowBuffaloState
from tasks import task1_grader, task2_grader, task3_grader, task4_grader, task5_grader

# Create FastAPI app
app = FastAPI(
    title="Fellow Buffalo - OpenEnv",
    description="Email triage environment for AI agents",
    version="1.0.0"
)

# ADD THIS: Mount Gradio interface BEFORE adding CORS and endpoints
app = gr.mount_gradio_app(app, gradio_interface, path="/gradio")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global environment instance
env = FellowBuffaloEnv()
last_reward = 0.0
last_task_id = 1


class BaselineResponse(BaseModel):
    task_1: float
    task_2: float
    task_3: float
    task_4: float
    task_5: float  # ADD THIS
    status: str


class StepRequest(BaseModel):
    action: FellowBuffaloAction


# CHANGE 3: Update ResetRequest model with seed parameter
class ResetRequest(BaseModel):
    task_id: int = 1
    seed: Optional[int] = None  # NEW


def get_ai_client():
    """Get AI client for baseline (works with Groq OR OpenAI)"""
    groq_key = os.getenv('GROQ_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    hf_key = os.getenv('HF_TOKEN')
    
    # Determine which API to use
    using_groq = bool(groq_key)
    api_key = groq_key or openai_key or hf_key
    api_base = os.getenv('API_BASE_URL')
    
    if not api_key:
        return None, None
    
    if api_base:
        client = OpenAI(api_key=api_key, base_url=api_base)
        model = os.getenv('MODEL_NAME', 'gpt-4o-mini')
    elif using_groq:
        # Using Groq
        client = OpenAI(api_key=api_key, base_url='https://api.groq.com/openai/v1')
        model = os.getenv('MODEL_NAME', 'llama-3.3-70b-versatile')
    else:
        # Using OpenAI
        client = OpenAI(api_key=api_key)
        model = os.getenv('MODEL_NAME', 'gpt-4o-mini')
    
    print(f"Using {'Groq' if using_groq else 'OpenAI'} API with model: {model}")
    return client, model


def run_task1_baseline(client, model) -> float:
    """Run Task 1 baseline - Multi-email version (5 emails)"""
    try:
        test_env = FellowBuffaloEnv()
        obs = test_env.reset(task_id=1)
        total_reward = 0.0
        step_count = 0
        max_emails = 5
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        while not obs.done and step_count < max_emails:
            step_count += 1
            
            prompt = f"""
            Today's date is {today}.
            
            Classify this email and rate your confidence:
            Subject: {obs.email_subject}
            Body: {obs.email_body[:500]}
            
            Return JSON only with: tab, color, deadline, confidence
            tab: Jobs, Internships, News, Sports, Events, Finance, General
            color: green (future), orange (0-7 days past), red (7+ days past)
            deadline: ISO datetime or null
            confidence: 0-100 (how sure you are)
            
            Example: {{"tab": "Internships", "color": "green", "deadline": "2025-04-15T23:59:00", "confidence": 85}}
            """
            
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = {}
            
            action = FellowBuffaloAction(
                task_id=1,
                tab=data.get('tab'),
                color=data.get('color'),
                deadline=data.get('deadline'),
                confidence=data.get('confidence', 50)
            )
            
            obs, step_reward, done = test_env.step(action)
            total_reward += step_reward
            
            if done:
                break
        
        return round(total_reward, 4)
        
    except Exception as e:
        print(f"Task 1 baseline error: {e}")
        return 0.0


def run_task2_baseline(client, model) -> float:
    """Run Task 2 baseline"""
    try:
        test_env = FellowBuffaloEnv()
        obs = test_env.reset(task_id=2)
        
        prompt = f"""
        Summarize this email and generate a tag cloud.
        
        Subject: {obs.email_subject}
        Body: {obs.email_body[:800]}
        Attachments: {obs.attachment_texts}
        
        Return JSON only with: summary, tag_cloud
        tag_cloud should be pipe-separated keywords (e.g., "keyword1|keyword2|keyword3")
        
        Example: {{"summary": "This email is about...", "tag_cloud": "AI|internship|deadline"}}
        """
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.1
        )
        
        content = response.choices[0].message.content
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = {}
        
        action = FellowBuffaloAction(
            task_id=2,
            summary=data.get('summary', ''),
            tag_cloud=data.get('tag_cloud', '')
        )
        
        _, reward, _ = test_env.step(action)
        return round(reward, 4)
        
    except Exception as e:
        print(f"Task 2 baseline error: {e}")
        return 0.0


def run_task3_baseline(client, model) -> float:
    """Run Task 3 baseline"""
    try:
        test_env = FellowBuffaloEnv()
        obs = test_env.reset(task_id=3)
        total_reward = 0.0
        step_count = 0
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        while not obs.done and step_count < 12:
            step_count += 1
            
            prompt = f"""
            Today is {today}.
            
            Email lifecycle decision.
            Subject: {obs.email_subject}
            Deadline: {obs.deadline}
            
            Decide:
            - color: green (future), orange (0-7 days past), red (7+ days past)
            - group: internships_q1, jobs_q1, finance_q1, events_q1, news_q1
            
            Return JSON only: {{"color": "green", "group": "internships_q1"}}
            """
            
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=80,
                    temperature=0.1
                )
                
                content = response.choices[0].message.content
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    data = {}
                
                action = FellowBuffaloAction(
                    task_id=3,
                    lifecycle_decisions=[{
                        'color': data.get('color', 'green'),
                        'group': data.get('group', 'general_q1'),
                        'deadline': obs.deadline
                    }]
                )
                
                obs, reward, done = test_env.step(action)
                total_reward += reward
                
                if done:
                    break
                    
            except Exception as e:
                print(f"Task 3 step {step_count} error: {e}")
                break
        
        return round(total_reward, 4)
        
    except Exception as e:
        print(f"Task 3 baseline error: {e}")
        return 0.0


def run_task4_baseline(client, model) -> float:
    """Run Task 4 baseline - Reply Generation"""
    try:
        test_env = FellowBuffaloEnv()
        obs = test_env.reset(task_id=4)
        
        prompt = f"""
        Write a professional reply to this email:
        
        Subject: {obs.email_subject}
        Body: {obs.email_body[:800]}
        
        Return JSON only with: reply
        Example: {{"reply": "Dear Sir/Madam,\\n\\nThank you for your email. I will...\\n\\nBest regards,\\n[Your Name]"}}
        """
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.1
        )
        
        content = response.choices[0].message.content
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = {}
        
        action = FellowBuffaloAction(
            task_id=4,
            reply=data.get('reply', '')
        )
        
        _, reward, _ = test_env.step(action)
        return round(reward, 4)
        
    except Exception as e:
        print(f"Task 4 baseline error: {e}")
        return 0.0


def run_task5_baseline(client, model) -> float:
    """Run Task 5 baseline - Priority Ranking"""
    try:
        test_env = FellowBuffaloEnv()
        obs = test_env.reset(task_id=5)
        
        # Get email IDs from metadata
        email_ids = obs.metadata.get('emails_to_rank', [])
        
        # Simple baseline ranking (just return as-is)
        action = FellowBuffaloAction(
            task_id=5,
            email_ranking=email_ids
        )
        
        _, reward, _ = test_env.step(action)
        return round(reward, 4)
        
    except Exception as e:
        print(f"Task 5 baseline error: {e}")
        return 0.0


@app.get("/")
async def root():
    return {
        "name": "Fellow Buffalo",
        "description": "Email triage OpenEnv environment",
        "endpoints": ["/health", "/reset", "/step", "/state", "/tasks", "/baseline", "/benchmark", "/info", "/web", "/gradio"],
        "api_key_configured": bool(os.getenv('GROQ_API_KEY') or os.getenv('OPENAI_API_KEY') or os.getenv('HF_TOKEN'))
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    api_key = os.getenv('GROQ_API_KEY') or os.getenv('OPENAI_API_KEY') or os.getenv('HF_TOKEN')
    return {
        "status": "healthy",
        "api_key_configured": bool(api_key),
        "api_key_preview": api_key[:20] + "..." if api_key else None,
        "task_id": last_task_id
    }


# CHANGE 3: Update reset endpoint to pass seed parameter
@app.post("/reset")
async def reset(request: ResetRequest = ResetRequest()) -> FellowBuffaloObservation:
    """Reset environment and return first observation"""
    global env, last_task_id
    last_task_id = request.task_id
    observation = env.reset(task_id=request.task_id, seed=request.seed)  # Pass seed
    return observation


@app.post("/step")
async def step(request: StepRequest) -> Dict[str, Any]:
    """Take an action and return observation, reward, done"""
    global env, last_reward
    observation, reward, done = env.step(request.action)
    last_reward = reward
    return {
        "observation": observation,
        "reward": reward,
        "done": done
    }


@app.get("/state")
async def state() -> FellowBuffaloState:
    """Return current episode state"""
    return env.state()


@app.get("/tasks")
async def tasks() -> Dict[str, Any]:
    """Return list of tasks and action schema"""
    return {
        "tasks": [
            {
                "id": 1,
                "name": "email-intake",
                "difficulty": "easy",
                "description": "Classify email into tab, color, and extract deadline",
                "action_schema": {
                    "tab": "string (Jobs/Internships/News/Sports/Events/Finance/General)",
                    "color": "string (green/orange/red)",
                    "deadline": "string (ISO datetime or null)",
                    "confidence": "integer (0-100)"
                }
            },
            {
                "id": 2,
                "name": "metadata-generation",
                "difficulty": "medium",
                "description": "Generate summary and tag cloud from email",
                "action_schema": {
                    "summary": "string (AI-generated summary)",
                    "tag_cloud": "string (pipe-separated keywords)"
                }
            },
            {
                "id": 3,
                "name": "lifecycle-manager",
                "difficulty": "hard",
                "description": "Manage color transitions and grouping for archiving",
                "action_schema": {
                    "lifecycle_decisions": "list of transitions"
                }
            },
            {
                "id": 4,
                "name": "reply-generation",
                "difficulty": "medium",
                "description": "Generate a professional reply to an email",
                "action_schema": {
                    "reply": "string (AI-generated email reply)"
                }
            },
            {
                "id": 5,
                "name": "priority-ranking",
                "difficulty": "hard",
                "description": "Rank 10 emails by priority/urgency",
                "action_schema": {
                    "email_ranking": "list of email IDs in priority order"
                }
            }
        ]
    }


@app.post("/baseline")
async def baseline() -> BaselineResponse:
    """Run baseline inference and return scores"""
    scores = {"task_1": 0.0, "task_2": 0.0, "task_3": 0.0, "task_4": 0.0, "task_5": 0.0}
    
    client, model = get_ai_client()
    
    if not client:
        return BaselineResponse(
            task_1=0.0,
            task_2=0.0,
            task_3=0.0,
            task_4=0.0,
            task_5=0.0,
            status="no_api_key"
        )
    
    # Run each task directly
    scores["task_1"] = run_task1_baseline(client, model)
    scores["task_2"] = run_task2_baseline(client, model)
    scores["task_3"] = run_task3_baseline(client, model)
    scores["task_4"] = run_task4_baseline(client, model)
    scores["task_5"] = run_task5_baseline(client, model)
    
    return BaselineResponse(
        task_1=scores["task_1"],
        task_2=scores["task_2"],
        task_3=scores["task_3"],
        task_4=scores["task_4"],
        task_5=scores["task_5"],
        status="completed"
    )


# CHANGE 1: Add benchmark endpoint
@app.post("/benchmark")
async def benchmark():
    """Run all tasks 5 times and return average + variance"""
    import statistics
    
    client, model = get_ai_client()
    if not client:
        return {"error": "no_api_key", "status": "failed"}
    
    results = {"task_1": [], "task_2": [], "task_3": [], "task_4": [], "task_5": []}
    
    for run in range(5):
        print(f"Benchmark run {run + 1}/5...")
        results["task_1"].append(run_task1_baseline(client, model))
        results["task_2"].append(run_task2_baseline(client, model))
        results["task_3"].append(run_task3_baseline(client, model))
        results["task_4"].append(run_task4_baseline(client, model))
        results["task_5"].append(run_task5_baseline(client, model))
    
    def stats(arr):
        return {
            "mean": round(statistics.mean(arr), 3),
            "stdev": round(statistics.stdev(arr), 3) if len(arr) > 1 else 0.0,
            "min": round(min(arr), 3),
            "max": round(max(arr), 3),
            "runs": arr
        }
    
    return {
        "task_1": stats(results["task_1"]),
        "task_2": stats(results["task_2"]),
        "task_3": stats(results["task_3"]),
        "task_4": stats(results["task_4"]),
        "task_5": stats(results["task_5"]),
        "status": "completed",
        "runs_completed": 5
    }


# CHANGE 2: Add info endpoint
@app.get("/info")
async def info():
    """Complete environment information for researchers"""
    return {
        "name": "Fellow Buffalo",
        "version": "1.0.0",
        "description": "Email triage RL environment — classify, summarize, manage lifecycle",
        "real_world_task": "Email management affects every professional daily. This environment trains AI to automate it.",
        "observation_space": {
            "task_id": "int — 1-5",
            "step": "int — current step number",
            "email_subject": "string — email subject line",
            "email_body": "string — email body text",
            "attachment_texts": "dict — parsed attachment content by filename",
            "deadline": "string — ISO datetime or null",
            "difficulty": "int — 1 easy, 2 medium, 3 hard",
            "hint": "string — optional hint after wrong answer (Task 1)",
            "episode_history": "list — last 3 step results",
            "metadata": "dict — storage info, simulated_date, etc.",
            "done": "bool",
            "reward": "float — step reward (for observation after step)"
        },
        "action_space": {
            "task_id": "int 1-5",
            "tab": "Jobs | Internships | News | Sports | Events | Finance | General (Task 1)",
            "color": "green | orange | red (Tasks 1, 3)",
            "deadline": "ISO datetime string or null (Task 1)",
            "confidence": "int 0-100 (Task 1)",
            "summary": "string (Task 2)",
            "tag_cloud": "pipe-separated keywords (Task 2)",
            "reply": "string (Task 4)",
            "email_ranking": "list of email IDs (Task 5)",
            "lifecycle_decisions": "list of dicts with color, group, account, trigger_relay (Task 3)"
        },
        "reward_range": [-0.5, 1.0],
        "reward_details": {
            "task_1": "tab(0.33) + color(0.33) + deadline(0.34) per email, max ~5.0",
            "task_2": "summary(0.5) + tag_cloud(0.5), max 1.0",
            "task_3": "color(+0.1/-0.05) + account(0.1) + relay(0.1) + grouping(0.15) + thread(0.05), range -0.5 to 1.0",
            "task_4": "AI-graded reply quality, 0.0-1.0",
            "task_5": "position-based ranking, max 1.0"
        },
        "tasks": [
            {"id": 1, "name": "email-intake", "difficulty": "easy", "max_steps": 5},
            {"id": 2, "name": "metadata-generation", "difficulty": "medium", "max_steps": 1},
            {"id": 3, "name": "lifecycle-manager", "difficulty": "hard", "max_steps": 10},
            {"id": 4, "name": "reply-generation", "difficulty": "medium", "max_steps": 1},
            {"id": 5, "name": "priority-ranking", "difficulty": "hard", "max_steps": 1}
        ],
        "why_novel": "Email triage has never been built as an OpenEnv environment. The storage relay mechanic (simulating Gmail's 15GB limit) with simulated date progression for temporal reasoning is unique to this environment.",
        "endpoints": ["/health", "/reset", "/step", "/state", "/tasks", "/baseline", "/benchmark", "/info", "/web", "/gradio"],
        "api_key_configured": bool(os.getenv('GROQ_API_KEY') or os.getenv('OPENAI_API_KEY'))
    }


@app.get("/grader")
async def grader() -> Dict[str, float]:
    """Return last episode score"""
    global last_reward
    return {"score": last_reward}


@app.get("/debug")
async def debug():
    """Debug endpoint to check API key and test calls"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    groq_key = os.getenv('GROQ_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    hf_token = os.getenv('HF_TOKEN')
    
    # Try to get client
    client, model = get_ai_client()
    
    result = {
        "groq_key_exists": bool(groq_key),
        "openai_key_exists": bool(openai_key),
        "hf_token_exists": bool(hf_token),
        "api_key_preview": (groq_key or openai_key or hf_token)[:20] + "..." if (groq_key or openai_key or hf_token) else None,
        "client_created": client is not None,
        "model": model if client else None,
        "test_call": None
    }
    
    # Test actual API call
    if client:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Say OK in one word"}],
                max_tokens=5,
                temperature=0
            )
            result["test_call"] = response.choices[0].message.content
        except Exception as e:
            result["test_call"] = f"Error: {str(e)}"
    
    return result


@app.get("/web", response_class=HTMLResponse)
async def web_interface():
    """Simple web UI for testing the environment"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Fellow Buffalo - OpenEnv</title>
        <style>
            body { font-family: Arial; max-width: 800px; margin: 40px auto; padding: 20px; }
            button { background: #2E86AB; color: white; padding: 10px 20px; border: none; cursor: pointer; margin: 5px; border-radius: 4px; }
            button:hover { background: #1A3C5E; }
            pre { background: #f4f4f4; padding: 15px; border-radius: 4px; overflow-x: auto; }
            input, select { padding: 8px; margin: 5px; border: 1px solid #ccc; border-radius: 4px; }
            .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }
        </style>
    </head>
    <body>
        <h1>Fellow Buffalo — Email Triage OpenEnv</h1>
        
        <div class="section">
            <h2>Reset Environment</h2>
            <select id="task-id">
                <option value="1">Task 1 — Email Classification (Easy)</option>
                <option value="2">Task 2 — Metadata Generation (Medium)</option>
                <option value="3">Task 3 — Lifecycle Manager (Hard)</option>
                <option value="4">Task 4 — Reply Generation (Medium)</option>
                <option value="5">Task 5 — Priority Ranking (Hard)</option>
            </select>
            <button onclick="reset()">Reset</button>
        </div>
        
        <div class="section">
            <h2>Current Observation</h2>
            <pre id="observation">Click Reset to start</pre>
        </div>
        
        <div class="section">
            <h2>Take Action (Task 1)</h2>
            <select id="tab">
                <option>Jobs</option><option>Internships</option><option>News</option>
                <option>Sports</option><option>Events</option><option>Finance</option><option>General</option>
            </select>
            <select id="color">
                <option>green</option><option>orange</option><option>red</option>
            </select>
            <input id="deadline" placeholder="Deadline (ISO or leave blank)" style="width:250px">
            <button onclick="step()">Step</button>
        </div>
        
        <div class="section">
            <h2>Result</h2>
            <pre id="result">No action taken yet</pre>
        </div>
        
        <div class="section">
            <h2>State</h2>
            <button onclick="getState()">Get State</button>
            <button onclick="getTasks()">Get Tasks</button>
            <pre id="state">-</pre>
        </div>
        
        <script>
            let taskId = 1;
            
            async function reset() {
                taskId = parseInt(document.getElementById('task-id').value);
                const r = await fetch('/reset', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({task_id: taskId})
                });
                const data = await r.json();
                document.getElementById('observation').textContent = JSON.stringify(data, null, 2);
                document.getElementById('result').textContent = 'Environment reset. Take an action.';
            }
            
            async function step() {
                const action = {
                    task_id: taskId,
                    tab: document.getElementById('tab').value,
                    color: document.getElementById('color').value,
                    deadline: document.getElementById('deadline').value || null
                };
                const r = await fetch('/step', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({action})
                });
                const data = await r.json();
                document.getElementById('observation').textContent = JSON.stringify(data.observation, null, 2);
                document.getElementById('result').textContent = 
                    'Reward: ' + data.reward + '\\nDone: ' + data.done;
            }
            
            async function getState() {
                const r = await fetch('/state');
                const data = await r.json();
                document.getElementById('state').textContent = JSON.stringify(data, null, 2);
            }
            
            async function getTasks() {
                const r = await fetch('/tasks');
                const data = await r.json();
                document.getElementById('state').textContent = JSON.stringify(data, null, 2);
            }
        </script>
    </body>
    </html>
    """


def main():
    """Main entry point for the server"""
    import uvicorn
    print("Starting Fellow Buffalo OpenEnv Server...")
    print(f"GROQ_API_KEY configured: {bool(os.getenv('GROQ_API_KEY'))}")
    print(f"OPENAI_API_KEY configured: {bool(os.getenv('OPENAI_API_KEY'))}")
    print(f"Server running on http://0.0.0.0:7860")
    print(f"Web UI available at http://localhost:7860/web")
    print(f"Gradio UI available at http://localhost:7860/gradio")
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()