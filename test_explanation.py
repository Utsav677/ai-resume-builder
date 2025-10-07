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

# Extract explanation section
if "Resume Optimizations:" in result:
    # Find start of explanation
    start_idx = result.find("**🎯 Resume Optimizations:")
    if start_idx == -1:
        start_idx = result.find("Resume Optimizations:")

    # Find end (look for next major section or end of string)
    end_markers = ["Copy this code", "Download your PDF"]
    end_idx = len(result)
    for marker in end_markers:
        idx = result.find(marker, start_idx)
        if idx != -1 and idx < end_idx:
            end_idx = idx

    explanation = result[start_idx:end_idx].strip()
    print("\n" + "="*60)
    print("EXPLANATION SECTION:")
    print("="*60)
    print(explanation)
    print("="*60)
else:
    print("\n[FAIL] No explanation found")
    print("\nShowing last 500 chars of response:")
    print(result[-500:])
