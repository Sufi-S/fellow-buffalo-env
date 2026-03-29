import json, os
os.makedirs("test_emails", exist_ok=True)

emails = [
  # TASK 1 emails (7 emails, one per tab)
  {"id":"e01","subject":"Software Engineer Intern — Meta Summer 2025","body":"We are excited to invite applications for our Summer 2025 internship program. Applications close April 15, 2025. Stipend: $8000/month. Requirements: Python, ML basics.","attachment_texts":{},"correct_tab":"Internships","correct_color":"green","correct_deadline":"2025-04-15T23:59:00","task":1},
  {"id":"e02","subject":"Full Stack Developer — Startup Hiring Now","body":"We are hiring a full-time Full Stack Developer. Apply by March 30, 2025. Salary: 12 LPA. Skills: React, Node, Python.","attachment_texts":{},"correct_tab":"Jobs","correct_color":"green","correct_deadline":"2025-03-30T23:59:00","task":1},
  {"id":"e03","subject":"AI Weekly Newsletter — Top Stories This Week","body":"This week in AI: OpenAI released GPT-5, Google announced Gemini Ultra 2, and Meta open-sourced a new model. Read the full stories below.","attachment_texts":{},"correct_tab":"News","correct_color":"green","correct_deadline":None,"task":1},
  {"id":"e04","subject":"IPL 2025 Match Schedule Released","body":"The IPL 2025 schedule is now live. Opening match: March 22 at Wankhede Stadium. Get your tickets now at the official website.","attachment_texts":{},"correct_tab":"Sports","correct_color":"green","correct_deadline":None,"task":1},
  {"id":"e05","subject":"TechFest 2025 — Register Before March 25","body":"VIT TechFest 2025 registrations are open. Events include hackathon, robotics, and coding competitions. Register before March 25, 2025.","attachment_texts":{},"correct_tab":"Events","correct_color":"green","correct_deadline":"2025-03-25T23:59:00","task":1},
  {"id":"e06","subject":"Tuition Fee Payment Due — VIT University","body":"Your semester fee of Rs 1,25,000 is due by March 31, 2025. Please pay via the student portal. Late fee applies after deadline.","attachment_texts":{},"correct_tab":"Finance","correct_color":"green","correct_deadline":"2025-03-31T23:59:00","task":1},
  {"id":"e07","subject":"Your Amazon Order Has Been Shipped","body":"Your order #402-8834521 has been shipped and will arrive by March 22. Track your package using the link below.","attachment_texts":{},"correct_tab":"General","correct_color":"green","correct_deadline":None,"task":1},

  # TASK 1 — Orange (deadline just passed)
  {"id":"e08","subject":"Google Research Internship — Application Closed","body":"Thank you for your interest. The application deadline was March 20, 2025. We received over 10,000 applications.","attachment_texts":{},"correct_tab":"Internships","correct_color":"orange","correct_deadline":"2025-03-20T23:59:00","task":1},
  {"id":"e09","subject":"Hackathon Registration Closed — March 15","body":"Registration for HackIndia 2025 closed on March 15. If you registered, check your email for team details.","attachment_texts":{},"correct_tab":"Events","correct_color":"orange","correct_deadline":"2025-03-15T23:59:00","task":1},

  # TASK 2 emails (with attachments)
  {"id":"e10","subject":"Research Internship at IIT Delhi — Summer 2025","body":"We are offering research internships in the areas of Machine Learning, Computer Vision, and NLP. Duration: May to July 2025. Stipend: Rs 15,000/month. Apply with your CV and a 500-word SOP by April 10, 2025.","attachment_texts":{"internship_details.pdf":"The internship will involve working on real research problems under faculty supervision. Students from top engineering colleges preferred. CGPA above 8.0 required. Submit your application at the portal."},"correct_tab":"Internships","correct_color":"green","correct_deadline":"2025-04-10T23:59:00","task":2},
  {"id":"e11","subject":"Invoice #INV-2025-0342 — Cloud Services","body":"Please find attached your invoice for cloud services for March 2025. Amount due: $149.00. Payment due by April 5, 2025.","attachment_texts":{"invoice_march.pdf":"Invoice Number: INV-2025-0342. Billing period: March 1-31 2025. AWS EC2: $89. S3 Storage: $35. Data Transfer: $25. Total: $149. Due date: April 5 2025."},"correct_tab":"Finance","correct_color":"green","correct_deadline":"2025-04-05T23:59:00","task":2},
  {"id":"e12","subject":"Project Report Submission — CS601 Advanced ML","body":"Submit your final project report by April 20, 2025. The report should be 15-20 pages and cover your methodology, experiments, and results. Submit via the course portal.","attachment_texts":{"project_guidelines.docx":"Report must include: Abstract (250 words), Introduction, Literature Review, Methodology, Experiments, Results, Conclusion. Use IEEE format. Font: Times New Roman 12pt. Submit as PDF."},"correct_tab":"General","correct_color":"green","correct_deadline":"2025-04-20T23:59:00","task":2},

  # TASK 3 emails (lifecycle management, 10 emails)
  {"id":"e13","subject":"Amazon SDE Intern — Application Open","body":"Apply for Amazon SDE internship. Deadline: March 10, 2025.","attachment_texts":{},"received_date":"2025-02-15","deadline":"2025-03-10","correct_group":"internships_q1","task":3},
  {"id":"e14","subject":"Microsoft Intern Application","body":"Microsoft internship applications close March 12, 2025.","attachment_texts":{},"received_date":"2025-02-16","deadline":"2025-03-12","correct_group":"internships_q1","task":3},
  {"id":"e15","subject":"Flipkart Campus Hiring","body":"Flipkart is hiring. Apply by March 8, 2025.","attachment_texts":{},"received_date":"2025-02-18","deadline":"2025-03-08","correct_group":"jobs_q1","task":3},
  {"id":"e16","subject":"VIT Semester Fee Due","body":"Pay your semester fee by March 15, 2025.","attachment_texts":{},"received_date":"2025-02-20","deadline":"2025-03-15","correct_group":"finance_q1","task":3},
  {"id":"e17","subject":"Google Summer of Code 2025","body":"GSoC applications open until April 2, 2025.","attachment_texts":{},"received_date":"2025-02-22","deadline":"2025-04-02","correct_group":"internships_q1","task":3},
  {"id":"e18","subject":"CodeChef Starters 120 — This Sunday","body":"Join CodeChef Starters 120 on March 19, 2025.","attachment_texts":{},"received_date":"2025-03-17","deadline":"2025-03-19","correct_group":"events_q1","task":3},
  {"id":"e19","subject":"Electricity Bill — March 2025","body":"Your electricity bill of Rs 1,240 is due March 20, 2025.","attachment_texts":{},"received_date":"2025-03-01","deadline":"2025-03-20","correct_group":"finance_q1","task":3},
  {"id":"e20","subject":"TCS NextStep Registration","body":"TCS NextStep registration closes March 25, 2025.","attachment_texts":{},"received_date":"2025-03-05","deadline":"2025-03-25","correct_group":"jobs_q1","task":3},
  {"id":"e21","subject":"HackIndia 2025 Registration","body":"Register for HackIndia 2025 by March 28, 2025.","attachment_texts":{},"received_date":"2025-03-10","deadline":"2025-03-28","correct_group":"events_q1","task":3},
  {"id":"e22","subject":"Infosys Internship Drive","body":"Infosys internship drive registration closes April 1, 2025.","attachment_texts":{},"received_date":"2025-03-12","deadline":"2025-04-01","correct_group":"internships_q1","task":3},
]

for email in emails:
    filename = f"test_emails/{email['id']}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(email, f, indent=2, ensure_ascii=False)

print(f"Created {len(emails)} test emails in test_emails/")