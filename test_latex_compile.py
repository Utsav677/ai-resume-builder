"""Test LaTeX compilation with sample data"""
import sys
sys.path.insert(0, 'src')

from resume_agent.latex_service import LaTeXService

# Sample profile data
sample_profile = {
    "contact": {
        "full_name": "John Doe",
        "phone": "555-1234",
        "email": "john@example.com",
        "linkedin": "https://linkedin.com/in/johndoe",
        "github": "https://github.com/johndoe"
    },
    "education": [
        {
            "institution": "University of Example",
            "location": "City, State",
            "degree": "Bachelor of Science in Computer Science",
            "dates": "Aug 2018 - May 2022",
            "gpa": "3.8"
        }
    ],
    "experience": [
        {
            "title": "Software Engineer",
            "dates": "Jun 2022 - Present",
            "organization": "Tech Company Inc",
            "location": "San Francisco, CA",
            "bullets": [
                "Developed web applications using Python and JavaScript",
                "Improved system performance by 40%",
                "Led team of 3 junior developers",
                "Developed a 3-stage neural network for energy disaggregation\nusing real-time data"  # Test newline handling
            ]
        }
    ],
    "projects": [
        {
            "name": "Resume Builder AI",
            "technologies": "Python, FastAPI, LangGraph",
            "dates": "2024",
            "bullets": [
                "Built AI-powered resume optimization tool",
                "Achieved 85% ATS score improvement"
            ]
        }
    ],
    "technical_skills": {
        "languages": ["Python", "JavaScript", "TypeScript"],
        "frameworks": ["FastAPI", "React", "Next.js"],
        "developer_tools": ["Git", "Docker", "VS Code"],
        "libraries": ["NumPy", "Pandas", "LangChain"]
    }
}

print("Testing LaTeX compilation...")
service = LaTeXService()

# Generate LaTeX code
latex_code = service.fill_template(sample_profile)
print(f"[OK] LaTeX code generated ({len(latex_code)} chars)")

# Try to compile
print("Compiling to PDF...")
pdf_path = service.compile_to_pdf(latex_code, "test_resume")

if pdf_path:
    print(f"[SUCCESS] PDF created at: {pdf_path}")
else:
    print("[FAILED] PDF compilation failed")
    print("Check the output above for error details")
