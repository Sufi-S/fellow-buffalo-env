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
---

# 📧 Fellow Buffalo — AI Email Operating System

An intelligent multi-task AI environment where agents learn to triage, understand, and manage emails like a real-world email system.

---

## 🚀 Overview

Fellow Buffalo simulates a real-world email inbox where an AI agent must:

* Classify emails
* Extract structured information
* Manage lifecycle decisions
* Generate replies
* Rank priorities

Built for OpenEnv evaluation, this environment enables testing LLM-based agents under realistic conditions.

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

Total score is the sum across multiple emails (~5 max).

---

### Task 2

* 0.5 → Summary quality
* 0.5 → Tag cloud quality

---

### Task 3

* Multi-step lifecycle rewards
* Temporal reasoning
* Storage-aware decisions

---

### Task 4

* Reply quality
* Professional tone

---

### Task 5

* Ranking accuracy

---

## ⚙️ Action Space

| Field               | Type   | Description                                                     |
| ------------------- | ------ | --------------------------------------------------------------- |
| task_id             | int    | Task identifier (1–5)                                           |
| tab                 | string | Jobs / Internships / News / Sports / Events / Finance / General |
| color               | string | green / orange / red                                            |
| deadline            | string | ISO datetime or null                                            |
| summary             | string | Email summary                                                   |
| tag_cloud           | string | Keywords                                                        |
| lifecycle_decisions | list   | Task 3 decisions                                                |
| reply               | string | Task 4 reply                                                    |
| email_ranking       | list   | Task 5 ranking                                                  |

---

## 📥 Observation Space

| Field            | Type   | Description             |
| ---------------- | ------ | ----------------------- |
| email_subject    | string | Email subject           |
| email_body       | string | Email content           |
| attachment_texts | dict   | Parsed attachments      |
| deadline         | string | Extracted deadline      |
| done             | bool   | Episode completion flag |

---

## 🧪 Evaluation (IMPORTANT)

Run:

```bash
python inference.py
```

### Required Output Format

```text
[START] task=<task_name>
[STEP] step=<n> reward=<value>
[END] task=<task_name> score=<total> steps=<n>
```

### Rules

* Only structured output
* No logs or debug prints
* No JSON output
* Extra output will fail evaluation

---

## 🏗️ Project Structure

```
fellow-buffalo-env/
├── inference.py
├── environment.py
├── models.py
├── app.py
├── server/
├── test_emails/
├── tasks.py
├── Dockerfile
└── requirements.txt
```

---

## ▶️ Run Locally

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 7860
```

Then:

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

* GROQ_API_KEY
* API_BASE_URL
* MODEL_NAME
* HF_TOKEN

---

## 🌟 Key Highlights

* Real-world email simulation
* Multi-step decision tasks
* RL-friendly environment
* OpenEnv compatible
* LLM-based automation

---

## 🎯 Use Cases

* AI agent training
* Email automation
* LLM benchmarking
* Reinforcement learning

---

## 🏆 Submission Note

This project follows OpenEnv evaluation requirements:

* Structured stdout output
* Multi-task execution
* Deterministic scoring

---
