---
title: Fellow Buffalo
emoji: 📧
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
tags:
  - openenv
  - email
  - nlp
  - real-world
  - rl
  - llm
---

# 🐃 Fellow Buffalo — AI Email Triage OpenEnv

An intelligent multi-task RL environment where agents learn to triage, understand, and manage emails like a real-world email operating system.

Built for the **Meta PyTorch Hackathon × Scaler School of Technology** on the OpenEnv framework.

---

## Overview

Fellow Buffalo simulates a real-world email inbox across five tasks of increasing difficulty. An AI agent must classify emails, extract metadata, manage lifecycle decisions over time, generate replies, and rank priorities — all with honest, calibrated rewards.

---

## Baseline Scores (llama-3.3-70b-versatile)

| Task | Name | Steps | Score Range | Difficulty |
|------|------|-------|-------------|------------|
| 1 | Email Intake | 5 | 0.54 – 0.68 | Easy |
| 2 | Metadata Generation | 1 | 0.65 – 0.85 | Medium |
| 3 | Lifecycle Manager | **15** | 0.52 – 0.72 | Hard |
| 4 | Reply Generation | 1 | 0.90 | Medium |
| 5 | Priority Ranking | 1 | 0.75 – 0.99 | Hard |

Scores vary per run due to randomized email selection. Task 4 is stable because reply quality is consistently high.

---

## Tasks

### Task 1 — Email Intake (Easy, 5 steps)
Agent receives 5 emails in curriculum order (easy → medium → hard) and must classify each:
- **tab**: Jobs / Internships / News / Sports / Events / Finance / General
- **color**: green (future deadline) / orange (0–7 days past) / red (7+ days past)
- **deadline**: ISO datetime or null
- **confidence**: 0–100

Supports alias matching (e.g. "Internship" accepted for "Internships") and deadline tolerance (±3 days).

### Task 2 — Metadata Generation (Medium, 1 step)
Agent receives email + parsed attachment texts and must produce:
- **summary**: 2–3 sentence description capturing company, amounts, dates, action needed
- **tag_cloud**: pipe-separated specific keywords (e.g. `meta|internship|deadline|stipend`)

Graded by AI (Groq) on relevance, specificity, and completeness.

### Task 3 — Lifecycle Manager (Hard, 15 steps)
Agent manages 15 emails with simulated time advancing each step. Storage fills up over the episode. Agent must decide per email:
- **color**: based on simulated date vs deadline
- **group**: internships_q1 / jobs_q1 / finance_q1 / events_q1 / news_q1 / general_q1
- **account**: primary or archive
- **trigger_relay**: true only when storage exceeds 14 GB (simulates Gmail 15GB limit)

Final score is normalized total across all 15 steps. Negative rewards possible for wrong decisions.

### Task 4 — Reply Generation (Medium, 1 step)
Agent writes a professional reply to an email. Graded by AI on relevance, professionalism, completeness, and clarity.

### Task 5 — Priority Ranking (Hard, 1 step)
Agent receives 10 shuffled emails and ranks them by urgency. Scored by position accuracy — closer to correct position = more points.

---

## Reward Design

### Task 1
- +0.33 correct tab (+ confidence bonus)
- +0.33 correct color
- +0.34 correct deadline (partial credit for close dates)
- Penalties for wrong answers scaled by confidence

### Task 2
- 0.5 × summary score (AI-graded 0–1)
- 0.5 × tag cloud score (AI-graded 0–1)
- Floor: minimum 0.45 for non-empty reasonable responses

### Task 3 (per step, then normalized)
- +0.05 correct color / −0.02 wrong
- +0.05 correct group / −0.02 wrong
- +0.02 correct storage relay / −0.03 missed relay when critical
- Final score = total / (15 × 0.12), range 0.01–0.99

### Task 4
- AI-graded 0.0–1.0 on relevance, tone, completeness, clarity

### Task 5
- Position-based: +0.10 exact / +0.07 off-by-1 / +0.04 off-by-2 / +0.02 off-by-3-4 / +0.01 far off

---

## Action Space

| Field | Type | Tasks | Description |
|-------|------|-------|-------------|
| task_id | int | all | 1–5 |
| tab | string | 1 | Jobs / Internships / News / Sports / Events / Finance / General |
| color | string | 1, 3 | green / orange / red |
| deadline | string | 1 | ISO datetime or null |
| confidence | int | 1 | 0–100 |
| summary | string | 2 | Email summary |
| tag_cloud | string | 2 | Pipe-separated keywords |
| lifecycle_decisions | list | 3 | [{color, group, account, trigger_relay}] |
| reply | string | 4 | Professional reply text |
| email_ranking | list | 5 | Email IDs in priority order |

---

## Observation Space

| Field | Type | Description |
|-------|------|-------------|
| email_subject | string | Email subject line |
| email_body | string | Email body text |
| attachment_texts | dict | Parsed attachment content by filename |
| deadline | string | Extracted deadline or null |
| difficulty | int | 1=easy, 2=medium, 3=hard |
| hint | string | Smart hint after wrong answer (Task 1) |
| episode_history | list | Last 3 steps with actions and rewards |
| metadata | dict | Storage info, simulated date, total steps |
| done | bool | Episode completion flag |
| reward | float | Step reward (populated after step) |

---

## Novel Mechanics

**Storage Relay** — simulates Gmail's 15GB limit. As the agent processes emails over 15 steps, storage fills up. When it exceeds 14GB, the agent must trigger a relay to switch accounts. Failing to relay when critical is penalized. This mechanic does not exist in any other RL email environment.

**Simulated Time Progression** — each step in Task 3 advances the simulated date by 1 day, starting from April 9, 2026. The correct color for each email is computed against this simulated date, not the real date — forcing the agent to reason temporally.

**Curriculum Learning** — Task 1 presents emails in easy → medium → hard order, with difficulty-tier shuffling each episode so the agent sees different emails every run.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root info |
| GET | `/health` | Health check + API key status |
| POST | `/reset` | Reset episode (supports `seed` parameter) |
| POST | `/step` | Take action, get reward |
| GET | `/state` | Current episode state |
| GET | `/tasks` | All 5 task definitions |
| POST | `/baseline` | Run AI baseline on all tasks |
| POST | `/benchmark` | Run 5× benchmark with mean + stdev |
| GET | `/info` | Full environment info for researchers |
| GET | `/grader` | Last episode score |
| GET | `/web` | HTML UI for manual testing |
| GET | `/gradio` | Gradio UI |
| GET | `/debug` | API key + connectivity debug |

---

## Quick Start

```bash
pip install -r requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 7860
python inference.py
```

---

## Docker

```bash
docker build -t fellow-buffalo .
docker run -p 7860:7860 --env-file .env fellow-buffalo
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| GROQ_API_KEY | Yes (local) | For Task 2 and Task 4 AI grading |
| OPENAI_API_KEY | Alternative | OpenAI instead of Groq |
| HF_TOKEN | HF Space | Auto-injected on HF Spaces |
| API_BASE_URL | Optional | Custom model endpoint |
| MODEL_NAME | Optional | Default: llama-3.3-70b-versatile |
| ENV_URL | Optional | inference.py target (default: localhost:7860) |

---

## Project Structure

```
fellow-buffalo-env/
├── inference.py        ← baseline agent (judges run this)
├── environment.py      ← reset(), step(), state() logic
├── models.py           ← Action, Observation, State classes
├── tasks.py            ← 5 task graders
├── app.py              ← FastAPI server (root copy)
├── gradio_app.py       ← Gradio UI
├── client.py           ← HTTP client (pip installable)
├── openenv.yaml        ← metadata manifest
├── Dockerfile
├── requirements.txt
├── pyproject.toml
└── test_emails/        ← 37 JSON email files across all tasks
    ├── e01–e22         ← base emails (Tasks 1–3)
    ├── adv01–adv07     ← adversarial emails
    ├── thr01–thr05     ← thread-aware emails
    ├── att01–att03     ← attachment emails
    ├── task3_*         ← lifecycle emails (green/orange/red)
    └── task4_*, task5_* ← reply and ranking emails
```

---

## Interfaces

| URL | Interface |
|-----|-----------|
| `http://localhost:7860/` | API Root |
| `http://localhost:7860/gradio` | Gradio UI |
| `http://localhost:7860/web` | HTML UI |
| `http://localhost:7860/info` | Full info |
| `http://localhost:7860/benchmark` | Benchmark |

---

## Changelog

### v2.1 (April 2026)
- Task 3 fixed to always run exactly 15 steps
- Task 3 score normalized honestly (total / max_possible)
- Task 1 normalization fixed (per-email average vs max possible)
- Task 5 baseline improved — AI now ranks by email IDs directly
- Task 2 floor raised to 0.45 for non-empty responses
- Gradio mount order fixed (CORS before Gradio)
- Task 3 email queue uses separate list, no mutation bug

### v2.0 (April 2026)
- Episode history tracking
- Difficulty progression (curriculum learning)
- Smart hints after wrong answers
- Benchmark and info endpoints
- Deterministic mode via seed parameter
- Gradio UI integration
- Storage relay mechanic

### v1.0 (March 2026)
- Initial release
- 5-task system
- OpenEnv compatibility

---

## Acknowledgments

Built for **Meta PyTorch Hackathon × Scaler School of Technology**

OpenEnv framework by Hugging Face × Meta