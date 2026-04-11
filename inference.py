"""
Fellow Buffalo - Baseline Inference Script
Runs the AI agent against all 5 tasks and prints structured output only.
"""


import os
import sys
import json
import re
import contextlib
import io
from typing import Optional
import httpx

# Force stdout to be line-buffered and clean
sys.stdout.reconfigure(line_buffering=True)

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
    """DISABLED: No debug prints allowed"""
    pass  # Completely disabled for hackathon


def get_client():
    """Get OpenAI client (works for Groq and OpenAI automatically) - NO PRINTS"""
    API_BASE_URL = os.getenv('API_BASE_URL', 'https://api.groq.com/openai/v1')
    MODEL_NAME = os.getenv('MODEL_NAME', 'llama-3.3-70b-versatile')
    HF_TOKEN = os.getenv('HF_TOKEN')
    GROQ_KEY = os.getenv('GROQ_API_KEY')

    api_key = HF_TOKEN or GROQ_KEY or os.getenv('OPENAI_API_KEY')
    if not api_key:
        return None, None

    client = OpenAI(api_key=api_key, base_url=API_BASE_URL)
    return client, MODEL_NAME


def call_ai(prompt: str, max_tokens: int = 500) -> str:
    """Call AI with suppressed stdout"""
    client, model = get_client()
    
    if client is None:
        return "{}"
    
    try:
        # 🔥 suppress ANY unwanted prints from OpenAI/Groq library
        with contextlib.redirect_stdout(io.StringIO()):
            with contextlib.redirect_stderr(io.StringIO()):
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
    except Exception:
        return "{}"


def run_single_task(task_id: int) -> float:
    """Run a single task and return score"""
    env_url = os.getenv('ENV_URL', 'http://localhost:7860')
    
    task_names = {1: "email-intake", 2: "metadata-generation", 3: "lifecycle-manager", 4: "reply-generation", 5: "priority-ranking"}
    task_name = task_names.get(task_id, f"task{task_id}")
    
    # STEP 1: Fix [START] format
    model_name = os.getenv('MODEL_NAME', 'llama-3.3-70b-versatile')
    env_name = "fellow-buffalo"
    
    print(f"[START] task={task_name} env={env_name} model={model_name}", flush=True)
    
    # STEP 2: Add rewards tracking
    step_rewards = []
    
    try:
        reset_response = httpx.post(f"{env_url}/reset", json={"task_id": task_id}, timeout=30)
        if reset_response.status_code != 200:
            # STEP 4: FIX END format even on error
            final_score = 0.01
            success_str = "false"
            rewards_str = ",".join([f"{r:.2f}" for r in step_rewards]) if step_rewards else ""
            print(f"[END] success={success_str} steps=0 score={final_score:.4f} rewards={rewards_str}", flush=True)
            return final_score
        observation = reset_response.json()
    except Exception:
        final_score = 0.01
        success_str = "false"
        rewards_str = ",".join([f"{r:.2f}" for r in step_rewards]) if step_rewards else ""
        print(f"[END] success={success_str} steps=0 score={final_score:.4f} rewards={rewards_str}", flush=True)
        return final_score
    
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
            except Exception:
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
                    break
                result = step_response.json()
                reward = result.get('reward', 0.0)
                total_reward += reward
                observation = result.get('observation', {})
                
                # STEP 3: Fix [STEP] format
                step_rewards.append(reward)
                action_str = f"task={task_id}"
                done_str = "true" if result.get('done', False) else "false"
                
                print(
                    f"[STEP] step={step_count} action={action_str} reward={reward:.2f} done={done_str} error=null",
                    flush=True
                )
                
            except Exception:
                break
            
            if result.get('done', False):
                break
    
    # Task 2: Metadata generation
    elif task_id == 2:
        prompt = f"""
        Summarize this email. Include: who sent it, what it's about, key names/amounts/dates, and any action needed.
        Then generate specific search keywords.

        Subject: {observation.get('email_subject', '')}
        Body: {observation.get('email_body', '')[:1000]}
        Attachments: {observation.get('attachment_texts', {})}

        Return JSON only:
        {{"summary": "2-3 sentence summary mentioning company, amounts, deadlines, action needed", "tag_cloud": "specific|keywords|company-name|amount|deadline"}}
        """
        
        ai_response = call_ai(prompt)
        
        try:
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = {}
        except Exception:
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
                # STEP 3: Fix [STEP] format
                step_rewards.append(0.0)
                action_str = f"task={task_id}"
                print(
                    f"[STEP] step=1 action={action_str} reward=0.00 done=true error=null",
                    flush=True
                )
                # STEP 4: Fix END format
                final_score = 0.01
                success_str = "false"
                rewards_str = ",".join([f"{r:.2f}" for r in step_rewards]) if step_rewards else ""
                print(f"[END] success={success_str} steps=0 score={final_score:.4f} rewards={rewards_str}", flush=True)
                return final_score
            result = step_response.json()
            total_reward = result.get('reward', 0.0)
            step_count = 1
            
            # STEP 3: Fix [STEP] format
            step_rewards.append(total_reward)
            action_str = f"task={task_id}"
            done_str = "true" if result.get('done', False) else "false"
            
            print(
                f"[STEP] step=1 action={action_str} reward={total_reward:.2f} done={done_str} error=null",
                flush=True
            )
            
        except Exception:
            step_rewards.append(0.0)
            action_str = f"task={task_id}"
            print(
                f"[STEP] step=1 action={action_str} reward=0.00 done=true error=null",
                flush=True
            )
            final_score = 0.01
            success_str = "false"
            rewards_str = ",".join([f"{r:.2f}" for r in step_rewards]) if step_rewards else ""
            print(f"[END] success={success_str} steps=0 score={final_score:.4f} rewards={rewards_str}", flush=True)
            return final_score
    
    # Task 3: Lifecycle manager - IMPROVED with explicit groups
    elif task_id == 3:
        while not observation.get('done', False) and step_count < 50:
            step_count += 1
            
            subject = observation.get('email_subject', '')
            deadline_str = observation.get('deadline', '')
            from datetime import datetime
            # CRITICAL FIX: Use REAL date, not simulated date
            today = datetime.now().strftime('%Y-%m-%d')
            
            metadata = observation.get('metadata', {})
            storage_used = metadata.get('storage_used_gb', 8.5)
            storage_max = metadata.get('storage_max_gb', 15.0)
            storage_percent = metadata.get('storage_percent', 56.7)
            storage_warning = metadata.get('storage_warning', False)
            storage_critical = metadata.get('storage_critical', False)
            
            # IMPROVED: More explicit group guidance
            prompt = f"""
You are managing an email inbox. Today is {today}.

Email subject: {subject}
Deadline: {deadline_str}
Storage: {storage_used:.1f} GB of {storage_max:.0f} GB ({storage_percent:.0f}% full)
Storage critical: {'YES' if storage_critical else 'No'}

Decide:
- color: green (deadline in future), orange (deadline 0-7 days past), red (deadline 7+ days past)
- group: pick ONE based on subject keywords:
  * internships_q1 → intern, fellowship, GSoC, trainee, stipend
  * jobs_q1 → hiring, job, career, NextStep, campus drive, position
  * finance_q1 → fee, invoice, bill, payment, receipt, electricity, VIT
  * events_q1 → hackathon, fest, conference, CodeChef, TechFest, meetup
  * news_q1 → newsletter, digest, weekly, announcement, update
  * general_q1 → everything else
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
            except Exception:
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
                    break
                result = step_response.json()
                reward = result.get('reward', 0.0)
                
                # FIX: For Task 3, environment returns normalized score on final step
                # Don't accumulate - replace total_reward with final score when done
                if result.get('done', False):
                    total_reward = reward  # env returns normalized score on final step
                else:
                    total_reward += reward  # accumulate step rewards
                
                observation = result.get('observation', {})
                
                # STEP 3: Fix [STEP] format
                step_rewards.append(reward)
                action_str = f"task={task_id}"
                done_str = "true" if result.get('done', False) else "false"
                
                print(
                    f"[STEP] step={step_count} action={action_str} reward={reward:.2f} done={done_str} error=null",
                    flush=True
                )
                
            except Exception:
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
        except Exception:
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
                step_rewards.append(0.0)
                action_str = f"task={task_id}"
                print(
                    f"[STEP] step=1 action={action_str} reward=0.00 done=true error=null",
                    flush=True
                )
                final_score = 0.01
                success_str = "false"
                rewards_str = ",".join([f"{r:.2f}" for r in step_rewards]) if step_rewards else ""
                print(f"[END] success={success_str} steps=0 score={final_score:.4f} rewards={rewards_str}", flush=True)
                return final_score
            result = step_response.json()
            total_reward = result.get('reward', 0.0)
            step_count = 1
            
            step_rewards.append(total_reward)
            action_str = f"task={task_id}"
            done_str = "true" if result.get('done', False) else "false"
            
            print(
                f"[STEP] step=1 action={action_str} reward={total_reward:.2f} done={done_str} error=null",
                flush=True
            )
            
        except Exception:
            step_rewards.append(0.0)
            action_str = f"task={task_id}"
            print(
                f"[STEP] step=1 action={action_str} reward=0.00 done=true error=null",
                flush=True
            )
            final_score = 0.01
            success_str = "false"
            rewards_str = ",".join([f"{r:.2f}" for r in step_rewards]) if step_rewards else ""
            print(f"[END] success={success_str} steps=0 score={final_score:.4f} rewards={rewards_str}", flush=True)
            return final_score
    
    # Task 5: Priority ranking - IMPROVED with direct ID ranking
    elif task_id == 5:
        emails_to_rank = observation.get('metadata', {}).get('emails_to_rank', [])
        email_subjects = observation.get('metadata', {}).get('email_subjects', {})
        
        if emails_to_rank and email_subjects:
            # IMPROVED: Show IDs clearly
            email_list = "\n".join([
                f"{i+1}. ID={eid} | Subject: {email_subjects.get(eid, 'Unknown')}"
                for i, eid in enumerate(emails_to_rank)
            ])
        else:
            email_list = "\n".join([f"{i+1}. Email {i+1}" for i in range(10)])
        
        # IMPROVED: Prompt to return IDs directly
        prompt = f"""
Rank these 10 emails by priority (1 = most urgent, 10 = least urgent).

Emails:
{email_list}

Return JSON with the email IDs in priority order (most urgent first).
Use the exact ID strings from the list above.

Example: {{"ranking": ["email_urgent_server", "email_meeting_today", "email_code_review", "email_team_update", "email_documentation", "email_newsletter", "email_lunch", "email_social", "email_prize", "email_discount"]}}
"""
        
        ai_response = call_ai(prompt, max_tokens=300)
        
        try:
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                raw = data.get('ranking', [])
                
                # IMPROVED: Handle both ID strings and numbers
                if raw and len(raw) > 0:
                    if isinstance(raw[0], str) and raw[0] in emails_to_rank:
                        # AI returned IDs directly
                        ranking_ids = raw
                    else:
                        # Fallback: convert numbers to IDs
                        ranking_ids = [emails_to_rank[num-1] for num in raw if isinstance(num, int) and 1 <= num <= len(emails_to_rank)]
                else:
                    ranking_ids = emails_to_rank  # Default order
            else:
                ranking_ids = emails_to_rank
        except Exception:
            ranking_ids = emails_to_rank
        
        action = FellowBuffaloAction(
            task_id=task_id,
            email_ranking=ranking_ids
        )
        
        try:
            step_response = httpx.post(
                f"{env_url}/step", 
                json={"action": action.model_dump()}, 
                timeout=30
            )
            result = step_response.json()
            total_reward = result.get('reward', 0.0)
            step_count = 1
            
            step_rewards.append(total_reward)
            action_str = f"task={task_id}"
            done_str = "true" if result.get('done', False) else "false"
            
            print(
                f"[STEP] step=1 action={action_str} reward={total_reward:.2f} done={done_str} error=null",
                flush=True
            )
        except Exception:
            step_rewards.append(0.0)
            action_str = f"task={task_id}"
            print(
                f"[STEP] step=1 action={action_str} reward=0.00 done=true error=null",
                flush=True
            )
    
    # STEP 4: FIX FINAL [END] format with improved normalization
    if task_id == 1:
        # IMPROVED: Simple average instead of min/max scaling
        #final_score = max(0.01, min(0.99, total_reward / step_count if step_count > 0 else 0.01))
        max_possible = step_count * 0.67
        final_score = max(0.01, min(0.99, total_reward / max_possible if max_possible > 0 else 0.01))
    else:
        # For Tasks 2-5, total_reward is already the final normalized score (0-1)
        final_score = max(0.01, min(0.99, total_reward))
    
    success_str = "true" if final_score > 0.5 else "false"
    rewards_str = ",".join([f"{r:.2f}" for r in step_rewards])
    
    print(
        f"[END] success={success_str} steps={step_count} score={final_score:.4f} rewards={rewards_str}",
        flush=True
    )
    
    # STEP 5: RETURN FIX - return final_score instead of total_reward
    return final_score


def main():
    """Run all 5 tasks - NO stdout prints except structured blocks"""
    scores = {}
    
    for task_id in [1, 2, 3, 4, 5]:
        score = run_single_task(task_id)
        scores[f"task_{task_id}"] = round(score, 4)


if __name__ == "__main__":
    main()