"""
Fellow Buffalo - OpenEnv Environment
Implements reset(), step(), and state() methods.
"""

import json
import os
import random
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
        self.transitions = []
        self.done = False
        self.task1_emails_queue = []
        self.task3_emails_queue = []   # NEW: separate queue for task 3
        self.task5_emails = []

        # Storage simulation
        self.storage_used_gb = 8.5
        self.storage_max_gb = 15.0
        self.storage_account_index = 1
        self.storage_warning_triggered = False

        # Temporal reasoning
        self.simulated_date = None
        self.days_per_step = 1

        # Task 3 running total (for honest normalization)
        self.task3_total_reward = 0.0
        self.task3_max_steps = 15   # Always 15 steps

        # Episode history
        self.episode_history = []

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    def _clamp_score(self, score: float) -> float:
        return round(max(0.01, min(0.99, score)), 4)

    def _normalize_difficulty(self, difficulty):
        if difficulty is None:
            return 1
        if isinstance(difficulty, int):
            return max(1, min(3, difficulty))
        if isinstance(difficulty, str):
            diff_map = {"easy": 1, "medium": 2, "hard": 3, "1": 1, "2": 2, "3": 3}
            return diff_map.get(difficulty.lower(), 1)
        return 1

    def _get_tab_hint(self, tab):
        hints = {
            "Jobs": "hiring, salary, position, full-time",
            "Internships": "intern, stipend, fellowship, trainee",
            "Finance": "invoice, payment, fee, bill, receipt",
            "Events": "conference, register, fest, webinar, meetup",
            "Sports": "match, game, tournament, cricket, ipl",
            "News": "newsletter, digest, update, announcement",
            "General": "general information",
        }
        return hints.get(tab, "")

    # ------------------------------------------------------------------ #
    #  Email loading
    # ------------------------------------------------------------------ #

    def _load_emails(self) -> Dict[int, list]:
        emails = {1: [], 2: [], 3: [], 4: [], 5: []}

        if not os.path.exists(self.test_emails_path):
            return self._create_default_emails()

        for filename in os.listdir(self.test_emails_path):
            if filename.endswith(".json"):
                filepath = os.path.join(self.test_emails_path, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        email = json.load(f)
                        task_id = email.get("task", 1)
                        emails[task_id].append(email)
                except Exception:
                    continue

        for task_id in [1, 2, 3, 4, 5]:
            if not emails[task_id]:
                emails[task_id] = self._create_default_emails()[task_id]

        return emails

    def _create_default_emails(self) -> Dict[int, list]:
        return {
            1: [
                {"id": "default_001", "subject": "Summer Internship 2025", "body": "Applications close April 15, 2025", "attachment_texts": {}, "correct_tab": "Internships", "correct_color": "green", "correct_deadline": "2025-04-15T23:59:00", "difficulty": 2},
                {"id": "default_002", "subject": "Job Opportunity: Software Engineer", "body": "Apply by May 1st.", "attachment_texts": {}, "correct_tab": "Jobs", "correct_color": "green", "correct_deadline": "2025-05-01T23:59:00", "difficulty": 2},
                {"id": "default_003", "subject": "Urgent: Project Deadline", "body": "Submit report by tomorrow EOD.", "attachment_texts": {}, "correct_tab": "General", "correct_color": "red", "correct_deadline": "2025-03-29T23:59:00", "difficulty": 3},
                {"id": "default_004", "subject": "Conference Call Summary", "body": "Meeting notes from the Q1 planning session.", "attachment_texts": {}, "correct_tab": "General", "correct_color": "green", "correct_deadline": None, "difficulty": 1},
                {"id": "default_005", "subject": "Newsletter", "body": "AI weekly digest.", "attachment_texts": {}, "correct_tab": "News", "correct_color": "green", "correct_deadline": None, "difficulty": 1},
            ],
            2: [
                {"id": "default_006", "subject": "Tech News: AI Update", "body": "OpenAI released a new model today.", "attachment_texts": {}, "difficulty": 2},
                {"id": "default_007", "subject": "Meeting Summary", "body": "Q2 roadmap, budget allocation discussed.", "attachment_texts": {}, "difficulty": 2},
            ],
            3: [
                {"id": "default_008", "subject": "VIT Fee Payment", "body": "Fee deadline is March 20", "attachment_texts": {}, "received_date": "2025-03-01", "deadline": "2025-03-20", "correct_group": "finance_q1", "difficulty": 2},
                {"id": "default_009", "subject": "Internship Application", "body": "Submit documents by April 15", "attachment_texts": {}, "received_date": "2025-03-15", "deadline": "2025-04-15", "correct_group": "internships_q1", "difficulty": 2},
            ],
            4: [
                {"id": "default_010", "subject": "Internship Question", "body": "When can I expect to hear back?", "attachment_texts": {}, "difficulty": 2},
            ],
            5: self._create_default_task5_emails(),
        }

    def _create_default_task5_emails(self) -> List[Dict]:
        return [
            {"id": "email_urgent_server", "subject": "URGENT: Production Server Down", "body": "Production server is down. P0 incident.", "importance": 1, "task": 5, "difficulty": 3},
            {"id": "email_meeting_today", "subject": "Client Meeting Today at 2PM", "body": "Important client presentation today.", "importance": 2, "task": 5, "difficulty": 2},
            {"id": "email_code_review", "subject": "Code Review Needed — PR #456", "body": "Blocking tomorrow's release.", "importance": 3, "task": 5, "difficulty": 2},
            {"id": "email_team_update", "subject": "Weekly Team Standup — Tomorrow 10AM", "body": "Update your task board.", "importance": 4, "task": 5, "difficulty": 1},
            {"id": "email_documentation", "subject": "API Documentation Update Required", "body": "Update before end of week.", "importance": 5, "task": 5, "difficulty": 1},
            {"id": "email_newsletter", "subject": "Company Newsletter — April 2026", "body": "Monthly company newsletter.", "importance": 6, "task": 5, "difficulty": 1},
            {"id": "email_lunch", "subject": "Team Lunch This Friday at 1PM", "body": "Please RSVP by Thursday.", "importance": 7, "task": 5, "difficulty": 1},
            {"id": "email_social", "subject": "Follow Us on LinkedIn!", "body": "Like our latest LinkedIn post.", "importance": 8, "task": 5, "difficulty": 1},
            {"id": "email_prize", "subject": "Congratulations! You Won a Gift Card", "body": "Claim your Rs 500 gift card.", "importance": 9, "task": 5, "difficulty": 1},
            {"id": "email_discount", "subject": "50% Off Sale — Today Only!", "body": "Massive sale today only!", "importance": 10, "task": 5, "difficulty": 1},
        ]

    # ------------------------------------------------------------------ #
    #  reset()
    # ------------------------------------------------------------------ #

    def reset(self, task_id: int = 1, seed: int = None) -> FellowBuffaloObservation:
        if seed is not None:
            random.seed(seed)

        self.current_task = task_id
        self.step_count = 0
        self.done = False
        self.transitions = []
        self.storage_used_gb = 8.5
        self.storage_warning_triggered = False
        self.task3_total_reward = 0.0
        self.episode_history = []
        self.simulated_date = datetime(2026, 4, 9)

        # ---- Task 1: 5 emails, easy→medium→hard ----
        if task_id == 1:
            pool = self.emails.get(1, [])
            easy   = [e for e in pool if self._normalize_difficulty(e.get("difficulty")) == 1]
            medium = [e for e in pool if self._normalize_difficulty(e.get("difficulty")) == 2]
            hard   = [e for e in pool if self._normalize_difficulty(e.get("difficulty")) == 3]
            random.shuffle(easy)
            random.shuffle(medium)
            random.shuffle(hard)
            ordered = easy + medium + hard
            self.task1_emails_queue = ordered[:5]
            if not self.task1_emails_queue:
                self.task1_emails_queue = self._create_default_emails()[1][:5]
            self.current_email = self.task1_emails_queue[0].copy()

        # ---- Task 3: exactly 15 emails, shuffled ----
        elif task_id == 3:
            pool = self.emails.get(3, [])
            if len(pool) >= self.task3_max_steps:
                selected = random.sample(pool, self.task3_max_steps)
            else:
                # pad with repeats if not enough
                selected = pool.copy()
                while len(selected) < self.task3_max_steps:
                    selected.append(random.choice(pool).copy())
            random.shuffle(selected)
            self.task3_emails_queue = selected
            self.current_email = self.task3_emails_queue[0].copy()

        # ---- Task 5: 10 shuffled emails ----
        elif task_id == 5:
            pool = self.emails.get(5, [])
            if len(pool) >= 10:
                self.task5_emails = random.sample(pool, 10)
            else:
                self.task5_emails = random.sample(self._create_default_task5_emails(), 10)
            random.shuffle(self.task5_emails)
            self.current_email = self.task5_emails[0]

        # ---- Task 2, 4: single random email ----
        else:
            pool = self.emails.get(task_id, [])
            if pool:
                self.current_email = random.choice(pool).copy()
            else:
                self.current_email = self._create_default_emails()[task_id][0].copy()

        # Build metadata
        metadata = {
            "storage_used_gb": self.storage_used_gb,
            "storage_max_gb": self.storage_max_gb,
            "storage_percent": round((self.storage_used_gb / self.storage_max_gb) * 100, 1),
            "storage_warning": self.storage_used_gb > 12.0,
            "storage_critical": self.storage_used_gb >= 14.0,
            "storage_account": f"Mail_{chr(ord('X') + self.storage_account_index - 1)}",
            "simulated_date": self.simulated_date.strftime("%Y-%m-%d"),
            "simulated_date_iso": self.simulated_date.isoformat(),
            "days_per_step": self.days_per_step,
        }
        if task_id == 5:
            metadata["emails_to_rank"] = [e["id"] for e in self.task5_emails]
            metadata["email_subjects"] = {e["id"]: e["subject"] for e in self.task5_emails}
        if task_id == 3:
            metadata["total_steps"] = self.task3_max_steps

        self.current_observation = FellowBuffaloObservation(
            task_id=task_id,
            step=0,
            email_subject=self.current_email.get("subject", ""),
            email_body=self.current_email.get("body", ""),
            attachment_texts=self.current_email.get("attachment_texts", {}),
            deadline=self.current_email.get("correct_deadline") or self.current_email.get("deadline"),
            done=False,
            metadata=metadata,
            episode_history=self.episode_history,
            difficulty=self._normalize_difficulty(self.current_email.get("difficulty")),
        )
        return self.current_observation

    # ------------------------------------------------------------------ #
    #  step()
    # ------------------------------------------------------------------ #

    def step(self, action: FellowBuffaloAction) -> Tuple[FellowBuffaloObservation, float, bool]:
        self.step_count += 1
        reward = 0.0

        # ================================================================
        # TASK 1 — Email Classification (5 emails)
        # ================================================================
        if self.current_task == 1:
            correct = {
                "tab": self.current_email.get("correct_tab"),
                "color": self.current_email.get("correct_color"),
                "deadline": self.current_email.get("correct_deadline"),
            }
            agent = {
                "tab": action.tab,
                "color": action.color,
                "deadline": action.deadline,
                "confidence": action.confidence or 50,
            }
            step_reward = task1_grader(correct, agent)

            self.episode_history.append({
                "step": self.step_count,
                "email_id": self.current_email.get("id", "unknown"),
                "subject": self.current_email.get("subject", "")[:50],
                "action_tab": action.tab,
                "action_color": action.color,
                "reward": step_reward,
            })
            self.episode_history = self.episode_history[-3:]

            hint = None
            if step_reward < 0.33:
                correct_tab = self.current_email.get("correct_tab")
                if action.tab != correct_tab and correct_tab:
                    hint = f"Hint: Look for keywords like {self._get_tab_hint(correct_tab)}"
                elif action.color != self.current_email.get("correct_color"):
                    hint = "Hint: Check the deadline carefully — past or future?"

            # More emails in queue?
            if self.step_count < len(self.task1_emails_queue):
                self.current_email = self.task1_emails_queue[self.step_count].copy()
                self.current_observation = FellowBuffaloObservation(
                    task_id=self.current_task,
                    step=self.step_count,
                    email_subject=self.current_email.get("subject", ""),
                    email_body=self.current_email.get("body", ""),
                    attachment_texts=self.current_email.get("attachment_texts", {}),
                    deadline=self.current_email.get("correct_deadline") or self.current_email.get("deadline"),
                    done=False,
                    episode_history=self.episode_history,
                    hint=hint,
                    difficulty=self._normalize_difficulty(self.current_email.get("difficulty")),
                )
                return self.current_observation, step_reward, False
            else:
                self.done = True
                reward = step_reward

        # ================================================================
        # TASK 2 — Metadata Generation (1 step)
        # ================================================================
        elif self.current_task == 2:
            reward = self._clamp_score(
                task2_grader(
                    self.current_email.get("body", ""),
                    action.summary or "",
                    action.tag_cloud or "",
                    self.current_email.get("attachment_texts", {}),
                )
            )
            self.done = True

        # ================================================================
        # TASK 3 — Lifecycle Manager (exactly 15 steps)
        # ================================================================
        elif self.current_task == 3:
            # Advance simulated time
            self.simulated_date += timedelta(days=self.days_per_step)

            # Simulate storage growth
            email_size_gb = random.uniform(0.05, 0.3)
            self.storage_used_gb += email_size_gb
            storage_warning  = self.storage_used_gb > 12.0
            storage_critical = self.storage_used_gb >= 14.0

            # Determine correct color from SIMULATED date
            correct_color_for_step = "green"
            correct_group_for_step = self.current_email.get("correct_group", "general_q1")
            deadline_str = self.current_email.get("deadline", "")

            if deadline_str:
                try:
                    deadline_dt = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
                    # Make both naive for comparison
                    sim_naive = self.simulated_date.replace(tzinfo=None)
                    dl_naive  = deadline_dt.replace(tzinfo=None)
                    days_diff = (dl_naive - sim_naive).days

                    if days_diff > 0:
                        correct_color_for_step = "green"
                    elif -7 <= days_diff <= 0:
                        correct_color_for_step = "orange"
                    else:
                        correct_color_for_step = "red"
                except Exception:
                    correct_color_for_step = "green"

            # Score this step
            step_reward = 0.0
            agent_color  = "green"
            agent_group  = "general_q1"
            trigger_relay = False

            if action.lifecycle_decisions:
                decision = action.lifecycle_decisions[-1]
                trigger_relay = decision.get("trigger_relay", False)
                agent_color   = decision.get("color", "green")
                agent_group   = decision.get("group", "general_q1")

                # COLOR: +0.05 correct / -0.02 wrong
                if agent_color == correct_color_for_step:
                    step_reward += 0.05
                else:
                    step_reward -= 0.02

                # GROUP: +0.05 correct / -0.02 wrong
                if agent_group == correct_group_for_step:
                    step_reward += 0.05
                else:
                    step_reward -= 0.02

                # STORAGE RELAY
                if storage_critical and trigger_relay:
                    step_reward += 0.02
                    self.storage_used_gb = 0.5
                    self.storage_account_index += 1
                    print("  💾 Storage relay triggered!")
                elif storage_critical and not trigger_relay:
                    step_reward -= 0.03
                elif not storage_critical and trigger_relay:
                    step_reward -= 0.02

                # Record transition
                decision["deadline"]            = self.current_email.get("deadline")
                decision["storage_used"]        = self.storage_used_gb
                decision["storage_warning"]     = storage_warning
                decision["simulated_date"]      = self.simulated_date.isoformat()
                decision["correct_color_for_step"] = correct_color_for_step
                decision["correct_group"]       = correct_group_for_step
                self.transitions.append(decision)

            # Clamp step reward to [-0.1, 0.12]
            step_reward = max(-0.1, min(0.12, step_reward))
            self.task3_total_reward += step_reward

            # ---- Check if episode is done (used all 15 emails) ----
            if self.step_count >= self.task3_max_steps:
                max_possible = self.task3_max_steps * 0.12   # 15 × 0.12 = 1.80
                normalized   = self.task3_total_reward / max_possible if max_possible > 0 else 0.0
                final_reward = round(max(0.01, min(0.99, normalized)), 4)
                self.done = True

                # Update final observation
                self.current_observation = FellowBuffaloObservation(
                    task_id=self.current_task,
                    step=self.step_count,
                    email_subject=self.current_email.get("subject", ""),
                    email_body=self.current_email.get("body", ""),
                    attachment_texts=self.current_email.get("attachment_texts", {}),
                    deadline=self.current_email.get("deadline"),
                    done=True,
                    reward=final_reward,
                    metadata={
                        "storage_used_gb":  self.storage_used_gb,
                        "storage_max_gb":   self.storage_max_gb,
                        "storage_percent":  round((self.storage_used_gb / self.storage_max_gb) * 100, 1),
                        "storage_warning":  self.storage_used_gb > 12.0,
                        "storage_critical": self.storage_used_gb >= 14.0,
                        "storage_account":  f"Mail_{chr(ord('X') + self.storage_account_index - 1)}",
                        "simulated_date":   self.simulated_date.strftime("%Y-%m-%d"),
                        "simulated_date_iso": self.simulated_date.isoformat(),
                        "days_per_step":    self.days_per_step,
                        "total_steps":      self.task3_max_steps,
                    },
                    difficulty=self._normalize_difficulty(self.current_email.get("difficulty")),
                )
                return self.current_observation, final_reward, True

            else:
                # Load next email from queue
                next_email = self.task3_emails_queue[self.step_count].copy()
                self.current_email = next_email
                self.current_observation = FellowBuffaloObservation(
                    task_id=self.current_task,
                    step=self.step_count,
                    email_subject=self.current_email.get("subject", ""),
                    email_body=self.current_email.get("body", ""),
                    attachment_texts=self.current_email.get("attachment_texts", {}),
                    deadline=self.current_email.get("deadline"),
                    done=False,
                    metadata={
                        "storage_used_gb":  self.storage_used_gb,
                        "storage_max_gb":   self.storage_max_gb,
                        "storage_percent":  round((self.storage_used_gb / self.storage_max_gb) * 100, 1),
                        "storage_warning":  self.storage_used_gb > 12.0,
                        "storage_critical": self.storage_used_gb >= 14.0,
                        "storage_account":  f"Mail_{chr(ord('X') + self.storage_account_index - 1)}",
                        "simulated_date":   self.simulated_date.strftime("%Y-%m-%d"),
                        "simulated_date_iso": self.simulated_date.isoformat(),
                        "days_per_step":    self.days_per_step,
                        "total_steps":      self.task3_max_steps,
                    },
                    difficulty=self._normalize_difficulty(self.current_email.get("difficulty")),
                )
                return self.current_observation, step_reward, False

        # ================================================================
        # TASK 4 — Reply Generation (1 step)
        # ================================================================
        elif self.current_task == 4:
            reward = self._clamp_score(
                task4_grader(
                    self.current_email.get("subject", ""),
                    self.current_email.get("body", ""),
                    action.reply or "",
                )
            )
            self.done = True

        # ================================================================
        # TASK 5 — Priority Ranking (1 step)
        # ================================================================
        elif self.current_task == 5:
            if action.email_ranking:
                # Sort task5_emails by importance to get correct order
                correct_order = [
                    e["id"]
                    for e in sorted(self.task5_emails, key=lambda x: x.get("importance", 99))
                ]
                reward = self._clamp_score(task5_grader(correct_order, action.email_ranking))
            else:
                reward = 0.01
            self.done = True

        # ---- Final observation for single-step tasks ----
        self.current_observation = FellowBuffaloObservation(
            task_id=self.current_task,
            step=self.step_count,
            email_subject=self.current_email.get("subject", ""),
            email_body=self.current_email.get("body", ""),
            attachment_texts=self.current_email.get("attachment_texts", {}),
            deadline=self.current_email.get("deadline"),
            done=self.done,
            reward=reward,
            episode_history=self.episode_history,
            difficulty=self._normalize_difficulty(self.current_email.get("difficulty")),
        )
        return self.current_observation, reward, self.done

    # ------------------------------------------------------------------ #
    #  state()
    # ------------------------------------------------------------------ #

    def state(self) -> FellowBuffaloState:
        task_names = {
            1: "email-intake",
            2: "metadata-generation",
            3: "lifecycle-manager",
            4: "reply-generation",
            5: "priority-ranking",
        }
        return FellowBuffaloState(
            task_id=self.current_task or 1,
            task_name=task_names.get(self.current_task, "unknown"),
            step_count=self.step_count,
            max_steps=self.task3_max_steps if self.current_task == 3 else self.max_steps,
            done=self.done,
        )