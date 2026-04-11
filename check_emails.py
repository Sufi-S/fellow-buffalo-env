"""
Run this from your fellow-buffalo-env folder to show all email contents
"""
import os
import json

email_dir = "test_emails"
emails_by_task = {1: [], 2: [], 3: [], 4: [], 5: []}

for filename in sorted(os.listdir(email_dir)):
    if filename.endswith('.json'):
        filepath = os.path.join(email_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            email = json.load(f)
        
        task = email.get('task', 1)
        emails_by_task[task].append({
            'file': filename,
            'id': email.get('id', ''),
            'subject': email.get('subject', ''),
            'deadline': email.get('deadline') or email.get('correct_deadline', ''),
            'correct_color': email.get('correct_color', ''),
            'expected_color': email.get('expected_color', ''),
            'correct_group': email.get('correct_group', ''),
            'difficulty': email.get('difficulty', '')
        })

for task_id, emails in emails_by_task.items():
    print(f"\n{'='*50}")
    print(f"TASK {task_id} — {len(emails)} emails")
    print('='*50)
    for e in emails:
        print(f"  {e['file']}: {e['subject'][:50]}")
        print(f"    deadline={e['deadline']} | color={e['correct_color'] or e['expected_color']} | group={e['correct_group']} | difficulty={e['difficulty']}")