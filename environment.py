"""
Fellow Buffalo - OpenEnv Environment
Implements reset(), step(), and state() methods.
"""

import json
import os
import random  # Added for random email selection
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from models import FellowBuffaloAction, FellowBuffaloObservation, FellowBuffaloState
from tasks import task1_grader, task2_grader, task3_grader


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
        
    def _load_emails(self) -> Dict[int, list]:
        """Load test emails from JSON files"""
        emails = {1: [], 2: [], 3: []}
        
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
        for task_id in [1, 2, 3]:
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
            ]
        }
    
    def reset(self, task_id: int = 1) -> FellowBuffaloObservation:
        """Reset environment and return first observation"""
        import random
        
        self.current_task = task_id
        self.step_count = 0
        self.done = False
        self.transitions = []
        
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
        else:
            # For Task 2 and 3: single email
            emails_for_task = self.emails.get(task_id, [])
            if emails_for_task:
                self.current_email = random.choice(emails_for_task).copy()
            else:
                self.current_email = self._create_default_emails()[task_id][0].copy()
        
        # Create observation
        self.current_observation = FellowBuffaloObservation(
            task_id=task_id,
            step=0,
            email_subject=self.current_email.get('subject', ''),
            email_body=self.current_email.get('body', ''),
            attachment_texts=self.current_email.get('attachment_texts', {}),
            deadline=self.current_email.get('correct_deadline') or self.current_email.get('deadline'),
            done=False
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
            # Task 2: Summary + Tag Cloud
            reward = task2_grader(
                self.current_email.get('body', ''),
                action.summary or '',
                action.tag_cloud or ''
            )
            self.done = True
            
        elif self.current_task == 3:
            # Task 3: Lifecycle Management
            if action.lifecycle_decisions:
                # Add deadline to each transition for proper grading
                for decision in action.lifecycle_decisions:
                    decision['deadline'] = self.current_email.get('deadline')
                self.transitions.extend(action.lifecycle_decisions)
            
            # Check if we've processed enough emails
            if self.step_count >= len(self.emails.get(3, [])):
                correct_groups = [e.get('correct_group') for e in self.emails.get(3, []) if e.get('correct_group')]
                reward = task3_grader(self.transitions, correct_groups)
                self.done = True
            else:
                # Load next email
                next_index = self.step_count
                if next_index < len(self.emails.get(3, [])):
                    self.current_email = self.emails[3][next_index].copy()
                    # Update observation with new email
                    self.current_observation = FellowBuffaloObservation(
                        task_id=self.current_task,
                        step=self.step_count,
                        email_subject=self.current_email.get('subject', ''),
                        email_body=self.current_email.get('body', ''),
                        attachment_texts=self.current_email.get('attachment_texts', {}),
                        deadline=self.current_email.get('deadline'),
                        done=False
                    )
                    return self.current_observation, 0.0, False
        
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
        task_names = {1: "email-intake", 2: "metadata-generation", 3: "lifecycle-manager"}
        return FellowBuffaloState(
            task_id=self.current_task or 1,
            task_name=task_names.get(self.current_task, "unknown"),
            step_count=self.step_count,
            max_steps=self.max_steps,
            done=self.done
        )