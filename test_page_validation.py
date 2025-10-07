"""Test page validation and counting"""
from src.resume_agent.latex_service import LaTeXService
from pathlib import Path
import glob

# Find the most recent PDF in outputs folder
output_dir = Path("outputs")
pdf_files = list(output_dir.glob("*.pdf"))

if not pdf_files:
    print("No PDF files found in outputs folder")
    exit(1)

# Get most recent PDF
most_recent = max(pdf_files, key=lambda p: p.stat().st_mtime)
print(f"Testing with: {most_recent}")

# Test page counting
service = LaTeXService()
page_count = service.count_pdf_pages(str(most_recent))

print(f"\nPage count: {page_count}")

if page_count == 1:
    print("[OK] Resume is 1 page!")
elif page_count > 1:
    print(f"[WARNING] Resume is {page_count} pages - validation loop should trim content")
else:
    print("[ERROR] Could not count pages")
