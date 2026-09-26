"""
Resume Parser Module
Project ID: P19 - Skill-Gap Predictor for Students (Career Navigation AI)
GITAM University, Bengaluru Campus
Developers: Vinay Kumar S, Yashwanth K, Mahesh B K
Mentor: Dr. N. Gayathri (M29)

Handles robust text & hyperlink extraction from PDF and DOCX files,
section segmentation, contact information extraction, structure analysis, and resume validation.
"""

import io
import re
from typing import Dict, Any, List, Tuple

# Try imports with graceful fallbacks
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import docx
except ImportError:
    docx = None

INVALID_PROFILE_WORDS = {
    "summary", "objective", "education", "experience", "projects", "skills",
    "certifications", "contact", "about", "home", "profile", "resume", "pdf",
    "doc", "docx", "mailto", "email", "phone", "user", "username", "example",
    "yourname", "name", "null", "undefined", "none", "test", "view", "download",
    "index", "main", "master", "blob", "raw", "tree", "commit", "releases",
    "github", "linkedin", "http", "https", "www", "in", "pub"
}


def is_valid_profile_link(url: str, platform: str) -> bool:
    """Strictly validate whether extracted link is a genuine student profile handle."""
    if not url:
        return False
    clean = url.split("?")[0].split("#")[0].rstrip("/")
    parts = [p.lower().strip() for p in clean.split("/") if p.strip()]
    if not parts:
        return False
    handle = parts[-1]
    if handle in INVALID_PROFILE_WORDS:
        return False
    if len(handle) < 3:
        return False
    if handle.isdigit():
        return False
    return True


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract raw text and embedded hyperlink URIs from PDF bytes."""
    text_chunks = []
    hyperlinks = []

    # Method 1: pdfplumber
    if pdfplumber is not None:
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_chunks.append(page_text)
                    if hasattr(page, "hyperlinks") and page.hyperlinks:
                        for link in page.hyperlinks:
                            if isinstance(link, dict) and "uri" in link:
                                hyperlinks.append(link["uri"])
        except Exception:
            text_chunks = []

    # Method 2: pypdf fallback + annotation extraction
    if pypdf is not None:
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            for page in reader.pages:
                if not text_chunks:
                    page_text = page.extract_text()
                    if page_text:
                        text_chunks.append(page_text)
                if "/Annots" in page:
                    try:
                        for annot in page["/Annots"]:
                            obj = annot.get_object()
                            if obj.get("/Subtype") == "/Link" and "/A" in obj:
                                action = obj["/A"].get_object()
                                if action.get("/S") == "/URI" and "/URI" in action:
                                    hyperlinks.append(str(action["/URI"]))
                    except Exception:
                        pass
        except Exception:
            pass

    combined_text = "\n".join(text_chunks)
    if hyperlinks:
        unique_links = list(set(hyperlinks))
        combined_text += "\n" + "\n".join(unique_links)

    return combined_text.strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text and embedded hyperlink URIs from Word (.docx) document bytes."""
    if docx is None:
        return ""
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]

        hyperlinks = []
        try:
            for rel in doc.part.rels.values():
                if "hyperlink" in rel.reltype and hasattr(rel, "target_ref"):
                    hyperlinks.append(rel.target_ref)
        except Exception:
            pass

        full_text = "\n".join(paragraphs)
        if hyperlinks:
            full_text += "\n" + "\n".join(set(hyperlinks))
        return full_text
    except Exception:
        return ""


def extract_contact_info(text: str) -> Dict[str, Any]:
    """Extract email, phone number, LinkedIn, and GitHub links from resume text with strict validation."""
    cleaned_text = re.sub(
        r"(linkedin|github)\s*\.\s*com\s*/\s*(in\s*/)?",
        r"\1.com/\2",
        text,
        flags=re.IGNORECASE,
    )

    # Email regex pattern
    email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", cleaned_text)
    email = email_match.group(0) if email_match else ""

    # Phone regex pattern
    phone_match = re.search(
        r"(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}", cleaned_text
    )
    phone = phone_match.group(0).strip() if phone_match else ""

    # LinkedIn profile regex with strict validation
    linkedin = ""
    linkedin_matches = re.findall(
        r"(https?://)?([a-z0-9-]+\.)?linkedin\.com/(in|profile|pub)/[a-zA-Z0-9%_.-]+",
        cleaned_text,
        re.IGNORECASE,
    )
    for m in re.finditer(r"(https?://)?([a-z0-9-]+\.)?linkedin\.com/(in|profile|pub)/[a-zA-Z0-9%_.-]+", cleaned_text, re.IGNORECASE):
        candidate = m.group(0).rstrip(".")
        if is_valid_profile_link(candidate, "linkedin"):
            linkedin = candidate
            break

    if not linkedin:
        li_fallback = re.search(r"linkedin\.com/in/[a-zA-Z0-9%_.-]+", text, re.IGNORECASE)
        if li_fallback:
            candidate = li_fallback.group(0).rstrip(".")
            if is_valid_profile_link(candidate, "linkedin"):
                linkedin = candidate

    # GitHub profile regex with strict validation
    github = ""
    for m in re.finditer(r"(https?://)?([a-z0-9-]+\.)?github\.com/[a-zA-Z0-9%_.-]+", cleaned_text, re.IGNORECASE):
        candidate = m.group(0).rstrip(".")
        if is_valid_profile_link(candidate, "github"):
            github = candidate
            break

    if not github:
        gh_fallback = re.search(r"github\.com/[a-zA-Z0-9%_.-]+", text, re.IGNORECASE)
        if gh_fallback:
            candidate = gh_fallback.group(0).rstrip(".")
            if is_valid_profile_link(candidate, "github"):
                github = candidate

    # Candidate name estimation
    lines = [line.strip() for line in cleaned_text.split("\n") if line.strip()]
    estimated_name = ""
    for line in lines[:5]:
        if len(line.split()) in [2, 3, 4] and not any(
            char in line for char in ["@", "http", ".com", "+", "1", "2", "3"]
        ):
            estimated_name = line
            break

    return {
        "name": estimated_name or "Student Applicant",
        "email": email,
        "phone": phone,
        "linkedin": linkedin if is_valid_profile_link(linkedin, "linkedin") else "",
        "github": github if is_valid_profile_link(github, "github") else "",
    }


def segment_resume_sections(text: str) -> Dict[str, str]:
    """Detect and segment standard resume sections."""
    section_patterns = {
        "education": r"(education|academic background|qualifications|academic credentials|academics)",
        "skills": r"(skills|technical skills|key competencies|core competencies|technologies|proficiencies|tools)",
        "experience": r"(work experience|experience|internships|employment history|work history|professional experience)",
        "projects": r"(projects|academic projects|key projects|personal projects|capstone|mini projects)",
        "certifications": r"(certifications|certificates|licenses|achievements|honors|awards)",
    }

    section_buffer: Dict[str, List[str]] = {"general": []}
    lines = text.split("\n")
    current_section = "general"

    for line in lines:
        cleaned_line = line.strip().lower()
        matched_section_name = None

        if len(cleaned_line) < 40:
            for sec_name, pattern in section_patterns.items():
                if re.fullmatch(r"[:\s\-*#]*" + pattern + r"[:\s\-*#]*", cleaned_line):
                    matched_section_name = sec_name
                    break

        if matched_section_name:
            current_section = matched_section_name
            if current_section not in section_buffer:
                section_buffer[current_section] = []
        else:
            if current_section not in section_buffer:
                section_buffer[current_section] = []
            section_buffer[current_section].append(line)

    return {sec: "\n".join(lines).strip() for sec, lines in section_buffer.items()}


def parse_resume(input_data: Any, file_name: str = "") -> Dict[str, Any]:
    """Parse resume document bytes, file path, or file-like object and return structured representation."""
    import os
    from pathlib import Path

    if isinstance(input_data, (str, Path)):
        p = Path(input_data)
        if p.exists() and p.is_file():
            if not file_name:
                file_name = p.name
            with open(p, "rb") as f:
                file_bytes = f.read()
        else:
            file_bytes = str(input_data).encode("utf-8")
            if not file_name:
                file_name = "resume.txt"
    elif isinstance(input_data, bytes):
        file_bytes = input_data
        if not file_name:
            file_name = "resume.pdf"
    elif hasattr(input_data, "read"):
        file_bytes = input_data.read()
        if not file_name:
            file_name = getattr(input_data, "name", "resume.pdf")
    else:
        file_bytes = b""
        if not file_name:
            file_name = "resume.txt"

    file_name = os.path.basename(str(file_name))
    ext = file_name.split(".")[-1].lower() if "." in file_name else ""

    if ext == "pdf":
        raw_text = extract_text_from_pdf(file_bytes)
    elif ext in ["docx", "doc"]:
        raw_text = extract_text_from_docx(file_bytes)
    else:
        raw_text = file_bytes.decode("utf-8", errors="ignore")

    contact_info = extract_contact_info(raw_text)
    sections = segment_resume_sections(raw_text)
    word_count = len(raw_text.split())

    section_presence = {
        "Education": bool(sections.get("education", "").strip()),
        "Technical Skills": bool(sections.get("skills", "").strip()),
        "Projects": bool(sections.get("projects", "").strip()),
        "Experience / Internships": bool(sections.get("experience", "").strip()),
        "Certifications": bool(sections.get("certifications", "").strip()),
    }

    return {
        "file_name": file_name,
        "word_count": word_count,
        "raw_text": raw_text,
        "contact_info": contact_info,
        "sections": sections,
        "section_presence": section_presence,
    }


def validate_is_resume(parsed_data: Dict[str, Any], extracted_skills: List[str]) -> Tuple[bool, str]:
    """Strictly validate whether uploaded document is a genuine resume."""
    word_count = parsed_data.get("word_count", 0)
    section_presence = parsed_data.get("section_presence", {})

    if word_count < 80:
        return False, "Document too short (less than 80 words). Please upload a complete resume."

    critical_sections = ["Education", "Technical Skills", "Projects", "Experience / Internships"]
    found_critical = sum(1 for sec in critical_sections if section_presence.get(sec, False))

    if found_critical < 1 and len(extracted_skills) < 2:
        return False, "Could not identify standard resume sections (Education, Technical Skills, Projects, or Work Experience)."

    return True, "Valid Resume"
