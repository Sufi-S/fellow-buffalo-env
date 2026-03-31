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

# Load .env file manually (handles Windows BOM)
def load_env_file(filepath='.env'):
    """Load environment variables from .env file"""
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
        
        while not observation.get('done', False) and step_count < 20:
            step_count += 1
            email_count += 1
            
            print(f"\n  📧 Email {email_count}: {observation.get('email_subject', '')[:60]}...")
            if observation.get('deadline'):
                print(f"  📅 Deadline: {observation.get('deadline')}")
            
            # Build prompt for classification
            prompt = f"""
            Classify this email:
            Subject: {observation.get('email_subject', '')}
            Body: {observation.get('email_body', '')[:500]}
            
            Return JSON with: tab, color, deadline
            tab options: Jobs, Internships, News, Sports, Events, Finance, General
            color options: green, orange, red
            deadline: ISO datetime or null
            
            Example: {{"tab": "Internships", "color": "green", "deadline": "2025-04-15T23:59:00"}}
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
                summary=None,
                tag_cloud=None,
                lifecycle_decisions=None
            )
            print(f"  🤖 AI predicted: tab={action.tab}, color={action.color}, deadline={action.deadline}")
            
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
        
        print(f"\n📊 Task 1 final score: {total_reward:.4f} (from {email_count} emails)")
    
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
    
    else:  # task_id == 3
        # Task 3: Multiple emails
        print(f"  📧 Starting Task 3 (lifecycle management)")
        
        while not observation.get('done', False) and step_count < 20:
            step_count += 1
            
            print(f"\n  📧 Email {step_count}: {observation.get('email_subject', '')[:60]}...")
            if observation.get('deadline'):
                print(f"  📅 Deadline: {observation.get('deadline')}")
            
            subject = observation.get('email_subject', '')
            body = observation.get('email_body', '')[:500]
            deadline_str = observation.get('deadline', '')
            
            prompt = f"""
            You are managing email lifecycle. Analyze this email and decide its status.
            
            Email subject: {subject}
            Email body: {body}
            Deadline: {deadline_str}
            
            Rules:
            - green: deadline is in the future (more than 0 days away)
            - orange: deadline just passed (0 to 7 days ago)  
            - red: deadline passed more than 7 days ago
            
            Also decide which group this email belongs to.
            Group options: internships_q1, jobs_q1, finance_q1, events_q1, news_q1
            
            Return ONLY valid JSON with these exact fields:
            {{"color": "green", "group": "internships_q1"}}
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
                    'deadline': observation.get('deadline'),
                    'email_id': observation.get('email_subject', '')[:20]
                }]
            )
            print(f"  🤖 AI decision: color={color}, group={group}")
            
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
    
    return total_reward


def main():
    """Run all 3 tasks and print scores"""
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
    
    for task_id in [1, 2, 3]:
        print(f"\n{'='*40}")
        print(f"Running Task {task_id}...")
        print('='*40)
        score = run_single_task(task_id)
        scores[f"task_{task_id}"] = round(score, 4)
        print(f"\n📊 Task {task_id} final score: {score:.4f}")
    
    print("\n" + "=" * 40)
    print("🏆 FINAL SCORES:")
    print(json.dumps(scores, indent=2))
    print("=" * 40)
    
    return scores


if __name__ == "__main__":
    main()