"""Test the basic LangGraph setup"""
from src.resume_agent.graph import graph
from src.resume_agent.models import User
from src.resume_agent.database import SessionLocal
from langchain_core.messages import HumanMessage

# Get a test user
db = SessionLocal()
test_user = db.query(User).filter(User.email == "testuser@example.com").first()
db.close()

if not test_user:
    print("❌ No test user found. Run test_auth.py first!")
    exit(1)

print(f"Testing with user: {test_user.email}\n")

# Create initial state
config = {"configurable": {"thread_id": "test-thread-1"}}

initial_state = {
    "user_id": test_user.user_id,
    "messages": [],
    "profile_complete": False,
    "output_format": "pdf",
    "current_stage": "init",
    "needs_user_input": False
}

# Run the graph
print("=== Starting Graph Execution ===\n")
result = graph.invoke(initial_state, config)

# Print the response
for message in result["messages"]:
    if hasattr(message, 'content'):
        print(f"\n{message.content}\n")

print("\n=== Graph State ===")
print(f"Current stage: {result['current_stage']}")
print(f"Profile complete: {result['profile_complete']}")
