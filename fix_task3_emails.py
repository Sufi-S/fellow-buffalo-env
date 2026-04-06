import json
import os
from datetime import datetime, timedelta

# Today's date for reference
today = datetime.now()
future_date = (today + timedelta(days=15)).strftime('%Y-%m-%d')
recent_past = (today - timedelta(days=3)).strftime('%Y-%m-%d')
old_past = (today - timedelta(days=30)).strftime('%Y-%m-%d')
very_old = (today - timedelta(days=365)).strftime('%Y-%m-%d')

# Balanced Task 3 emails
balanced_task3_emails = [
    # GREEN (future deadlines)
    {
        "id": "task3_future_001",
        "subject": "Google Summer Internship 2026",
        "body": "Applications for Google Summer Internship 2026 are now open. Deadline: " + future_date,
        "attachment_texts": {},
        "received_date": (today - timedelta(days=5)).strftime('%Y-%m-%d'),
        "deadline": future_date,
        "correct_group": "internships_q1",
        "task": 3,
        "expected_color": "green"
    },
    {
        "id": "task3_future_002",
        "subject": "Upcoming Tech Conference",
        "body": "Register for TechConf 2026 before " + (today + timedelta(days=20)).strftime('%Y-%m-%d'),
        "attachment_texts": {},
        "received_date": (today - timedelta(days=2)).strftime('%Y-%m-%d'),
        "deadline": (today + timedelta(days=20)).strftime('%Y-%m-%d'),
        "correct_group": "events_q1",
        "task": 3,
        "expected_color": "green"
    },
    {
        "id": "task3_future_003",
        "subject": "Fee Payment Deadline Extended",
        "body": "Last date to pay semester fee: " + (today + timedelta(days=10)).strftime('%Y-%m-%d'),
        "attachment_texts": {},
        "received_date": (today - timedelta(days=1)).strftime('%Y-%m-%d'),
        "deadline": (today + timedelta(days=10)).strftime('%Y-%m-%d'),
        "correct_group": "finance_q1",
        "task": 3,
        "expected_color": "green"
    },
    
    # ORANGE (recently passed - 0 to 7 days ago)
    {
        "id": "task3_orange_001",
        "subject": "Hackathon Registration Closed",
        "body": "Registration for HackIndia 2026 closed on " + recent_past,
        "attachment_texts": {},
        "received_date": (today - timedelta(days=10)).strftime('%Y-%m-%d'),
        "deadline": recent_past,
        "correct_group": "events_q1",
        "task": 3,
        "expected_color": "orange"
    },
    {
        "id": "task3_orange_002",
        "subject": "Job Application Deadline Passed",
        "body": "Applications for Software Engineer role closed on " + recent_past,
        "attachment_texts": {},
        "received_date": (today - timedelta(days=8)).strftime('%Y-%m-%d'),
        "deadline": recent_past,
        "correct_group": "jobs_q1",
        "task": 3,
        "expected_color": "orange"
    },
    {
        "id": "task3_orange_003",
        "subject": "Scholarship Application Due",
        "body": "Last date to apply for scholarship was " + (today - timedelta(days=5)).strftime('%Y-%m-%d'),
        "attachment_texts": {},
        "received_date": (today - timedelta(days=15)).strftime('%Y-%m-%d'),
        "deadline": (today - timedelta(days=5)).strftime('%Y-%m-%d'),
        "correct_group": "finance_q1",
        "task": 3,
        "expected_color": "orange"
    },
    
    # RED (old deadlines - more than 7 days ago)
    {
        "id": "task3_red_001",
        "subject": "Old Internship Application",
        "body": "This internship application closed on " + old_past,
        "attachment_texts": {},
        "received_date": (today - timedelta(days=60)).strftime('%Y-%m-%d'),
        "deadline": old_past,
        "correct_group": "internships_q1",
        "task": 3,
        "expected_color": "red"
    },
    {
        "id": "task3_red_002",
        "subject": "Expired Promo Code",
        "body": "Your discount code expired on " + (today - timedelta(days=20)).strftime('%Y-%m-%d'),
        "attachment_texts": {},
        "received_date": (today - timedelta(days=30)).strftime('%Y-%m-%d'),
        "deadline": (today - timedelta(days=20)).strftime('%Y-%m-%d'),
        "correct_group": "general_q1",
        "task": 3,
        "expected_color": "red"
    },
    {
        "id": "task3_red_003",
        "subject": "Old Fee Reminder",
        "body": "Your semester fee was due on " + very_old,
        "attachment_texts": {},
        "received_date": (today - timedelta(days=400)).strftime('%Y-%m-%d'),
        "deadline": very_old,
        "correct_group": "finance_q1",
        "task": 3,
        "expected_color": "red"
    },
]

# Also keep some thread emails (but with balanced dates)
thread_emails = [
    # Thread 1: Google internship (3 emails) - mix of colors
    {
        "id": "thr_fix_01",
        "subject": "Google SWE Intern — Application Received",
        "body": "Thank you for applying. We will review your application.",
        "attachment_texts": {},
        "received_date": (today - timedelta(days=25)).strftime('%Y-%m-%d'),
        "deadline": (today + timedelta(days=5)).strftime('%Y-%m-%d'),
        "correct_group": "internships_q1",
        "thread_id": "google_fixed_2026",
        "task": 3,
        "expected_color": "green"
    },
    {
        "id": "thr_fix_02",
        "subject": "Google SWE Intern — Interview Scheduled",
        "body": "Please schedule your technical interview by " + (today - timedelta(days=2)).strftime('%Y-%m-%d'),
        "attachment_texts": {},
        "received_date": (today - timedelta(days=10)).strftime('%Y-%m-%d'),
        "deadline": (today - timedelta(days=2)).strftime('%Y-%m-%d'),
        "correct_group": "internships_q1",
        "thread_id": "google_fixed_2026",
        "task": 3,
        "expected_color": "orange"
    },
    {
        "id": "thr_fix_03",
        "subject": "Google SWE Intern — Offer Expired",
        "body": "Your offer letter expired on " + (today - timedelta(days=15)).strftime('%Y-%m-%d'),
        "attachment_texts": {},
        "received_date": (today - timedelta(days=30)).strftime('%Y-%m-%d'),
        "deadline": (today - timedelta(days=15)).strftime('%Y-%m-%d'),
        "correct_group": "internships_q1",
        "thread_id": "google_fixed_2026",
        "task": 3,
        "expected_color": "red"
    },
]

# Delete old Task 3 emails and add new ones
test_emails_path = "test_emails"

# First, remove old Task 3 emails
for filename in os.listdir(test_emails_path):
    if filename.endswith('.json'):
        filepath = os.path.join(test_emails_path, filename)
        with open(filepath, 'r') as f:
            try:
                data = json.load(f)
                if data.get('task') == 3:
                    os.remove(filepath)
                    print(f"Removed old: {filename}")
            except:
                pass

# Add new balanced emails
all_new_emails = balanced_task3_emails + thread_emails
for email in all_new_emails:
    filename = f"test_emails/{email['id']}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(email, f, indent=2)
    print(f"Created: {filename}")

print(f"\n✅ Done! Added {len(all_new_emails)} balanced Task 3 emails")
print("\nColor distribution:")
colors = {}
for email in all_new_emails:
    color = email.get('expected_color', 'unknown')
    colors[color] = colors.get(color, 0) + 1
for color, count in colors.items():
    print(f"  {color}: {count} emails")