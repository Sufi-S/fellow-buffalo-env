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

def load_env_file():
    for filepath in [".env", "../.env"]:
        if os.path.exists(filepath):
            with open(filepath, "rb") as f:
                content = f.read()
            if content.startswith(b"\xef\xbb\xbf"):
                content = content[3:]
            text = content.decode("utf-8")
            for line in text.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
            return True
    return False

load_env_file()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from openai import OpenAI
import gradio as gr
from gradio_app import demo as gradio_interface

from environment import FellowBuffaloEnv
from models import FellowBuffaloAction, FellowBuffaloObservation, FellowBuffaloState
from tasks import task1_grader, task2_grader, task3_grader, task4_grader, task5_grader

# ------------------------------------------------------------------ #
#  App setup — CORS first, Gradio last
# ------------------------------------------------------------------ #

app = FastAPI(
    title="Fellow Buffalo - OpenEnv",
    description="Email triage environment for AI agents",
    version="1.0.0",
)

# CORS must be added BEFORE mounting Gradio
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Gradio AFTER middleware
app = gr.mount_gradio_app(app, gradio_interface, path="/gradio")

# ------------------------------------------------------------------ #
#  Global state
# ------------------------------------------------------------------ #

env = FellowBuffaloEnv()
last_reward = 0.0
last_task_id = 1


class BaselineResponse(BaseModel):
    task_1: float
    task_2: float
    task_3: float
    task_4: float
    task_5: float
    status: str


class StepRequest(BaseModel):
    action: FellowBuffaloAction


class ResetRequest(BaseModel):
    task_id: int = 1
    seed: Optional[int] = None


# ------------------------------------------------------------------ #
#  AI client
# ------------------------------------------------------------------ #

def get_ai_client():
    groq_key   = os.getenv("GROQ_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    hf_key     = os.getenv("HF_TOKEN")
    using_groq = bool(groq_key)
    api_key    = groq_key or openai_key or hf_key
    api_base   = os.getenv("API_BASE_URL")

    if not api_key:
        return None, None

    if api_base:
        client = OpenAI(api_key=api_key, base_url=api_base)
        model  = os.getenv("MODEL_NAME", "gpt-4o-mini")
    elif using_groq:
        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        model  = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
    else:
        client = OpenAI(api_key=api_key)
        model  = os.getenv("MODEL_NAME", "gpt-4o-mini")

    print(f"Using {'Groq' if using_groq else 'OpenAI'} — model: {model}")
    return client, model


# ------------------------------------------------------------------ #
#  Baseline helpers
# ------------------------------------------------------------------ #

def run_task1_baseline(client, model) -> float:
    try:
        test_env = FellowBuffaloEnv()
        obs = test_env.reset(task_id=1)
        total_reward = 0.0
        step_count = 0
        today = datetime.now().strftime("%Y-%m-%d")

        while not obs.done and step_count < 5:
            step_count += 1
            prompt = f"""
Today is {today}.
Classify this email — return JSON only.

Subject: {obs.email_subject}
Body: {obs.email_body[:500]}

Fields: tab (Jobs|Internships|News|Sports|Events|Finance|General), color (green|orange|red), deadline (ISO or null), confidence (0-100)
Example: {{"tab":"Internships","color":"green","deadline":"2026-04-15T23:59:00","confidence":85}}
"""
            try:
                resp = client.chat.completions.create(
                    model=model, messages=[{"role": "user", "content": prompt}],
                    max_tokens=120, temperature=0.1,
                )
                data = json.loads(re.search(r"\{.*\}", resp.choices[0].message.content, re.DOTALL).group())
            except Exception:
                data = {}

            action = FellowBuffaloAction(
                task_id=1, tab=data.get("tab"), color=data.get("color"),
                deadline=data.get("deadline"), confidence=data.get("confidence", 50),
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
    try:
        test_env = FellowBuffaloEnv()
        obs = test_env.reset(task_id=2)
        prompt = f"""
Summarize this email and generate a pipe-separated tag cloud.
Subject: {obs.email_subject}
Body: {obs.email_body[:800]}
Attachments: {obs.attachment_texts}

Return JSON only: {{"summary":"...","tag_cloud":"kw1|kw2|kw3"}}
"""
        resp = client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": prompt}],
            max_tokens=400, temperature=0.1,
        )
        try:
            data = json.loads(re.search(r"\{.*\}", resp.choices[0].message.content, re.DOTALL).group())
        except Exception:
            data = {}

        action = FellowBuffaloAction(
            task_id=2, summary=data.get("summary", ""), tag_cloud=data.get("tag_cloud", ""),
        )
        _, reward, _ = test_env.step(action)
        return round(reward, 4)
    except Exception as e:
        print(f"Task 2 baseline error: {e}")
        return 0.0


def run_task3_baseline(client, model) -> float:
    """Run Task 3 baseline — exactly 15 steps, returns normalized score."""
    try:
        test_env  = FellowBuffaloEnv()
        obs       = test_env.reset(task_id=3)
        last_reward = 0.0
        step_count  = 0

        while not obs.done and step_count < 15:
            step_count += 1
            metadata         = obs.metadata or {}
            storage_critical = metadata.get("storage_critical", False)
            sim_date         = metadata.get("simulated_date", datetime.now().strftime("%Y-%m-%d"))

            prompt = f"""
Simulated date: {sim_date}.
Email subject: {obs.email_subject}
Deadline: {obs.deadline or "No deadline"}
Storage: {metadata.get("storage_used_gb", 8.5):.1f} GB / 15 GB
Storage critical: {"YES — trigger relay NOW" if storage_critical else "No"}

Return JSON only:
{{"color":"green","group":"internships_q1","account":"primary","trigger_relay":false}}

color: green=future deadline, orange=0-7 days past, red=7+ days past
group: internships_q1 | jobs_q1 | finance_q1 | events_q1 | news_q1 | general_q1
account: primary (green/orange) or archive (red)
trigger_relay: true ONLY if storage critical
"""
            try:
                resp = client.chat.completions.create(
                    model=model, messages=[{"role": "user", "content": prompt}],
                    max_tokens=80, temperature=0.1,
                )
                data = json.loads(re.search(r"\{.*\}", resp.choices[0].message.content, re.DOTALL).group())
            except Exception:
                data = {}

            action = FellowBuffaloAction(
                task_id=3,
                lifecycle_decisions=[{
                    "color":         data.get("color", "green"),
                    "group":         data.get("group", "general_q1"),
                    "account":       data.get("account", "primary"),
                    "trigger_relay": data.get("trigger_relay", False),
                    "deadline":      obs.deadline,
                }],
            )
            obs, reward, done = test_env.step(action)
            last_reward = reward   # env returns normalized score on done step
            if done:
                break

        return round(last_reward, 4)
    except Exception as e:
        print(f"Task 3 baseline error: {e}")
        return 0.0


def run_task4_baseline(client, model) -> float:
    try:
        test_env = FellowBuffaloEnv()
        obs = test_env.reset(task_id=4)
        prompt = f"""
Write a professional reply to this email.
Subject: {obs.email_subject}
Body: {obs.email_body[:800]}

Return JSON only: {{"reply":"Dear ...\\n\\nThank you...\\n\\nBest regards"}}
"""
        resp = client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": prompt}],
            max_tokens=300, temperature=0.1,
        )
        try:
            data = json.loads(re.search(r"\{.*\}", resp.choices[0].message.content, re.DOTALL).group())
        except Exception:
            data = {}

        action = FellowBuffaloAction(task_id=4, reply=data.get("reply", ""))
        _, reward, _ = test_env.step(action)
        return round(reward, 4)
    except Exception as e:
        print(f"Task 4 baseline error: {e}")
        return 0.0


def run_task5_baseline(client, model) -> float:
    try:
        test_env = FellowBuffaloEnv()
        obs = test_env.reset(task_id=5)

        email_ids   = obs.metadata.get("emails_to_rank", [])
        subj_map    = obs.metadata.get("email_subjects", {})
        email_list  = "\n".join(
            f"{i+1}. [{eid}] {subj_map.get(eid, 'Unknown')}"
            for i, eid in enumerate(email_ids)
        )

        prompt = f"""
Rank these 10 emails by urgency/priority (1 = most urgent, 10 = least urgent).

{email_list}

Return JSON only with the IDs in priority order:
{{"ranking": ["id1", "id2", ...]}}
"""
        try:
            resp = client.chat.completions.create(
                model=model, messages=[{"role": "user", "content": prompt}],
                max_tokens=200, temperature=0.1,
            )
            data = json.loads(re.search(r"\{.*\}", resp.choices[0].message.content, re.DOTALL).group())
            ranking_ids = data.get("ranking", email_ids)
        except Exception:
            ranking_ids = email_ids   # fallback: as-is

        action = FellowBuffaloAction(task_id=5, email_ranking=ranking_ids)
        _, reward, _ = test_env.step(action)
        return round(reward, 4)
    except Exception as e:
        print(f"Task 5 baseline error: {e}")
        return 0.0


# ------------------------------------------------------------------ #
#  Endpoints
# ------------------------------------------------------------------ #

@app.get("/")
async def root():
    return {
        "name": "Fellow Buffalo",
        "description": "Email triage OpenEnv environment",
        "endpoints": ["/health", "/reset", "/step", "/state", "/tasks", "/baseline", "/benchmark", "/info", "/web", "/gradio"],
        "api_key_configured": bool(os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("HF_TOKEN")),
    }


@app.get("/health")
async def health():
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("HF_TOKEN")
    return {
        "status": "healthy",
        "api_key_configured": bool(api_key),
        "api_key_preview": api_key[:20] + "..." if api_key else None,
        "task_id": last_task_id,
    }


@app.post("/reset")
async def reset(request: ResetRequest = ResetRequest()) -> FellowBuffaloObservation:
    global env, last_task_id
    last_task_id = request.task_id
    return env.reset(task_id=request.task_id, seed=request.seed)


@app.post("/step")
async def step(request: StepRequest) -> Dict[str, Any]:
    global env, last_reward
    observation, reward, done = env.step(request.action)
    last_reward = reward
    return {"observation": observation, "reward": reward, "done": done}


@app.get("/state")
async def state() -> FellowBuffaloState:
    return env.state()


@app.get("/tasks")
async def tasks() -> Dict[str, Any]:
    return {
        "tasks": [
            {"id": 1, "name": "email-intake",          "difficulty": "easy",   "max_steps": 5,  "description": "Classify email: tab + color + deadline"},
            {"id": 2, "name": "metadata-generation",   "difficulty": "medium", "max_steps": 1,  "description": "Generate summary + tag cloud"},
            {"id": 3, "name": "lifecycle-manager",     "difficulty": "hard",   "max_steps": 15, "description": "Manage color transitions, grouping, storage relay"},
            {"id": 4, "name": "reply-generation",      "difficulty": "medium", "max_steps": 1,  "description": "Write a professional email reply"},
            {"id": 5, "name": "priority-ranking",      "difficulty": "hard",   "max_steps": 1,  "description": "Rank 10 emails by urgency"},
        ]
    }


@app.post("/baseline")
async def baseline() -> BaselineResponse:
    client, model = get_ai_client()
    if not client:
        return BaselineResponse(task_1=0.0, task_2=0.0, task_3=0.0, task_4=0.0, task_5=0.0, status="no_api_key")

    return BaselineResponse(
        task_1=run_task1_baseline(client, model),
        task_2=run_task2_baseline(client, model),
        task_3=run_task3_baseline(client, model),
        task_4=run_task4_baseline(client, model),
        task_5=run_task5_baseline(client, model),
        status="completed",
    )


@app.post("/benchmark")
async def benchmark():
    import statistics
    client, model = get_ai_client()
    if not client:
        return {"error": "no_api_key"}

    results: Dict[str, list] = {f"task_{i}": [] for i in range(1, 6)}
    for run in range(5):
        print(f"Benchmark run {run + 1}/5…")
        results["task_1"].append(run_task1_baseline(client, model))
        results["task_2"].append(run_task2_baseline(client, model))
        results["task_3"].append(run_task3_baseline(client, model))
        results["task_4"].append(run_task4_baseline(client, model))
        results["task_5"].append(run_task5_baseline(client, model))

    def stats(arr):
        return {
            "mean":  round(statistics.mean(arr), 3),
            "stdev": round(statistics.stdev(arr), 3) if len(arr) > 1 else 0.0,
            "min":   round(min(arr), 3),
            "max":   round(max(arr), 3),
            "runs":  arr,
        }

    return {k: stats(v) for k, v in results.items()} | {"status": "completed", "runs_completed": 5}


@app.get("/info")
async def info():
    return {
        "name": "Fellow Buffalo",
        "version": "1.0.0",
        "description": "Email triage RL environment",
        "observation_space": {
            "task_id": "int 1-5", "step": "int", "email_subject": "str",
            "email_body": "str", "attachment_texts": "dict", "deadline": "str|null",
            "difficulty": "int 1-3", "hint": "str|null", "episode_history": "list",
            "metadata": "dict (storage, simulated_date)", "done": "bool", "reward": "float",
        },
        "action_space": {
            "task_1": "tab + color + deadline + confidence",
            "task_2": "summary + tag_cloud",
            "task_3": "lifecycle_decisions[{color,group,account,trigger_relay}]",
            "task_4": "reply",
            "task_5": "email_ranking (list of email IDs)",
        },
        "reward_range": [-0.1, 0.99],
        "tasks": [
            {"id": 1, "name": "email-intake",        "difficulty": "easy",   "max_steps": 5},
            {"id": 2, "name": "metadata-generation", "difficulty": "medium", "max_steps": 1},
            {"id": 3, "name": "lifecycle-manager",   "difficulty": "hard",   "max_steps": 15},
            {"id": 4, "name": "reply-generation",    "difficulty": "medium", "max_steps": 1},
            {"id": 5, "name": "priority-ranking",    "difficulty": "hard",   "max_steps": 1},
        ],
        "novel_mechanic": "Storage relay (15 GB Gmail simulation) + simulated date progression for temporal RL.",
    }


@app.get("/grader")
async def grader() -> Dict[str, float]:
    return {"score": last_reward}


@app.get("/web", response_class=HTMLResponse)
async def web_interface():
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
            select, input { padding: 8px; margin: 5px; border: 1px solid #ccc; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>🐃 Fellow Buffalo — Email Triage OpenEnv</h1>
        <p>Use the <a href="/gradio">Gradio UI</a> for a richer interface.</p>
        <div>
            <h2>Reset</h2>
            <select id="task-id">
                <option value="1">Task 1 — Classification (Easy, 5 steps)</option>
                <option value="2">Task 2 — Metadata (Medium, 1 step)</option>
                <option value="3">Task 3 — Lifecycle (Hard, 15 steps)</option>
                <option value="4">Task 4 — Reply (Medium, 1 step)</option>
                <option value="5">Task 5 — Ranking (Hard, 1 step)</option>
            </select>
            <button onclick="reset()">Reset</button>
        </div>
        <div>
            <h2>Observation</h2>
            <pre id="observation">Click Reset to start.</pre>
        </div>
        <div>
            <h2>Action (Task 1)</h2>
            <select id="tab">
                <option>Jobs</option><option>Internships</option><option>News</option>
                <option>Sports</option><option>Events</option><option>Finance</option><option>General</option>
            </select>
            <select id="color"><option>green</option><option>orange</option><option>red</option></select>
            <input id="deadline" placeholder="Deadline ISO (or blank)" style="width:250px">
            <button onclick="doStep()">Step</button>
        </div>
        <div>
            <h2>Result</h2>
            <pre id="result">—</pre>
        </div>
        <script>
            let taskId = 1;
            async function reset() {
                taskId = parseInt(document.getElementById("task-id").value);
                const r = await fetch("/reset", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({task_id:taskId})});
                document.getElementById("observation").textContent = JSON.stringify(await r.json(), null, 2);
                document.getElementById("result").textContent = "Ready.";
            }
            async function doStep() {
                const action = {task_id:taskId,tab:document.getElementById("tab").value,color:document.getElementById("color").value,deadline:document.getElementById("deadline").value||null};
                const r = await fetch("/step",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({action})});
                const d = await r.json();
                document.getElementById("observation").textContent = JSON.stringify(d.observation, null, 2);
                document.getElementById("result").textContent = "Reward: "+d.reward+"  Done: "+d.done;
            }
        </script>
    </body>
    </html>
    """


@app.get("/debug")
async def debug():
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("HF_TOKEN")
    client, model = get_ai_client()
    result = {
        "groq_key":   bool(os.getenv("GROQ_API_KEY")),
        "openai_key": bool(os.getenv("OPENAI_API_KEY")),
        "hf_token":   bool(os.getenv("HF_TOKEN")),
        "client":     client is not None,
        "model":      model,
        "test_call":  None,
    }
    if client:
        try:
            resp = client.chat.completions.create(
                model=model, messages=[{"role": "user", "content": "Say OK"}],
                max_tokens=5, temperature=0,
            )
            result["test_call"] = resp.choices[0].message.content
        except Exception as e:
            result["test_call"] = f"Error: {e}"
    return result


def main():
    import uvicorn
    print("Starting Fellow Buffalo OpenEnv Server…")
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()