import json, os

attachment_emails = [
    {
        "id": "att01",
        "subject": "Offer Letter — Software Engineer Meta",
        "body": "Please find your offer letter attached. Review and sign by the acceptance deadline.",
        "attachment_texts": {
            "offer_letter.pdf": "OFFER LETTER\nPosition: Software Engineer L4\nCompany: Meta Platforms Inc\nBase Salary: $185,000\nRSU: $200,000 over 4 years\nSigning Bonus: $20,000\nStart Date: June 1, 2026\nOffer Expires: April 15, 2026\nAcceptance Deadline: April 10, 2026"
        },
        "correct_tab": "Jobs",
        "correct_color": "green",
        "correct_deadline": "2026-04-10T23:59:00",
        "task": 2
    },
    {
        "id": "att02",
        "subject": "Fee Receipt — Semester 6",
        "body": "Your fee payment has been processed. Receipt attached for your records.",
        "attachment_texts": {
            "fee_receipt.pdf": "OFFICIAL FEE RECEIPT\nStudent: Azam Sufiyan S\nRoll No: 22BCE1234\nSemester: 6 (Jan-May 2026)\nAmount Paid: Rs 1,25,000\nDate: March 15, 2026\nMode: Online Transfer\nTransaction ID: TXN789456123\nStatus: PAID"
        },
        "correct_tab": "Finance",
        "correct_color": "green",
        "correct_deadline": None,
        "task": 2
    },
    {
        "id": "att03",
        "subject": "Internship Certificate — Summer 2025",
        "body": "Please find your internship completion certificate attached.",
        "attachment_texts": {
            "certificate.pdf": "INTERNSHIP COMPLETION CERTIFICATE\nThis is to certify that Azam Sufiyan S has successfully completed\na 2-month internship at Google India Pvt Ltd\nDuration: June 1 - July 31, 2025\nProject: ML Pipeline Optimization\nPerformance Rating: Outstanding\nSigned: HR Manager, Google India"
        },
        "correct_tab": "Internships",
        "correct_color": "green",
        "correct_deadline": None,
        "task": 2
    }
]

os.makedirs("test_emails", exist_ok=True)
for email in attachment_emails:
    path = f"test_emails/{email['id']}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(email, f, indent=2)
    print(f"Created {path}")

print(f"\nDone — added {len(attachment_emails)} rich attachment emails")