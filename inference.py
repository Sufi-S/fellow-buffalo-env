"""
Fellow Buffalo - Baseline Inference Script
Runs the AI agent against all 5 tasks and prints structured output only.
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


def log_debug(msg: str):
    """Print debug messages to stderr (not stdout)"""
    print(msg, file=sys.stderr, flush=True)


def get_client():
    """Get OpenAI client (works for Groq and OpenAI automatically)"""
    groq_key = os.getenv('GROQ_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    hf_key = os.getenv('HF_TOKEN')
    
    # Determine which API to use
    using_groq = bool(groq_key)
    api_key = groq_key or openai_key or hf_key
    
    if not api_key:
        log_debug("ERROR: No API key found")
        return None, None
    
    api_base_url = os.getenv('API_BASE_URL')
    
    # Set model and base URL based on which key is available
    if api_base_url:
        client = OpenAI(api_key=api_key, base_url=api_base_url)
        model_name = os.getenv('MODEL_NAME', 'llama-3.3-70b-versatile')
    elif using_groq:
        # Using Groq
        client = OpenAI(api_key=api_key, base_url='https://api.groq.com/openai/v1')
        model_name = os.getenv('MODEL_NAME', 'llama-3.3-70b-versatile')
    else:
        # Using OpenAI
        client = OpenAI(api_key=api_key)
        model_name = os.getenv('MODEL_NAME', 'gpt-4o-mini')
    
    log_debug(f"Using {'Groq' if using_groq else 'OpenAI'} API with model: {model_name}")
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
        log_debug(f"AI call failed: {e}")
        return "{}"


def run_single_task(task_id: int) -> float:
    """Run a single task and return score"""
    env_url = os.getenv('ENV_URL', 'http://localhost:7860')
    
    task_names = {1: "email-intake", 2: "metadata-generation", 3: "lifecycle-manager", 4: "reply-generation", 5: "priority-ranking"}
    task_name = task_names.get(task_id, f"task{task_id}")
    
    print(f"[START] task={task_name}", flush=True)
    
    try:
        reset_response = httpx.post(f"{env_url}/reset", json={"task_id": task_id}, timeout=30)
        if reset_response.status_code != 200:
            log_debug(f"Failed to reset task {task_id}")
            print(f"[END] task={task_name} score=0.0 steps=0", flush=True)
            return 0.0
        observation = reset_response.json()
    except Exception as e:
        log_debug(f"Connection error: {e}")
        print(f"[END] task={task_name} score=0.0 steps=0", flush=True)
        return 0.0
    
    total_reward = 0.0
    step_count = 0
    
    # Task 1: Multi-email mode
    if task_id == 1:
        while not observation.get('done', False) and step_count < 50:
            step_count += 1
            
            prompt = f"""
Classify this email and rate your confidence:

Subject: {observation.get('email_subject', '')}
Body: {observation.get('email_body', '')[:500]}

Return JSON with: tab, color, deadline, confidence
tab options: Jobs, Internships, News, Sports, Events, Finance, General
color options: green, orange, red
deadline: ISO datetime or null
confidence: 0-100

Example: {{"tab": "Internships", "color": "green", "deadline": "2025-04-15T23:59:00", "confidence": 85}}
"""
            
            ai_response = call_ai(prompt)
            
            try:
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    data = {}
            except Exception as e:
                log_debug(f"JSON parse error: {e}")
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
            
            try:
                step_response = httpx.post(
                    f"{env_url}/step", 
                    json={"action": action.model_dump()}, 
                    timeout=30
                )
                if step_response.status_code != 200:
                    log_debug(f"Step failed: {step_response.status_code}")
                    break
                result = step_response.json()
                reward = result.get('reward', 0.0)
                total_reward += reward
                observation = result.get('observation', {})
                
                print(f"[STEP] step={step_count} reward={reward:.4f}", flush=True)
                
            except Exception as e:
                log_debug(f"Step error: {e}")
                break
            
            if result.get('done', False):
                break
    
    # Task 2: Metadata generation
    elif task_id == 2:
        prompt = f"""
        Summarize this email and generate tag cloud:
        Subject: {observation.get('email_subject', '')}
        Body: {observation.get('email_body', '')[:1000]}
        Attachments: {observation.get('attachment_texts', {})}
        
        Return JSON with: summary, tag_cloud
        tag_cloud: pipe-separated keywords
        
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
            log_debug(f"JSON parse error: {e}")
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
        
        try:
            step_response = httpx.post(
                f"{env_url}/step", 
                json={"action": action.model_dump()}, 
                timeout=30
            )
            if step_response.status_code != 200:
                log_debug(f"Step failed: {step_response.status_code}")
                print(f"[STEP] step=1 reward=0.0", flush=True)
                print(f"[END] task={task_name} score=0.0 steps=0", flush=True)
                return 0.0
            result = step_response.json()
            total_reward = result.get('reward', 0.0)
            step_count = 1
            
            print(f"[STEP] step=1 reward={total_reward:.4f}", flush=True)
            
        except Exception as e:
            log_debug(f"Step error: {e}")
            print(f"[STEP] step=1 reward=0.0", flush=True)
            print(f"[END] task={task_name} score=0.0 steps=0", flush=True)
            return 0.0
    
    # Task 3: Lifecycle manager
    elif task_id == 3:
        while not observation.get('done', False) and step_count < 50:
            step_count += 1
            
            subject = observation.get('email_subject', '')
            deadline_str = observation.get('deadline', '')
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')
            
            metadata = observation.get('metadata', {})
            storage_used = metadata.get('storage_used_gb', 8.5)
            storage_max = metadata.get('storage_max_gb', 15.0)
            storage_percent = metadata.get('storage_percent', 56.7)
            storage_warning = metadata.get('storage_warning', False)
            storage_critical = metadata.get('storage_critical', False)
            simulated_date = metadata.get('simulated_date', datetime.now().strftime('%Y-%m-%d'))
            
            prompt = f"""
IMPORTANT: Current simulation date is {simulated_date}.

Email subject: {subject}
Deadline: {deadline_str}
Storage: {storage_used:.1f} GB of {storage_max:.0f} GB ({storage_percent:.0f}% full)
Storage critical: {'YES' if storage_critical else 'No'}

Based on {simulated_date}:
- color: green (deadline AFTER {simulated_date})
- orange (deadline 0-7 days BEFORE {simulated_date})
- red (deadline MORE than 7 days BEFORE {simulated_date})
- group: internships_q1, jobs_q1, finance_q1, events_q1, news_q1, general_q1
- account: primary or archive
- trigger_relay: true ONLY if storage critical (>14 GB)

Return JSON only:
{{"color": "red", "group": "finance_q1", "account": "archive", "trigger_relay": false}}
"""
            
            ai_response = call_ai(prompt)
            
            try:
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    data = {}
            except Exception as e:
                log_debug(f"JSON parse error: {e}")
                data = {}
            
            action = FellowBuffaloAction(
                task_id=task_id,
                tab=None,
                color=None,
                deadline=None,
                summary=None,
                tag_cloud=None,
                lifecycle_decisions=[{
                    'color': data.get('color', 'green'),
                    'group': data.get('group', 'general_q1'),
                    'account': data.get('account', 'primary'),
                    'trigger_relay': data.get('trigger_relay', False),
                    'deadline': observation.get('deadline'),
                    'email_id': observation.get('email_subject', '')[:20],
                    'thread_id': data.get('thread_id', '')
                }]
            )
            
            try:
                step_response = httpx.post(
                    f"{env_url}/step", 
                    json={"action": action.model_dump()}, 
                    timeout=30
                )
                if step_response.status_code != 200:
                    log_debug(f"Step failed: {step_response.status_code}")
                    break
                result = step_response.json()
                reward = result.get('reward', 0.0)
                total_reward += reward
                observation = result.get('observation', {})
                
                print(f"[STEP] step={step_count} reward={reward:.4f}", flush=True)
                
            except Exception as e:
                log_debug(f"Step error: {e}")
                break
            
            if result.get('done', False):
                break
    
    # Task 4: Reply generation
    elif task_id == 4:
        prompt = f"""
        Write a professional reply to this email:
        
        Subject: {observation.get('email_subject', '')}
        Body: {observation.get('email_body', '')[:800]}
        
        Return JSON only with: reply
        Example: {{"reply": "Dear Sir/Madam,\\n\\nThank you for your email...\\n\\nBest regards"}}
        """
        
        ai_response = call_ai(prompt, max_tokens=300)
        
        try:
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = {}
        except Exception as e:
            log_debug(f"JSON parse error: {e}")
            data = {}
        
        action = FellowBuffaloAction(
            task_id=task_id,
            reply=data.get('reply', '')
        )
        
        try:
            step_response = httpx.post(
                f"{env_url}/step", 
                json={"action": action.model_dump()}, 
                timeout=30
            )
            if step_response.status_code != 200:
                log_debug(f"Step failed: {step_response.status_code}")
                print(f"[STEP] step=1 reward=0.0", flush=True)
                print(f"[END] task={task_name} score=0.0 steps=0", flush=True)
                return 0.0
            result = step_response.json()
            total_reward = result.get('reward', 0.0)
            step_count = 1
            
            print(f"[STEP] step=1 reward={total_reward:.4f}", flush=True)
            
        except Exception as e:
            log_debug(f"Step error: {e}")
            print(f"[STEP] step=1 reward=0.0", flush=True)
            print(f"[END] task={task_name} score=0.0 steps=0", flush=True)
            return 0.0
    
    # Task 5: Priority ranking
    elif task_id == 5:
        emails_to_rank = observation.get('metadata', {}).get('emails_to_rank', [])
        email_subjects = observation.get('metadata', {}).get('email_subjects', {})
        
        if emails_to_rank and email_subjects:
            email_list = "\n".join([
                f"{i+1}. {email_subjects.get(eid, 'Unknown')}"
                for i, eid in enumerate(emails_to_rank)
            ])
        else:
            email_list = "\n".join([f"{i+1}. Email {i+1}" for i in range(10)])
        
        prompt = f"""
Rank these 10 emails by priority (1 = most urgent, 10 = least urgent).

Emails:
{email_list}

Return JSON with ranking as list of numbers 1-10.
Example: {{"ranking": [3, 1, 5, 2, 4, 6, 7, 8, 9, 10]}}
"""
        
        ai_response = call_ai(prompt, max_tokens=200)
        
        try:
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                ranking_numbers = data.get('ranking', list(range(1, 11)))
            else:
                ranking_numbers = list(range(1, 11))
        except Exception as e:
            log_debug(f"JSON parse error: {e}")
            ranking_numbers = list(range(1, 11))
        
        email_ids = observation.get('metadata', {}).get('emails_to_rank', [])
        if not email_ids:
            email_ids = [f"email_{i}" for i in range(10)]
        
        ranking_ids = [email_ids[num-1] for num in ranking_numbers]
        
        action = FellowBuffaloAction(
            task_id=task_id,
            email_ranking=ranking_ids
        )
        
        step_response = httpx.post(
            f"{env_url}/step", 
            json={"action": action.model_dump()}, 
            timeout=30
        )
        result = step_response.json()
        total_reward = result.get('reward', 0.0)
        step_count = 1
        
        print(f"[STEP] step=1 reward={total_reward:.4f}", flush=True)
    
    print(f"[END] task={task_name} score={total_reward:.4f} steps={step_count}", flush=True)
    
    return total_reward


def main():
    """Run all 5 tasks - NO stdout prints except structured blocks"""
    scores = {}
    
    for task_id in [1, 2, 3, 4, 5]:
        score = run_single_task(task_id)
        scores[f"task_{task_id}"] = round(score, 4)


if __name__ == "__main__":
    main()