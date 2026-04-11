"""
Fellow Buffalo - Gradio Web Interface
Professional UI for the OpenEnv environment.
Mounts cleanly under FastAPI via gr.mount_gradio_app.
"""

import gradio as gr
import httpx
import json
import os


def get_api_base() -> str:
    """Resolve API base URL — works locally and on HF Spaces."""
    space_host = os.getenv("SPACE_HOST", "").strip()
    if space_host:
        base = f"https://{space_host}"
    else:
        base = os.getenv("API_BASE_URL", "http://localhost:7860")
    return base.rstrip("/")




# ------------------------------------------------------------------ #
#  API helpers
# ------------------------------------------------------------------ #

def _post(path: str, body: dict) -> dict:
    try:
        r = httpx.post(f"{get_api_base()}{path}", json=body, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        return {"error": str(exc)}


def _get(path: str) -> dict:
    try:
        r = httpx.get(f"{get_api_base()}{path}", timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        return {"error": str(exc)}


# ------------------------------------------------------------------ #
#  Gradio callback functions
# ------------------------------------------------------------------ #

def reset_env(task_id: str):
    data = _post("/reset", {"task_id": int(task_id)})
    if "error" in data:
        return (
            json.dumps(data, indent=2),
            f"❌ Reset failed: {data['error']}",
            "", "", "",
        )
    subject  = data.get("email_subject", "")
    body     = data.get("email_body", "")[:600]
    deadline = str(data.get("deadline") or "No deadline")
    msg = f"✅ Task {task_id} ready — {data.get('step', 0)} steps done"
    if task_id == "3":
        msg += f" | simulated date: {data.get('metadata', {}).get('simulated_date', '')}"
    if task_id == "5":
        ids = data.get("metadata", {}).get("emails_to_rank", [])
        subj_map = data.get("metadata", {}).get("email_subjects", {})
        ranked_display = "\n".join(
            f"{i+1}. [{eid}] {subj_map.get(eid, 'Unknown')}"
            for i, eid in enumerate(ids)
        )
        body = f"Emails to rank (shuffled order):\n\n{ranked_display}"
    return json.dumps(data, indent=2), msg, subject, body, deadline


def take_action(task_id: str, tab: str, color: str, deadline_input: str,
                summary: str, tag_cloud: str, reply: str, ranking: str):
    task_id_int = int(task_id)
    action: dict = {"task_id": task_id_int}

    if task_id == "1":
        action.update({
            "tab":      tab or None,
            "color":    color or None,
            "deadline": deadline_input.strip() or None,
        })
    elif task_id == "2":
        action.update({
            "summary":   summary or None,
            "tag_cloud": tag_cloud or None,
        })
    elif task_id == "3":
        action.update({
            "lifecycle_decisions": [{
                "color":         color or "green",
                "group":         "general_q1",
                "account":       "primary",
                "trigger_relay": False,
            }]
        })
    elif task_id == "4":
        action.update({"reply": reply or "Thank you for your email."})
    elif task_id == "5":
        # ranking is comma-separated numbers like "1,3,2,..."
        try:
            nums = [int(x.strip()) for x in ranking.split(",") if x.strip()]
            # convert position numbers to email IDs via the last reset
            obs_data = _get("/state")
            # we can't recover email IDs from state easily, so just send the raw list
            action.update({"email_ranking": [str(n) for n in nums]})
        except Exception:
            action.update({"email_ranking": []})

    data = _post("/step", {"action": action})
    if "error" in data:
        return json.dumps(data, indent=2), f"❌ Step failed: {data['error']}", "", "", ""

    obs    = data.get("observation", {})
    reward = data.get("reward", 0)
    done   = data.get("done", False)
    subject  = obs.get("email_subject", "")
    body     = obs.get("email_body", "")[:600]
    deadline = str(obs.get("deadline") or "No deadline")
    msg = f"💰 Reward: {reward:.4f}  |  {'✅ Episode done!' if done else '⏳ Continue...'}"
    if not done and task_id == "3":
        meta = obs.get("metadata", {})
        msg += f"  |  simulated date: {meta.get('simulated_date', '')}"
        msg += f"  |  storage: {meta.get('storage_used_gb', 0):.1f} GB"
    return json.dumps(obs, indent=2), msg, subject, body, deadline


def get_state():
    return json.dumps(_get("/state"), indent=2)


def get_tasks():
    return json.dumps(_get("/tasks"), indent=2)


def get_health():
    data = _get("/health")
    ok   = "error" not in data and data.get("status") == "healthy"
    api  = data.get("api_key_configured", False)
    return f"{'✅' if ok else '❌'} {'Healthy' if ok else 'Unhealthy'}  |  API key: {'✓' if api else '✗'}"


def run_baseline():
    data = _post("/baseline", {})
    if "error" in data:
        return f"❌ {data['error']}"
    lines = [
        f"Task 1 — Email Intake:        {data.get('task_1', 0):.4f}",
        f"Task 2 — Metadata Gen:        {data.get('task_2', 0):.4f}",
        f"Task 3 — Lifecycle Manager:   {data.get('task_3', 0):.4f}",
        f"Task 4 — Reply Generation:    {data.get('task_4', 0):.4f}",
        f"Task 5 — Priority Ranking:    {data.get('task_5', 0):.4f}",
        f"Status: {data.get('status', 'unknown')}",
    ]
    return "\n".join(lines)


# ------------------------------------------------------------------ #
#  Build Gradio UI
# ------------------------------------------------------------------ #

with gr.Blocks(
    title="🐃 Fellow Buffalo — Email Triage OpenEnv",
    theme=gr.themes.Soft(),
    css=".label-wrap { font-weight: 600; }",
) as demo:

    gr.Markdown("""
# 🐃 Fellow Buffalo — Email Triage OpenEnv

An RL training environment for email management. Five tasks, increasing difficulty.

| Task | Name | Steps | Difficulty |
|------|------|-------|------------|
| 1 | Email Classification | 5 | Easy |
| 2 | Metadata Generation | 1 | Medium |
| 3 | Lifecycle Manager | **15** | Hard |
| 4 | Reply Generation | 1 | Medium |
| 5 | Priority Ranking | 1 | Hard |
""")

    with gr.Row():
        # ---- Left panel: controls ----
        with gr.Column(scale=1):
            gr.Markdown("### 🎮 Environment Controls")

            task_id = gr.Dropdown(
                choices=[
                    ("Task 1 — Email Classification (Easy)", "1"),
                    ("Task 2 — Metadata Generation (Medium)", "2"),
                    ("Task 3 — Lifecycle Manager (Hard, 15 steps)", "3"),
                    ("Task 4 — Reply Generation (Medium)", "4"),
                    ("Task 5 — Priority Ranking (Hard)", "5"),
                ],
                label="Select Task",
                value="1",
            )

            with gr.Row():
                reset_btn   = gr.Button("🔄 Reset", variant="primary")
                health_btn  = gr.Button("❤️ Health")
                baseline_btn = gr.Button("🤖 Run Baseline")

            with gr.Row():
                state_btn = gr.Button("📊 State")
                tasks_btn = gr.Button("📋 Tasks")

            gr.Markdown("---")
            gr.Markdown("### ✏️ Action")

            tab = gr.Dropdown(
                choices=["Jobs", "Internships", "News", "Sports", "Events", "Finance", "General"],
                label="Tab (Task 1)",
                value="General",
            )
            color = gr.Dropdown(
                choices=["green", "orange", "red"],
                label="Color (Tasks 1 & 3)",
                value="green",
            )
            deadline_input = gr.Textbox(
                label="Deadline ISO (Task 1, leave blank if none)",
                placeholder="2026-04-30T23:59:00",
            )
            summary = gr.Textbox(
                label="Summary (Task 2)",
                lines=3,
                placeholder="Summarise the email here…",
            )
            tag_cloud = gr.Textbox(
                label="Tag Cloud (Task 2, pipe-separated)",
                placeholder="internship|meta|deadline",
            )
            reply = gr.Textbox(
                label="Reply (Task 4)",
                lines=5,
                placeholder="Dear Sir/Madam,\n\nThank you for your email…",
            )
            ranking = gr.Textbox(
                label="Priority Ranking (Task 5, comma-separated positions)",
                placeholder="1,2,3,4,5,6,7,8,9,10",
            )

            step_btn = gr.Button("⚡ Take Action", variant="primary")

        # ---- Right panel: output ----
        with gr.Column(scale=1):
            gr.Markdown("### 📧 Current Email")
            email_subject  = gr.Textbox(label="Subject")
            email_body_out = gr.Textbox(label="Body / Context", lines=10)
            email_deadline_out = gr.Textbox(label="Deadline")

            gr.Markdown("### 📊 Output")
            observation_out = gr.Textbox(label="Full Observation JSON", lines=14)
            status_out = gr.Textbox(label="Status / Reward")

    # ---- Wire up events ----
    reset_btn.click(
        fn=reset_env,
        inputs=[task_id],
        outputs=[observation_out, status_out, email_subject, email_body_out, email_deadline_out],
    )
    step_btn.click(
        fn=take_action,
        inputs=[task_id, tab, color, deadline_input, summary, tag_cloud, reply, ranking],
        outputs=[observation_out, status_out, email_subject, email_body_out, email_deadline_out],
    )
    health_btn.click(fn=get_health,   inputs=[], outputs=[status_out])
    state_btn.click( fn=get_state,    inputs=[], outputs=[observation_out])
    tasks_btn.click( fn=get_tasks,    inputs=[], outputs=[observation_out])
    baseline_btn.click(fn=run_baseline, inputs=[], outputs=[status_out])


# app.py imports `demo` from here — no __main__ block needed