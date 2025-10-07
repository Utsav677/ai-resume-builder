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

    def bold_keywords(self, text: str, matched_keywords: set) -> str:
        """Bold matched keywords in text (case-insensitive)"""
        if not text or not matched_keywords:
            return text

        # Sort keywords by length (longest first) to avoid partial replacements
        sorted_keywords = sorted(matched_keywords, key=len, reverse=True)

        for keyword in sorted_keywords:
            # Create case-insensitive pattern
            import re
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            # Bold the keyword
            text = pattern.sub(lambda m: r'\textbf{' + m.group(0) + '}', text)

        return text

    def bold_keywords_escaped(self, escaped_text: str, matched_keywords: set) -> str:
        """Bold matched keywords in already-escaped LaTeX text"""
        if not escaped_text or not matched_keywords:
            return escaped_text

        import re

        # Sort keywords by length (longest first) to avoid partial replacements
        sorted_keywords = sorted(matched_keywords, key=len, reverse=True)

        print(f"[BOLD] bold_keywords_escaped called with {len(sorted_keywords)} keywords")

        for keyword in sorted_keywords:
            # Escape the keyword to match against escaped text
            escaped_keyword = self.escape_latex(keyword)

            # Create case-insensitive pattern to find the escaped keyword
            # Use word boundaries to avoid partial matches
            pattern = re.compile(re.escape(escaped_keyword), re.IGNORECASE)

            # Check if pattern matches anything
            matches = pattern.findall(escaped_text)
            if matches:
                print(f"[BOLD] Bolding keyword '{keyword}' ({len(matches)} matches)")

            # Replace with bolded version (the matched text is already escaped)
            escaped_text = pattern.sub(lambda m: r'\textbf{' + m.group(0) + '}', escaped_text)

        return escaped_text

    @staticmethod
    def escape_latex(text: str) -> str:
        """Escape special LaTeX characters"""
        if not text:
            return ""

        # IMPORTANT: Escape backslash FIRST to avoid double-escaping
        text = text.replace('\\', r'\textbackslash{}')

        # Then escape other special characters
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
        }

        for char, escaped in replacements.items():
            text = text.replace(char, escaped)

        return text

    @staticmethod
    def normalize_dates(dates: str) -> str:
        """Normalize date format to ensure dash is present for ranges only"""
        if not dates:
            return ""

        # Don't add dash if already present
        if '-' in dates:
            return dates

        # Don't add dash for single dates (expected graduation, ongoing, etc.)
        single_date_indicators = ['expected', 'present', 'current', 'ongoing', 'graduation']
        if any(indicator in dates.lower() for indicator in single_date_indicators):
            return dates

        # Only add dash if we have exactly 4 parts that look like: Month Year Month Year
        # e.g., "May 2025 August 2025" -> "May 2025 - August 2025"
        parts = dates.split()
        if len(parts) == 4:
            # Check if pattern is Month Year Month Year (basic heuristic)
            # First and third parts should be non-numeric (months)
            # Second and fourth should be numeric (years)
            try:
                int(parts[1])  # Should be year
                int(parts[3])  # Should be year
                # Looks like a date range
                return f"{parts[0]} {parts[1]} - {parts[2]} {parts[3]}"
            except ValueError:
                # Not a date range pattern
                pass

        return dates

    def format_education_entry(self, edu: Dict) -> str:
        """Format a single education entry for LaTeX"""
        institution = self.escape_latex(edu.get("institution", ""))
        location = self.escape_latex(edu.get("location", ""))
        degree = self.escape_latex(edu.get("degree", ""))
        dates = self.normalize_dates(edu.get("dates", ""))
        dates = self.escape_latex(dates)

        # Add GPA if present
        gpa = edu.get("gpa")
        if gpa:
            degree = f"{degree}, GPA: {self.escape_latex(str(gpa))}"

        return f"    \\resumeSubheading\n      {{{institution}}}{{{location}}}\n      {{{degree}}}{{{dates}}}"

    def format_experience_entry(self, exp: Dict) -> str:
        """Format a single experience entry for LaTeX"""
        title = self.escape_latex(exp.get("title", ""))
        dates = self.normalize_dates(exp.get("dates", ""))
        dates = self.escape_latex(dates)
        organization = self.escape_latex(exp.get("organization", ""))
        location = self.escape_latex(exp.get("location", ""))
        bullets = exp.get("bullets", [])

        entry = f"    \\resumeSubheading\n      {{{title}}}{{{dates}}}\n      {{{organization}}}{{{location}}}\n"

        if bullets:
            entry += "      \\resumeItemListStart\n"
            for bullet in bullets:
                # Clean bullet: remove newlines and normalize whitespace
                clean_bullet = " ".join(bullet.split())
                # Escape FIRST, then bold with escaped keywords
                escaped_bullet = self.escape_latex(clean_bullet)
                bolded_bullet = self.bold_keywords_escaped(escaped_bullet, getattr(self, 'matched_keywords', set()))
                entry += f"        \\resumeItem{{{bolded_bullet}}}\n"
            entry += "      \\resumeItemListEnd\n"

        return entry

    def format_project_entry(self, proj: Dict) -> str:
        """Format a single project entry for LaTeX"""
        name = self.escape_latex(proj.get("name", ""))
        technologies = self.escape_latex(proj.get("technologies", ""))
        dates = self.normalize_dates(proj.get("dates", ""))
        dates = self.escape_latex(dates)
        bullets = proj.get("bullets", [])

        entry = f"      \\resumeProjectHeading\n          {{\\textbf{{{name}}} $|$ \\emph{{{technologies}}}}}{{{dates}}}\n"

        if bullets:
            entry += "          \\resumeItemListStart\n"
            for bullet in bullets:
                # Clean bullet: remove newlines and normalize whitespace
                clean_bullet = " ".join(bullet.split())
                # Escape FIRST, then bold with escaped keywords
                escaped_bullet = self.escape_latex(clean_bullet)
                bolded_bullet = self.bold_keywords_escaped(escaped_bullet, getattr(self, 'matched_keywords', set()))
                entry += f"            \\resumeItem{{{bolded_bullet}}}\n"
            entry += "          \\resumeItemListEnd\n"

        return entry

    def fill_template(
        self,
        profile_data: Dict,
        selected_experiences: Optional[List[Dict]] = None,
        selected_projects: Optional[List[Dict]] = None,
        prioritized_skills: Optional[Dict] = None,
        matched_keywords: Optional[List[str]] = None
    ) -> str:
        """Fill LaTeX template with user data"""

        # Store matched keywords for bolding
        self.matched_keywords = set([kw.lower().strip() for kw in (matched_keywords or [])])
        print(f"[BOLD] Matched keywords to bold: {self.matched_keywords}")
        print(f"[BOLD] Total keywords: {len(self.matched_keywords)}")

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

        # Bold matched keywords in skills
        def format_skill_list(skill_list):
            """Format and bold matched skills"""
            formatted_skills = []
            for skill in skill_list:
                escaped_skill = self.escape_latex(skill)
                # Check if this skill is a matched keyword (case-insensitive)
                if skill.lower().strip() in self.matched_keywords:
                    formatted_skills.append(f"\\textbf{{{escaped_skill}}}")
                    print(f"[BOLD] Bolding skill: {skill}")
                else:
                    formatted_skills.append(escaped_skill)
            return ", ".join(formatted_skills)

        languages = format_skill_list(skills.get("languages", []))
        frameworks = format_skill_list(skills.get("frameworks", []))
        developer_tools = format_skill_list(skills.get("developer_tools", []))
        libraries = format_skill_list(skills.get("libraries", []))

        template = template.replace("{{LANGUAGES}}", languages)
        template = template.replace("{{FRAMEWORKS}}", frameworks)
        template = template.replace("{{DEVELOPER_TOOLS}}", developer_tools)
        template = template.replace("{{LIBRARIES}}", libraries)

        return template

    @staticmethod
    def count_pdf_pages(pdf_path: str) -> int:
        """
        Count pages in a PDF file using pdfinfo

        Args:
            pdf_path: Path to PDF file

        Returns:
            Number of pages, or 0 if error
        """
        try:
            result = subprocess.run(
                ['pdfinfo', pdf_path],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                # Parse output for "Pages: N"
                for line in result.stdout.split('\n'):
                    if line.startswith('Pages:'):
                        return int(line.split(':')[1].strip())

            return 0
        except Exception as e:
            print(f"Error counting PDF pages: {e}")
            return 0

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
                for i in range(2):
                    print(f"Running pdflatex (pass {i+1}/2)...")
                    result = subprocess.run(
                        ['pdflatex', '-interaction=nonstopmode', f'{output_filename}.tex'],
                        cwd=temp_path,
                        capture_output=True,
                        text=True,
                        timeout=120  # Increased from 30s to 120s for package installation
                    )

                    if result.returncode != 0:
                        print(f"LaTeX compilation error (pass {i+1}):")
                        print(f"Return code: {result.returncode}")
                        print(f"STDOUT: {result.stdout[-1000:]}")  # Last 1000 chars
                        print(f"STDERR: {result.stderr[-500:]}")  # Last 500 chars
                        # Don't return on first pass - second pass might succeed
                        if i == 1:  # Only fail after second pass
                            # Save failed LaTeX file for debugging
                            debug_path = self.OUTPUT_DIR / f"FAILED_{output_filename}.tex"
                            try:
                                shutil.copy(tex_file, debug_path)
                                print(f"Saved failed LaTeX to: {debug_path}")
                            except Exception as e:
                                print(f"Could not save debug file: {e}")
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
