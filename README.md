---

---

title: Fellow Buffalo
emoji: 📧
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
tags:

* openenv
* email
* nlp
* real-world
* rl
* llm

---

# Fellow Buffalo — AI Email Operating System

An intelligent multi-task AI environment where agents learn to triage, understand, and manage emails like a real-world email system.

---

##  Overview

Fellow Buffalo simulates a real-world email inbox where an AI agent must:

* Classify emails
* Extract structured information
* Manage lifecycle decisions
* Generate replies
* Rank priorities

Built for OpenEnv evaluation, this environment enables testing LLM-based agents under realistic conditions with **curriculum learning**, **temporal reasoning**, and **storage-aware decisions**.

---

##  Tasks

| Task | Name                | Description                            | Max Score |
| ---- | ------------------- | -------------------------------------- | --------- |
| 1    | Email Intake        | Classify emails (tab, color, deadline) | 5.0      |
| 2    | Metadata Generation | Generate summary & tag cloud           | 1.0       |
| 3    | Lifecycle Manager   | Multi-email lifecycle decisions        | 1.0      |
| 4    | Reply Generation    | Generate professional replies          | 1.0       |
| 5    | Priority Ranking    | Rank emails by importance              | 1.0       |

---

## Reward Design

### Task 1 (Multi-step)

* +0.33 → Correct tab
* +0.33 → Correct color
* +0.34 → Correct deadline

Total score is the sum across multiple emails (~5 max).

**Enhancements:**

* Alias matching (e.g., Internship = Internships)
* Deadline tolerance (±3 days)
* Difficulty progression (easy → medium → hard)

---

### Task 2

* 0.5 → Summary quality (AI-graded)
* 0.5 → Tag cloud quality (AI-graded)

---

### Task 3

* Color correctness: +0.1 / -0.05
* Account routing: up to 0.1
* Storage relay: up to 0.1
* Grouping accuracy: up to 0.15
* Thread consistency: up to 0.05

**Enhancements:**

* Simulated time progression
* Storage monitoring (15GB limit)
* Auto account switching

---

### Task 4

* Reply quality
* Professional tone
* Completeness

---

### Task 5

* Ranking accuracy

---

##  Action Space

| Field               | Type   | Description                                                     |
| ------------------- | ------ | --------------------------------------------------------------- |
| task_id             | int    | Task identifier (1–5)                                           |
| tab                 | string | Jobs / Internships / News / Sports / Events / Finance / General |
| color               | string | green / orange / red                                            |
| deadline            | string | ISO datetime or null                                            |
| confidence          | int    | 0-100 confidence score (Task 1)                                 |
| summary             | string | Email summary                                                   |
| tag_cloud           | string | Pipe-separated keywords                                         |
| lifecycle_decisions | list   | Task 3 decisions                                                |
| reply               | string | Task 4 reply                                                    |
| email_ranking       | list   | Task 5 ranking                                                  |

---

##  Observation Space

| Field            | Type   | Description                        |
| ---------------- | ------ | ---------------------------------- |
| email_subject    | string | Email subject                      |
| email_body       | string | Email content                      |
| attachment_texts | dict   | Parsed attachments                 |
| deadline         | string | Extracted deadline                 |
| difficulty       | int    | 1=easy, 2=medium, 3=hard           |
| hint             | string | Smart hint after wrong answer      |
| episode_history  | list   | Last 3 steps (actions & rewards)   |
| metadata         | dict   | Storage info, simulated date, etc. |
| done             | bool   | Episode completion flag            |

---

##  New Features (v2.0)

* Episode history tracking
* Difficulty progression (curriculum learning)
* Smart hints for guidance
* Benchmark mode (`/benchmark`)
* Info endpoint (`/info`)
* Deterministic runs using seed
* Gradio UI integration

---

##  Evaluation (IMPORTANT)

Run:

```
python inference.py
```

### Required Output Format

```
[START] task=<task_name>
[STEP] step=<n> reward=<value>
[END] task=<task_name> score=<total> steps=<n>
```

### Rules

* Only structured output to stdout
* Debug logs allowed in stderr
* No JSON output
* Extra output will fail evaluation

---

##  Project Structure

```
fellow-buffalo-env/
├── inference.py
├── environment.py
├── models.py
├── app.py
├── gradio_app.py
├── tasks.py
├── test_emails/
├── client.py
├── Dockerfile
└── requirements.txt
```

---

##  Run Locally

```
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 7860
```

Then:

```
python inference.py
```

---

##  Interfaces

| URL                                                                | Interface |
| ------------------------------------------------------------------ | --------- |
| [http://localhost:7860/](http://localhost:7860/)                   | API Root  |
| [http://localhost:7860/gradio](http://localhost:7860/gradio)       | Gradio UI |
| [http://localhost:7860/web](http://localhost:7860/web)             | HTML UI   |
| [http://localhost:7860/info](http://localhost:7860/info)           | Info      |
| [http://localhost:7860/benchmark](http://localhost:7860/benchmark) | Benchmark |

---

##  Docker Setup

```
docker build -t fellow-buffalo .
docker run -p 7860:7860 --env-file .env fellow-buffalo
```

---

##  Environment Variables

* GROQ_API_KEY
* OPENAI_API_KEY
* HF_TOKEN
* API_BASE_URL
* MODEL_NAME
* ENV_URL

---

## API Endpoints

| Method | Endpoint     | Description            |
| ------ | ------------ | ---------------------- |
| GET    | `/`          | Root                   |
| GET    | `/health`    | Health                 |
| POST   | `/reset`     | Reset (seed supported) |
| POST   | `/step`      | Take action            |
| GET    | `/state`     | Current state          |
| GET    | `/tasks`     | Tasks list             |
| POST   | `/baseline`  | Run baseline           |
| POST   | `/benchmark` | Benchmark              |
| GET    | `/info`      | Full info              |
| GET    | `/grader`    | Score                  |
| GET    | `/web`       | HTML UI                |
| GET    | `/gradio`    | Gradio UI              |

---

##  Key Highlights

* Real-world email simulation
* Multi-step RL tasks
* Curriculum learning enabled
* Temporal reasoning
* Storage-aware decisions
* LLM-based automation
* Reproducible experiments

---

## Use Cases

* AI agent training
* Email automation
* LLM benchmarking
* Reinforcement learning research
* Curriculum learning experiments

---

##  Submission Note

This project follows OpenEnv evaluation requirements:

* Structured stdout output
* Multi-task execution
* Deterministic scoring

---

##  Changelog

### v2.0 (April 2026)

* Added episode history
* Added difficulty progression
* Added smart hints
* Added benchmark & info endpoints
* Added deterministic mode
* Added Gradio UI

### v1.0 (March 2026)

* Initial release
* 5-task system
* OpenEnv compatibility

---

##  Acknowledgments

Built for **Meta PyTorch Hackathon x Scaler School of Technology**

---
