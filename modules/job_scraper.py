"""
Job Scraper & Dynamic Job Ranking Module
Project ID: P19 - Skill-Gap Predictor for Students (Career Navigation AI)
GITAM University, Bengaluru Campus
Developers: Vinay Kumar S, Yashwanth K, Mahesh B K
Mentor: Dr. N. Gayathri (M29)

Implements Automatic Web Retrieval (AWR) using Requests & BeautifulSoup,
and ranks multi-role job opportunities dynamically based on student skills.
"""

import json
import os
import re
from typing import Dict, List, Any, Optional
import requests
from bs4 import BeautifulSoup

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "company_roles.json")


def fetch_job_description_from_url(url: str) -> Dict[str, Any]:
    """
    Automatic Web Retrieval (AWR):
    Fetches job description text and title from a live web URL using Requests and BeautifulSoup.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Strip scripts, styles, navigation, footer
        for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            element.decompose()

        # Extract title
        page_title = soup.title.string.strip() if soup.title else "Job Posting"

        # Attempt to grab main content containers
        main_content = soup.find("main") or soup.find("article") or soup.find("div", {"class": re.compile(r"job|desc|content|posting", re.I)})
        if main_content:
            text = main_content.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)

        # Clean text
        cleaned_text = re.sub(r"\n{2,}", "\n\n", text)

        return {
            "status": "success",
            "title": page_title,
            "text": cleaned_text[:10000],  # Limit length for performance
            "error": None
        }
    except Exception as e:
        return {
            "status": "error",
            "title": "Failed to Fetch",
            "text": "",
            "error": str(e)
        }


# Alias for backward and cross-module compatibility
scrape_career_url = fetch_job_description_from_url


def get_all_benchmark_roles() -> List[Dict[str, Any]]:
    """Load all companies and roles from company_roles.json into a flat list."""
    if not os.path.exists(DATA_FILE):
        return []

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    benchmark_list = []
    for company, comp_info in data.get("companies", {}).items():
        for role, role_info in comp_info.get("roles", {}).items():
            benchmark_list.append({
                "company": company,
                "tier": comp_info.get("tier", "IT Services"),
                "role": role,
                "domain": role_info.get("domain", "General"),
                "required_skills": role_info.get("required_skills", []),
                "nice_to_have": role_info.get("nice_to_have", []),
                "experience_level": role_info.get("experience_level", "Entry Level"),
                "interview_rounds": role_info.get("interview_rounds", []),
            })
    return benchmark_list


def rank_jobs_for_candidate(candidate_skills: List[str], filter_domain: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Dynamic Job Ranking Algorithm:
    Evaluates candidate skills across all benchmark roles and ranks them by match readiness.
    """
    all_roles = get_all_benchmark_roles()
    cand_norm = {s.strip().lower() for s in candidate_skills}

    ranked_results = []
    for item in all_roles:
        if filter_domain and filter_domain != "All Domains" and item["domain"] != filter_domain:
            continue

        req = item["required_skills"]
        if not req:
            continue

        matched = [r for r in req if r.strip().lower() in cand_norm or any(r.strip().lower() in c or c in r.strip().lower() for c in cand_norm)]
        missing = [r for r in req if r not in matched]

        match_pct = round((len(matched) / len(req)) * 100, 1)

        # Readiness classification
        if match_pct >= 75:
            fit_label = "High Fit"
            fit_color = "#10B981"
        elif match_pct >= 50:
            fit_label = "Moderate Fit"
            fit_color = "#F59E0B"
        else:
            fit_label = "Low Fit"
            fit_color = "#EF4444"

        ranked_results.append({
            "company": item["company"],
            "tier": item["tier"],
            "role": item["role"],
            "domain": item["domain"],
            "match_pct": match_pct,
            "matched_count": len(matched),
            "total_count": len(req),
            "matched_skills": matched,
            "missing_skills": missing,
            "fit_label": fit_label,
            "fit_color": fit_color,
            "experience_level": item["experience_level"],
            "interview_rounds": item["interview_rounds"],
        })

    # Sort descending by match percentage
    ranked_results.sort(key=lambda x: x["match_pct"], reverse=True)
    return ranked_results


def get_live_job_market_samples() -> List[Dict[str, Any]]:
    """Curated live job market opportunities for student career exploration."""
    return [
        {
            "id": 1,
            "company": "Google",
            "role": "Software Development Engineer - Campus 2026",
            "location": "Bengaluru, Karnataka",
            "type": "Full-time",
            "domain": "Software Engineering",
            "skills": ["Data Structures", "Algorithms", "Java", "Python", "Git"],
            "posted": "2 days ago",
            "url": "https://careers.google.com"
        },
        {
            "id": 2,
            "company": "Microsoft",
            "role": "Data Scientist - Azure AI Team",
            "location": "Hyderabad, Telangana",
            "type": "Full-time",
            "domain": "Data Science & Analytics",
            "skills": ["Python", "SQL", "Pandas", "Machine Learning", "Power BI"],
            "posted": "Just now",
            "url": "https://careers.microsoft.com"
        },
        {
            "id": 3,
            "company": "Amazon",
            "role": "Cloud Support Associate (AWS)",
            "location": "Bengaluru, Karnataka",
            "type": "Full-time",
            "domain": "Cloud & DevOps",
            "skills": ["AWS", "Linux", "Networking", "Python", "Bash Scripting"],
            "posted": "3 days ago",
            "url": "https://amazon.jobs"
        },
        {
            "id": 4,
            "company": "TCS",
            "role": "Digital Cadre - Full Stack Developer",
            "location": "Bengaluru / Pan-India",
            "type": "Full-time",
            "domain": "Web & Full Stack",
            "skills": ["React", "JavaScript", "Node.js", "SQL", "MongoDB"],
            "posted": "1 week ago",
            "url": "https://www.tcs.com/careers"
        },
        {
            "id": 5,
            "company": "Infosys",
            "role": "Cybersecurity Analyst - SOC Operations",
            "location": "Bengaluru / Pune",
            "type": "Full-time",
            "domain": "Cybersecurity & Networking",
            "skills": ["Network Security", "Ethical Hacking", "Linux", "SIEM", "Python"],
            "posted": "4 days ago",
            "url": "https://www.infosys.com/careers"
        }
    ]
