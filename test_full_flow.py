import requests
import json
import time

BASE_URL = "http://localhost:8000"

# Test resume content  
resume = """Here's my resume:

Utsav Arora
480-882-8549 | arora252@purdue.edu

Education:
Purdue University, BS Computer Science, Expected Graduation: May 2027

Experience:

Data Engineer/AI Researcher
Smart Energy Water | May 2025 - August 2025
- Developed neural network for energy disaggregation using regression networks and CNN
- Built interactive frontend allowing users to upload meter readings
- Created channel optimization models using linear regression

Head Frontend Developer  
Huddle Social | Jan 2025 - Present
- Led development of 10+ dynamic pages using Next.js and React.js
- Optimized page load times implementing Firebase Authentication
- Scaled from 400 to 800+ active users

Projects:

Energy Disaggregation Neural Network (2025)
Technologies: Python, TensorFlow, CNN, Frontend Development
- Designed 3-stage neural network achieving 72% accuracy
- Developed interactive web application prototype

Plate Mate (2024)
Technologies: Python, Web Scraping, KNN, GPT-4
- Developed meal recommendation platform using KNN and GPT-4
- Won Best Presentation award

Technical Skills:
Languages: JavaScript, SQL, Python, Java, C
Frameworks: React.js, Next.js, Node.js, Tailwind CSS, Flask
Developer Tools: Git, AWS, Firebase, Vercel
Libraries: TensorFlow, KNN, GPT-4
"""

job_description = """Software Engineer - Full Stack
TechCorp Inc.

Required Skills:
- React and Node.js
- Python backend
- AWS (Lambda, DynamoDB, CloudWatch)
- RESTful APIs
- SQL databases
- Git

Nice to have:
- Next.js
- TensorFlow/ML
- CI/CD
- Microservices
"""

print("=" * 80)
print("FULL END-TO-END TEST")
print("=" * 80)

# Step 1: Send resume directly
print("\n[1/3] Sending resume...")
response = requests.post(
    f"{BASE_URL}/api/chat/message",
    json={"message": resume, "is_guest": True}
)
print(f"Status: {response.status_code}")
data = response.json()
thread_id = data["thread_id"]
print(f"Thread ID: {thread_id}")
print(f"Response preview: {data['response'][:150]}...")

time.sleep(2)

# Step 2: Confirm profile
print("\n[2/3] Confirming profile...")
response = requests.post(
    f"{BASE_URL}/api/chat/message",
    json={"message": "yes looks perfect", "thread_id": thread_id, "is_guest": True}
)
print(f"Status: {response.status_code}")
data = response.json()
print(f"Response preview: {data['response'][:150]}...")

time.sleep(2)

# Step 3: Submit job description
print("\n[3/3] Submitting job description and generating resume...")
print("(This will take 30-60 seconds)")
response = requests.post(
    f"{BASE_URL}/api/chat/message",
    json={"message": job_description, "thread_id": thread_id, "is_guest": True}
)

print(f"Status: {response.status_code}")
result = response.json()

print("\n" + "=" * 80)
print("FINAL RESULT:")
print("=" * 80)
print(result['response'])

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)

# Check for key indicators
if "📝 AI Content Enhancements" in result['response']:
    print("✅ Content enhancement explanation FOUND")
else:
    print("❌ Content enhancement explanation MISSING")

if "Keywords Added:" in result['response']:
    print("✅ Keywords list FOUND")
else:
    print("❌ Keywords list MISSING")

if result.get('ats_score'):
    print(f"✅ ATS Score: {result['ats_score']}%")
else:
    print("❌ ATS Score MISSING")

if result.get('latex_code'):
    # Check if keywords are bolded in LaTeX
    latex = result['latex_code']
    if '\textbf{' in latex:
        count = latex.count('\textbf{')
        print(f"✅ Found {count} bolded keywords in LaTeX")
    else:
        print("❌ NO bolded keywords in LaTeX")

