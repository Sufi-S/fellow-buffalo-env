"""
Fellow Buffalo - Baseline Inference Script
Runs the AI agent against all 3 tasks and prints scores.
"""


import os
import sys
import json
import re
from typing import Optional
import httpx

# Load .env file manually (handles Windows BOM) - looks in current or parent dir
def load_env_file():
    """Load .env from current dir or parent dir"""
    for filepath in ['.env', '../.env']:
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                content = f.read()
            
            # Remove BOM if present
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

# Load .env at startup
load_env_file()

from openai import OpenAI
from models import FellowBuffaloAction


def get_client():
    """Get OpenAI client (works for Groq and OpenAI)"""
    # Try to get API key from multiple sources
    api_key = os.getenv('GROQ_API_KEY') or os.getenv('OPENAI_API_KEY') or os.getenv('HF_TOKEN')
    
    if not api_key:
        print("ERROR: No API key found. Check your .env file.")
        print(f"GROQ_API_KEY in env: {os.getenv('GROQ_API_KEY') is not None}")
        return None, None
    
    api_base_url = os.getenv('API_BASE_URL')
    model_name = os.getenv('MODEL_NAME', 'llama-3.3-70b-versatile')
    
    if api_base_url:
        # Judge environment
        client = OpenAI(api_key=api_key, base_url=api_base_url)
    else:
        # Development with Groq
        client = OpenAI(
            api_key=api_key,
            base_url='https://api.groq.com/openai/v1'
        )
    
    return client, model_name


def call_ai(prompt: str, max_tokens: int = 500) -> str:
    """Call AI with fallback"""
    client, model = get_client()
    
    if client is None:
        return "{}"
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an email management AI. Return JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        print(f"AI call failed: {e}")
        return "{}"


def run_single_task(task_id: int) -> float:
    """Run a single task and return score - Multi-email support for Task 1"""
    env_url = os.getenv('ENV_URL', 'http://localhost:7860')
    
    # Reset environment
    try:
        reset_response = httpx.post(f"{env_url}/reset", json={"task_id": task_id}, timeout=30)
        if reset_response.status_code != 200:
            print(f"Failed to reset task {task_id}: {reset_response.status_code}")
            return 0.0
        observation = reset_response.json()
    except Exception as e:
        print(f"Connection error: {e}")
        return 0.0
    
    total_reward = 0.0
    step_count = 0
    email_count = 0
    
    # Task 1: Multi-email mode
    if task_id == 1:
        print(f"  📧 Starting multi-email Task 1 (will process multiple emails)")
        
        while not observation.get('done', False) and step_count < 50:
            step_count += 1
            email_count += 1
            
            print(f"\n  📧 Email {email_count}: {observation.get('email_subject', '')[:60]}...")
            if observation.get('deadline'):
                print(f"  📅 Deadline: {observation.get('deadline')}")
            
            # Build prompt for classification with confidence
            prompt = f"""
Classify this email and rate your confidence:

Subject: {observation.get('email_subject', '')}
Body: {observation.get('email_body', '')[:500]}

Return JSON with: tab, color, deadline, confidence
tab options: Jobs, Internships, News, Sports, Events, Finance, General
color options: green, orange, red
deadline: ISO datetime or null
confidence: 0-100 (how sure are you? 100 = extremely confident)

Example: {{"tab": "Internships", "color": "green", "deadline": "2025-04-15T23:59:00", "confidence": 85}}
"""
            
            # Get AI response
            ai_response = call_ai(prompt)
            
            # Parse JSON
            try:
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    data = {}
            except Exception as e:
                print(f"JSON parse error: {e}")
                data = {}
            
            action = FellowBuffaloAction(
                task_id=task_id,
                tab=data.get('tab'),
                color=data.get('color'),
                deadline=data.get('deadline'),
                confidence=data.get('confidence', 50),
                summary=None,
                tag_cloud=None,
                lifecycle_decisions=None
            )
            print(f"  🤖 AI predicted: tab={action.tab}, color={action.color}, deadline={action.deadline}, confidence={action.confidence}")
            
            # Step
            try:
                step_response = httpx.post(
                    f"{env_url}/step", 
                    json={"action": action.model_dump()}, 
                    timeout=30
                )
                if step_response.status_code != 200:
                    print(f"Step failed: {step_response.status_code}")
                    break
                result = step_response.json()
                reward = result.get('reward', 0.0)
                total_reward += reward
                observation = result.get('observation', {})
                print(f"  💰 Reward: {reward:.2f}, Total: {total_reward:.2f}")
            except Exception as e:
                print(f"Step error: {e}")
                break
            
            if result.get('done', False):
                print(f"\n  ✅ Task completed after {email_count} emails")
                break
        
        # UPDATED: Show score as X/5.0
        print(f"\n📊 Task 1 final score: {total_reward:.4f} / 5.0 (from {email_count} emails)")
    
    elif task_id == 2:
        # Task 2: Single email
        print(f"  📧 Processing email: {observation.get('email_subject', '')[:60]}...")
        
        prompt = f"""
        Summarize this email and generate tag cloud:
        Subject: {observation.get('email_subject', '')}
        Body: {observation.get('email_body', '')[:1000]}
        Attachments: {observation.get('attachment_texts', {})}
        
        Return JSON with: summary, tag_cloud
        tag_cloud: pipe-separated keywords (e.g., "keyword1|keyword2|keyword3")
        
        Example: {{"summary": "This email is about...", "tag_cloud": "keyword1|keyword2|keyword3"}}
        """
        
        ai_response = call_ai(prompt)
        
        try:
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = {}
        except Exception as e:
            print(f"JSON parse error: {e}")
            data = {}
        
        action = FellowBuffaloAction(
            task_id=task_id,
            tab=None,
            color=None,
            deadline=None,
            summary=data.get('summary', ''),
            tag_cloud=data.get('tag_cloud', ''),
            lifecycle_decisions=None
        )
        print(f"  🤖 AI summary: {action.summary[:50]}..." if action.summary else "  🤖 AI summary: None")
        print(f"  🏷️  AI tags: {action.tag_cloud}")
        
        try:
            step_response = httpx.post(
                f"{env_url}/step", 
                json={"action": action.model_dump()}, 
                timeout=30
            )
            if step_response.status_code != 200:
                print(f"Step failed: {step_response.status_code}")
                return 0.0
            result = step_response.json()
            total_reward = result.get('reward', 0.0)
        except Exception as e:
            print(f"Step error: {e}")
            return 0.0
    
    elif task_id == 3:
        # Task 3: Multiple emails
        print(f"  📧 Starting Task 3 (lifecycle management with temporal reasoning and storage monitoring)")
        
        while not observation.get('done', False) and step_count < 50:
            step_count += 1
            
            print(f"\n  📧 Email {step_count}: {observation.get('email_subject', '')[:60]}...")
            if observation.get('deadline'):
                print(f"  📅 Deadline: {observation.get('deadline')}")
            
            subject = observation.get('email_subject', '')
            body = observation.get('email_body', '')[:500]
            deadline_str = observation.get('deadline', '')
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Get storage AND temporal info from metadata
            metadata = observation.get('metadata', {})
            storage_used = metadata.get('storage_used_gb', 8.5)
            storage_max = metadata.get('storage_max_gb', 15.0)
            storage_percent = metadata.get('storage_percent', 56.7)
            storage_warning = metadata.get('storage_warning', False)
            storage_critical = metadata.get('storage_critical', False)
            
            # NEW: Get simulated date
            simulated_date = metadata.get('simulated_date', datetime.now().strftime('%Y-%m-%d'))
            
            # Updated prompt with simulated date
            prompt = f"""
IMPORTANT: The current date in this simulation is {simulated_date}.
(This may be different from today's real date. Use THIS date for all deadline calculations.)

Today's real date is {today} (for reference only - use {simulated_date} for decisions).

Email subject: {subject}
Deadline: {deadline_str}
Storage: {storage_used:.1f} GB of {storage_max:.0f} GB ({storage_percent:.0f}% full)
Storage warning: {'YES - over 12GB' if storage_warning else 'No'}
Storage critical: {'YES - over 14GB, MUST RELAY!' if storage_critical else 'No'}

Based on the SIMULATED DATE ({simulated_date}), decide:
- color: green (deadline is AFTER {simulated_date})
- orange (deadline was 0-7 days BEFORE {simulated_date})
- red (deadline was MORE than 7 days before {simulated_date})
- group: internships_q1, jobs_q1, finance_q1, events_q1, news_q1, general_q1
- account: primary (active emails) or archive (old/red emails)
- trigger_relay: true ONLY if storage is critical (>14 GB), otherwise false

If storage is critical (>14 GB), you MUST trigger relay by setting trigger_relay=true

Return JSON only:
{{"color": "red", "group": "finance_q1", "account": "archive", "trigger_relay": false, "thread_id": "vit_fee_2026"}}
"""
            
            ai_response = call_ai(prompt)
            
            try:
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    data = {}
            except Exception as e:
                print(f"JSON parse error: {e}")
                data = {}
            
            color = data.get('color', 'green')
            group = data.get('group', 'general_q1')
            account = data.get('account', 'primary')
            trigger_relay = data.get('trigger_relay', False)
            
            # Updated action creation with account, thread_id, and trigger_relay
            action = FellowBuffaloAction(
                task_id=task_id,
                tab=None,
                color=None,
                deadline=None,
                summary=None,
                tag_cloud=None,
                lifecycle_decisions=[{
                    'color': color,
                    'group': group,
                    'account': account,
                    'trigger_relay': trigger_relay,
                    'deadline': observation.get('deadline'),
                    'email_id': observation.get('email_subject', '')[:20],
                    'thread_id': data.get('thread_id', '')
                }]
            )
            print(f"  🤖 AI decision: color={color}, group={group}, account={account}, trigger_relay={trigger_relay}, thread_id={data.get('thread_id', '')[:30]}")
            
            try:
                step_response = httpx.post(
                    f"{env_url}/step", 
                    json={"action": action.model_dump()}, 
                    timeout=30
                )
                if step_response.status_code != 200:
                    print(f"Step failed: {step_response.status_code}")
                    break
                result = step_response.json()
                reward = result.get('reward', 0.0)
                total_reward += reward
                observation = result.get('observation', {})
                print(f"  💰 Reward: {reward:.2f}, Total: {total_reward:.2f}")
            except Exception as e:
                print(f"Step error: {e}")
                break
            
            if result.get('done', False):
                print(f"\n  ✅ Task completed after {step_count} steps")
                break
    
    elif task_id == 4:
        # Task 4: Reply Generation
        print(f"  📧 Processing email for reply: {observation.get('email_subject', '')[:60]}...")
        
        prompt = f"""
        Write a professional reply to this email:
        
        Subject: {observation.get('email_subject', '')}
        Body: {observation.get('email_body', '')[:800]}
        
        Return JSON only with: reply
        Example: {{"reply": "Dear Sir/Madam,\\n\\nThank you for your email. I will...\\n\\nBest regards,\\n[Your Name]"}}
        """
        
        ai_response = call_ai(prompt, max_tokens=300)
        
        try:
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = {}
        except Exception as e:
            print(f"JSON parse error: {e}")
            data = {}
        
        action = FellowBuffaloAction(
            task_id=task_id,
            reply=data.get('reply', '')
        )
        print(f"  🤖 AI reply: {action.reply[:100]}..." if action.reply else "  🤖 AI reply: None")
        
        try:
            step_response = httpx.post(
                f"{env_url}/step", 
                json={"action": action.model_dump()}, 
                timeout=30
            )
            if step_response.status_code != 200:
                print(f"Step failed: {step_response.status_code}")
                return 0.0
            result = step_response.json()
            total_reward = result.get('reward', 0.0)
        except Exception as e:
            print(f"Step error: {e}")
            return 0.0
    
    return total_reward


def main():
    """Run all 4 tasks and print scores"""
    print("Fellow Buffalo Baseline Agent")
    print("=" * 40)
    
    # Print environment info for debugging
    api_key = os.getenv('GROQ_API_KEY') or os.getenv('OPENAI_API_KEY')
    print(f"API Key found: {bool(api_key)}")
    if api_key:
        print(f"API Key preview: {api_key[:20]}...")
    print(f"Using Groq: {os.getenv('GROQ_API_KEY') is not None}")
    print(f"Environment URL: {os.getenv('ENV_URL', 'http://localhost:7860')}")
    print("=" * 40)
    
    scores = {}
    
    for task_id in [1, 2, 3, 4]:
        print(f"\n{'='*40}")
        print(f"Running Task {task_id}...")
        print('='*40)
        score = run_single_task(task_id)
        scores[f"task_{task_id}"] = round(score, 4)
        
        # Show score with denominator based on task
        if task_id == 1:
            print(f"\n📊 Task {task_id} final score: {score:.4f} / 5.0")
        else:
            print(f"\n📊 Task {task_id} final score: {score:.4f} / 1.0")
    
    print("\n" + "=" * 40)
    print("🏆 FINAL SCORES:")
    print(json.dumps(scores, indent=2))
    print("=" * 40)
    
    return scores


if __name__ == "__main__":
    main()