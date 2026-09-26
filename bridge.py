"""
Python Helper Bridge for Skill-Gap Predictor PHP Application
Project ID: P19 - Skill-Gap Predictor for Students (Career Navigation AI)
IEEE CS Bangalore Chapter | GITAM University, Bengaluru
"""

import sys
import os
import json
import base64
import traceback

# Ensure modules directory is in path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULES_DIR = os.path.join(BASE_DIR, "modules")

if MODULES_DIR not in sys.path:
    sys.path.insert(0, MODULES_DIR)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


from modules.resume_parser import parse_resume, validate_is_resume

from modules.skill_extractor import (
    extract_skills_from_text,
    detect_candidate_domain,
    get_all_canonical_skills,
)

from modules.ats_engine import (
    calculate_ats_score,
    calculate_readiness_score,
    evaluate_resume_strength,
    calculate_ai_confidence,
    generate_ai_insights,
)

from modules.job_scraper import (
    fetch_job_description_from_url,
    get_all_benchmark_roles,
    rank_jobs_for_candidate,
)

from modules.roadmap_generator import generate_learning_roadmap

from modules.interview_prep import (
    generate_interview_prep,
    ask_ai_interview_assistant,
    evaluate_user_answer,
)

from modules.pdf_generator import generate_pdf_report


# ============================================================
# COMMON ERROR RESPONSE
# ============================================================

def error_response(message, exception=None):
    """
    Always return valid JSON-compatible error data.
    This makes debugging PHP <-> Python failures much easier.
    """

    result = {
        "status": "error",
        "message": str(message),
    }

    if exception is not None:
        result["error_type"] = type(exception).__name__
        result["error_details"] = str(exception)

        # Keep traceback available for server-side debugging.
        result["traceback"] = traceback.format_exc()

    return result


# ============================================================
# CANONICAL SKILLS
# ============================================================

def handle_get_canonical_skills():
    try:
        return {
            "status": "success",
            "skills": get_all_canonical_skills()
        }

    except Exception as e:
        return error_response(
            "Unable to load canonical skills.",
            e
        )


# ============================================================
# BENCHMARK DATA
# ============================================================

def handle_get_benchmark_data():
    try:
        json_path = os.path.join(
            BASE_DIR,
            "data",
            "company_roles.json"
        )

        if not os.path.exists(json_path):
            return {
                "status": "error",
                "message": "Benchmark data file not found."
            }

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return {
            "status": "success",
            "companies": data.get("companies", {})
        }

    except Exception as e:
        return error_response(
            "Unable to load benchmark data.",
            e
        )


# ============================================================
# RESUME PARSING
# ============================================================

def handle_parse_resume(payload):
    """
    Parse an uploaded resume.

    PHP sends:
        {
            "file_path": "...",
            "file_name": "resume.pdf"
        }

    The parser receives the actual file bytes.
    """

    try:
        file_path = payload.get("file_path")
        file_name = payload.get("file_name", "resume.pdf")

        # ----------------------------------------------------
        # Validate file path
        # ----------------------------------------------------

        if not file_path:
            return {
                "status": "error",
                "message": "Resume file path was not provided."
            }

        file_path = os.path.abspath(str(file_path))

        if not os.path.exists(file_path):
            return {
                "status": "error",
                "message": "Uploaded resume file does not exist on the server.",
                "file_path": file_path
            }

        if not os.path.isfile(file_path):
            return {
                "status": "error",
                "message": "Uploaded resume path is not a valid file."
            }

        # ----------------------------------------------------
        # Check file size
        # ----------------------------------------------------

        file_size = os.path.getsize(file_path)

        if file_size <= 0:
            return {
                "status": "error",
                "message": "The uploaded resume file is empty."
            }

        # Prevent accidental extremely large files
        max_size = 15 * 1024 * 1024

        if file_size > max_size:
            return {
                "status": "error",
                "message": "Resume file is too large. Maximum allowed size is 15 MB."
            }

        # ----------------------------------------------------
        # Read file
        # ----------------------------------------------------

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        if not file_bytes:
            return {
                "status": "error",
                "message": "Unable to read the uploaded resume."
            }

        # ----------------------------------------------------
        # Normalize filename
        # ----------------------------------------------------

        file_name = os.path.basename(str(file_name))

        extension = os.path.splitext(file_name)[1].lower()

        supported_extensions = {
            ".pdf",
            ".doc",
            ".docx",
            ".txt"
        }

        if extension not in supported_extensions:
            return {
                "status": "error",
                "message": (
                    "Unsupported resume format. "
                    "Please upload a PDF, DOC, DOCX, or TXT file."
                )
            }

        # ----------------------------------------------------
        # Parse resume
        # ----------------------------------------------------

        parsed = parse_resume(
            file_bytes,
            file_name
        )

        # Parser must return a dictionary
        if parsed is None:
            return {
                "status": "error",
                "message": "Resume parser returned no data."
            }

        if not isinstance(parsed, dict):
            return {
                "status": "error",
                "message": (
                    "Resume parser returned an invalid response. "
                    "Expected a dictionary."
                ),
                "parser_result_type": type(parsed).__name__
            }

        # ----------------------------------------------------
        # Get raw resume text
        # ----------------------------------------------------

        raw_text = parsed.get("raw_text", "")

        if raw_text is None:
            raw_text = ""

        raw_text = str(raw_text)

        # Some parsers may use "text" instead of "raw_text"
        if not raw_text.strip():
            alternative_text = parsed.get("text", "")

            if alternative_text:
                raw_text = str(alternative_text)

        # ----------------------------------------------------
        # Make sure text was extracted
        # ----------------------------------------------------

        if not raw_text.strip():
            return {
                "status": "error",
                "message": (
                    "The resume was uploaded successfully, "
                    "but no readable text could be extracted from it. "
                    "If this is a scanned/image-based PDF, please upload "
                    "a text-based PDF or DOCX resume."
                ),
                "parsed_resume": parsed
            }

        # ----------------------------------------------------
        # Extract skills
        # ----------------------------------------------------

        extracted_skills = extract_skills_from_text(
            raw_text
        )

        if extracted_skills is None:
            extracted_skills = []

        if not isinstance(extracted_skills, list):
            try:
                extracted_skills = list(extracted_skills)
            except Exception:
                extracted_skills = []

        # ----------------------------------------------------
        # Validate resume
        # ----------------------------------------------------

        validation_result = validate_is_resume(
            parsed,
            extracted_skills
        )

        # Support both:
        #     (True, "message")
        # and
        #     True
        # styles of validation functions.

        if isinstance(validation_result, tuple):
            is_valid = validation_result[0]

            if len(validation_result) > 1:
                validation_msg = validation_result[1]
            else:
                validation_msg = ""
        else:
            is_valid = bool(validation_result)
            validation_msg = ""

        if not is_valid:
            return {
                "status": "error",
                "message": (
                    str(validation_msg)
                    if validation_msg
                    else "The uploaded file does not appear to be a valid resume."
                ),
                "parsed_resume": parsed,
                "extracted_skills": extracted_skills
            }

        # ----------------------------------------------------
        # ATS score
        # ----------------------------------------------------

        ats_result = calculate_ats_score(
            parsed,
            extracted_skills
        )

        # Expected:
        #     ats_score, breakdown

        if isinstance(ats_result, tuple):
            if len(ats_result) >= 2:
                ats_score = ats_result[0]
                breakdown = ats_result[1]
            elif len(ats_result) == 1:
                ats_score = ats_result[0]
                breakdown = {}
            else:
                ats_score = 0
                breakdown = {}
        else:
            ats_score = ats_result
            breakdown = {}

        # ----------------------------------------------------
        # Candidate domain
        # ----------------------------------------------------

        domain_result = detect_candidate_domain(
            extracted_skills
        )

        if isinstance(domain_result, tuple):
            if len(domain_result) >= 2:
                detected_domain = domain_result[0]
                domain_percentages = domain_result[1]
            elif len(domain_result) == 1:
                detected_domain = domain_result[0]
                domain_percentages = {}
            else:
                detected_domain = "Unknown"
                domain_percentages = {}
        else:
            detected_domain = domain_result
            domain_percentages = {}

        # ----------------------------------------------------
        # Final response
        # ----------------------------------------------------

        return {
            "status": "success",

            "parsed_resume": parsed,

            "extracted_skills": extracted_skills,

            "ats_score": float(ats_score),

            "ats_breakdown": breakdown,

            "detected_domain": detected_domain,

            "domain_percentages": domain_percentages,

            "file_name": file_name,

            "file_size": file_size,

            "text_length": len(raw_text)
        }

    except Exception as e:

        return error_response(
            "Resume parsing failed.",
            e
        )


# ============================================================
# SAMPLE RESUME
# ============================================================

def handle_parse_sample(payload):

    try:

        user_name = payload.get(
            "name",
            "Student Applicant"
        )

        email = payload.get(
            "email",
            "student@gitam.in"
        )

        branch = payload.get(
            "branch",
            "Computer Science & Engineering"
        )

        year = payload.get(
            "year",
            2026
        )

        sample_text = f"""
        {user_name}
        GITAM University, Bengaluru | {email} | +91 9876543210
        LinkedIn: linkedin.com/in/{user_name.lower().replace(' ', '')}
        GitHub: github.com/{user_name.lower().replace(' ', '')}

        EDUCATION

        GITAM University, Bengaluru
        {branch} ({year})
        CGPA: 8.8 / 10.0

        TECHNICAL SKILLS

        Programming:
        Python, Java, C++, SQL, JavaScript

        Core:
        Data Structures, Algorithms,
        Object-Oriented Programming (OOP),
        DBMS, System Design

        Libraries:
        Pandas, NumPy, Scikit-Learn

        Tools:
        Git, GitHub, Docker, VS Code, Linux

        PROJECTS

        Skill-Gap Predictor for Students
        Career Navigation AI

        - Built an AI career navigation platform using PHP,
          HTML/CSS/JS, Python NLP, BeautifulSoup and ReportLab.

        - Implemented automated ATS resume screening
          and dynamic job ranking.

        EXPERIENCE / INTERNSHIPS

        Software Engineering Intern
        Summer 2025

        - Developed backend REST APIs in Python
          and improved query performance.

        CERTIFICATIONS

        - AWS Certified Cloud Practitioner
        """

        file_name = (
            f"{user_name.replace(' ', '_')}_Sample_Resume.pdf"
        )

        parsed = parse_resume(
            sample_text.encode("utf-8"),
            file_name
        )

        extracted_skills = extract_skills_from_text(
            sample_text
        )

        ats_score, breakdown = calculate_ats_score(
            parsed,
            extracted_skills
        )

        detected_domain, domain_percentages = (
            detect_candidate_domain(
                extracted_skills
            )
        )

        return {
            "status": "success",
            "parsed_resume": parsed,
            "extracted_skills": extracted_skills,
            "ats_score": ats_score,
            "ats_breakdown": breakdown,
            "detected_domain": detected_domain,
            "domain_percentages": domain_percentages
        }

    except Exception as e:

        return error_response(
            "Sample resume parsing failed.",
            e
        )


# ============================================================
# METRICS
# ============================================================

def handle_calculate_metrics(payload):

    try:

        extracted_skills = payload.get(
            "extracted_skills",
            []
        )

        required_skills = payload.get(
            "required_skills",
            []
        )

        ats_score = float(
            payload.get(
                "ats_score",
                70.0
            )
        )

        target_company = payload.get(
            "target_company",
            "Not specified"
        )

        target_role = payload.get(
            "target_role",
            "Not specified"
        )

        readiness_pct, matched_skills, missing_skills = (
            calculate_readiness_score(
                extracted_skills,
                required_skills
            )
        )

        detected_domain, domain_percentages = (
            detect_candidate_domain(
                extracted_skills
            )
        )

        strength_label, strength_color, strength_msg = (
            evaluate_resume_strength(
                ats_score,
                readiness_pct
            )
        )

        confidence_pct = calculate_ai_confidence(
            ats_score,
            readiness_pct,
            len(extracted_skills)
        )

        ai_insights = generate_ai_insights(
            ats_score=ats_score,
            readiness_pct=readiness_pct,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            sections=payload.get(
                "section_presence",
                {}
            ),
            target_role=target_role,
            target_company=target_company
        )

        return {
            "status": "success",
            "readiness_pct": readiness_pct,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "detected_domain": detected_domain,
            "domain_percentages": domain_percentages,
            "strength_label": strength_label,
            "strength_color": strength_color,
            "strength_msg": strength_msg,
            "confidence_pct": confidence_pct,
            "ai_insights": ai_insights
        }

    except Exception as e:

        return error_response(
            "Unable to calculate resume metrics.",
            e
        )


# ============================================================
# JOB RANKING
# ============================================================

def handle_rank_jobs(payload):

    try:

        extracted_skills = payload.get(
            "extracted_skills",
            []
        )

        domain_filter = payload.get(
            "domain_filter",
            "All Domains"
        )

        ranked_jobs = rank_jobs_for_candidate(
            extracted_skills,
            domain_filter
        )

        return {
            "status": "success",
            "jobs": ranked_jobs
        }

    except Exception as e:

        return error_response(
            "Unable to rank jobs.",
            e
        )


# ============================================================
# URL SCRAPING
# ============================================================

def handle_scrape_url(payload):

    try:

        url = payload.get(
            "url",
            ""
        )

        if not url:
            return {
                "status": "error",
                "message": "Career URL was not provided."
            }

        return fetch_job_description_from_url(
            url
        )

    except Exception as e:

        return error_response(
            "Unable to scrape the career URL.",
            e
        )


# ============================================================
# ROADMAP
# ============================================================

def handle_generate_roadmap(payload):

    try:

        missing_skills = payload.get(
            "missing_skills",
            []
        )

        target_role = payload.get(
            "target_role",
            "Not specified"
        )

        target_company = payload.get(
            "target_company",
            "Not specified"
        )

        roadmap = generate_learning_roadmap(
            missing_skills,
            target_role,
            target_company
        )

        return {
            "status": "success",
            "roadmap": roadmap
        }

    except Exception as e:

        return error_response(
            "Unable to generate learning roadmap.",
            e
        )


# ============================================================
# INTERVIEW PREPARATION
# ============================================================

def handle_generate_interview(payload):

    try:

        target_role = payload.get(
            "target_role",
            "Not specified"
        )

        matched_skills = payload.get(
            "matched_skills",
            []
        )

        missing_skills = payload.get(
            "missing_skills",
            []
        )

        prep_data = generate_interview_prep(
            target_role,
            matched_skills,
            missing_skills
        )

        return {
            "status": "success",
            "prep_data": prep_data
        }

    except Exception as e:

        return error_response(
            "Unable to generate interview preparation.",
            e
        )


# ============================================================
# INTERVIEW AI
# ============================================================

def handle_ask_interview_ai(payload):

    try:

        prompt = payload.get(
            "prompt",
            ""
        )

        target_role = payload.get(
            "target_role",
            "Not specified"
        )

        target_company = payload.get(
            "target_company",
            "Not specified"
        )

        return ask_ai_interview_assistant(
            prompt,
            target_role,
            target_company
        )

    except Exception as e:

        return error_response(
            "Unable to process interview AI request.",
            e
        )


# ============================================================
# ANSWER EVALUATION
# ============================================================

def handle_evaluate_answer(payload):

    try:

        question = payload.get(
            "question",
            ""
        )

        user_answer = payload.get(
            "user_answer",
            ""
        )

        target_role = payload.get(
            "target_role",
            "Not specified"
        )

        return evaluate_user_answer(
            question,
            user_answer,
            target_role
        )

    except Exception as e:

        return error_response(
            "Unable to evaluate interview answer.",
            e
        )


# ============================================================
# PDF GENERATION
# ============================================================

def handle_generate_pdf(payload):

    try:

        student_name = payload.get(
            "student_name",
            "Student Applicant"
        )

        target_role = payload.get(
            "target_role",
            "Not specified"
        )

        target_company = payload.get(
            "target_company",
            "Not specified"
        )

        domain = payload.get(
            "domain",
            "Career Domain"
        )

        ats_score = float(
            payload.get(
                "ats_score",
                70.0
            )
        )

        readiness_score = float(
            payload.get(
                "readiness_score",
                65.0
            )
        )

        confidence_score = float(
            payload.get(
                "confidence_score",
                80.0
            )
        )

        resume_strength = payload.get(
            "resume_strength",
            "Strong"
        )

        matched_skills = payload.get(
            "matched_skills",
            []
        )

        missing_skills = payload.get(
            "missing_skills",
            []
        )

        recommendations = payload.get(
            "recommendations",
            [
                "Build a portfolio project targeting missing competencies."
            ]
        )

        roadmap_phases = payload.get(
            "roadmap_phases",
            []
        )

        pdf_bytes = generate_pdf_report(
            student_name=student_name,
            target_role=target_role,
            target_company=target_company,
            domain=domain,
            ats_score=ats_score,
            readiness_score=readiness_score,
            confidence_score=confidence_score,
            resume_strength=resume_strength,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            recommendations=recommendations,
            roadmap_phases=roadmap_phases
        )

        output_path = payload.get(
            "output_path"
        )

        if output_path:

            with open(
                output_path,
                "wb"
            ) as f:
                f.write(pdf_bytes)

            return {
                "status": "success",
                "output_path": output_path
            }

        return {
            "status": "success",
            "pdf_b64": base64.b64encode(
                pdf_bytes
            ).decode("utf-8")
        }

    except Exception as e:

        return error_response(
            "Unable to generate PDF report.",
            e
        )


# ============================================================
# MAIN
# ============================================================

def main():

    if len(sys.argv) < 2:

        print(
            json.dumps(
                {
                    "status": "error",
                    "message": "No action specified."
                }
            )
        )

        sys.exit(1)

    action = sys.argv[1]

    try:

        if not sys.stdin.isatty():
            raw_input = sys.stdin.read().strip()
        else:
            raw_input = "{}"

        payload = (
            json.loads(raw_input)
            if raw_input
            else {}
        )

    except Exception as e:

        print(
            json.dumps(
                error_response(
                    "Invalid JSON input received by Python bridge.",
                    e
                )
            )
        )

        sys.exit(1)

    try:

        if action == "get_canonical_skills":

            res = handle_get_canonical_skills()

        elif action == "get_benchmark_data":

            res = handle_get_benchmark_data()

        elif action == "parse_resume":

            res = handle_parse_resume(payload)

        elif action == "parse_sample":

            res = handle_parse_sample(payload)

        elif action == "calculate_metrics":

            res = handle_calculate_metrics(payload)

        elif action == "rank_jobs":

            res = handle_rank_jobs(payload)

        elif action == "scrape_url":

            res = handle_scrape_url(payload)

        elif action == "generate_roadmap":

            res = handle_generate_roadmap(payload)

        elif action == "generate_interview":

            res = handle_generate_interview(payload)

        elif action == "ask_interview_ai":

            res = handle_ask_interview_ai(payload)

        elif action == "evaluate_answer":

            res = handle_evaluate_answer(payload)

        elif action == "generate_pdf":

            res = handle_generate_pdf(payload)

        else:

            res = {
                "status": "error",
                "message": f"Unknown action: {action}"
            }

    except Exception as e:

        res = error_response(
            "Python bridge execution failed.",
            e
        )

    # --------------------------------------------------------
    # Guarantee valid JSON output to PHP
    # --------------------------------------------------------

    try:

        print(
            json.dumps(
                res,
                ensure_ascii=False,
                default=str
            )
        )

    except Exception as e:

        print(
            json.dumps(
                {
                    "status": "error",
                    "message": "Unable to serialize Python response.",
                    "error_details": str(e)
                }
            )
        )


if __name__ == "__main__":
    main()