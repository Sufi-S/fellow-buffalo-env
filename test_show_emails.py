"""
Test script to verify adversarial emails are in the environment
"""

import json
import os
import random

# Load all Task 1 emails
task1_emails = []

for filename in os.listdir("test_emails"):
    if filename.endswith('.json'):
        with open(os.path.join("test_emails", filename), 'r', encoding='utf-8') as f:
            email = json.load(f)
            if email.get('task') == 1:
                task1_emails.append(email)

print(f"Total Task 1 emails: {len(task1_emails)}")
print(f"  - Normal emails: {len([e for e in task1_emails if not e.get('adversarial')])}")
print(f"  - Adversarial emails: {len([e for e in task1_emails if e.get('adversarial')])}")
print()

# Show 5 random emails
print("Random sample of emails:")
for email in random.sample(task1_emails, min(5, len(task1_emails))):
    adversarial = "🔴 ADVERSARIAL" if email.get('adversarial') else "🟢 NORMAL"
    print(f"  {adversarial} - {email['id']}: {email['subject'][:50]}... → {email['correct_tab']}")