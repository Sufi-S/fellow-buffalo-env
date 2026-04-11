"""
fix_emails_v2.py - Fix all emails for April 10-14 evaluation window
Evaluation runs April 10-14, 2026
green  = deadline AFTER April 14 (future during eval)
orange = deadline April 7-14 (0-7 days past during eval)  
red    = deadline BEFORE April 7 (7+ days past during eval)
"""
import os
import json

email_dir = "test_emails"

# ============================================================
# TASK 1 FIXES
# ============================================================
task1_fixes = {
    # GREEN emails — deadline must be AFTER April 14
    "e01.json": {
        "correct_deadline": "2026-05-15T23:59:00",
        "correct_color": "green"
        # Software Engineer Intern — future deadline ✅
    },
    "e02.json": {
        "correct_deadline": "2026-04-30T23:59:00",
        "correct_color": "green"
        # Full Stack Developer — future deadline ✅
    },
    "e05.json": {
        "correct_deadline": "2026-04-25T23:59:00",
        "correct_color": "green"
        # TechFest — future deadline ✅
    },
    "e06.json": {
        "correct_deadline": "2026-04-20T23:59:00",
        "correct_color": "green"
        # Tuition Fee — future deadline ✅
    },
    "adv_005.json": {
        "correct_deadline": "2026-04-20T23:59:00",
        "correct_color": "green"
        # AI Webinar — future deadline ✅
    },

    # ORANGE emails — deadline must be April 7-14
    "e08.json": {
        "correct_deadline": "2026-04-10T23:59:00",
        "correct_color": "orange"
        # Google Internship — just passed during eval ✅
    },
    "e09.json": {
        "correct_deadline": "2026-04-08T23:59:00",
        "correct_color": "orange"
        # Hackathon Registration — just passed during eval ✅
    },

    # RED emails — deadline must be BEFORE April 7
    # adv_003 deadline 2026-03-01 = RED ✅ already correct
    # e03, e04, e07 have no deadline = GREEN ✅ already correct
}

# ============================================================
# TASK 3 FIXES — most important
# ============================================================
task3_fixes = {
    # e13-e22 are all 2025 = definitely RED ✅ no change needed

    # FUTURE (green) — deadline AFTER April 14
    "task3_future_001.json": {
        "deadline": "2026-04-21",
        "expected_color": "green"   # ✅ already correct
    },
    "task3_future_002.json": {
        "deadline": "2026-04-26",
        "expected_color": "green"   # ✅ already correct
    },
    "task3_future_003.json": {
        "deadline": "2026-04-16",
        "expected_color": "green"   # ✅ already correct
    },
    "task3_future_1.json": {
        "deadline": "2026-04-17",
        "expected_color": "green"   # ✅ already correct
    },
    "task3_future_2.json": {
        "deadline": "2026-04-17",
        "expected_color": "green"   # ✅ already correct
    },
    "task3_future_3.json": {
        "deadline": "2026-04-17",
        "expected_color": "green"   # ✅ already correct
    },

    # ORANGE — deadline April 7-14 (0-7 days past during eval)
    "task3_orange_001.json": {
        "deadline": "2026-04-10",
        "expected_color": "orange"  # April 10 = valid orange during eval ✅
    },
    "task3_orange_002.json": {
        "deadline": "2026-04-08",
        "expected_color": "orange"  # April 8 = valid orange during eval ✅
    },
    "task3_orange_003.json": {
        "deadline": "2026-04-07",
        "expected_color": "orange"  # April 7 = valid orange during eval ✅
    },
    "task3_recent_1.json": {
        "deadline": "2026-04-11",
        "expected_color": "orange"  # April 11 = valid orange during eval ✅
    },
    "task3_recent_2.json": {
        "deadline": "2026-04-09",
        "expected_color": "orange"  # April 9 = valid orange during eval ✅
    },
    "task3_recent_3.json": {
        "deadline": "2026-04-12",
        "expected_color": "orange"  # April 12 = valid orange during eval ✅
    },

    # RED — deadline BEFORE April 7
    "task3_old_1.json": {
        "deadline": "2026-03-08",
        "expected_color": "red"     # ✅ already correct
    },
    "task3_old_2.json": {
        "deadline": "2026-03-08",
        "expected_color": "red"     # ✅ already correct
    },
    "task3_old_3.json": {
        "deadline": "2026-03-08",
        "expected_color": "red"     # ✅ already correct
    },
    "task3_red_001.json": {
        "deadline": "2026-03-07",
        "expected_color": "red"     # ✅ already correct
    },
    "task3_red_002.json": {
        "deadline": "2026-03-17",
        "expected_color": "red"     # ✅ already correct
    },
    "task3_red_003.json": {
        "deadline": "2025-04-06",
        "expected_color": "red"     # ✅ already correct
    },

    # THREAD EMAILS — fix these carefully
    "thr01.json": {
        "deadline": "2026-04-15",
        "expected_color": "green"   # April 15 = future during eval ✅
    },
    "thr02.json": {
        "deadline": "2026-03-15",
        "expected_color": "red"     # March 15 = 25+ days past = RED ✅
    },
    "thr03.json": {
        "deadline": "2026-04-20",
        "expected_color": "green"   # April 20 = future during eval ✅
    },
    "thr04.json": {
        "deadline": "2026-04-07",
        "expected_color": "orange"  # April 7 = valid orange during eval ✅
    },
    "thr05.json": {
        "deadline": "2026-04-07",
        "expected_color": "orange"  # April 7 = valid orange during eval ✅
    },
    "thr_fix_01.json": {
        "deadline": "2026-04-20",
        "expected_color": "green"   # April 20 = future ✅
    },
    "thr_fix_02.json": {
        "deadline": "2026-04-10",
        "expected_color": "orange"  # April 10 = valid orange ✅
    },
    "thr_fix_03.json": {
        "deadline": "2026-03-22",
        "expected_color": "red"     # March 22 = RED ✅
    },
}

# ============================================================
# TASK 5 — CREATE 10 EMAILS (was 0!)
# ============================================================
task5_emails = [
    {
        "id": "email_urgent_server",
        "subject": "URGENT: Production Server Down",
        "body": "Production server is down. Customers cannot access service. All hands on deck. P0 incident.",
        "attachment_texts": {},
        "importance": 1,
        "task": 5,
        "difficulty": 3
    },
    {
        "id": "email_meeting_today",
        "subject": "Client Meeting Today at 2PM — Board Room",
        "body": "Important client meeting today at 2PM. Please prepare Q1 presentation. Client is from Infosys.",
        "attachment_texts": {},
        "importance": 2,
        "task": 5,
        "difficulty": 2
    },
    {
        "id": "email_code_review",
        "subject": "Code Review Needed — PR #456 Payment Gateway",
        "body": "Please review PR #456 for the payment gateway. This is blocking tomorrow's release.",
        "attachment_texts": {},
        "importance": 3,
        "task": 5,
        "difficulty": 2
    },
    {
        "id": "email_team_update",
        "subject": "Weekly Team Standup — Tomorrow 10AM",
        "body": "Weekly standup tomorrow at 10AM. Please update your task board before the meeting.",
        "attachment_texts": {},
        "importance": 4,
        "task": 5,
        "difficulty": 1
    },
    {
        "id": "email_documentation",
        "subject": "API Documentation Update Required",
        "body": "The API documentation needs to be updated before end of week. Please review and update.",
        "attachment_texts": {},
        "importance": 5,
        "task": 5,
        "difficulty": 1
    },
    {
        "id": "email_newsletter",
        "subject": "Company Newsletter — April 2026",
        "body": "Monthly company newsletter. New office opening, team awards, and upcoming events.",
        "attachment_texts": {},
        "importance": 6,
        "task": 5,
        "difficulty": 1
    },
    {
        "id": "email_lunch",
        "subject": "Team Lunch This Friday at 1PM",
        "body": "Team lunch this Friday at 1PM at the cafeteria. Please RSVP by Thursday.",
        "attachment_texts": {},
        "importance": 7,
        "task": 5,
        "difficulty": 1
    },
    {
        "id": "email_social",
        "subject": "Follow Us on LinkedIn!",
        "body": "Please like and share our latest LinkedIn post. Help us reach 10,000 followers!",
        "attachment_texts": {},
        "importance": 8,
        "task": 5,
        "difficulty": 1
    },
    {
        "id": "email_prize",
        "subject": "Congratulations! You Won a Gift Card",
        "body": "You have been selected as our lucky winner! Claim your Rs 500 gift card by clicking below.",
        "attachment_texts": {},
        "importance": 9,
        "task": 5,
        "difficulty": 1
    },
    {
        "id": "email_discount",
        "subject": "50% Off Sale — Today Only!",
        "body": "Massive sale today only! Get 50% off on all electronics. Use code SAVE50 at checkout.",
        "attachment_texts": {},
        "importance": 10,
        "task": 5,
        "difficulty": 1
    }
]

# ============================================================
# APPLY ALL FIXES
# ============================================================
def apply_fixes(fixes_dict, task_name):
    print(f"\nFixing {task_name} emails...")
    for filename, changes in fixes_dict.items():
        filepath = os.path.join(email_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                email = json.load(f)
            email.update(changes)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(email, f, indent=2)
            color = changes.get('correct_color') or changes.get('expected_color', '?')
            deadline = changes.get('correct_deadline') or changes.get('deadline', '?')
            print(f"  ✅ {filename}: {color} | {deadline}")
        else:
            print(f"  ❌ NOT FOUND: {filename}")

apply_fixes(task1_fixes, "Task 1")
apply_fixes(task3_fixes, "Task 3")

print("\nCreating Task 5 emails...")
for email in task5_emails:
    filepath = os.path.join(email_dir, f"task5_{email['id']}.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(email, f, indent=2)
    print(f"  ✅ Created task5_{email['id']}.json (importance={email['importance']})")

# ============================================================
# VERIFY — show color distribution
# ============================================================
print("\n" + "="*50)
print("VERIFICATION — Color distribution after fixes")
print("="*50)

for task_id in [1, 3]:
    colors = {"green": 0, "orange": 0, "red": 0, "unknown": 0}
    for filename in os.listdir(email_dir):
        if not filename.endswith('.json'):
            continue
        with open(os.path.join(email_dir, filename), 'r') as f:
            email = json.load(f)
        if email.get('task') != task_id:
            continue
        color = email.get('correct_color') or email.get('expected_color', '')
        if color in colors:
            colors[color] += 1
        else:
            colors['unknown'] += 1
    print(f"\nTask {task_id}: green={colors['green']} orange={colors['orange']} red={colors['red']} unknown={colors['unknown']}")

print("\nTask 5:", len([f for f in os.listdir(email_dir) if f.startswith('task5_')]), "emails")
print("\n✅ All done! Push and resubmit.")