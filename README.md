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

# 📧 Fellow Buffalo — AI Email Operating System

An intelligent multi-task AI environment where agents learn to **triage, understand, and manage emails like a real-world email system**.

---

## 🚀 Overview

Fellow Buffalo simulates a real-world email inbox where an AI agent must:

* Classify emails
* Extract structured information
* Manage lifecycle decisions
* Generate replies
* Rank priorities

Built for **OpenEnv evaluation**, this environment enables testing **LLM-based decision agents** under realistic conditions.

---

## 🧠 Tasks

| Task | Name                | Description                            | Max Score |
| ---- | ------------------- | -------------------------------------- | --------- |
| 1    | Email Intake        | Classify emails (tab, color, deadline) | ~5.0      |
| 2    | Metadata Generation | Generate summary & tag cloud           | 1.0       |
| 3    | Lifecycle Manager   | Multi-email lifecycle decisions        | ~1.0      |
| 4    | Reply Generation    | Generate professional replies          | 1.0       |
| 5    | Priority Ranking    | Rank emails by importance              | 1.0       |

---

## 📊 Reward Design

### Task 1 (Multi-step)

* +0.33 → Correct tab
* +0.33 → Correct color
* +0.34 → Correct deadline

👉 Total score = **sum over multiple emails (~5 max)**

---

### Task 2

* 0.5 → Summary quality
* 0.5 → Tag cloud quality

---

### Task 3

* Per-step lifecycle reward
* Temporal reasoning + storage awareness

---

### Task 4

* Reply quality
* Professional tone

---

### Task 5

* Ranking accuracy

---

## ⚙️ Action Space

| Field                 | Type   | Description                                                     |
| --------------------- | ------ | --------------------------------------------------------------- |
| `task_id`             | int    | Task identifier (1–5)                                           |
| `tab`                 | string | Jobs / Internships / News / Sports / Events / Finance / General |
| `color`               | string | green / orange / red                                            |
| `deadline`            | string | ISO datetime or null                                            |
| `summary`             | string | Email summary                                                   |
| `tag_cloud`           | string | Keywords                                                        |
| `lifecycle_decisions` | list   | Task 3 decisions                                                |
| `reply`               | string | Task 4 reply                                                    |
| `email_ranking`       | list   | Task 5 ranking                                                  |

---

## 📥 Observation Space

| Field              | Type   | Description        |
| ------------------ | ------ | ------------------ |
| `email_subject`    | string | Subject            |
| `email_body`       | string | Content            |
| `attachment_texts` | dict   | Attachments        |
| `deadline`         | string | Extracted deadline |
| `done`             | bool   | Episode finished   |

---

## 🧪 Evaluation (IMPORTANT)

The evaluator runs:

```bash
python inference.py
```

### ✅ Required Output Format (STRICT)

```text
[START] task=<task_name>
[STEP] step=<n> reward=<value>
[END] task=<task_name> score=<total> steps=<n>
```

### ⚠️ Rules

* ONLY structured lines in stdout
* No logs / prints / JSON
* Any extra output → ❌ FAIL

---

## 🏗️ Project Structure

```
fellow-buffalo-env/
│
├── inference.py        # 🚨 Main evaluation script
├── environment.py      # Core environment logic
├── models.py           # Action schemas
├── app.py              # FastAPI server
├── server/             # Backend logic
├── test_emails/        # Email datasets
├── tasks.py            # Task definitions
├── Dockerfile
└── requirements.txt
```

---

## ▶️ Run Locally

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 7860
```

Then in another terminal:

```bash
python inference.py
```

---

## 🐳 Docker Setup

```bash
docker build -t fellow-buffalo .
docker run -p 7860:7860 --env-file .env fellow-buffalo
```

---

## 🔐 Environment Variables

| Variable     | Description        |
| ------------ | ------------------ |
| GROQ_API_KEY | API key (dev)      |
| API_BASE_URL | Judge endpoint     |
| MODEL_NAME   | Model used         |
| HF_TOKEN     | Hugging Face token |

---

## 🌟 Key Highlights

* Real-world email simulation
* Multi-step RL-compatible tasks
* Temporal + storage reasoning
* LLM-powered decision making
* Strict evaluation pipeline

---

## 🎯 Use Cases

* AI Agents & Autonomous Systems
* Email Automation
* LLM Evaluation
* Reinforcement Learning

---

## 🏆 Submission Note

This project strictly follows **OpenEnv evaluation requirements**, including:

* Structured stdout output
* Multi-task execution
* Deterministic scoring

---
