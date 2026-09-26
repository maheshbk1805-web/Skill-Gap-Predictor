"""
Skill-Gap Predictor & Career Navigator
Dynamic Placement Readiness & ATS Intelligence Engine

Run via: python -m streamlit run app.py
"""

import os
import sys
import json
import sqlite3
import hashlib
from datetime import datetime
import streamlit as st

# ----------------------------------------------------
# Directory & Path Configuration
# ----------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULES_DIR = os.path.join(BASE_DIR, "modules")
if MODULES_DIR not in sys.path:
    sys.path.insert(0, MODULES_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Import Core AI Engine Modules
from modules.resume_parser import parse_resume, validate_is_resume
from modules.skill_extractor import extract_skills_from_text, detect_candidate_domain, get_all_canonical_skills
from modules.ats_engine import (
    calculate_ats_score,
    calculate_readiness_score,
    evaluate_resume_strength,
    calculate_ai_confidence,
    generate_ai_insights,
)
from modules.roadmap_generator import generate_learning_roadmap
from modules.interview_prep import (
    generate_interview_prep,
    evaluate_user_answer,
    ask_ai_interview_assistant,
)
from modules.pdf_generator import generate_pdf_report
from modules.job_scraper import fetch_job_description_from_url

# ----------------------------------------------------
# Database Management (SQLite)
# ----------------------------------------------------
DB_PATH = os.path.join(BASE_DIR, "career_navigation.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            university TEXT,
            branch TEXT,
            year TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS student_targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER UNIQUE,
            target_company TEXT,
            target_role TEXT,
            target_url TEXT,
            target_skills_json TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id)
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS student_resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER UNIQUE,
            file_name TEXT,
            raw_text TEXT,
            word_count INTEGER,
            contact_json TEXT,
            skills_json TEXT,
            ats_score REAL,
            ats_breakdown_json TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id)
        );
    """)
    conn.commit()
    conn.close()

init_db()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def register_user(name, email, password, university, branch, year):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO students (name, email, password, university, branch, year) VALUES (?, ?, ?, ?, ?, ?)",
            (name.strip(), email.strip().lower(), hash_password(password), university.strip(), branch.strip(), year)
        )
        conn.commit()
        return True, "Registration successful! Please sign in."
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists."
    except Exception as e:
        return False, f"Registration error: {e}"
    finally:
        conn.close()

def authenticate_user(email, password):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, email, university, branch, year FROM students WHERE email = ? AND password = ?",
        (email.strip().lower(), hash_password(password))
    )
    user_row = cur.fetchone()
    conn.close()
    if user_row:
        return {
            "id": user_row[0],
            "name": user_row[1],
            "email": user_row[2],
            "university": user_row[3],
            "branch": user_row[4],
            "year": user_row[5],
        }
    return None

def save_user_target(student_id, target_company, target_role, target_url, target_skills):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO student_targets (student_id, target_company, target_role, target_url, target_skills_json, updated_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(student_id) DO UPDATE SET
            target_company = excluded.target_company,
            target_role = excluded.target_role,
            target_url = excluded.target_url,
            target_skills_json = excluded.target_skills_json,
            updated_at = CURRENT_TIMESTAMP
    """, (student_id, target_company.strip(), target_role.strip(), target_url.strip(), json.dumps(target_skills or [])))
    conn.commit()
    conn.close()

def load_user_target(student_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT target_company, target_role, target_url, target_skills_json FROM student_targets WHERE student_id = ?", (student_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            "target_company": row[0] or "",
            "target_role": row[1] or "",
            "target_url": row[2] or "",
            "target_skills": json.loads(row[3]) if row[3] else []
        }
    return None

def save_user_resume(student_id, file_name, raw_text, word_count, contact, skills, ats_score, breakdown):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO student_resumes (
            student_id, file_name, raw_text, word_count, contact_json, skills_json, ats_score, ats_breakdown_json, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(student_id) DO UPDATE SET
            file_name = excluded.file_name,
            raw_text = excluded.raw_text,
            word_count = excluded.word_count,
            contact_json = excluded.contact_json,
            skills_json = excluded.skills_json,
            ats_score = excluded.ats_score,
            ats_breakdown_json = excluded.ats_breakdown_json,
            updated_at = CURRENT_TIMESTAMP
    """, (
        student_id,
        file_name,
        raw_text,
        word_count,
        json.dumps(contact or {}),
        json.dumps(skills or []),
        ats_score,
        json.dumps(breakdown or {})
    ))
    conn.commit()
    conn.close()

def load_user_resume(student_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT file_name, raw_text, word_count, contact_json, skills_json, ats_score, ats_breakdown_json
        FROM student_resumes WHERE student_id = ?
    """, (student_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            "file_name": row[0],
            "raw_text": row[1],
            "word_count": row[2],
            "contact_info": json.loads(row[3]) if row[3] else {},
            "skills": json.loads(row[4]) if row[4] else [],
            "ats_score": row[5] or 0.0,
            "ats_breakdown": json.loads(row[6]) if row[6] else {}
        }
    return None

def delete_user_resume(student_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM student_resumes WHERE student_id = ?", (student_id,))
    conn.commit()
    conn.close()

# ----------------------------------------------------
# Comprehensive Self-Contained Learning Roadmap Catalog
# (No external link redirects - everything explained on page)
# ----------------------------------------------------
ROADMAP_KNOWLEDGE_BASE = {
    "Data Structures": {
        "summary": "Master fundamental memory layouts, pointers, tree traversal algorithms, and optimal asymptotic time-space complexities.",
        "theory": "Data structures organize data in memory for optimal retrieval. Key pillars include Linear structures (Arrays, Linked Lists, Stacks, Queues) and Hierarchical structures (Binary Trees, BSTs, Heaps, Trie, Graphs, Hash Tables).",
        "syllabus": [
            "Week 1: Arrays & Dynamic Arrays, amortized analysis, Two-Pointer technique, and Fast-Slow pointers.",
            "Week 2: Singly/Doubly Linked Lists, cycle detection, Stack & Monotonic Stack pattern, Priority Queues/Min-Heaps.",
            "Week 3: Trees: DFS/BFS Traversal, Binary Search Tree invariants, Lowest Common Ancestor (LCA).",
            "Week 4: Hash Table collision resolution, Tries for string prefix search, and Disjoint Set Union (Union-Find)."
        ],
        "project": "Build an In-Memory Key-Value Storage Engine featuring LRU Cache eviction and Trie-based auto-complete.",
        "interview_qa": [
            {"q": "How does an LRU Cache work in O(1) time?", "a": "Combine a Hash Map with a Doubly Linked List. The hash map provides O(1) key lookup pointing to nodes, while the doubly linked list maintains recency order with O(1) removals and prepends."},
            {"q": "What is the difference between Array and Linked List in cache locality?", "a": "Arrays store elements in contiguous memory chunks, triggering CPU L1/L2 cache line prefetching. Linked list nodes reside in random heap addresses, causing frequent cache misses."}
        ]
    },
    "Algorithms": {
        "summary": "Core algorithmic strategies: Divide and Conquer, Greedy algorithms, Dynamic Programming, and Graph Traversals.",
        "theory": "Algorithms provide optimal step-by-step procedures. Companies test efficiency, recursive state transition modeling, and edge cases.",
        "syllabus": [
            "Week 1: Binary Search variations on sorted arrays and monotonic solution spaces.",
            "Week 2: Graph Theory: Breadth-First Search (shortest path in unweighted graphs), DFS, Topological Sort (Kahn's algo).",
            "Week 3: Dijkstra's Algorithm for weighted shortest paths, Bellman-Ford, and Minimum Spanning Trees (Kruskal/Prim).",
            "Week 4: Dynamic Programming: 1D memoization, 2D grid DP (Knapsack, LCS, Edit Distance), and Bitmask DP."
        ],
        "project": "Graph Route Optimization & Ride-Sharing Dispatch Simulator using Dijkstra and Spatial Indexing.",
        "interview_qa": [
            {"q": "How to detect a cycle in a directed graph?", "a": "Use DFS with 3-state coloring (White=unvisited, Gray=in current recursion stack, Black=fully explored). A back-edge to a Gray node indicates a cycle."},
            {"q": "Explain 0/1 Knapsack state relation.", "a": "dp[i][w] = max(dp[i-1][w], val[i-1] + dp[i-1][w - wt[i-1]]). Can be optimized to 1D array iterating weights backwards."}
        ]
    },
    "System Design": {
        "summary": "Design resilient, distributed, high-throughput backend services handling millions of concurrent users.",
        "theory": "Distributed systems require understanding trade-offs: CAP Theorem, PACELC, horizontal vs vertical scaling, load balancers, caching layers, and database sharding.",
        "syllabus": [
            "Week 1: Vertical vs Horizontal scaling, L4/L7 Load Balancing, Consistent Hashing algorithms.",
            "Week 2: Caching strategies (Write-Through, Write-Back, Cache-Aside), Redis cluster architecture, and CDN edge caching.",
            "Week 3: Database scaling: Read replicas, Vertical/Horizontal Sharding, ACID vs BASE, and Eventual Consistency.",
            "Week 4: Message Queues (Kafka/RabbitMQ), Rate Limiting algorithms (Token Bucket, Leaky Bucket), and High Availability."
        ],
        "project": "Distributed URL Shortener & Analytics System with Redis caching, Kafka click logging, and PostgreSQL sharding.",
        "interview_qa": [
            {"q": "How does Consistent Hashing minimize data movement during server scale-out?", "a": "Consistent hashing maps servers and keys onto a virtual 360° hash ring. When a node is added or removed, only keys in its immediate neighboring sector move, reducing re-mapping to K/N keys."},
            {"q": "Compare Redis vs Memcached.", "a": "Redis is single-threaded event-driven supporting rich data structures (Hashes, Sets, Sorted Sets), persistence (RDB/AOF), and pub-sub. Memcached is multi-threaded purely for simple key-value memory caching."}
        ]
    },
    "Python": {
        "summary": "Modern Python programming: OOP, async I/O, generators, memory management, and writing production REST APIs.",
        "theory": "Python is an interpreted, dynamically typed language with automatic memory management via reference counting and cyclic garbage collector.",
        "syllabus": [
            "Week 1: Core syntax, list/dict comprehensions, *args/**kwargs, decorators, and context managers (`with` statement).",
            "Week 2: Advanced OOP, dunder magic methods (__iter__, __call__, __repr__), dataclasses, and typing annotations.",
            "Week 3: Concurrency: Threading vs Multiprocessing, the GIL (Global Interpreter Lock), and AsyncIO event loops.",
            "Week 4: Web frameworks: FastAPI/Flask, Pydantic validation, SQLAlchemy ORM, and PyTest unit testing."
        ],
        "project": "Asynchronous REST API Gateway with FastAPI, JWT Authentication, Redis rate-limiting, and PyTest suite.",
        "interview_qa": [
            {"q": "What is the Python GIL and how do you bypass it?", "a": "The Global Interpreter Lock ensures only one thread executes Python bytecode at a time to keep reference counts thread-safe. Bypass it using `multiprocessing` for CPU-bound tasks or `asyncio` for I/O-bound tasks."},
            {"q": "How do generators work in Python?", "a": "Generators use the `yield` keyword to yield values lazily one at a time, suspending function execution state and consuming O(1) memory regardless of sequence size."}
        ]
    },
    "Docker": {
        "summary": "Containerization fundamentals, multi-stage Dockerfiles, image optimization, volume mounts, and network orchestration.",
        "theory": "Docker packages applications and dependencies into standardized containers utilizing Linux cgroups (resource limits) and namespaces (isolation).",
        "syllabus": [
            "Week 1: Container vs Virtual Machine architectures, Linux namespaces & cgroups, Docker daemon CLI.",
            "Week 2: Writing multi-stage Dockerfiles, optimizing layer caching, using slim base images (Alpine/Distroless).",
            "Week 3: Managing persistent state with Named Volumes and Bind Mounts; configuring custom bridge networks.",
            "Week 4: Multi-service orchestration with Docker Compose: setting dependencies, health checks, and secrets."
        ],
        "project": "Multi-tier Docker Compose environment deploying a React frontend, Python API, and PostgreSQL database.",
        "interview_qa": [
            {"q": "What is the purpose of multi-stage Docker builds?", "a": "Multi-stage builds separate the build environment (compilers, build tools, dev dependencies) from the runtime environment, resulting in lightweight, secure production images without SDK bloat."},
            {"q": "Explain the difference between ADD and COPY in Dockerfile.", "a": "COPY simply copies files from local host to the container image. ADD has extra features like auto-extracting tar archives and fetching files from remote URLs; COPY is preferred for transparency."}
        ]
    },
    "Kubernetes": {
        "summary": "Container orchestration: Pods, Deployments, Services, ConfigMaps, Ingress, and self-healing cloud clusters.",
        "theory": "Kubernetes (K8s) automates deployment, scaling, and operational management of containerized applications across node clusters.",
        "syllabus": [
            "Week 1: Architecture: Control Plane (API Server, etcd, Scheduler, Controller Manager) vs Worker Nodes (Kubelet, Kube-proxy).",
            "Week 2: Workloads: Pods, ReplicaSets, Deployments, rolling update strategies, and rollback commands.",
            "Week 3: Networking: ClusterIP, NodePort, LoadBalancer Services, and Ingress Controllers.",
            "Week 4: Storage & Config: ConfigMaps, Secrets, PersistentVolumes (PV), PersistentVolumeClaims (PVC), and HPA auto-scaling."
        ],
        "project": "Zero-Downtime Microservice Deployment on Minikube with Ingress routing, Secret configs, and Horizontal Pod Autoscaler.",
        "interview_qa": [
            {"q": "What is the difference between a Deployment and a StatefulSet?", "a": "Deployments manage stateless pods with interchangeable identities and random pod names. StatefulSets manage stateful pods with persistent unique network identities and dedicated persistent volume attachments."},
            {"q": "How does Kubernetes perform health checks?", "a": "Via Liveness probes (detects if container crashed and needs restart), Readiness probes (detects if container is ready to accept traffic), and Startup probes (protects slow-starting apps)."}
        ]
    },
    "SQL": {
        "summary": "Relational database mastery: Complex JOINs, subqueries, indexing strategies, normalization, and ACID transactions.",
        "theory": "Structured Query Language manages relational schemas, enforcing referential integrity and transactional reliability via B-Trees.",
        "syllabus": [
            "Week 1: DDL/DML, INNER/LEFT/RIGHT/FULL JOINs, GROUP BY, HAVING, and set operations (UNION, INTERSECT).",
            "Week 2: Advanced Window Functions (ROW_NUMBER, RANK, DENSE_RANK, LEAD, LAG, PARTITION BY).",
            "Week 3: Indexing: B-Tree vs Hash indexes, composite indexes, query execution plans (EXPLAIN ANALYZE).",
            "Week 4: Database design: 1NF to 3NF Normalization, ACID transaction isolation levels, and row-level locking."
        ],
        "project": "High-Volume Financial Ledger Database with complex analytical window reporting queries and transaction locks.",
        "interview_qa": [
            {"q": "What is the difference between WHERE and HAVING?", "a": "WHERE filters rows before aggregation occurs and cannot use aggregate functions. HAVING filters aggregated grouped rows after GROUP BY execution."},
            {"q": "Explain the four ACID properties.", "a": "Atomicity (all or nothing), Consistency (preserves schema constraints), Isolation (concurrent transactions execute independently without dirty reads), Durability (committed data survives crashes)."}
        ]
    }
}

def get_skill_learning_content(skill_name: str, target_company: str, target_role: str):
    """Retrieve or dynamically generate detailed self-contained roadmap content for any skill."""
    if skill_name in ROADMAP_KNOWLEDGE_BASE:
        return ROADMAP_KNOWLEDGE_BASE[skill_name]
    
    # Dynamic fallback generator for custom/niche skills
    return {
        "summary": f"Comprehensive study syllabus and practical implementation blueprint to master {skill_name} for {target_role} hiring standards.",
        "theory": f"{skill_name} is a key operational requirement sought by {target_company} for {target_role}. Mastery requires grasping core primitives, architecture design, and real-world debugging.",
        "syllabus": [
            f"Week 1: Fundamentals — Syntax, runtime environment setup, and foundational principles of {skill_name}.",
            f"Week 2: Core Patterns — Design patterns, component integration, and standard libraries for {skill_name}.",
            f"Week 3: Advanced Implementation — Concurrency, performance profiling, error handling, and unit testing.",
            f"Week 4: Production Readiness — Security auditing, CI/CD integration, and architecture review."
        ],
        "project": f"Production-grade {skill_name} Implementation project featuring unit tests, CI automation, and full documentation.",
        "interview_qa": [
            {"q": f"What are the core advantages and architectural trade-offs of {skill_name}?", "a": f"{skill_name} provides specialized capabilities for {target_role}. Key trade-offs involve implementation complexity, resource overhead, and team learning curves."},
            {"q": f"How do you debug performance bottlenecks when using {skill_name} in production?", "a": f"Profile execution with runtime monitoring tools, inspect latency bottlenecks, optimize memory allocations, and review query/processing algorithms."}
        ]
    }

# ----------------------------------------------------
# Page Configuration & Styling
# ----------------------------------------------------
st.set_page_config(
    page_title="Skill-Gap Predictor & Career Navigator",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #3b82f6, #06b6d4, #10b981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 0.95rem;
        color: #94a3b8;
        margin-bottom: 1.2rem;
    }
    .skill-badge-matched {
        display: inline-block;
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid #10b981;
        border-radius: 6px;
        padding: 4px 10px;
        margin: 3px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .skill-badge-missing {
        display: inline-block;
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid #ef4444;
        border-radius: 6px;
        padding: 4px 10px;
        margin: 3px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .skill-badge-extracted {
        display: inline-block;
        background: rgba(59, 130, 246, 0.15);
        color: #60a5fa;
        border: 1px solid #3b82f6;
        border-radius: 6px;
        padding: 4px 10px;
        margin: 3px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .error-card-overlay {
        background: rgba(220, 38, 38, 0.12);
        border: 2px solid #ef4444;
        border-radius: 12px;
        padding: 22px;
        margin-bottom: 24px;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# Session State Initialization
# ----------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None

if "target_company" not in st.session_state:
    st.session_state.target_company = ""
if "target_role" not in st.session_state:
    st.session_state.target_role = ""
if "target_url" not in st.session_state:
    st.session_state.target_url = ""
if "target_skills" not in st.session_state:
    st.session_state.target_skills = []

if "resume_data" not in st.session_state:
    st.session_state.resume_data = None
if "extracted_skills" not in st.session_state:
    st.session_state.extracted_skills = []
if "ats_score" not in st.session_state:
    st.session_state.ats_score = None
if "ats_breakdown" not in st.session_state:
    st.session_state.ats_breakdown = {}

if "resume_invalid_error" not in st.session_state:
    st.session_state.resume_invalid_error = False
if "resume_error_message" not in st.session_state:
    st.session_state.resume_error_message = ""
if "show_edit_target" not in st.session_state:
    st.session_state.show_edit_target = False

# ----------------------------------------------------
# AUTHENTICATION SCREEN (SIGN IN / SIGN UP)
# ----------------------------------------------------
if not st.session_state.authenticated or not st.session_state.current_user:
    st.markdown('<p class="main-title">Skill-Gap Predictor & Career Navigator</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Sign in to configure your target company, upload your resume, and generate dynamic ATS readiness analytics.</p>', unsafe_allow_html=True)

    auth_tab_login, auth_tab_register = st.tabs(["🔐 Sign In", "📝 Create New Account"])

    with auth_tab_login:
        st.markdown("#### Enter your credentials")
        with st.form("form_login"):
            login_email = st.text_input("Email Address", placeholder="student@example.com")
            login_password = st.text_input("Password", type="password")
            submitted_login = st.form_submit_button("Sign In", type="primary")

            if submitted_login:
                if not login_email or not login_password:
                    st.error("Please enter both your email and password.")
                else:
                    user = authenticate_user(login_email, login_password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.current_user = user

                        # Load saved target company & role
                        target_info = load_user_target(user["id"])
                        if target_info:
                            st.session_state.target_company = target_info.get("target_company", "")
                            st.session_state.target_role = target_info.get("target_role", "")
                            st.session_state.target_url = target_info.get("target_url", "")
                            st.session_state.target_skills = target_info.get("target_skills", [])

                        # Load saved resume
                        saved_resume = load_user_resume(user["id"])
                        if saved_resume:
                            st.session_state.resume_data = saved_resume
                            st.session_state.extracted_skills = saved_resume.get("skills", [])
                            st.session_state.ats_score = saved_resume.get("ats_score", None)
                            st.session_state.ats_breakdown = saved_resume.get("ats_breakdown", {})
                        else:
                            st.session_state.resume_data = None
                            st.session_state.extracted_skills = []
                            st.session_state.ats_score = None
                            st.session_state.ats_breakdown = {}

                        st.success(f"Welcome, {user['name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid email or password. Please try again.")

    with auth_tab_register:
        st.markdown("#### Register a student account")
        with st.form("form_register"):
            reg_name = st.text_input("Full Name", placeholder="Your Name")
            reg_email = st.text_input("Email Address", placeholder="name@example.com")
            reg_password = st.text_input("Choose Password", type="password")
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                reg_uni = st.text_input("University / College", placeholder="e.g., University Campus")
                reg_branch = st.text_input("Branch / Specialization", placeholder="e.g., Computer Science")
            with col_r2:
                reg_year = st.selectbox("Academic Year", ["1st Year", "2nd Year", "3rd Year", "4th Year / Final Year"])

            submitted_reg = st.form_submit_button("Create Account", type="primary")

            if submitted_reg:
                if not reg_name or not reg_email or not reg_password:
                    st.error("Please provide your name, email, and password.")
                elif len(reg_password) < 4:
                    st.error("Password must be at least 4 characters long.")
                else:
                    ok, msg = register_user(reg_name, reg_email, reg_password, reg_uni, reg_branch, reg_year)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

    st.stop()

# ----------------------------------------------------
# MAIN DASHBOARD (FOR AUTHENTICATED USER)
# ----------------------------------------------------
user = st.session_state.current_user
if not user:
    st.stop()

# Helper flags
has_target = bool(st.session_state.target_company.strip() and st.session_state.target_role.strip())
has_resume = bool(st.session_state.resume_data is not None and len(st.session_state.extracted_skills) > 0)

# Sidebar
with st.sidebar:
    st.markdown("### 🎯 Career Navigator")
    st.markdown(f"👤 **{user['name']}**")
    st.caption(f"📧 {user['email']}\n\n🏫 {user.get('university') or 'Student'} | {user.get('branch') or ''}")

    if st.button("🚪 Sign Out", type="secondary", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.session_state.target_company = ""
        st.session_state.target_role = ""
        st.session_state.target_url = ""
        st.session_state.target_skills = []
        st.session_state.resume_data = None
        st.session_state.extracted_skills = []
        st.session_state.ats_score = None
        st.session_state.ats_breakdown = {}
        st.session_state.resume_invalid_error = False
        st.rerun()

    st.divider()

    # Sidebar Target Status & Change Button
    if has_target:
        st.markdown("#### 🎯 Active Target")
        st.write(f"🏢 **{st.session_state.target_company}**")
        st.write(f"💼 **{st.session_state.target_role}**")
        if st.session_state.target_url:
            st.caption(f"🔗 {st.session_state.target_url[:35]}...")

        if st.button("✏️ Change Company / Role", type="secondary", use_container_width=True):
            st.session_state.show_edit_target = True
            st.rerun()
        st.divider()

    menu = st.radio(
        "Navigation",
        [
            "🏢 1. Target Company Setup",
            "📄 2. Resume Parser & ATS",
            "📊 3. Placement Dashboard",
            "🎯 4. Skill-Gap Predictor",
            "🗺️ 5. Personalized Learning Roadmap",
            "🎙️ 6. AI Interview Prep",
            "📑 7. Export Progress Report"
        ]
    )

# Dynamic calculations based on target skills and resume skills
required_skills = st.session_state.target_skills if st.session_state.target_skills else ["Problem Solving", "Data Structures", "Algorithms", "Git", "Python"]

if has_resume:
    readiness_pct, matched_skills, missing_skills = calculate_readiness_score(
        st.session_state.extracted_skills,
        required_skills
    )
    current_ats = float(st.session_state.ats_score) if st.session_state.ats_score is not None else 0.0
else:
    readiness_pct = 0.0
    matched_skills = []
    missing_skills = list(required_skills)
    current_ats = 0.0

# ----------------------------------------------------
# POPUP DIALOG MODAL FOR INVALID RESUME (WITH X BUTTON)
# ----------------------------------------------------
if hasattr(st, "dialog"):
    @st.dialog("❌ Invalid Document Detected")
    def show_invalid_resume_popup(error_msg=""):
        st.error("### You have not uploaded a valid resume.")
        st.markdown(
            "The uploaded file does not appear to be a genuine resume document. "
            "A valid resume must contain standard sections (such as Education, Technical Skills, Projects, or Work Experience) and readable text.\n\n"
            "👉 **Please re-upload a genuine resume in PDF, DOCX, or TXT format.**"
        )
        if error_msg:
            st.caption(f"Verification detail: {error_msg}")
        if st.button("✕ Dismiss & Re-Upload Resume", type="primary", use_container_width=True, key="btn_popup_dismiss"):
            st.session_state.resume_invalid_error = False
            st.session_state.resume_error_message = ""
            st.rerun()
else:
    def show_invalid_resume_popup(error_msg=""):
        st.error(f"❌ You have not uploaded a valid resume. {error_msg}")

if st.session_state.get("resume_invalid_error", False):
    show_invalid_resume_popup(st.session_state.get("resume_error_message", ""))

# Header
st.markdown('<p class="main-title">Skill-Gap Predictor & Career Navigator</p>', unsafe_allow_html=True)
if has_target:
    st.markdown(
        f'<p class="sub-title">Targeting: <b>{st.session_state.target_role}</b> at <b>{st.session_state.target_company}</b></p>',
        unsafe_allow_html=True
    )
else:
    st.markdown(
        '<p class="sub-title">Set your target company and role first to begin personalized resume evaluation.</p>',
        unsafe_allow_html=True
    )

# ====================================================
# TAB 1: TARGET COMPANY SETUP (DYNAMIC INPUT & LIVE URL)
# ====================================================
if menu == "🏢 1. Target Company Setup" or st.session_state.show_edit_target or not has_target:
    st.markdown("### 🏢 Step 1: Set Target Company & Job Opportunity")
    st.write("Specify the company you are targeting or applying for. You can enter any custom company, role, or paste a live career posting URL.")

    with st.form("form_target_company"):
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            inp_company = st.text_input(
                "Company Name *",
                value=st.session_state.target_company,
                placeholder="e.g., Google, Amazon, TCS, Infosys, Startup X"
            )
        with col_t2:
            inp_role = st.text_input(
                "Job Title / Target Role *",
                value=st.session_state.target_role,
                placeholder="e.g., Software Development Engineer, Frontend Developer, Data Analyst"
            )

        inp_url = st.text_input(
            "Company Career Page / Job Posting URL (Optional)",
            value=st.session_state.target_url,
            placeholder="https://careers.example.com/job/12345"
        )

        inp_job_desc = st.text_area(
            "Paste Job Description / Requirements (Optional — requirements will be extracted automatically)",
            placeholder="Paste the requirements or key skills from the job posting here...",
            height=120
        )

        submitted_target = st.form_submit_button("✅ Save Target & Continue to Resume Upload", type="primary")

        if submitted_target:
            if not inp_company.strip() or not inp_role.strip():
                st.error("Please provide both the Company Name and Job Title.")
            else:
                extracted_req_skills = []
                # If URL provided, attempt scraping
                if inp_url.strip():
                    with st.spinner("Retrieving job requirements from career URL..."):
                        scraped = fetch_job_description_from_url(inp_url.strip())
                        if scraped.get("status") == "success" and scraped.get("text"):
                            extracted_req_skills = extract_skills_from_text(scraped["text"])

                # If job description provided, extract skills
                if inp_job_desc.strip():
                    desc_skills = extract_skills_from_text(inp_job_desc.strip())
                    for s in desc_skills:
                        if s not in extracted_req_skills:
                            extracted_req_skills.append(s)

                # Fallback if no specific skills extracted
                if not extracted_req_skills:
                    extracted_req_skills = ["Data Structures", "Algorithms", "Python", "Git", "Problem Solving", "System Design"]

                st.session_state.target_company = inp_company.strip()
                st.session_state.target_role = inp_role.strip()
                st.session_state.target_url = inp_url.strip()
                st.session_state.target_skills = extracted_req_skills
                st.session_state.show_edit_target = False

                save_user_target(user["id"], inp_company.strip(), inp_role.strip(), inp_url.strip(), extracted_req_skills)
                st.success(f"Target set to **{inp_role.strip()}** at **{inp_company.strip()}**! Required skills identified: {len(extracted_req_skills)}")
                st.rerun()

    if has_target:
        st.markdown("---")
        st.markdown(f"#### Identified Key Requirements for **{st.session_state.target_role}** at **{st.session_state.target_company}**:")
        st.markdown("".join([f'<span class="skill-badge-extracted">{s}</span>' for s in st.session_state.target_skills]), unsafe_allow_html=True)

# ====================================================
# TAB 2: RESUME PARSER & ATS CHECKER
# ====================================================
elif menu == "📄 2. Resume Parser & ATS":
    st.markdown("### 📄 Step 2: Upload Resume for Evaluation")

    if not has_target:
        st.warning("⚠️ Please complete **Step 1: Target Company Setup** first before uploading your resume.")
        st.stop()

    st.write(f"Upload your resume to evaluate ATS compatibility against **{st.session_state.target_role}** at **{st.session_state.target_company}**.")

    uploaded_file = st.file_uploader(
        "Upload Resume Document (PDF, DOCX, TXT)",
        type=["pdf", "docx", "txt"],
        key="resume_uploader_main"
    )

    if uploaded_file is not None:
        if st.button("🚀 Analyze Uploaded Resume", type="primary"):
            with st.spinner("Validating document and extracting skills..."):
                file_bytes = uploaded_file.read()
                parsed = parse_resume(file_bytes, uploaded_file.name)
                raw_text = parsed.get("raw_text", "")
                word_count = parsed.get("word_count", 0)

                # Strict Resume Validation Check
                extracted_skills = extract_skills_from_text(raw_text)
                is_valid, validation_msg = validate_is_resume(parsed, extracted_skills)

                if not is_valid or word_count < 50:
                    st.session_state.resume_invalid_error = True
                    st.session_state.resume_error_message = validation_msg or "The uploaded document is not a genuine resume."
                    st.rerun()
                else:
                    st.session_state.resume_invalid_error = False
                    ats_score, breakdown = calculate_ats_score(parsed, extracted_skills)

                    st.session_state.resume_data = parsed
                    st.session_state.extracted_skills = extracted_skills
                    st.session_state.ats_score = ats_score
                    st.session_state.ats_breakdown = breakdown

                    save_user_resume(
                        user["id"],
                        uploaded_file.name,
                        raw_text,
                        word_count,
                        parsed.get("contact_info", {}),
                        extracted_skills,
                        ats_score,
                        breakdown
                    )

                    st.success(f"Resume '{uploaded_file.name}' verified and analyzed successfully!")
                    st.rerun()

    if not has_resume:
        st.info("👆 Please upload your resume above to calculate your real ATS score and match metrics.")
    else:
        st.markdown("---")
        res_info = st.session_state.resume_data
        contact = res_info.get("contact_info", {})

        col_top, col_del = st.columns([3, 1])
        with col_top:
            st.markdown(f"#### Active Resume: **{res_info.get('file_name', 'Uploaded Resume')}**")
        with col_del:
            if st.button("🗑️ Remove / Re-upload Resume", type="secondary"):
                delete_user_resume(user["id"])
                st.session_state.resume_data = None
                st.session_state.extracted_skills = []
                st.session_state.ats_score = None
                st.session_state.ats_breakdown = {}
                st.rerun()

        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            st.markdown(f"**Identified Name:** {contact.get('name') or user['name']}")
            st.markdown(f"**Email:** {contact.get('email') or user['email']}")
        with col_c2:
            st.markdown(f"**Phone:** {contact.get('phone') or 'Not identified'}")
            st.markdown(f"**Word Count:** {res_info.get('word_count', 0)} words")
        with col_c3:
            st.markdown(f"**LinkedIn:** {contact.get('linkedin') or 'Not identified'}")
            st.markdown(f"**GitHub:** {contact.get('github') or 'Not identified'}")

        st.divider()

        col_ats1, col_ats2 = st.columns([1, 2])
        with col_ats1:
            st.markdown("#### ATS Compatibility Score")
            st.metric("Overall Score", f"{current_ats:.0f} / 100")
            st.progress(float(current_ats / 100.0))

            strength_label, strength_color, strength_desc = evaluate_resume_strength(current_ats, readiness_pct)
            st.markdown(f"Strength Rating: **{strength_label}**")
            st.caption(strength_desc)

        with col_ats2:
            st.markdown("#### Extracted Technical Skills from Resume")
            if st.session_state.extracted_skills:
                st.markdown("".join([f'<span class="skill-badge-extracted">{s}</span>' for s in st.session_state.extracted_skills]), unsafe_allow_html=True)
            else:
                st.info("No technical skills identified in the document.")

# ====================================================
# TAB 3: PLACEMENT DASHBOARD
# ====================================================
elif menu == "📊 3. Placement Dashboard":
    st.markdown("### 📊 Placement Competency Dashboard")

    if not has_target:
        st.warning("⚠️ Please set your Target Company & Role in **Step 1**.")
    elif not has_resume:
        st.warning("⚠️ No resume analyzed yet. Please upload your resume in **Step 2** to calculate competency metrics.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                label="Enterprise ATS Score",
                value=f"{current_ats:.0f}%",
                delta="75%+ Recommended for shortlisting" if current_ats >= 75 else "Action required",
                delta_color="normal" if current_ats >= 75 else "inverse"
            )
        with col2:
            st.metric(
                label="Job Readiness",
                value=f"{readiness_pct:.1f}%",
                delta=f"{len(matched_skills)} of {len(required_skills)} required skills met"
            )
        with col3:
            st.metric(
                label="Identified Resume Skills",
                value=len(st.session_state.extracted_skills),
                delta="Extracted from your resume"
            )
        with col4:
            st.metric(
                label="Critical Skill Gaps",
                value=len(missing_skills),
                delta=f"{len(missing_skills)} gaps to bridge",
                delta_color="inverse"
            )

        st.markdown("---")

        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.markdown(f"#### 🎯 Skill Breakdown for {st.session_state.target_role}")
            st.markdown("**Matched Skills (Acquired):**")
            if matched_skills:
                st.markdown("".join([f'<span class="skill-badge-matched">✓ {s}</span>' for s in matched_skills]), unsafe_allow_html=True)
            else:
                st.warning("No matching skills found in your resume for this role.")

            st.markdown("<br>**Missing Skills to Learn:**", unsafe_allow_html=True)
            if missing_skills:
                st.markdown("".join([f'<span class="skill-badge-missing">✗ {s}</span>' for s in missing_skills]), unsafe_allow_html=True)
            else:
                st.success("All required skills met!")

        with col_right:
            st.markdown("#### 🌐 Candidate Domain Profile")
            domain_name, domain_percentages = detect_candidate_domain(st.session_state.extracted_skills)
            st.write(f"Primary Focus Area: **{domain_name}**")
            for d_name, pct in domain_percentages.items():
                if pct > 0:
                    st.write(f"**{d_name}**: {pct:.1f}%")
                    st.progress(float(pct / 100.0))

# ====================================================
# TAB 4: SKILL-GAP PREDICTOR
# ====================================================
elif menu == "🎯 4. Skill-Gap Predictor":
    st.markdown("### 🎯 Dynamic Skill-Gap Prediction Engine")

    if not has_target:
        st.warning("⚠️ Please configure your Target Company & Role in **Step 1**.")
    elif not has_resume:
        st.warning("⚠️ Please upload your resume in **Step 2** to calculate skill gaps.")
    else:
        st.write(f"Comparing your resume against requirements for **{st.session_state.target_role}** at **{st.session_state.target_company}**.")

        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Role Readiness Score", f"{readiness_pct:.1f}%")
            st.progress(float(readiness_pct / 100.0))
        with col_m2:
            st.metric("Matched Skills", f"{len(matched_skills)} / {len(required_skills)}")
        with col_m3:
            st.metric("Identified Skill Gaps", len(missing_skills))

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"#### ✅ Matched Skills ({len(matched_skills)})")
            for s in matched_skills:
                st.success(f"✓ {s}")
        with c2:
            st.markdown(f"#### ⚠️ Missing Skills ({len(missing_skills)})")
            for s in missing_skills:
                st.error(f"✗ {s} (Action Required)")

# ====================================================
# TAB 5: PERSONALIZED LEARNING ROADMAP
# (COMPARE FIRST, POST EVERYTHING DIRECTLY ON PAGE, NO EXTERNAL LINKS)
# ====================================================
elif menu == "🗺️ 5. Personalized Learning Roadmap":
    st.markdown("### 🗺️ Tailored Learning Roadmap & Curriculum")

    if not has_target or not has_resume:
        st.warning("⚠️ Please configure your target company and upload your resume to generate a customized roadmap.")
    else:
        st.markdown(f"#### 1️⃣ Company Requirements vs Your Resume Comparison")
        st.write(f"Targeting: **{st.session_state.target_role}** at **{st.session_state.target_company}**")

        # Direct Comparison Table
        comp_rows = []
        for req in required_skills:
            status = "✅ Matched" if req in matched_skills else "❌ Skill Gap"
            comp_rows.append({"Target Requirement": req, "Resume Status": status})

        st.table(comp_rows)

        st.markdown("---")
        st.markdown("#### 2️⃣ Self-Contained Skill Learning Guides (Complete On-Page Syllabus)")
        st.info("Everything is published directly on this page for immediate study — no external link redirects.")

        if not missing_skills:
            st.success("🎉 You meet all core requirements for this role! Focus on advanced system design and portfolio capstones.")
        else:
            for s in missing_skills:
                content = get_skill_learning_content(s, st.session_state.target_company, st.session_state.target_role)
                with st.expander(f"📘 Master '{s}' — Complete Learning Syllabus & Project Guide", expanded=True):
                    st.markdown(f"**Overview:** {content['summary']}")
                    st.markdown(f"**Core Theory & Mechanics:**\n{content['theory']}")

                    st.markdown("**📅 4-Week Step-by-Step Curriculum:**")
                    for step in content["syllabus"]:
                        st.write(f"• {step}")

                    st.markdown(f"**🚀 Resume-Ready Capstone Project:**\n{content['project']}")

                    st.markdown("**🎙️ Placement Interview Questions & Answers:**")
                    for qa in content["interview_qa"]:
                        st.markdown(f"**Q:** *{qa['q']}*")
                        st.markdown(f"**Ideal Answer:** {qa['a']}")
                        st.write("")

# ====================================================
# TAB 6: AI INTERVIEW PREPARATION
# ====================================================
elif menu == "🎙️ 6. AI Interview Prep":
    st.markdown("### 🎙️ AI Interview Assistant & Live Answer Evaluator")

    if not has_target:
        st.warning("⚠️ Please configure your target company and role in **Step 1**.")
    else:
        st.write(f"Interactive preparation for **{st.session_state.target_role}** at **{st.session_state.target_company}**")

        prep_data = generate_interview_prep(st.session_state.target_role, st.session_state.extracted_skills, missing_skills)

        tab_eval, tab_qs, tab_chat = st.tabs(["✍️ Live Answer Evaluator", "🎯 Role Question Bank", "🤖 AI Interview Coach"])

        with tab_eval:
            st.markdown("#### Live Answer Evaluator")
            st.write("Submit your answer to an interview question for instant 5-criterion grading.")

            question_options = [
                "Explain how indexing works in relational databases and its performance trade-offs.",
                "Describe the difference between process and thread in operating systems.",
                "How do you design a scalable rate limiter for a REST API?",
                "Tell me about a time you handled a difficult technical challenge in a team project."
            ]
            chosen_q = st.selectbox("Select Question to Practice", question_options)
            user_answer = st.text_area("Your Response", height=140)

            if st.button("Evaluate My Answer", type="primary"):
                if user_answer.strip():
                    with st.spinner("Scoring answer across 5 evaluation criteria..."):
                        eval_result = evaluate_user_answer(chosen_q, user_answer, st.session_state.target_role)

                        st.markdown("---")
                        st.markdown(f"### Overall Score: **{eval_result.get('total_score', 0)} / 100** ({eval_result.get('rating', 'Good')})")

                        breakdown = eval_result.get("breakdown", {})
                        col_b1, col_b2, col_b3, col_b4, col_b5 = st.columns(5)
                        col_b1.metric("Technical Accuracy", f"{breakdown.get('technical_accuracy', 0)}/20")
                        col_b2.metric("Keywords", f"{breakdown.get('keywords_terminology', 0)}/20")
                        col_b3.metric("Clarity & Structure", f"{breakdown.get('structure_clarity', 0)}/20")
                        col_b4.metric("Real-World Context", f"{breakdown.get('real_world_relevance', 0)}/20")
                        col_b5.metric("Completeness", f"{breakdown.get('completeness', 0)}/20")

                        st.markdown("#### Strengths Identified:")
                        for s in eval_result.get("strengths", []):
                            st.success(f"✓ {s}")

                        st.markdown("#### Key Points to Add / Improve:")
                        for m in eval_result.get("missing_points", []):
                            st.warning(f"• {m}")

                        st.markdown("#### 🌟 Ideal Answer Blueprint:")
                        st.info(eval_result.get("ideal_answer", ""))
                else:
                    st.warning("Please type your answer before submitting.")

        with tab_qs:
            st.markdown(f"#### 🎯 Complete Interview Question Bank for **{st.session_state.target_role}** at **{st.session_state.target_company}**")

            qb_tab1, qb_tab2, qb_tab3 = st.tabs([
                "💻 Role Technical Questions",
                "⚠️ Skill-Gap Priority Questions",
                "👔 Behavioral & HR Questions (STAR)"
            ])

            with qb_tab1:
                role_qs = prep_data.get("all_questions", [])
                if role_qs:
                    for i, q_item in enumerate(role_qs, 1):
                        with st.expander(f"Q{i}: {q_item.get('q', 'Question')} [{q_item.get('skill', 'Core')}]", expanded=(i <= 2)):
                            st.markdown(f"**Topic / Skill:** `{q_item.get('skill', 'General')}`")
                            st.markdown(f"**💡 Model Answer:**\n{q_item.get('a', 'Focus on explaining core principles clearly.')}")
                            if q_item.get('tip'):
                                st.info(f"🎯 **Interviewer Tip:** {q_item.get('tip')}")
                else:
                    st.info("No role-specific technical questions generated.")

            with qb_tab2:
                gap_qs = prep_data.get("gap_questions", [])
                if gap_qs:
                    st.markdown("*These questions focus specifically on the skill gaps identified between your resume and the target role.*")
                    for i, q_item in enumerate(gap_qs, 1):
                        with st.expander(f"Gap Q{i}: {q_item.get('q', 'Question')} [{q_item.get('skill', 'Gap')}]"):
                            st.markdown(f"**Missing Skill Targeted:** `{q_item.get('skill', 'Gap')}`")
                            st.markdown(f"**💡 Expected Technical Answer:**\n{q_item.get('a', '')}")
                            if q_item.get('tip'):
                                st.warning(f"🎯 **What interviewers look for:** {q_item.get('tip')}")
                else:
                    st.success("🎉 No missing skill gaps! Review the main Technical Questions tab.")

            with qb_tab3:
                st.markdown("*Behavioral questions evaluated using the STAR technique (Situation, Task, Action, Result).*")
                behavioral_qs = prep_data.get("behavioral", [])
                for i, b_item in enumerate(behavioral_qs, 1):
                    with st.expander(f"HR Q{i}: {b_item.get('q', 'Behavioral Question')}"):
                        st.markdown(f"**Framework:** `{b_item.get('framework', 'STAR Framework')}`")
                        st.markdown(f"**Answering Blueprint & Strategy:**\n{b_item.get('guide', '')}")

        with tab_chat:
            st.markdown("#### Interactive AI Interview Coach")
            chat_prompt = st.text_input(f"Ask for company-specific interview advice (e.g., 'How to answer Why {st.session_state.target_company}?', 'STAR method tips')")
            if st.button("Ask Coach"):
                if chat_prompt:
                    with st.spinner("Generating coach guidance..."):
                        reply = ask_ai_interview_assistant(chat_prompt, st.session_state.target_role, st.session_state.target_company)
                        st.markdown(f"**Coach Guidance:**\n\n{reply}")

# ====================================================
# TAB 7: EXPORT PROGRESS REPORT
# ====================================================
elif menu == "📑 7. Export Progress Report":
    st.markdown("### 📑 Detailed Career Readiness & Progress Report")

    if not has_target or not has_resume:
        st.warning("⚠️ Please set your target company and upload your resume to generate a complete report.")
    else:
        st.write(f"Generate a comprehensive PDF report for **{user['name']}** targeting **{st.session_state.target_role}** at **{st.session_state.target_company}**.")

        domain_name, _ = detect_candidate_domain(st.session_state.extracted_skills)
        strength_label, _, _ = evaluate_resume_strength(current_ats, readiness_pct)
        ai_confidence = calculate_ai_confidence(current_ats, readiness_pct, len(st.session_state.extracted_skills))
        roadmap_data = generate_learning_roadmap(missing_skills, st.session_state.target_role, st.session_state.target_company)

        phases_list = []
        for p in roadmap_data.get("phases", []):
            if isinstance(p, dict):
                phases_list.append(p)

        if st.button("🔨 Generate Detailed Progress Report (PDF)", type="primary"):
            with st.spinner("Compiling publication-grade PDF report..."):
                try:
                    pdf_bytes = generate_pdf_report(
                        student_name=user["name"],
                        target_role=st.session_state.target_role,
                        target_company=st.session_state.target_company,
                        domain=domain_name,
                        ats_score=current_ats,
                        readiness_score=readiness_pct,
                        confidence_score=ai_confidence,
                        resume_strength=strength_label,
                        matched_skills=matched_skills,
                        missing_skills=missing_skills,
                        recommendations=[
                            f"Focus study on {', '.join(missing_skills[:3]) if missing_skills else 'Advanced System Design'}",
                            f"Tailor resume impact metrics specifically for {st.session_state.target_company}",
                            "Highlight quantifiable metrics in project bullet points"
                        ],
                        roadmap_phases=phases_list
                    )

                    st.success("Detailed report successfully generated!")
                    st.download_button(
                        label="📥 Download Detailed Career Report (PDF)",
                        data=pdf_bytes,
                        file_name=f"{user['name'].replace(' ', '_')}_{st.session_state.target_company}_Report.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"Error compiling PDF report: {e}")
