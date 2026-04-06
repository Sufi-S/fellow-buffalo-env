import json, os

task4_emails = [
    {
        "id": "task4_001",
        "subject": "Internship Application Deadline Extended",
        "body": "Dear Applicant,\n\nThe deadline for the Summer Internship 2026 has been extended to April 30, 2026. Please submit your application by the new deadline.\n\nBest regards,\nHR Team",
        "attachment_texts": {},
        "task": 4
    },
    {
        "id": "task4_002",
        "subject": "Interview Invitation - Software Engineer",
        "body": "Dear Candidate,\n\nCongratulations! You have been shortlisted for a technical interview. Please select a time slot from the calendar link below.\n\nDate: April 10-15, 2026\nDuration: 60 minutes\n\nBest regards,\nRecruiting Team",
        "attachment_texts": {},
        "task": 4
    },
    {
        "id": "task4_003",
        "subject": "Fee Payment Reminder",
        "body": "Dear Student,\n\nThis is a reminder that your semester fee of Rs 1,25,000 is due by April 10, 2026. Late fee of Rs 5,000 will apply after the deadline.\n\nPlease make the payment at your earliest convenience.\n\nRegards,\nAccounts Office",
        "attachment_texts": {},
        "task": 4
    },
]

os.makedirs("test_emails", exist_ok=True)
for email in task4_emails:
    with open(f"test_emails/{email['id']}.json", "w", encoding="utf-8") as f:
        json.dump(email, f, indent=2)
    print(f"Created test_emails/{email['id']}.json")

print(f"\nDone! Added {len(task4_emails)} Task 4 emails")