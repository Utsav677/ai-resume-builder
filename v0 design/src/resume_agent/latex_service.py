"""LaTeX template filling and PDF compilation service"""
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, List


class LaTeXService:
    """Handle LaTeX template filling and PDF compilation"""

    TEMPLATE_PATH = Path(__file__).parent.parent.parent / "templates" / "resume_template.tex"
    OUTPUT_DIR = Path(__file__).parent.parent.parent / "outputs"

    def __init__(self):
        # Ensure output directory exists
        self.OUTPUT_DIR.mkdir(exist_ok=True)

    @staticmethod
    def escape_latex(text: str) -> str:
        """Escape special LaTeX characters"""
        if not text:
            return ""

        # Common LaTeX special characters
        replacements = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\^{}',
            '\\': r'\textbackslash{}',
        }

        for char, escaped in replacements.items():
            text = text.replace(char, escaped)

        return text

    @staticmethod
    def format_education_entry(edu: Dict) -> str:
        """Format a single education entry for LaTeX"""
        institution = LaTeXService.escape_latex(edu.get("institution", ""))
        location = LaTeXService.escape_latex(edu.get("location", ""))
        degree = LaTeXService.escape_latex(edu.get("degree", ""))
        dates = LaTeXService.escape_latex(edu.get("dates", ""))

        # Add GPA if present
        gpa = edu.get("gpa")
        if gpa:
            degree = f"{degree}, GPA: {LaTeXService.escape_latex(str(gpa))}"

        return f"    \\resumeSubheading\n      {{{institution}}}{{{location}}}\n      {{{degree}}}{{{dates}}}"

    @staticmethod
    def format_experience_entry(exp: Dict) -> str:
        """Format a single experience entry for LaTeX"""
        title = LaTeXService.escape_latex(exp.get("title", ""))
        dates = LaTeXService.escape_latex(exp.get("dates", ""))
        organization = LaTeXService.escape_latex(exp.get("organization", ""))
        location = LaTeXService.escape_latex(exp.get("location", ""))
        bullets = exp.get("bullets", [])

        entry = f"    \\resumeSubheading\n      {{{title}}}{{{dates}}}\n      {{{organization}}}{{{location}}}\n"

        if bullets:
            entry += "      \\resumeItemListStart\n"
            for bullet in bullets:
                escaped_bullet = LaTeXService.escape_latex(bullet)
                entry += f"        \\resumeItem{{{escaped_bullet}}}\n"
            entry += "      \\resumeItemListEnd\n"

        return entry

    @staticmethod
    def format_project_entry(proj: Dict) -> str:
        """Format a single project entry for LaTeX"""
        name = LaTeXService.escape_latex(proj.get("name", ""))
        technologies = LaTeXService.escape_latex(proj.get("technologies", ""))
        dates = LaTeXService.escape_latex(proj.get("dates", ""))
        bullets = proj.get("bullets", [])

        entry = f"      \\resumeProjectHeading\n          {{\\textbf{{{name}}} $|$ \\emph{{{technologies}}}}}{{{dates}}}\n"

        if bullets:
            entry += "          \\resumeItemListStart\n"
            for bullet in bullets:
                escaped_bullet = LaTeXService.escape_latex(bullet)
                entry += f"            \\resumeItem{{{escaped_bullet}}}\n"
            entry += "          \\resumeItemListEnd\n"

        return entry

    def fill_template(
        self,
        profile_data: Dict,
        selected_experiences: Optional[List[Dict]] = None,
        selected_projects: Optional[List[Dict]] = None,
        prioritized_skills: Optional[Dict] = None
    ) -> str:
        """Fill LaTeX template with user data"""

        # Read template
        with open(self.TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            template = f.read()

        # Extract contact info
        contact = profile_data.get("contact", {})
        full_name = self.escape_latex(contact.get("full_name", ""))
        phone = self.escape_latex(contact.get("phone", ""))
        email = contact.get("email", "")  # Don't escape email
        linkedin = contact.get("linkedin", "")
        github = contact.get("github", "")
        portfolio = contact.get("portfolio")

        # Portfolio link (optional)
        portfolio_link = ""
        if portfolio:
            portfolio_link = f" $|$ \\href{{{portfolio}}}{{\\underline{{Portfolio}}}}"

        # Fill contact info
        template = template.replace("{{FULL_NAME}}", full_name)
        template = template.replace("{{PHONE}}", phone)
        template = template.replace("{{EMAIL}}", email)
        template = template.replace("{{LINKEDIN_URL}}", linkedin or "https://linkedin.com")
        template = template.replace("{{GITHUB_URL}}", github or "https://github.com")
        template = template.replace("{{PORTFOLIO_LINK}}", portfolio_link)

        # Format education entries
        education_list = profile_data.get("education", [])
        education_entries = "\n".join([self.format_education_entry(edu) for edu in education_list])
        template = template.replace("{{EDUCATION_ENTRIES}}", education_entries)

        # Format experience entries (use selected if provided)
        if selected_experiences is not None:
            experience_list = selected_experiences
        else:
            experience_list = profile_data.get("experience", [])
        experience_entries = "\n\n".join([self.format_experience_entry(exp) for exp in experience_list])
        template = template.replace("{{EXPERIENCE_ENTRIES}}", experience_entries)

        # Format project entries (use selected if provided)
        if selected_projects is not None:
            project_list = selected_projects
        else:
            project_list = profile_data.get("projects", [])
        project_entries = "\n".join([self.format_project_entry(proj) for proj in project_list])
        template = template.replace("{{PROJECT_ENTRIES}}", project_entries)

        # Format technical skills (use prioritized if provided)
        if prioritized_skills:
            skills = prioritized_skills
        else:
            skills = profile_data.get("technical_skills", {})

        languages = ", ".join(skills.get("languages", []))
        frameworks = ", ".join(skills.get("frameworks", []))
        developer_tools = ", ".join(skills.get("developer_tools", []))
        libraries = ", ".join(skills.get("libraries", []))

        template = template.replace("{{LANGUAGES}}", self.escape_latex(languages))
        template = template.replace("{{FRAMEWORKS}}", self.escape_latex(frameworks))
        template = template.replace("{{DEVELOPER_TOOLS}}", self.escape_latex(developer_tools))
        template = template.replace("{{LIBRARIES}}", self.escape_latex(libraries))

        # Format awards (optional)
        awards = profile_data.get("awards", [])
        if awards:
            awards_section = "\n%-----------AWARDS-----------\n\\section{Awards}\n\\begin{itemize}[leftmargin=0.15in, label={}]\n"
            for award in awards:
                title = self.escape_latex(award.get("title", ""))
                desc = award.get("description")
                if desc:
                    awards_section += f"  \\item \\textbf{{{title}}}: {self.escape_latex(desc)}\n"
                else:
                    awards_section += f"  \\item \\textbf{{{title}}}\n"
            awards_section += "\\end{itemize}\n"
            template = template.replace("{{AWARDS_SECTION}}", awards_section)
        else:
            template = template.replace("{{AWARDS_SECTION}}", "")

        return template

    def compile_to_pdf(self, latex_code: str, output_filename: str = "resume") -> Optional[str]:
        """
        Compile LaTeX code to PDF

        Args:
            latex_code: The LaTeX source code
            output_filename: Base name for output file (without extension)

        Returns:
            Path to generated PDF file, or None if compilation failed
        """
        # Create temporary directory for compilation
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            tex_file = temp_path / f"{output_filename}.tex"

            # Write LaTeX code to temp file
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(latex_code)

            try:
                # Run pdflatex twice (for references)
                for _ in range(2):
                    result = subprocess.run(
                        ['pdflatex', '-interaction=nonstopmode', f'{output_filename}.tex'],
                        cwd=temp_path,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    if result.returncode != 0:
                        print(f"LaTeX compilation error: {result.stdout}")
                        print(f"LaTeX stderr: {result.stderr}")
                        return None

                # Move PDF to output directory
                pdf_file = temp_path / f"{output_filename}.pdf"
                if pdf_file.exists():
                    output_path = self.OUTPUT_DIR / f"{output_filename}.pdf"
                    shutil.copy(pdf_file, output_path)
                    return str(output_path)
                else:
                    print("PDF file was not generated")
                    return None

            except FileNotFoundError:
                print("ERROR: pdflatex not found. Please install LaTeX (MiKTeX or TeX Live)")
                return None
            except subprocess.TimeoutExpired:
                print("ERROR: LaTeX compilation timed out")
                return None
            except Exception as e:
                print(f"ERROR: Unexpected error during PDF compilation: {e}")
                return None
