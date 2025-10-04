# Resume Builder Agent - Quick Start Guide

## 🚀 Start Testing Now

```bash
langgraph dev
```

Then open http://localhost:2024 in your browser.

---

## 💬 How to Use

### Step 1: Paste Your Resume
```
You: "hello"
Agent: "Welcome! Please paste your resume..."

[Paste your entire resume - any format works]

Agent: "✅ Profile Created! Extracted 3 experiences, 2 projects. Now paste job description."
```

### Step 2: Paste Job Description
```
[Paste the job posting]

Agent:
- "Job Analysis Complete! Position: Software Engineer..."
- "Content Selection Complete! Selected 3 experiences..."
- "ATS Score: 78%"
- "✅ Resume Generated! PDF: outputs/resume_xxx_timestamp.pdf"
```

### Step 3: Get Your Resume
- LaTeX code shown in chat
- PDF saved to `outputs/` folder
- Both optimized for ATS with your matching skills prioritized

---

## 📁 What's Generated

Each resume generation creates:
1. **Tailored LaTeX Code** - Professional ATS-friendly format
2. **PDF File** - In `outputs/resume_USER_TIMESTAMP.pdf` (if LaTeX installed)
3. **Database Record** - Saved in `resume_generations` table with ATS score

---

## 🎯 Key Features

✅ **Profile Persistence** - Enter resume once, use for multiple jobs
✅ **Smart Content Selection** - AI ranks your experiences by relevance
✅ **ATS Optimization** - Keywords prioritized, score calculated (0-100%)
✅ **Professional Template** - Clean, parseable LaTeX format
✅ **Database Storage** - All resumes saved with timestamps

---

## 🔧 Requirements

### Must Have
- Python 3.11+
- OpenAI API key in `.env`
- Dependencies installed: `pip install -e .`

### Optional (for PDF)
- **LaTeX Distribution:**
  - Windows: [MiKTeX](https://miktex.org/download)
  - Mac: MacTeX
  - Linux: `sudo apt install texlive-full`

**Without LaTeX:** Agent returns LaTeX code - paste into [Overleaf.com](https://overleaf.com) to compile.

---

## 📊 What Gets Extracted

From your resume:
- ✅ Contact info (name, email, phone, LinkedIn, GitHub)
- ✅ Education (schools, degrees, GPAs, dates)
- ✅ Work experiences (title, company, dates, achievements)
- ✅ Projects (name, tech stack, dates, descriptions)
- ✅ Technical skills (languages, frameworks, tools, libraries)
- ✅ Awards (optional)

---

## 🎓 Example Conversation

```
USER: hi

AGENT: Welcome to the AI Resume Builder!
       First, paste your resume (full text or detailed summary).

USER: [pastes resume with 3 experiences, 2 projects, skills]

AGENT: ✅ Profile Created!
       Extracted:
       - 3 work experience(s)
       - 2 project(s)

       Great! Now paste the job description for the position you're applying to.

USER: [pastes Software Engineer job description]

AGENT: Got it! Analyzing the job description...

AGENT: Job Analysis Complete!
       Position: Software Engineer
       Level: mid
       Key Skills: Python, React, AWS, Docker, SQL...

       Now selecting most relevant experiences...

AGENT: Content Selection Complete!
       Selected 3 experiences and 2 projects.
       Prioritized experiences matching required skills: Python, cloud services...

AGENT: ATS Optimization Complete!
       ATS Score: 82.5%
       Matched 33/40 keywords
       ✓ Strong match!

       Generating resume...

AGENT: LaTeX code generated successfully!
       Compiling to PDF...

AGENT: ✅ Resume Generated Successfully!
       PDF saved to: outputs/resume_user123_20250102_143022.pdf
       ATS Score: 82.5%

       Your tailored resume is ready!

       **LaTeX Code:**
       ```latex
       \documentclass[letterpaper,11pt]{article}
       ...
       ```
```

---

## 🗂️ File Structure

```
resume-builder-agent/
├── outputs/                          # Generated PDFs
│   └── resume_user_20250102.pdf
├── templates/
│   └── resume_template.tex          # LaTeX template
├── resume_builder.db                # SQLite database (user profiles)
├── resume_builder_checkpoints.db    # LangGraph state (conversation memory)
├── .env                             # Your API keys (keep secret!)
├── langgraph.json                   # Deployment config
├── QUICK_START.md                   # This file
├── DEPLOYMENT_GUIDE.md              # Full deployment instructions
└── src/resume_agent/
    ├── graph.py                     # LangGraph workflow
    ├── nodes.py                     # All processing nodes
    ├── latex_service.py             # PDF generation
    └── database.py                  # Data persistence
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| "pdflatex not found" | Install LaTeX or use Overleaf.com with the code |
| Graph restarts | Check thread ID hasn't changed in Studio |
| No profile extracted | Paste at least 100 characters |
| Wrong ATS score | Verify job description has clear requirements |
| Import errors | Run `pip install -e .` |

---

## 💡 Pro Tips

1. **Better Extraction:** Include quantified achievements with metrics
2. **Higher ATS Score:** Use exact keywords from job description
3. **Multiple Jobs:** Same profile works for many job descriptions
4. **Edit Template:** Customize `templates/resume_template.tex`
5. **Check Output:** Review LaTeX before compiling for edge cases

---

## 📚 Next Steps

### For Testing
- Try with your real resume
- Test with 2-3 different job descriptions
- Compare ATS scores

### For Production
- Follow `DEPLOYMENT_GUIDE.md` for GCP deployment
- Switch to PostgreSQL for production database
- Add authentication if building a web interface

### For Customization
- Edit LaTeX template in `templates/resume_template.tex`
- Modify AI prompts in `nodes.py`
- Adjust ATS scoring logic in `ats_optimization_node`

---

## 🎉 You're Ready!

Run `langgraph dev` and start building ATS-optimized resumes!

**Need help?** Check:
- `DEPLOYMENT_GUIDE.md` - Comprehensive deployment guide
- `CONVERSATION_FIX.md` - How the conversation flow works
- `test_graph.py` - System verification script

**Questions or bugs?** Check the console logs - DEBUG messages show exactly what's happening at each step.

---

**Built with LangGraph** | **Powered by OpenAI** | **Template by Jake Gutierrez**
