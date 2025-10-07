import requests
import time

BASE_URL = "http://localhost:8000"

resume = """Here's my resume:

Utsav Arora
arora252@purdue.edu | 480-882-8549

Education:
Purdue University, BS Computer Science, May 2027

Experience:
- Data Engineer at Smart Energy Water (May-Aug 2025): Built neural networks with Python and TensorFlow
- Frontend Developer at Huddle Social (Jan 2025-Present): Developed pages with React.js and Next.js

Technical Skills:
Languages: JavaScript, SQL, Python
Frameworks: React.js, Next.js, Node.js
Tools: AWS, Git
"""

job = """Software Engineer - Full Stack

Required: React, Node.js, Python, AWS, SQL

Nice to have: Next.js, TensorFlow
"""

print("Testing resume generation...")

# Step 1: Send resume
r1 = requests.post(f"{BASE_URL}/api/chat/message", json={"message": resume, "is_guest": True})
thread_id = r1.json()["thread_id"]
print(f"[OK] Resume uploaded (thread: {thread_id})")
time.sleep(1)

# Step 2: Confirm
r2 = requests.post(f"{BASE_URL}/api/chat/message", json={"message": "yes", "thread_id": thread_id, "is_guest": True})
print("[OK] Profile confirmed")
time.sleep(1)

# Step 3: Generate
r3 = requests.post(f"{BASE_URL}/api/chat/message", json={"message": job, "thread_id": thread_id, "is_guest": True})
result = r3.json()["response"]

print("\n" + "="*60)
print("RESULT:")
print("="*60)
print(result[:2000])  # First 2000 chars
print("="*60)

# Check for expected sections
if "Resume Optimizations" in result:
    print("[OK] Explanation section FOUND")
else:
    print("[FAIL] Explanation section MISSING")

if "Bolded Keywords:" in result:
    print("[OK] Keyword list FOUND")
else:
    print("[FAIL] Keyword list MISSING")

