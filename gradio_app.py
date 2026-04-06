"""
Fellow Buffalo - Gradio Web Interface
Professional UI for the OpenEnv environment
"""

import gradio as gr
import httpx
import json

ENV_URL = "https://sufi-sufi-fellow-buffalo-env.hf.space"

# API endpoints
API_BASE = ENV_URL

def reset_env(task_id):
    """Reset the environment for a given task"""
    try:
        response = httpx.post(f"{API_BASE}/reset", json={"task_id": int(task_id)}, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return (
                json.dumps(data, indent=2),
                f"✅ Reset successful! Task {task_id} ready.",
                data.get('email_subject', 'No email'),
                data.get('email_body', 'No content')[:500],
                str(data.get('deadline', 'No deadline'))
            )
        else:
            return f"Error: {response.status_code}", f"Reset failed", "", "", ""
    except Exception as e:
        return f"Error: {e}", f"Connection failed", "", "", ""

def take_action(task_id, tab, color, deadline, summary, tag_cloud, reply, ranking):
    """Take an action in the environment"""
    try:
        # Build action based on task
        action = {"task_id": int(task_id)}
        
        if task_id == "1":
            action.update({
                "tab": tab if tab else None,
                "color": color if color else None,
                "deadline": deadline if deadline else None
            })
        elif task_id == "2":
            action.update({
                "summary": summary if summary else None,
                "tag_cloud": tag_cloud if tag_cloud else None
            })
        elif task_id == "3":
            # For Task 3, need lifecycle_decisions
            action.update({
                "lifecycle_decisions": [{
                    "color": color if color else "green",
                    "group": "general_q1",
                    "account": "primary",
                    "trigger_relay": False
                }]
            })
        elif task_id == "4":
            action.update({
                "reply": reply if reply else "Thank you for your email."
            })
        elif task_id == "5":
            # Parse ranking string like "1,2,3,4,5,6,7,8,9,10"
            ranking_list = [f"email_{x.strip()}" for x in ranking.split(",")] if ranking else []
            action.update({
                "email_ranking": ranking_list
            })
        
        response = httpx.post(f"{API_BASE}/step", json={"action": action}, timeout=30)
        if response.status_code == 200:
            data = response.json()
            obs = data.get('observation', {})
            reward = data.get('reward', 0)
            done = data.get('done', False)
            
            return (
                json.dumps(obs, indent=2),
                f"💰 Reward: {reward:.2f} | ✅ Done: {done}",
                obs.get('email_subject', ''),
                obs.get('email_body', '')[:500],
                str(obs.get('deadline', 'No deadline'))
            )
        else:
            return f"Error: {response.status_code}", f"Step failed", "", "", ""
    except Exception as e:
        return f"Error: {e}", f"Step failed", "", "", ""

def get_state():
    """Get current environment state"""
    try:
        response = httpx.get(f"{API_BASE}/state", timeout=30)
        if response.status_code == 200:
            return json.dumps(response.json(), indent=2)
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Error: {e}"

def get_tasks():
    """Get available tasks"""
    try:
        response = httpx.get(f"{API_BASE}/tasks", timeout=30)
        if response.status_code == 200:
            return json.dumps(response.json(), indent=2)
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Error: {e}"

def get_health():
    """Get health status"""
    try:
        response = httpx.get(f"{API_BASE}/health", timeout=30)
        if response.status_code == 200:
            data = response.json()
            return f"✅ Healthy | API Key: {data.get('api_key_configured', False)}"
        else:
            return f"❌ Error: {response.status_code}"
    except Exception as e:
        return f"❌ Connection error: {e}"

# Create the Gradio interface
with gr.Blocks(title="Fellow Buffalo - Email Triage Environment", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🐃 Fellow Buffalo - Email Triage OpenEnv
    
    An AI training environment for email management tasks. Train agents to:
    - **Task 1:** Classify emails by tab, color, and deadline
    - **Task 2:** Generate summaries and tag clouds
    - **Task 3:** Manage email lifecycle (Green → Orange → Red)
    - **Task 4:** Generate professional replies
    - **Task 5:** Rank emails by priority
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 🎮 Control Panel")
            task_id = gr.Dropdown(
                choices=[("Task 1 - Classification", "1"), ("Task 2 - Summary", "2"), 
                        ("Task 3 - Lifecycle", "3"), ("Task 4 - Reply", "4"), 
                        ("Task 5 - Ranking", "5")],
                label="Select Task",
                value="1"
            )
            
            with gr.Row():
                reset_btn = gr.Button("🔄 Reset Environment", variant="primary")
                state_btn = gr.Button("📊 Get State")
                tasks_btn = gr.Button("📋 Get Tasks")
                health_btn = gr.Button("❤️ Health Check")
            
            gr.Markdown("### ✏️ Action Inputs")
            
            # Task 1 inputs
            with gr.Group(visible=True) as task1_inputs:
                gr.Markdown("**Task 1: Classification**")
                tab = gr.Dropdown(choices=["Jobs", "Internships", "News", "Sports", "Events", "Finance", "General"], label="Tab")
                color = gr.Dropdown(choices=["green", "orange", "red"], label="Color")
                deadline = gr.Textbox(label="Deadline (ISO format or leave blank)", placeholder="2025-04-15T23:59:00")
            
            # Task 2 inputs
            with gr.Group(visible=False) as task2_inputs:
                gr.Markdown("**Task 2: Summary + Tags**")
                summary = gr.Textbox(label="Summary", lines=3, placeholder="Write a summary of the email...")
                tag_cloud = gr.Textbox(label="Tag Cloud", placeholder="keyword1|keyword2|keyword3")
            
            # Task 3 inputs
            with gr.Group(visible=False) as task3_inputs:
                gr.Markdown("**Task 3: Lifecycle**")
                # Reuse color dropdown
                gr.Markdown("*Use color dropdown above*")
            
            # Task 4 inputs
            with gr.Group(visible=False) as task4_inputs:
                gr.Markdown("**Task 4: Reply Generation**")
                reply = gr.Textbox(label="Your Reply", lines=5, placeholder="Write a professional reply to this email...")
            
            # Task 5 inputs
            with gr.Group(visible=False) as task5_inputs:
                gr.Markdown("**Task 5: Priority Ranking**")
                ranking = gr.Textbox(label="Ranking (comma-separated, 1=most important)", placeholder="1,2,3,4,5,6,7,8,9,10")
            
            step_btn = gr.Button("⚡ Take Action", variant="primary")
        
        with gr.Column(scale=1):
            gr.Markdown("### 📧 Current Email")
            email_subject = gr.Textbox(label="Subject", lines=1)
            email_body = gr.Textbox(label="Body", lines=8)
            email_deadline = gr.Textbox(label="Deadline")
            
            gr.Markdown("### 📊 Results")
            observation_out = gr.Textbox(label="Observation", lines=10)
            reward_out = gr.Textbox(label="Reward / Status", lines=2)
    
    # Task visibility functions
    def update_visibility(task_id):
        return {
            task1_inputs: gr.update(visible=(task_id == "1")),
            task2_inputs: gr.update(visible=(task_id == "2")),
            task3_inputs: gr.update(visible=(task_id == "3")),
            task4_inputs: gr.update(visible=(task_id == "4")),
            task5_inputs: gr.update(visible=(task_id == "5"))
        }
    
    task_id.change(fn=update_visibility, inputs=task_id, outputs=[task1_inputs, task2_inputs, task3_inputs, task4_inputs, task5_inputs])
    
    # Event handlers
    reset_btn.click(
        fn=reset_env,
        inputs=[task_id],
        outputs=[observation_out, reward_out, email_subject, email_body, email_deadline]
    )
    
    step_btn.click(
        fn=take_action,
        inputs=[task_id, tab, color, deadline, summary, tag_cloud, reply, ranking],
        outputs=[observation_out, reward_out, email_subject, email_body, email_deadline]
    )
    
    state_btn.click(fn=get_state, inputs=[], outputs=[observation_out])
    tasks_btn.click(fn=get_tasks, inputs=[], outputs=[observation_out])
    health_btn.click(fn=get_health, inputs=[], outputs=[reward_out])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)