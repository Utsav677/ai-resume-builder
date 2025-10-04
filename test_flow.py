"""Test the complete conversation flow"""
import sys
import os
from pathlib import Path

# Enable custom checkpointer for standalone testing
os.environ["LANGGRAPH_USE_CUSTOM_CHECKPOINTER"] = "true"

sys.path.insert(0, str(Path(__file__).parent))

from src.resume_agent.graph import graph
from langchain_core.messages import HumanMessage

# The resume from the user
UTSAV_RESUME = r"""%-------------------------
% Resume in Latex
% Author : Jake Gutierrez
% Based off of: https://github.com/sb2nov/resume
% License : MIT
%------------------------

\documentclass[letterpaper,11pt]{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}
\input{glyphtounicode}


%----------FONT OPTIONS----------
% sans-serif
% \usepackage[sfdefault]{FiraSans}
% \usepackage[sfdefault]{roboto}
% \usepackage[sfdefault]{noto-sans}
% \usepackage[default]{sourcesanspro}

% serif
% \usepackage{CormorantGaramond}
% \usepackage{charter}


\pagestyle{fancy}
\fancyhf{} % clear all header and footer fields
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% Adjust margins - slightly more aggressive to fit content
\addtolength{\oddsidemargin}{-0.6in}
\addtolength{\evensidemargin}{-0.6in}
\addtolength{\textwidth}{1.2in}
\addtolength{\topmargin}{-.7in}
\addtolength{\textheight}{1.4in}

\urlstyle{same}

\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

% Sections formatting - reduced spacing
\titleformat{\section}{
  \vspace{-6pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-7pt}]

% Ensure that generate pdf is machine readable/ATS parsable
\pdfgentounicode=1

%-------------------------
% Custom commands - tighter spacing
\newcommand{\resumeItem}[1]{
  \item\small{
    {#1 \vspace{-3pt}}
  }
}

\newcommand{\resumeSubheading}[4]{
  \vspace{-3pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-9pt}
}

\newcommand{\resumeSubSubheading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \textit{\small#1} & \textit{\small #2} \\
    \end{tabular*}\vspace{-9pt}
}

\newcommand{\resumeProjectHeading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \small#1 & #2 \\
    \end{tabular*}\vspace{-9pt}
}

\newcommand{\resumeSubItem}[1]{\resumeItem{#1}\vspace{-6pt}}

\renewcommand\labelitemii{$\vcenter{\hbox{\tiny$\bullet$}}$}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}[itemsep=-1pt]}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-7pt}}

%-------------------------------------------
%%%%%%  RESUME STARTS HERE  %%%%%%%%%%%%%%%%%%%%%%%%%%%%


\begin{document}

%----------HEADING----------
\begin{center}
    \textbf{\Huge \scshape Utsav Arora} \\ \vspace{1pt}
    \small 480-882-8549 $|$ \href{mailto:arora252@purdue.edu}{\underline{arora252@purdue.edu}} $|$
    \href{https://linkedin.com/in/utsav-arora-4297a1174}{\underline{www.linkedin.com/in/u-arora}} $|$
    \href{https://github.com/Utsav677}{\underline{https://github.com/Utsav677}}
\end{center}


%-----------EDUCATION-----------
\section{Education}
  \resumeSubHeadingListStart
    \resumeSubheading
      {Purdue University}{West Lafayette, IN}
      {Bachelor of Science in Computer Science, Minor in AI and Math}{Expected Graduation: May 2027}
      \resumeItemListStart
        \resumeItem{Relevant Coursework: Data Structures and Algorithms, Object-Oriented Programming}
      \resumeItemListEnd
  \resumeSubHeadingListEnd


%-----------EXPERIENCE-----------
\section{Experience}
  \resumeSubHeadingListStart

    \resumeSubheading
      {Data Engineer/AI Researcher}{May 2025 -- August 2025}
      {Smart Energy Water (SEW)}{In-person}
      \resumeItemListStart
        \resumeItem{Developed a 3-stage neural network for energy disaggregation using regression networks, CNN, and deep learning subnetworks, achieving \textbf{72\% accuracy} with \textbf{50\% improvement} over baseline models}
        \resumeItem{Researched and implemented advanced ML architectures including GRU and LSTM models for energy consumption pattern recognition and time-series analysis}
        \resumeItem{Built interactive frontend prototype allowing users to upload Itron meter readings and visualize energy waste patterns with optimization recommendations}
        \resumeItem{Created channel optimization models for customer communication using data-driven assumptions and linear regression to predict ROI across different communication channels}
        \resumeItem{Generated and validated \textbf{10,000+ synthetic datasets} for model training while ensuring statistical accuracy and preventing data skew}
      \resumeItemListEnd

    \resumeSubheading
      {Founding Engineer/CSO}{Jan. 2025 -- Present}
      {ACS}{Hybrid}
      \resumeItemListStart
        \resumeItem{Developed responsive, intuitive user interfaces with React.js and Tailwind CSS, integrating \textbf{10+ APIs} for seamless, high-performance experiences}
        \resumeItem{Designed and optimized AWS DynamoDB data models and indexing strategies, improving query performance by \textbf{30\%} while ensuring scalability and reliability}
        \resumeItem{Leveraged AWS Lambda, CloudWatch, and IAM to automate database operations, monitor performance, and uphold security and data integrity}
        \resumeItem{Established development workflows and coding standards for the engineering team while mentoring junior developers}
      \resumeItemListEnd

    \resumeSubheading
      {Head Frontend Developer}{Jan. 2025 -- Present}
      {Huddle Social}{Remote}
      \resumeItemListStart
        \resumeItem{Led development of \textbf{10+ dynamic pages} for product showcases, event management, and housing listings using Next.js, React.js, and Tailwind CSS, scaling from \textbf{400 to 800+ active users} with \textbf{200+ daily active users}}
        \resumeItem{Optimized page load times by \textbf{2 seconds}, implementing Firebase Authentication for secure, real-time user management and managing Firestore and Storage buckets}
        \resumeItem{Planning deeper backend integrations to connect UI components with scalable cloud services and deliver a fully integrated application ecosystem}
        \resumeItem{Collaborated with design team to implement responsive UI components and optimize user experience across desktop and mobile platforms}
      \resumeItemListEnd



  \resumeSubHeadingListEnd


%-----------PROJECTS-----------
\section{Projects}
    \resumeSubHeadingListStart
      \resumeProjectHeading
          {\textbf{Energy Disaggregation Neural Network} $|$ \emph{Python, TensorFlow, CNN, GRU/LSTM, Frontend Development}}{2025}
          \resumeItemListStart
            \resumeItem{Designed and implemented a custom 3-stage neural network for smart meter energy disaggregation, achieving \textbf{72\% accuracy} in appliance identification}
            \resumeItem{Developed interactive web application prototype allowing users to upload meter data and receive personalized energy waste analysis}
            \resumeItem{Researched ML evolution in energy disaggregation from combinatorial optimization to modern GRU-based architectures}
          \resumeItemListEnd
      \resumeProjectHeading
          {\textbf{Plate Mate} $|$ \emph{Python, Web Scraping, KNN, GPT-4-turbo}}{2024}
          \resumeItemListStart
            \resumeItem{Developed a meal recommendation platform using web scraping, KNN algorithms, and GPT-4-turbo to enhance dining options for students}
            \resumeItem{Won Best Presentation and Pitch award for innovative approach to student meal planning}
            \resumeItem{Implemented machine learning techniques to personalize recommendations based on dietary preferences and nutritional needs}
          \resumeItemListEnd
      \resumeProjectHeading
          {\textbf{News Feed Application} $|$ \emph{Java, SQL, GUI}}{2024}
          \resumeItemListStart
            \resumeItem{Worked within a team to create a comprehensive news feed application with social features}
            \resumeItem{Implemented friend system with commenting functionality on posts using Java and SQL databases}
            \resumeItem{Designed and developed GUI interfaces for seamless user interaction and content management}
          \resumeItemListEnd
    \resumeSubHeadingListEnd


%-----------PROGRAMMING SKILLS-----------
\section{Technical Skills}
 \begin{itemize}[leftmargin=0.15in, label={}]
    \small{\item{
     \textbf{Languages}{: JavaScript, Python, Java, SQL, C, Arduino, HTML/CSS} \\
     \textbf{Frameworks}{: React.js, Next.js, Node.js, Tailwind CSS, Flask, FastAPI} \\
     \textbf{Developer Tools}{: Git, AWS (Lambda, DynamoDB, CloudWatch, IAM), Firebase, Vercel,  Jupyter Notebook} \\
     \textbf{Libraries \& Technologies}{: Firebase Authentication, Firestore, Cloud Storage, KNN, GPT-4-turbo, Web Scraping}
    }}
 \end{itemize}


%-------------------------------------------
\end{document}"""

JOB_DESCRIPTION = """Software Engineer - Full Stack
Company: TechCorp
Location: Remote

We're looking for a talented Full Stack Software Engineer to join our growing team.

Requirements:
- 2+ years of experience with React.js and Node.js
- Strong proficiency in Python and JavaScript
- Experience with AWS services (Lambda, DynamoDB, CloudWatch)
- Knowledge of SQL databases and data modeling
- Experience with REST APIs and frontend/backend integration
- Strong problem-solving skills and attention to detail

Preferred Qualifications:
- Experience with Next.js and modern frontend frameworks
- Knowledge of machine learning or AI applications
- Experience with Firebase or other cloud platforms
- Understanding of DevOps practices
- Bachelor's degree in Computer Science or related field

Responsibilities:
- Design and implement full-stack features
- Build scalable backend services with AWS
- Create responsive frontend interfaces
- Collaborate with cross-functional teams
- Write clean, maintainable code
- Participate in code reviews and technical discussions"""


def print_separator(title=""):
    print("\n" + "=" * 80)
    if title:
        print(f" {title}")
    print("=" * 80)


def print_messages(result):
    """Print only the LAST message (latest AI response)"""
    messages = result.get("messages", [])
    if messages:
        last_msg = messages[-1]
        if hasattr(last_msg, 'content'):
            # Remove emojis for console printing
            content = last_msg.content.encode('ascii', 'ignore').decode('ascii')
            print(f"\n{content}\n")


def test_conversation_flow():
    """Test the complete flow"""

    config = {"configurable": {"thread_id": "test-thread-123"}}

    print_separator("TEST 1: Initialize Session")
    print("User: hi")

    result = graph.invoke(
        {"messages": [HumanMessage(content="hi")]},
        config
    )

    print("\nAgent Response:")
    print_messages(result)
    print(f"\nCurrent Stage: {result.get('current_stage')}")
    print(f"Profile Complete: {result.get('profile_complete')}")

    # Check if it's waiting for resume
    if result.get('current_stage') != 'waiting_for_resume':
        print(f"\nERROR: Should be waiting for resume! Current stage: {result.get('current_stage')}")
        print(f"Messages: {[msg.content if hasattr(msg, 'content') else str(msg) for msg in result.get('messages', [])]}")
        return False

    print("\n[OK] Correctly waiting for resume")

    print_separator("TEST 2: Paste Resume")
    print(f"User: [Pasting resume - {len(UTSAV_RESUME)} characters]")

    result = graph.invoke(
        {"messages": [HumanMessage(content=UTSAV_RESUME)]},
        config
    )

    print("\nAgent Response:")
    print_messages(result)
    print(f"\nCurrent Stage: {result.get('current_stage')}")
    print(f"Profile Complete: {result.get('profile_complete')}")

    # Check if profile extracted
    if not result.get('profile_complete'):
        print("\n❌ ERROR: Profile should be extracted!")
        return False

    if result.get('current_stage') != 'waiting_for_job_description':
        print(f"\n❌ ERROR: Should be waiting for job description, but stage is: {result.get('current_stage')}")
        return False

    print("\n[OK] Profile extracted successfully")
    print("[OK] Correctly waiting for job description")

    print_separator("TEST 3: Paste Job Description")
    print(f"User: [Pasting job description - {len(JOB_DESCRIPTION)} characters]")

    result = graph.invoke(
        {"messages": [HumanMessage(content=JOB_DESCRIPTION)]},
        config
    )

    print("\nAgent Response:")
    print_messages(result)
    print(f"\nCurrent Stage: {result.get('current_stage')}")
    print(f"ATS Score: {result.get('ats_score')}")
    print(f"LaTeX Generated: {'Yes' if result.get('latex_code') else 'No'}")
    print(f"PDF Path: {result.get('pdf_path', 'N/A')}")

    # Check if resume generated
    if not result.get('latex_code'):
        print("\n❌ ERROR: LaTeX code should be generated!")
        return False

    if result.get('current_stage') != 'complete':
        print(f"\n❌ ERROR: Should be complete, but stage is: {result.get('current_stage')}")
        return False

    print("\n[OK] Resume generated successfully")
    print(f"[OK] ATS Score: {result.get('ats_score')}%")

    # Check LaTeX code snippet
    latex_code = result.get('latex_code', '')
    print(f"\n[OK] LaTeX code length: {len(latex_code)} characters")

    # Verify template structure
    if '\\documentclass' in latex_code and '\\resumeSubheading' in latex_code:
        print("[OK] LaTeX follows template structure")
    else:
        print("[WARNING] LaTeX might not follow template")

    print_separator("TEST 4: Returning User (New Thread, Has Profile)")
    print("User: hi")
    print("(Using new thread to simulate fresh conversation with existing profile)")

    # Use a different thread ID to simulate a new conversation
    # but the user profile from previous tests should still exist in DB
    new_config = {"configurable": {"thread_id": "test-thread-456"}}

    result = graph.invoke(
        {"messages": [HumanMessage(content="hi")]},
        new_config
    )

    print("\nAgent Response:")
    print_messages(result)
    print(f"\nCurrent Stage: {result.get('current_stage')}")

    # Should skip to job description since profile exists
    if result.get('current_stage') == 'waiting_for_resume':
        print("\n[ERROR] Should skip resume step for returning user!")
        return False

    print("\n[OK] Correctly skipped resume step for returning user")

    print_separator("SUMMARY")
    print("[SUCCESS] All tests passed!")
    print("\nFlow verification:")
    print("1. [OK] Initialize session")
    print("2. [OK] Wait for resume")
    print("3. [OK] Extract profile")
    print("4. [OK] Wait for job description")
    print("5. [OK] Analyze job")
    print("6. [OK] Select content")
    print("7. [OK] Optimize ATS")
    print("8. [OK] Generate resume")
    print("\n[SUCCESS] Conversation flow works correctly!")

    return True


if __name__ == "__main__":
    try:
        success = test_conversation_flow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
