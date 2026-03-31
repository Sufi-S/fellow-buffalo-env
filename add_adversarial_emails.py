"""
Add adversarial test emails to challenge the AI agent.
These emails look like one category but belong to another.
"""

import json
import os

# Ensure test_emails folder exists
os.makedirs("test_emails", exist_ok=True)

adversarial_emails = [
    # Looks like Internship but is actually Finance (stipend payment)
    {
        "id": "adv_001",
        "subject": "Internship Stipend Payment — March 2026",
        "body": "Dear Intern,\n\nYour internship stipend of Rs 15,000 has been credited to your account ending 4521. Transaction ID: TRX-2026-03-21. Please check your bank statement.\n\nRegards,\nHR Department",
        "attachment_texts": {},
        "correct_tab": "Finance",  # NOT Internships
        "correct_color": "green",
        "correct_deadline": None,
        "task": 1,
        "difficulty": "hard",
        "adversarial": True
    },
    
    # Looks like Jobs but is actually News (report about hiring)
    {
        "id": "adv_002",
        "subject": "Google is Hiring 50,000 Engineers — Report",
        "body": "According to a Bloomberg report published today, Google plans to hire 50,000 engineers globally in 2026. The hiring spree focuses on AI and cloud divisions. This is the largest expansion in the company's history.",
        "attachment_texts": {},
        "correct_tab": "News",  # NOT Jobs
        "correct_color": "green",
        "correct_deadline": None,
        "task": 1,
        "difficulty": "hard",
        "adversarial": True
    },
    
    # Looks urgent but deadline already passed (should be red)
    {
        "id": "adv_003",
        "subject": "URGENT: Apply Now — Last 2 Seats Left",
        "body": "URGENT: Only 2 seats remain for our Advanced Python Bootcamp! Registration closes March 1, 2026. Don't miss this opportunity to upskill with industry experts. Limited seats available!",
        "attachment_texts": {},
        "correct_tab": "Events",
        "correct_color": "red",  # March 1 is past (today is March 31)
        "correct_deadline": "2026-03-01T23:59:00",
        "task": 1,
        "difficulty": "hard",
        "adversarial": True
    },
    
    # Looks like Sports but is actually Finance (betting/gambling)
    {
        "id": "adv_004",
        "subject": "IPL 2026 — Betting Odds & Predictions",
        "body": "IPL 2026: Best betting odds for today's match. Mumbai Indians vs Chennai Super Kings. Place your bets now! Get 50% bonus on first deposit.",
        "attachment_texts": {},
        "correct_tab": "Finance",  # Betting/gambling is finance, not sports
        "correct_color": "green",
        "correct_deadline": None,
        "task": 1,
        "difficulty": "hard",
        "adversarial": True
    },
    
    # Looks like News but is actually Events (webinar invitation)
    {
        "id": "adv_005",
        "subject": "Breaking: New AI Model Released — Join Our Webinar",
        "body": "Breaking news: We've released a revolutionary new AI model! Join our exclusive webinar on April 5, 2026 to learn how it works. Register now! Limited slots available.",
        "attachment_texts": {},
        "correct_tab": "Events",  # Webinar invitation is an event, not news
        "correct_color": "green",
        "correct_deadline": "2026-04-05T23:59:00",
        "task": 1,
        "difficulty": "hard",
        "adversarial": True
    },
    
    # Looks like General but is actually Internships (hidden internship)
    {
        "id": "adv_006",
        "subject": "Hello from the Tech Team!",
        "body": "Hey there! Quick update from our tech team. We're looking for a few passionate students to join us this summer. If you're interested in building cool stuff, let us know. We have a special program for students.",
        "attachment_texts": {},
        "correct_tab": "Internships",  # Hidden internship opportunity
        "correct_color": "green",
        "correct_deadline": None,
        "task": 1,
        "difficulty": "hard",
        "adversarial": True
    },
    
    # Looks like Finance but is actually Scam (phishing)
    {
        "id": "adv_007",
        "subject": "Your Account Will Be Suspended — Verify Now",
        "body": "IMPORTANT: Your account has been flagged for suspicious activity. Click here to verify your credentials immediately: http://fake-bank-verify.com",
        "attachment_texts": {},
        "correct_tab": "General",  # Scam/phishing goes to General
        "correct_color": "green",
        "correct_deadline": None,
        "task": 1,
        "difficulty": "hard",
        "adversarial": True
    },
]

# Save all emails
for email in adversarial_emails:
    filename = f"test_emails/{email['id']}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(email, f, indent=2, ensure_ascii=False)

print(f"✅ Added {len(adversarial_emails)} adversarial emails to test_emails/")
print("\nAdversarial emails added:")
for email in adversarial_emails:
    print(f"  - {email['id']}: {email['subject'][:50]}... → {email['correct_tab']}")