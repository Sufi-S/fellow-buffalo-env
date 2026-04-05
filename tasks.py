"""
Fellow Buffalo - Task Graders
Contains the 3 tasks with their scoring functions.
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from openai import OpenAI


# Load Groq API key for Task 2 grader - looks in current or parent dir
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


# Load .env at module import
load_env_file()


def get_client():
    """Get OpenAI client for Task 2 grader"""
    api_key = os.getenv('GROQ_API_KEY')
    if api_key:
        return OpenAI(
            api_key=api_key,
            base_url='https://api.groq.com/openai/v1'
        )
    return None


def task1_grader(correct: Dict[str, Any], agent: Dict[str, Any]) -> float:
    """
    Task 1: Email Classification with Confidence Scoring
    Scores: tab (0.33), color (0.33), deadline (0.34)
    Confidence bonus/penalty applied to tab score
    """
    score = 0.0
    confidence = agent.get('confidence', 50)
    confidence = max(0, min(100, confidence or 50))
    
    # Tab (0.33) - with confidence bonus/penalty
    if agent.get('tab') == correct.get('tab'):
        # Correct answer: bonus for high confidence
        bonus = (confidence - 50) / 500  # Max +0.10 at confidence 100
        score += 0.33 + max(0.0, round(bonus, 3))
    else:
        # Wrong answer: penalty for high confidence
        penalty = confidence / 1000  # Max -0.10 at confidence 100
        score -= round(penalty, 3)
    
    # Color (0.33)
    if agent.get('color') == correct.get('color'):
        score += 0.33
    else:
        # Small penalty for wrong color
        score -= confidence / 2000
    
    # Deadline (0.34)
    agent_deadline = agent.get('deadline')
    correct_deadline = correct.get('deadline')
    
    if agent_deadline == correct_deadline:
        score += 0.34
    elif agent_deadline and correct_deadline:
        # Partial credit if dates are within 1 day
        try:
            agent_dt = datetime.fromisoformat(agent_deadline.replace('Z', '+00:00'))
            correct_dt = datetime.fromisoformat(correct_deadline.replace('Z', '+00:00'))
            diff_days = abs((agent_dt - correct_dt).days)
            if diff_days == 0:
                score += 0.34
            elif diff_days <= 1:
                score += 0.17  # Half credit
            elif diff_days <= 3:
                score += 0.10
            elif diff_days <= 7:
                score += 0.05
        except:
            pass
    elif correct_deadline is None and agent_deadline is None:
        score += 0.34  # Both correctly have no deadline
    
    return round(max(0.0, min(1.0, score)), 2)


def task2_grader(email_body: str, agent_summary: str, agent_tag_cloud: str) -> float:
    """
    Task 2: Metadata Generation
    Uses AI to score summary quality (0.5) and tag cloud quality (0.5)
    
    Args:
        email_body: Original email content
        agent_summary: AI-generated summary
        agent_tag_cloud: AI-generated tag cloud (pipe-separated)
    
    Returns:
        Score between 0.0 and 1.0
    """
    client = get_client()
    
    if not client:
        # Fallback: simple length-based scoring if no API
        summary_score = min(1.0, len(agent_summary) / 200) if agent_summary else 0.0
        tag_count = len(agent_tag_cloud.split('|')) if agent_tag_cloud else 0
        tag_score = min(1.0, tag_count / 5) if tag_count > 0 else 0.0
        return round((summary_score * 0.5 + tag_score * 0.5), 2)
    
    summary_score = 0.5
    tag_score = 0.5
    
    # Score summary
    try:
        summary_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an evaluator. Score this email summary from 0.0 to 1.0 based on: accuracy (captures main points), completeness (covers key details), and conciseness. Return only the number."},
                {"role": "user", "content": f"Original email: {email_body[:1000]}\n\nSummary: {agent_summary}"}
            ],
            max_tokens=10,
            temperature=0
        )
        summary_score = float(summary_response.choices[0].message.content.strip())
        # Clamp to 0-1 range
        summary_score = max(0.0, min(1.0, summary_score))
    except Exception as e:
        print(f"Summary scoring failed: {e}")
        summary_score = 0.5
    
    # Score tag cloud
    try:
        tag_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Score this tag cloud from 0.0 to 1.0 based on: relevance to email, coverage of key topics, and quality of tags. Return only the number."},
                {"role": "user", "content": f"Original email: {email_body[:500]}\n\nTag cloud: {agent_tag_cloud}"}
            ],
            max_tokens=10,
            temperature=0
        )
        tag_score = float(tag_response.choices[0].message.content.strip())
        tag_score = max(0.0, min(1.0, tag_score))
    except Exception as e:
        print(f"Tag cloud scoring failed: {e}")
        tag_score = 0.5
    
    final_score = (summary_score * 0.5 + tag_score * 0.5)
    return round(final_score, 2)


def task3_grader(transitions: List[Dict], correct_groups: List[str]) -> float:
    """
    Task 3: Lifecycle Management - Fixed scoring
    - Color correctness: normalized by number of emails (max 0.8)
    - Grouping: up to 0.15
    - Thread bonus: up to 0.05
    """
    if not transitions:
        return 0.0

    total_emails = len(transitions)
    if total_emails == 0:
        return 0.0

    # Color score (max 0.8) - normalized by actual email count
    per_email_color_score = 0.8 / total_emails
    color_score = 0.0

    for t in transitions:
        color = t.get('color', '').lower()
        deadline_str = t.get('deadline', '')
        
        # Determine correct color based on deadline
        correct_color = 'green'  # default
        if deadline_str:
            try:
                from datetime import datetime, timezone
                deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
                if deadline.tzinfo:
                    now = datetime.now(timezone.utc)
                else:
                    now = datetime.now()
                    deadline = deadline.replace(tzinfo=None)
                days_diff = (deadline - now).days
                
                if days_diff > 0:
                    correct_color = 'green'
                elif -7 <= days_diff <= 0:
                    correct_color = 'orange'
                else:
                    correct_color = 'red'
            except:
                correct_color = 'green'
        else:
            correct_color = 'green'
        
        # Award normalized score only if color matches
        if color == correct_color:
            color_score += per_email_color_score
    
    # Cap at 0.8
    color_score = min(color_score, 0.8)
    
    # Grouping score (max 0.15)
    grouping_score = 0.0
    agent_groups = [t.get('group', '').lower() for t in transitions if t.get('group')]
    if agent_groups and correct_groups:
        correct_set = set(g.lower() for g in correct_groups)
        matches = sum(1 for g in agent_groups if g in correct_set)
        ratio = matches / max(len(correct_groups), 1)
        grouping_score = round(ratio * 0.15, 2)
    
    # Thread bonus (max 0.05)
    thread_bonus = 0.0
    thread_groups = {}
    for t in transitions:
        tid = t.get('thread_id')
        if tid:
            thread_groups.setdefault(tid, []).append(t.get('group', ''))
    for tid, groups in thread_groups.items():
        if len(groups) > 1 and len(set(groups)) == 1:
            thread_bonus += 0.025
    thread_bonus = min(thread_bonus, 0.05)
    
    final_score = min(color_score + grouping_score + thread_bonus, 1.0)
    return round(final_score, 2)


def evaluate_task1(correct: Dict[str, Any], agent: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate Task 1 and return detailed results
    
    Args:
        correct: Ground truth labels
        agent: Agent's predictions
    
    Returns:
        Dictionary with score and individual component scores
    """
    tab_correct = agent.get('tab') == correct.get('tab')
    color_correct = agent.get('color') == correct.get('color')
    deadline_correct = agent.get('deadline') == correct.get('deadline')
    
    score = task1_grader(correct, agent)
    
    return {
        'score': score,
        'tab_correct': tab_correct,
        'color_correct': color_correct,
        'deadline_correct': deadline_correct,
        'agent_tab': agent.get('tab'),
        'agent_color': agent.get('color'),
        'agent_deadline': agent.get('deadline'),
        'correct_tab': correct.get('tab'),
        'correct_color': correct.get('color'),
        'correct_deadline': correct.get('deadline')
    }


def evaluate_task2(email_body: str, agent_summary: str, agent_tag_cloud: str) -> Dict[str, Any]:
    """
    Evaluate Task 2 and return detailed results
    
    Args:
        email_body: Original email content
        agent_summary: Agent's summary
        agent_tag_cloud: Agent's tag cloud
    
    Returns:
        Dictionary with score and metadata
    """
    score = task2_grader(email_body, agent_summary, agent_tag_cloud)
    
    return {
        'score': score,
        'summary_length': len(agent_summary),
        'tag_count': len(agent_tag_cloud.split('|')) if agent_tag_cloud else 0,
        'summary_preview': agent_summary[:100] if agent_summary else '',
        'tag_cloud': agent_tag_cloud
    }


def evaluate_task3(transitions: List[Dict], correct_groups: List[str]) -> Dict[str, Any]:
    """
    Evaluate Task 3 and return detailed results
    
    Args:
        transitions: Agent's lifecycle decisions
        correct_groups: Expected group names
    
    Returns:
        Dictionary with score and transition details
    """
    score = task3_grader(transitions, correct_groups)
    
    # Count valid transitions
    valid_colors = ['green', 'orange', 'red']
    valid_transitions = sum(1 for t in transitions if t.get('color', '').lower() in valid_colors)
    
    # Count matching groups
    agent_groups = [t.get('group', '').lower() for t in transitions if t.get('group')]
    correct_set = set(g.lower() for g in correct_groups)
    matching_groups = sum(1 for g in agent_groups if g in correct_set)
    
    return {
        'score': score,
        'total_transitions': len(transitions),
        'valid_transitions': valid_transitions,
        'color_score': min(len(transitions) * 0.1, 0.8),
        'matching_groups': matching_groups,
        'total_groups': len(correct_groups),
        'agent_groups': agent_groups,
        'expected_groups': correct_groups,
        'transitions': transitions
    }


if __name__ == "__main__":
    # Test the graders
    print("Testing Task 1 Grader...")
    correct = {"tab": "Jobs", "color": "green", "deadline": "2025-04-15T23:59:00"}
    agent = {"tab": "Jobs", "color": "green", "deadline": "2025-04-15T23:59:00", "confidence": 100}
    print(f"Perfect score with high confidence: {task1_grader(correct, agent)}")
    
    # Test partial deadline
    agent_wrong = {"tab": "Jobs", "color": "green", "deadline": "2025-04-16T23:59:00", "confidence": 100}
    print(f"Partial deadline with high confidence: {task1_grader(correct, agent_wrong)}")
    
    # Test wrong answer with confidence
    agent_wrong_tab = {"tab": "Finance", "color": "green", "deadline": "2025-04-15T23:59:00", "confidence": 100}
    print(f"Wrong tab with high confidence: {task1_grader(correct, agent_wrong_tab)}")
    
    print("\nTesting Task 2 Grader...")
    email = "We are excited to announce a new internship program for students interested in AI and machine learning. Applications are open until May 15th."
    summary = "Company announces new internship program for AI/ML students"
    tags = "internship|AI|machine learning|career"
    print(f"Score: {task2_grader(email, summary, tags)}")
    
    print("\nTesting Task 3 Grader...")
    
    # Test with correct colors based on deadlines
    from datetime import datetime, timedelta
    future = (datetime.now() + timedelta(days=10)).isoformat()
    recent = (datetime.now() - timedelta(days=3)).isoformat()
    old = (datetime.now() - timedelta(days=10)).isoformat()
    
    transitions_correct = [
        {"color": "green", "deadline": future, "group": "internships_q1"},
        {"color": "orange", "deadline": recent, "group": "internships_q1"},
        {"color": "red", "deadline": old, "group": "jobs_q1"}
    ]
    correct_groups = ["internships_q1", "jobs_q1", "finance_q1"]
    print(f"Correct colors score: {task3_grader(transitions_correct, correct_groups)}")
    
    # Test with thread bonus
    transitions_with_thread = [
        {"color": "green", "deadline": future, "group": "internships_q1", "thread_id": "thread_123"},
        {"color": "orange", "deadline": recent, "group": "internships_q1", "thread_id": "thread_123"},
        {"color": "red", "deadline": old, "group": "jobs_q1", "thread_id": "thread_456"}
    ]
    print(f"Thread bonus score: {task3_grader(transitions_with_thread, correct_groups)}")
    
    # Test with incorrect colors
    transitions_wrong = [
        {"color": "red", "deadline": future, "group": "internships_q1"},  # Wrong: future should be green
        {"color": "green", "deadline": old, "group": "internships_q1"},    # Wrong: old should be red
        {"color": "orange", "deadline": old, "group": "jobs_q1"}           # Wrong: old should be red
    ]
    print(f"Wrong colors score: {task3_grader(transitions_wrong, correct_groups)}")
    
    # Test no deadlines
    transitions_no_deadline = [
        {"color": "green", "group": "internships_q1"},
        {"color": "green", "group": "jobs_q1"}
    ]
    print(f"No deadlines score: {task3_grader(transitions_no_deadline, correct_groups)}")