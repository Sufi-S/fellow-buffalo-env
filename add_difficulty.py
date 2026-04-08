import json
import os
from datetime import datetime

def add_difficulty_to_emails():
    """Add difficulty field to all email JSON files"""
    
    test_emails_dir = "test_emails"
    
    if not os.path.exists(test_emails_dir):
        print(f"Directory {test_emails_dir} not found!")
        return
    
    files_updated = 0
    
    for filename in os.listdir(test_emails_dir):
        if not filename.endswith('.json'):
            continue
        
        filepath = os.path.join(test_emails_dir, filename)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        # Check if content is a list or single object
        if isinstance(content, list):
            emails = content
            modified = False
            for email in emails:
                if 'difficulty' not in email:
                    difficulty = determine_difficulty(email)
                    email['difficulty'] = difficulty
                    modified = True
            if modified:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(emails, f, indent=2)
                files_updated += 1
                print(f"Updated: {filename} ({len(emails)} emails)")
        else:
            # Single email object
            if 'difficulty' not in content:
                difficulty = determine_difficulty(content)
                content['difficulty'] = difficulty
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(content, f, indent=2)
                files_updated += 1
                print(f"Updated: {filename}")
    
    print(f"\n✅ Done! Updated {files_updated} files.")

def determine_difficulty(email):
    """Determine difficulty level based on email content"""
    
    body = email.get('body', '').lower()
    subject = email.get('subject', '').lower()
    deadline = email.get('correct_deadline', email.get('deadline', ''))
    
    # Hard (3): No deadline, ambiguous language, or urgent
    if not deadline or deadline == 'null' or deadline == '':
        return 3
    if 'asap' in body or 'urgent' in body:
        return 3
    if 'soon' in body:
        return 3
    if 'immediately' in body:
        return 3
    
    # Medium (2): Close deadlines, requires inference
    if 'tomorrow' in body or 'today' in body:
        return 2
    if 'this week' in body:
        return 2
    if 'by friday' in body:
        return 2
    
    # Check if deadline is within 3 days
    if deadline:
        try:
            # Try to parse deadline
            if 'T' in deadline:
                deadline_date = datetime.fromisoformat(deadline.split('T')[0])
            else:
                deadline_date = datetime.fromisoformat(deadline)
            
            days_diff = (deadline_date - datetime.now()).days
            if 0 <= days_diff <= 3:
                return 2  # Very close deadline = medium
        except:
            pass
    
    # Easy (1): Clear deadline, obvious keywords
    return 1

if __name__ == "__main__":
    add_difficulty_to_emails()