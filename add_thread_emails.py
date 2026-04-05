import json, os

thread_emails = [
    # Thread 1: Google internship (3 emails, same thread)
    {"id":"thr01","subject":"Google SWE Intern — Application Received","body":"Thank you for applying to Google SWE Internship 2026. We will review your application.","attachment_texts":{},"received_date":"2026-02-01","deadline":"2026-04-01","correct_group":"internships_q1","thread_id":"google_intern_2026","task":3},
    {"id":"thr02","subject":"Google SWE Intern — Interview Scheduled","body":"We would like to schedule a technical interview. Please select a slot by March 15.","attachment_texts":{},"received_date":"2026-03-01","deadline":"2026-03-15","correct_group":"internships_q1","thread_id":"google_intern_2026","task":3},
    {"id":"thr03","subject":"Google SWE Intern — Offer Letter","body":"Congratulations! We are pleased to offer you the Software Engineer Intern position. Please respond by April 5.","attachment_texts":{},"received_date":"2026-03-20","deadline":"2026-04-05","correct_group":"internships_q1","thread_id":"google_intern_2026","task":3},

    # Thread 2: Fee payment (2 emails, same thread)
    {"id":"thr04","subject":"VIT Semester Fee — First Notice","body":"Your semester fee of Rs 1,25,000 is due by March 31, 2026.","attachment_texts":{},"received_date":"2026-03-01","deadline":"2026-03-31","correct_group":"finance_q1","thread_id":"vit_fee_q1_2026","task":3},
    {"id":"thr05","subject":"VIT Semester Fee — Final Reminder","body":"FINAL REMINDER: Your semester fee is due tomorrow March 31. Late fee of Rs 5000 will apply.","attachment_texts":{},"received_date":"2026-03-30","deadline":"2026-03-31","correct_group":"finance_q1","thread_id":"vit_fee_q1_2026","task":3},
]

os.makedirs("test_emails", exist_ok=True)
for email in thread_emails:
    path = f"test_emails/{email['id']}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(email, f, indent=2)
    print(f"Created {path}")

print(f"Done — added {len(thread_emails)} thread emails")