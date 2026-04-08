"""
Fellow Buffalo - OpenEnv Environment
Implements reset(), step(), and state() methods.
"""

import json
import os
import random  # Added for random email selection
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta

from models import FellowBuffaloAction, FellowBuffaloObservation, FellowBuffaloState
from tasks import task1_grader, task2_grader, task3_grader, task4_grader, task5_grader


class FellowBuffaloEnv:
    """
    OpenEnv environment for email triage.
    """
    
    def __init__(self, test_emails_path: str = "test_emails"):
        self.test_emails_path = test_emails_path
        self.emails = self._load_emails()
        self.current_task = None
        self.current_email = None
        self.current_observation = None
        self.step_count = 0
        self.max_steps = 10
        self.transitions = []  # For Task 3
        self.done = False
        self.task1_emails_queue = []  # For Task 3 multi-email mode
        self.task5_emails = []  # For Task 5 - list of 10 emails to rank
        
        # Storage simulation variables
        self.storage_used_gb = 8.5
        self.storage_max_gb = 15.0
        self.storage_account_index = 1
        self.storage_warning_triggered = False
        
        # NEW: Temporal reasoning variables
        self.simulated_date = None  # Will be set in reset
        self.days_per_step = 2  # Each step advances 2 days
        
        # FIX 1: Add pending_storage_reward for Task 3
        self.pending_storage_reward = 0.0
        
    def _load_emails(self) -> Dict[int, list]:
        """Load test emails from JSON files"""
        emails = {1: [], 2: [], 3: [], 4: [], 5: []}
        
        if not os.path.exists(self.test_emails_path):
            return self._create_default_emails()
        
        for filename in os.listdir(self.test_emails_path):
            if filename.endswith('.json'):
                filepath = os.path.join(self.test_emails_path, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        email = json.load(f)
                        task_id = email.get('task', 1)
                        emails[task_id].append(email)
                except:
                    continue
        
        # If no emails found, create defaults
        for task_id in [1, 2, 3, 4, 5]:
            if not emails[task_id]:
                emails[task_id] = self._create_default_emails()[task_id]
        
        return emails
    
    def _create_default_emails(self) -> Dict[int, list]:
        """Create default test emails if none exist"""
        return {
            1: [
                {
                    "id": "default_001",
                    "subject": "Summer Internship 2025",
                    "body": "Applications close April 15, 2025",
                    "attachment_texts": {},
                    "correct_tab": "Internships",
                    "correct_color": "green",
                    "correct_deadline": "2025-04-15T23:59:00"
                },
                {
                    "id": "default_002",
                    "subject": "Job Opportunity: Software Engineer",
                    "body": "We are hiring for multiple positions. Apply by May 1st.",
                    "attachment_texts": {},
                    "correct_tab": "Jobs",
                    "correct_color": "green",
                    "correct_deadline": "2025-05-01T23:59:00"
                },
                {
                    "id": "default_003",
                    "subject": "Urgent: Project Deadline",
                    "body": "Please submit your report by tomorrow EOD.",
                    "attachment_texts": {},
                    "correct_tab": "General",
                    "correct_color": "red",
                    "correct_deadline": "2025-03-29T23:59:00"
                },
                {
                    "id": "default_004",
                    "subject": "Conference Call Summary",
                    "body": "Meeting notes from the Q1 planning session.",
                    "attachment_texts": {},
                    "correct_tab": "General",
                    "correct_color": "green",
                    "correct_deadline": None
                }
            ],
            2: [
                {
                    "id": "default_005",
                    "subject": "Tech News: AI Update",
                    "body": "OpenAI released a new model today. The new model shows significant improvements in reasoning capabilities.",
                    "attachment_texts": {}
                },
                {
                    "id": "default_006",
                    "subject": "Meeting Summary",
                    "body": "We discussed the Q2 roadmap, budget allocation, and resource planning.",
                    "attachment_texts": {}
                },
                {
                    "id": "default_007",
                    "subject": "Product Launch Announcement",
                    "body": "We're excited to announce our new product line launching next month. Features include improved performance and user experience.",
                    "attachment_texts": {}
                }
            ],
            3: [
                {
                    "id": "default_008",
                    "subject": "VIT Fee Payment",
                    "body": "Fee deadline is March 20",
                    "attachment_texts": {},
                    "received_date": "2025-03-01",
                    "deadline": "2025-03-20",
                    "correct_group": "finance_q1"
                },
                {
                    "id": "default_009",
                    "subject": "Internship Application",
                    "body": "Please submit your documents by April 15",
                    "attachment_texts": {},
                    "received_date": "2025-03-15",
                    "deadline": "2025-04-15",
                    "correct_group": "internships_q1"
                },
                {
                    "id": "default_010",
                    "subject": "Job Interview",
                    "body": "Your interview is scheduled for March 25",
                    "attachment_texts": {},
                    "received_date": "2025-03-10",
                    "deadline": "2025-03-25",
                    "correct_group": "jobs_q1"
                },
                {
                    "id": "default_011",
                    "subject": "Newsletter Subscription",
                    "body": "Weekly tech news digest",
                    "attachment_texts": {},
                    "received_date": "2025-03-20",
                    "deadline": None,
                    "correct_group": "news_q1"
                }
            ],
            4: [
                {
                    "id": "default_012",
                    "subject": "Internship Application Question",
                    "body": "Dear Team, I applied for the summer internship last week. When can I expect to hear back? Thank you.",
                    "attachment_texts": {}
                },
                {
                    "id": "default_013",
                    "subject": "Meeting Reschedule Request",
                    "body": "Hi, I need to reschedule our meeting for tomorrow. Would Thursday work instead? Let me know.",
                    "attachment_texts": {}
                },
                {
                    "id": "default_014",
                    "subject": "Invoice Inquiry",
                    "body": "I haven't received the invoice for last month's services. Can you please send it again?",
                    "attachment_texts": {}
                }
            ],
            5: self._create_default_task5_emails()
        }
    
    def _create_default_task5_emails(self) -> List[Dict]:
        """Create default emails for Task 5 priority ranking with unique IDs and full content"""
        return [
            {"id": "email_urgent_server", "subject": "URGENT: Server Down", "body": "Production server is down. Immediate action required.", "importance": 1, "task": 5},
            {"id": "email_meeting_today", "subject": "Client Meeting Today at 2PM", "body": "Client meeting scheduled for 2PM today. Please prepare slides.", "importance": 2, "task": 5},
            {"id": "email_team_update", "subject": "Weekly Team Update", "body": "Weekly team sync tomorrow at 10AM.", "importance": 3, "task": 5},
            {"id": "email_documentation", "subject": "Project Documentation", "body": "Please review the updated documentation.", "importance": 4, "task": 5},
            {"id": "email_code_review", "subject": "Code Review Request", "body": "Please review PR #123 when you have time.", "importance": 5, "task": 5},
            {"id": "email_newsletter", "subject": "Company Newsletter", "body": "Monthly company newsletter attached.", "importance": 6, "task": 5},
            {"id": "email_lunch", "subject": "Lunch Invitation", "body": "Team lunch this Friday at 1PM.", "importance": 7, "task": 5},
            {"id": "email_social", "subject": "Social Media Post", "body": "Please like our new LinkedIn post.", "importance": 8, "task": 5},
            {"id": "email_prize", "subject": "You Won a Prize!", "body": "Congratulations! You've won a free gift card.", "importance": 9, "task": 5},
            {"id": "email_discount", "subject": "Discount Offer", "body": "50% off on all products today only!", "importance": 10, "task": 5},
        ]
    
    def reset(self, task_id: int = 1) -> FellowBuffaloObservation:
        """Reset environment and return first observation"""
        import random
        from datetime import datetime, timedelta
        
        self.current_task = task_id
        self.step_count = 0
        self.done = False
        self.transitions = []
        self.storage_used_gb = 8.5
        self.storage_warning_triggered = False
        
        # FIX 1: Reset pending_storage_reward
        self.pending_storage_reward = 0.0
        
        # NEW: Initialize simulated date (starting March 1, 2026)
        self.simulated_date = datetime(2026, 3, 1)
        
        # For Task 1: multi-email mode (process up to 5 emails)
        if task_id == 1:
            emails_for_task = self.emails.get(task_id, [])
            if emails_for_task:
                # Take up to 5 emails (or all if less) and randomize
                max_emails = min(5, len(emails_for_task))
                self.task1_emails_queue = random.sample(emails_for_task, max_emails)
                self.current_email = self.task1_emails_queue[0].copy()
            else:
                self.task1_emails_queue = []
                self.current_email = self._create_default_emails()[task_id][0].copy()
        elif task_id == 5:
            # Task 5: Priority Ranking - load 10 emails
            emails_for_task = self.emails.get(task_id, [])
            if len(emails_for_task) >= 10:
                self.task5_emails = random.sample(emails_for_task, 10)
                self.current_email = self.task5_emails[0]
            else:
                self.task5_emails = self._create_default_task5_emails()
                self.current_email = self.task5_emails[0]
        else:
            # For Task 2, 3, and 4: single email
            emails_for_task = self.emails.get(task_id, [])
            if emails_for_task:
                self.current_email = random.choice(emails_for_task).copy()
            else:
                self.current_email = self._create_default_emails()[task_id][0].copy()
        
        # FIX 2: Add email_subjects to Task 5 metadata
        metadata = {
            "storage_used_gb": self.storage_used_gb,
            "storage_max_gb": self.storage_max_gb,
            "storage_percent": round((self.storage_used_gb / self.storage_max_gb) * 100, 1),
            "storage_warning": self.storage_used_gb > 12.0,
            "storage_account": f"Mail_{chr(ord('X') + self.storage_account_index - 1)}",
            # NEW: Temporal metadata
            "simulated_date": self.simulated_date.strftime('%Y-%m-%d'),
            "simulated_date_iso": self.simulated_date.isoformat(),
            "days_per_step": self.days_per_step,
        }
        
        # Add Task 5 specific metadata if applicable
        if task_id == 5:
            metadata["emails_to_rank"] = [e['id'] for e in self.task5_emails]
            metadata["email_subjects"] = {e['id']: e['subject'] for e in self.task5_emails}  # FIX 2
        
        # Create observation with storage AND temporal metadata
        self.current_observation = FellowBuffaloObservation(
            task_id=task_id,
            step=0,
            email_subject=self.current_email.get('subject', ''),
            email_body=self.current_email.get('body', ''),
            attachment_texts=self.current_email.get('attachment_texts', {}),
            deadline=self.current_email.get('correct_deadline') or self.current_email.get('deadline'),
            done=False,
            metadata=metadata
        )
        
        return self.current_observation
    
    def step(self, action: FellowBuffaloAction) -> Tuple[FellowBuffaloObservation, float, bool]:
        """Take an action, return observation, reward, done"""
        self.step_count += 1
        reward = 0.0
        
        # Calculate reward based on task
        if self.current_task == 1:
            # Task 1: Classification - Multi-email mode
            correct = {
                'tab': self.current_email.get('correct_tab'),
                'color': self.current_email.get('correct_color'),
                'deadline': self.current_email.get('correct_deadline')
            }
            agent = {
                'tab': action.tab,
                'color': action.color,
                'deadline': action.deadline
            }
            step_reward = task1_grader(correct, agent)
            reward += step_reward
            
            # Check if there are more emails in the queue
            if hasattr(self, 'task1_emails_queue') and len(self.task1_emails_queue) > self.step_count:
                # Load next email
                self.current_email = self.task1_emails_queue[self.step_count].copy()
                self.current_observation = FellowBuffaloObservation(
                    task_id=self.current_task,
                    step=self.step_count,
                    email_subject=self.current_email.get('subject', ''),
                    email_body=self.current_email.get('body', ''),
                    attachment_texts=self.current_email.get('attachment_texts', {}),
                    deadline=self.current_email.get('correct_deadline') or self.current_email.get('deadline'),
                    done=False
                )
                # Return with reward so far, episode continues
                return self.current_observation, reward, False
            else:
                # No more emails, episode done
                self.done = True
            
        elif self.current_task == 2:
            # Task 2: Summary + Tag Cloud with Rich Attachment Understanding
            reward = task2_grader(
                self.current_email.get('body', ''),
                action.summary or '',
                action.tag_cloud or '',
                self.current_email.get('attachment_texts', {})
            )
            self.done = True
            
        elif self.current_task == 3:
            # NEW: Advance simulated time each step
            from datetime import timedelta
            self.simulated_date += timedelta(days=self.days_per_step)
            
            # Simulate storage usage increase with each email (0.05 to 0.3 GB per email)
            import random
            email_size_gb = random.uniform(0.05, 0.3)  # 50MB to 300MB per email
            self.storage_used_gb += email_size_gb
            
            # Check storage warning (at 12 GB - 80% full)
            storage_warning = self.storage_used_gb > 12.0
            storage_critical = self.storage_used_gb >= 14.0  # 14 GB - almost full
            
            # Storage relay reward/penalty
            storage_reward = 0.0
            
            # NEW: Determine correct color based on SIMULATED DATE, not real date
            correct_color_for_step = 'green'
            deadline_str = self.current_email.get('deadline', '')
            if deadline_str:
                try:
                    from datetime import datetime
                    deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
                    # Use simulated_date for comparison
                    days_diff = (deadline - self.simulated_date).days
                    
                    if days_diff > 0:
                        correct_color_for_step = 'green'
                    elif -7 <= days_diff <= 0:
                        correct_color_for_step = 'orange'
                    else:
                        correct_color_for_step = 'red'
                except:
                    correct_color_for_step = 'green'
            
            # Check if agent triggered relay when critical
            if action.lifecycle_decisions:
                decision = action.lifecycle_decisions[-1]
                trigger_relay = decision.get('trigger_relay', False)
                agent_color = decision.get('color', 'green')
                
                # Storage relay logic
                if storage_critical and trigger_relay:
                    storage_reward = 0.15  # Bonus for triggering relay at right time
                    # Reset storage for new account
                    self.storage_used_gb = 0.5
                    self.storage_account_index += 1
                    print(f"  💾 Storage relay triggered! Moving to {chr(ord('X') + self.storage_account_index - 1)} account")
                elif storage_critical and not trigger_relay:
                    storage_reward = -0.1  # Penalty for not triggering relay
                elif not storage_critical and trigger_relay:
                    storage_reward = -0.05  # Small penalty for premature relay
                
                # Add temporal info to action decisions for grading
                for decision in action.lifecycle_decisions:
                    decision['deadline'] = self.current_email.get('deadline')
                    decision['storage_used'] = self.storage_used_gb
                    decision['storage_warning'] = storage_warning
                    decision['simulated_date'] = self.simulated_date.isoformat()  # NEW
                    decision['correct_color_for_step'] = correct_color_for_step  
            
            self.transitions.extend(action.lifecycle_decisions) if action.lifecycle_decisions else None
            
            # Check if we've processed enough emails
            if self.step_count >= len(self.emails.get(3, [])):
                correct_groups = [e.get('correct_group') for e in self.emails.get(3, []) if e.get('correct_group')]
                
                # FIX 1: Add pending_storage_reward to final score instead of returning it mid-episode
                reward = task3_grader(self.transitions, correct_groups)
                reward += self.pending_storage_reward  # Add all accumulated storage rewards
                reward = max(0.0, min(1.0, reward))  # Clamp between 0 and 1
                self.pending_storage_reward = 0.0  # Reset for next episode
                self.done = True
            else:
                # Load next email
                next_index = self.step_count
                if next_index < len(self.emails.get(3, [])):
                    self.current_email = self.emails[3][next_index].copy()
                    
                    # FIX 1: Store storage_reward for final accumulation, don't return it now
                    self.pending_storage_reward += storage_reward
                    
                    # Update observation with storage AND temporal info
                    self.current_observation = FellowBuffaloObservation(
                        task_id=self.current_task,
                        step=self.step_count,
                        email_subject=self.current_email.get('subject', ''),
                        email_body=self.current_email.get('body', ''),
                        attachment_texts=self.current_email.get('attachment_texts', {}),
                        deadline=self.current_email.get('deadline'),
                        done=False,
                        metadata={
                            "storage_used_gb": self.storage_used_gb,
                            "storage_max_gb": self.storage_max_gb,
                            "storage_percent": round((self.storage_used_gb / self.storage_max_gb) * 100, 1),
                            "storage_warning": self.storage_used_gb > 12.0,
                            "storage_critical": self.storage_used_gb >= 14.0,
                            "storage_account": f"Mail_{chr(ord('X') + self.storage_account_index - 1)}",
                            # NEW: Temporal metadata
                            "simulated_date": self.simulated_date.strftime('%Y-%m-%d'),
                            "simulated_date_iso": self.simulated_date.isoformat(),
                            "days_per_step": self.days_per_step
                        }
                    )
                    # FIX 1: Return 0.0 reward for intermediate steps (storage reward stored in pending)
                    return self.current_observation, 0.0, False
        
        elif self.current_task == 4:
            # Task 4: Reply Generation
            reward = task4_grader(
                self.current_email.get('subject', ''),
                self.current_email.get('body', ''),
                action.reply or ''
            )
            self.done = True
        
        elif self.current_task == 5:
            # Task 5: Priority Ranking
            if action.email_ranking:
                correct_order = [e['id'] for e in self.task5_emails]
                reward = task5_grader(correct_order, action.email_ranking)
            else:
                reward = 0.0
            self.done = True
        
        # Update observation for single-step tasks
        self.current_observation = FellowBuffaloObservation(
            task_id=self.current_task,
            step=self.step_count,
            email_subject=self.current_email.get('subject', ''),
            email_body=self.current_email.get('body', ''),
            attachment_texts=self.current_email.get('attachment_texts', {}),
            deadline=self.current_email.get('deadline'),
            done=self.done,
            reward=reward
        )
        
        return self.current_observation, reward, self.done
    
    def state(self) -> FellowBuffaloState:
        """Return current episode state"""
        task_names = {1: "email-intake", 2: "metadata-generation", 3: "lifecycle-manager", 4: "reply-generation", 5: "priority-ranking"}
        return FellowBuffaloState(
            task_id=self.current_task or 1,
            task_name=task_names.get(self.current_task, "unknown"),
            step_count=self.step_count,
            max_steps=self.max_steps,
            done=self.done
        )