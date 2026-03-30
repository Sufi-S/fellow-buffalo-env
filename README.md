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

---

#  Fellow Buffalo — OpenEnv Email Triage Environment

An AI training environment where agents learn to manage emails like a real-world email operating system.

---

##  Real-World Motivation

Email triage is a daily task for professionals.
Fellow Buffalo trains AI agents to automate:

* Email classification
* Information extraction
* Lifecycle management

---

##  Action Space

| Field                 | Type   | Description                                                     |
| --------------------- | ------ | --------------------------------------------------------------- |
| `task_id`             | int    | Task identifier (1, 2, or 3)                                    |
| `tab`                 | string | Jobs / Internships / News / Sports / Events / Finance / General |
| `color`               | string | Priority: green / orange / red                                  |
| `deadline`            | string | ISO datetime or `null`                                          |
| `summary`             | string | AI-generated email summary                                      |
| `tag_cloud`           | string | Pipe-separated keywords                                         |
| `lifecycle_decisions` | list   | Decisions for Task 3 (color + grouping)                         |

---

##  Observation Space

| Field              | Type   | Description                 |
| ------------------ | ------ | --------------------------- |
| `email_subject`    | string | Email subject line          |
| `email_body`       | string | Email content               |
| `attachment_texts` | dict   | Parsed attachment content   |
| `deadline`         | string | Extracted deadline (if any) |
| `done`             | bool   | Episode completion flag     |

---

##  Tasks

| Task   | Difficulty | Description                           | Max Score |
| ------ | ---------- | ------------------------------------- | --------- |
| Task 1 | Easy       | Classify email (tab, color, deadline) | 1.0       |
| Task 2 | Medium     | Generate summary and tag cloud        | 1.0       |
| Task 3 | Hard       | Manage lifecycle across 10 emails     | 1.0       |

---

##  Reward Design

### Task 1

* +0.33 → Correct tab
* +0.33 → Correct color
* +0.34 → Correct deadline

### Task 2

* 0.5 → Summary quality
* 0.5 → Tag cloud quality

### Task 3

* +0.1 → Per correct lifecycle decision (max 0.8)
* +0.2 → Correct grouping

---

##  Baseline Performance

| Task   | Score |
| ------ | ----- |
| Task 1 | 0.67  |
| Task 2 | 0.84  |
| Task 3 | 0.80  |

---

##  API Endpoints

| Endpoint    | Method | Description                |
| ----------- | ------ | -------------------------- |
| `/health`   | GET    | Health check               |
| `/reset`    | POST   | Start new episode          |
| `/step`     | POST   | Take action and get reward |
| `/state`    | GET    | Current episode state      |
| `/tasks`    | GET    | List all tasks             |
| `/baseline` | POST   | Run baseline agent         |
| `/grader`   | GET    | Get last episode score     |

---

## Quick Start

### Run locally

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 7860
```

---

## 🐳 Docker Setup

Run the project using Docker:

```bash
docker build -t fellow-buffalo .
docker run -p 7860:7860 --env-file .env fellow-buffalo
```

---

##  Environment Variables

| Variable       | Required    | Description            |
| -------------- | ----------- | ---------------------- |
| `GROQ_API_KEY` | Yes (Dev)   | Groq API key           |
| `API_BASE_URL` | Yes (Judge) | LLM API base URL       |
| `MODEL_NAME`   | Yes (Judge) | Model identifier       |
| `HF_TOKEN`     | Yes (Judge) | API / Hugging Face key |

---

##  Key Highlights

* Real-world email automation environment
* Multi-step decision-making tasks
* Reinforcement learning friendly
* Built for OpenEnv evaluation systems
* Supports lifecycle-level reasoning

---

##  Use Cases

* AI Agent Training
* RL-based Decision Systems
* Email Automation Research
* LLM Evaluation Benchmarks

---
