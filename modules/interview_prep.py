"""
AI Interview Preparation Module
Project ID: P19 - Skill-Gap Predictor for Students (Career Navigation AI)
GITAM University, Bengaluru Campus
Developers: Vinay Kumar S, Yashwanth K, Mahesh B K
Mentor: Dr. N. Gayathri (M29)

Provides role-specific technical questions, skill-gap-focused interview questions,
and behavioral HR preparation using the STAR technique.
"""

from typing import Dict, List, Any

# Technical question bank mapped to skills
SKILL_QUESTIONS: Dict[str, List[Dict[str, str]]] = {
    "Data Structures": [
        {
            "q": "How would you detect a cycle in a singly linked list with O(1) extra space?",
            "a": "Use Floyd's Cycle-Finding Algorithm (Tortoise and Hare). Maintain two pointers: slow moves 1 step, fast moves 2 steps. If they meet, a cycle exists; if fast reaches NULL, no cycle exists.",
            "tip": "Always discuss edge cases like empty lists or single nodes."
        },
        {
            "q": "Explain the internal difference between a Hash Map and a Balanced Binary Search Tree (like Red-Black Tree).",
            "a": "Hash Maps offer O(1) average time complexity for lookup/insert via hashing, but lack ordered traversal. Balanced BSTs maintain elements in sorted order with guaranteed O(log N) operations even in worst cases.",
            "tip": "Mention collision resolution techniques like chaining vs open addressing."
        }
    ],
    "Algorithms": [
        {
            "q": "When would you choose Dijkstra's algorithm over Breadth-First Search (BFS)?",
            "a": "BFS finds shortest paths only in unweighted graphs. Dijkstra's handles non-negative weighted graphs by employing a min-priority queue.",
            "tip": "Point out that Dijkstra fails on negative weight edges and Bellman-Ford should be used instead."
        }
    ],
    "Python": [
        {
            "q": "What is Python's Global Interpreter Lock (GIL) and how does it affect multi-threaded programs?",
            "a": "The GIL is a mutex that prevents multiple native threads from executing Python bytecodes simultaneously. It protects memory management, but CPU-bound tasks do not achieve true multi-core parallelism. Use multiprocessing for CPU tasks.",
            "tip": "Distinguish between I/O-bound tasks (threading helps) vs CPU-bound tasks (multiprocessing required)."
        },
        {
            "q": "Explain the difference between deep copy and shallow copy in Python.",
            "a": "A shallow copy constructs a new compound object and inserts references into it. A deep copy recursively copies all nested objects found in the original.",
            "tip": "Give an example with nested lists or dictionaries."
        }
    ],
    "Java": [
        {
            "q": "Explain the JVM memory model: Stack vs Heap memory.",
            "a": "Stack memory stores local primitive variables and method call execution frames. Heap memory stores dynamically allocated objects and JRE classes, managed by the Garbage Collector.",
            "tip": "Explain StackOverflowError vs OutOfMemoryError."
        }
    ],
    "SQL": [
        {
            "q": "What is the difference between WHERE and HAVING clauses?",
            "a": "WHERE filters rows before any aggregate functions are applied. HAVING filters groups produced by GROUP BY clauses.",
            "tip": "Write an example query grouping department salaries."
        }
    ],
    "React": [
        {
            "q": "What problem does the Virtual DOM solve and how does reconciliation work?",
            "a": "Manipulating the real browser DOM is computationally expensive. React maintains a Virtual DOM in memory, calculates minimal diffs using its reconciliation algorithm (Fiber), and batches updates efficiently.",
            "tip": "Explain why keys are vital when rendering lists in React."
        }
    ],
    "Machine Learning": [
        {
            "q": "Explain the Bias-Variance Tradeoff and how you diagnose high bias vs high variance.",
            "a": "High bias leads to underfitting (model is too simplistic, high training & validation error). High variance leads to overfitting (low training error, high validation error). Regularization, more data, or pruning address high variance.",
            "tip": "Draw or describe the learning curves of training loss vs validation loss."
        }
    ],
    "Cloud & DevOps": [
        {
            "q": "What is the fundamental difference between a Docker Container and a Virtual Machine?",
            "a": "VMs virtualize hardware and run a complete guest OS on top of a hypervisor. Docker containers share the host OS kernel and isolate user spaces, making them lightweight and fast to boot.",
            "tip": "Highlight resource utilization and startup speed benefits."
        }
    ],
    "System Design": [
        {
            "q": "How would you design a scalable URL Shortener service like TinyURL handling 100M URLs per day?",
            "a": "Use Base62 encoding on unique 64-bit auto-incrementing IDs (generated via Snowflake). Employ a distributed cache (Redis) for hot URL lookups, and partition the database by hash of the short key with read replicas.",
            "tip": "Cover both functional and non-functional requirements (read-to-write ratio, latency targets, 5-year storage estimates)."
        },
        {
            "q": "Explain the difference between Strong Consistency and Eventual Consistency with examples.",
            "a": "Strong consistency guarantees every read receives the most recent write (RDBMS transactions). Eventual consistency allows temporary replication lag across replicas, guaranteeing reads eventually converge (DNS, Amazon DynamoDB, social feeds).",
            "tip": "Reference the CAP theorem and discuss trade-offs between latency and strict ordering."
        }
    ],
    "Git": [
        {
            "q": "What is the difference between 'git merge' and 'git rebase'?",
            "a": "'git merge' creates a new commit that ties the histories of both branches together, preserving chronological order. 'git rebase' rewrites the commit history by moving the base of your branch onto the target branch, producing a clean linear history.",
            "tip": "Emphasize the golden rule of rebasing: never rebase a shared public branch."
        }
    ],
    "Docker": [
        {
            "q": "What are multi-stage builds in Docker and why are they used?",
            "a": "Multi-stage builds allow using multiple FROM statements in a single Dockerfile. You can compile your application with full build tools in an initial stage, then copy only the finalized executable or artifact into a minimal base image (like Alpine or Distroless), minimizing image size and attack surface.",
            "tip": "Mention how it optimizes layer caching and reduces deployment bandwidth."
        }
    ],
    "Kubernetes": [
        {
            "q": "Explain the roles of Pods, ReplicaSets, and Deployments in Kubernetes.",
            "a": "A Pod is the smallest deployable unit containing one or more tightly coupled containers. A ReplicaSet ensures a specified number of identical pod replicas are running at any time. A Deployment provides declarative updates for Pods and ReplicaSets, enabling rolling upgrades and rollbacks.",
            "tip": "Discuss zero-downtime deployment strategies like RollingUpdate vs Recreate."
        }
    ],
    "C++": [
        {
            "q": "Explain the difference between std::unique_ptr, std::shared_ptr, and std::weak_ptr in modern C++.",
            "a": "std::unique_ptr owns a resource exclusively and cannot be copied (only moved). std::shared_ptr uses reference counting to allow multiple owners. std::weak_ptr provides a non-owning observer to break cyclic reference loops between shared_ptrs.",
            "tip": "Explain the RAII (Resource Acquisition Is Initialization) idiom."
        }
    ],
    "Node.js": [
        {
            "q": "How does the Node.js Event Loop handle non-blocking asynchronous I/O?",
            "a": "Node.js runs single-threaded JavaScript execution on the V8 engine, while offloading I/O tasks (file system, network) to the C++ Libuv thread pool. When an I/O task completes, Libuv queues its callback into event loop phases (Timers, Poll, Check) to execute on the main thread.",
            "tip": "Explain process.nextTick() vs setImmediate() execution priorities."
        }
    ],
    "Problem Solving": [
        {
            "q": "How do you systematically approach an unfamiliar algorithmic problem under interview pressure?",
            "a": "1. Clarify constraints and edge cases (empty inputs, negative numbers, scale). 2. Discuss a brute-force baseline to establish an upper bound. 3. Identify recurring patterns (Two Pointers, Sliding Window, Monotonic Stack, DP). 4. Code cleanly while articulating time and space complexities.",
            "tip": "Always walk through a test case manually before declaring your code complete."
        }
    ]
}

# Standard HR behavioral questions based on STAR methodology
BEHAVIORAL_QUESTIONS: List[Dict[str, str]] = [
    {
        "q": "Tell me about a time you faced a difficult technical bug in a project and how you solved it.",
        "framework": "STAR (Situation, Task, Action, Result)",
        "guide": "Describe the bug's context (Situation), your responsibility (Task), the systematic debugging steps or tools you used like logging or profilers (Action), and the measurable outcome (Result, e.g. reduced crash rate by 90%)."
    },
    {
        "q": "Why do you want to join our company and this specific role?",
        "framework": "Motivation & Alignment",
        "guide": "Link your genuine technical projects with the company's recent engineering advancements or products. Show familiarity with their core values and tech stack."
    },
    {
        "q": "How do you handle disagreement with a team member during a group project?",
        "framework": "Collaboration & Conflict Resolution",
        "guide": "Emphasize active listening, focusing on data and project requirements over personal opinions, and finding a consensus or prototype to test both approaches."
    }
]


def generate_interview_prep(role: str, matched_skills: List[str], missing_skills: List[str]) -> Dict[str, Any]:
    """
    Generate an extensive interview question set:
    - Technical questions on skills candidate knows
    - High-frequency questions on missing skills they should study
    - Core system design & algorithmic fundamentals
    - Behavioral questions with STAR frameworks
    """
    technical_known = []
    for skill in (matched_skills or []):
        if skill in SKILL_QUESTIONS:
            for q_data in SKILL_QUESTIONS[skill]:
                technical_known.append({"skill": skill, **q_data})

    gap_questions = []
    for skill in (missing_skills or []):
        if skill in SKILL_QUESTIONS:
            for q_data in SKILL_QUESTIONS[skill]:
                gap_questions.append({"skill": skill, **q_data})

    # Core algorithmic & architectural baseline
    core_questions = []
    for cs in ["Data Structures", "Algorithms", "System Design", "Problem Solving"]:
        if cs in SKILL_QUESTIONS:
            for q_data in SKILL_QUESTIONS[cs]:
                core_questions.append({"skill": cs, **q_data})

    # Fallback if specific skills aren't in dictionary
    if not technical_known and not gap_questions:
        gap_questions = core_questions[:4]

    all_questions = []
    seen = set()
    for item in (technical_known + gap_questions + core_questions):
        if item["q"] not in seen:
            seen.add(item["q"])
            all_questions.append(item)

    return {
        "role": role,
        "all_questions": all_questions,
        "technical_known": technical_known,
        "gap_questions": gap_questions,
        "behavioral": BEHAVIORAL_QUESTIONS,
    }


def ask_ai_interview_assistant(prompt: str, role: str = "Software Engineer", company: str = "Google") -> Dict[str, Any]:
    """
    AI Interview Assistant chatbot logic: answers questions, gives tips,
    and provides customized drill questions for any company or technical topic.
    """
    p_lower = prompt.lower().strip()
    
    if any(k in p_lower for k in ["why", "company", "culture", "fit", "join"]):
        response_title = f"🎯 How to Answer 'Why {company}?' for a {role} Position"
        advice = [
            f"1. **Research Core Values**: Align your response with {company}'s tech innovations and culture.",
            f"2. **Connect Past Projects**: Explicitly state how your skills map to expected deliverables for {role}.",
            "3. **Highlight Long-term Growth**: Explain why this environment challenges you to solve high-impact engineering problems.",
            "4. **Avoid Generic Praise**: Don't just compliment the brand name—cite specific engineering blogs, OSS contributions, or product features."
        ]
        sample_q = f"What specific architectural challenges or technical products at {company} excite you most as a {role}?"
        sample_a = f"At {company}, system reliability at immense scale is key. In my previous work, I focused on high-throughput microservices, and I want to apply those distributed systems patterns to {company}'s core infrastructure."
        
    elif any(k in p_lower for k in ["system design", "architecture", "scale", "system"]):
        response_title = f"🏗️ System Design Interview Blueprint for {role} at {company}"
        advice = [
            "1. **Clarify Scope & Requirements**: Establish Functional vs Non-Functional requirements (latency, throughput, availability, consistency).",
            "2. **Estimate Scale**: Calculate Requests Per Second (RPS), bandwidth, and storage capacity for 5 years.",
            "3. **Define High-Level API & Data Schema**: Sketch REST/gRPC endpoints and SQL vs NoSQL schema selection.",
            "4. **Deep Dive Key Components**: Load Balancers, CDN, Caching layer (Redis), DB Sharding/Replication, and Message Queues (Kafka).",
            "5. **Address Bottlenecks & Single Points of Failure**: Discuss rate limiting, circuit breakers, and monitoring metrics."
        ]
        sample_q = "How would you design a rate limiter service handling 100,000 requests per second?"
        sample_a = "Use the Token Bucket or Leaky Bucket algorithm implemented over a distributed Redis cluster using atomic Lua scripts to maintain accurate per-user sliding window counters."

    elif any(k in p_lower for k in ["behavioral", "hr", "star", "conflict", "tell me about"]):
        response_title = "👔 Behavioral HR Strategy (STAR Framework)"
        advice = [
            "1. **Situation**: Set the context in 2-3 concise sentences (project goals, team size, deadline).",
            "2. **Task**: Define the exact problem or conflict you personally were assigned to resolve.",
            "3. **Action**: Spend 60% of your answer on concrete technical actions YOU took, decisions made, and tools used.",
            "4. **Result**: Quantify your outcome with metrics (% performance gain, crash reduction, on-time delivery)."
        ]
        sample_q = "Tell me about a technical decision you made that turned out to be wrong and how you handled it."
        sample_a = "Initially chose an unindexed SQL query approach for search. When load testing revealed 3s latency spikes, I acknowledged the flaw, conducted benchmark tests with Elasticsearch, and migrated the indexing pipeline, reducing latency to 120ms."

    elif any(k in p_lower for k in ["coding", "algorithm", "data structure", "leetcode", "dsa"]):
        response_title = f"💻 Technical Coding Interview Master Plan for {role}"
        advice = [
            "1. **Think Out Loud**: Communicate your initial brute force idea before typing code.",
            "2. **State Time & Space Complexity**: Always state O(N) time and O(1) space before optimizing.",
            "3. **Test with Edge Cases**: Check null pointers, empty arrays, negative numbers, single element lists, and large inputs.",
            "4. **Write Clean Code**: Use descriptive variable names, modular functions, and idiomatic patterns."
        ]
        sample_q = "Given an unsorted array of integers, find the length of the longest consecutive elements sequence in O(N) time."
        sample_a = "Insert all numbers into a Hash Set. Iterate through numbers; if (num - 1) is not in the set, it's the start of a sequence. Count upwards in O(1) lookups per element, running in total O(N) time."

    else:
        response_title = f"🤖 AI Guidance for {role} at {company}"
        advice = [
            f"1. **Master High-Frequency Core Concepts**: Deep-dive into data structures, algorithms, and system design tailored for {role}.",
            f"2. **Tailor Your Resume Metrics**: Ensure your past experience at {company} interviews highlights measurable impact.",
            "3. **Mock Practice Daily**: Rehearse answering out loud using structured frameworks (STAR for HR, 5-Step System Design).",
            f"4. **Review Skill Gaps**: Focus on mastering missing technical competencies prior to your interview round."
        ]
        sample_q = f"What core technical skills distinguish a top-tier {role} candidate during technical rounds?"
        sample_a = f"A top {role} candidate demonstrates clean code design, deep knowledge of underlying frameworks, edge-case validation, and clear architectural communication."

    return {
        "status": "success",
        "prompt": prompt,
        "title": response_title,
        "advice_steps": advice,
        "sample_question": sample_q,
        "sample_answer": sample_a,
        "role": role,
        "company": company
    }


def evaluate_user_answer(question: str, user_answer: str, role: str = "Software Engineer") -> Dict[str, Any]:
    """
    Evaluates a candidate's written interview response on 5 criteria:
    1. Technical Accuracy (0-20)
    2. Terminology & Keywords (0-20)
    3. Structure & Clarity (0-20)
    4. Real-world Relevance / STAR (0-20)
    5. Completeness (0-20)
    """
    ans_clean = user_answer.strip()
    words = ans_clean.split()
    word_count = len(words)

    if word_count < 5:
        return {
            "status": "success",
            "total_score": 25,
            "rating": "Needs Improvement",
            "color": "#ef4444",
            "breakdown": {
                "technical_accuracy": 5,
                "keywords_terminology": 5,
                "structure_clarity": 5,
                "real_world_relevance": 5,
                "completeness": 5
            },
            "strengths": ["Answer was submitted."],
            "missing_points": [
                "Answer is too short (fewer than 5 words). Provide a detailed technical explanation.",
                "Include core algorithms, data structures, or trade-offs.",
                "Structure your response with clear technical steps or the STAR technique."
            ],
            "ideal_answer": "Provide a comprehensive answer covering key technical mechanisms, time/space complexity, and practical examples."
        }

    # Keyword analysis
    tech_keywords = [
        "complexity", "time", "space", "o(1)", "o(n)", "log", "algorithm", "structure",
        "data", "database", "sql", "index", "cache", "redis", "async", "thread",
        "lock", "memory", "heap", "stack", "pointer", "array", "map", "tree", "graph",
        "api", "rest", "grpc", "service", "system", "scale", "test", "unit", "design",
        "refactor", "latency", "throughput", "star", "situation", "task", "action", "result"
    ]

    matched_kw = [kw for kw in tech_keywords if kw in ans_clean.lower()]
    kw_score = min(20, max(6, len(matched_kw) * 4))

    # Completeness based on length
    if word_count >= 60:
        comp_score = 20
    elif word_count >= 35:
        comp_score = 16
    elif word_count >= 20:
        comp_score = 12
    else:
        comp_score = 8

    # Structure & Clarity
    has_punctuation = ("." in ans_clean or ";" in ans_clean or "\n" in ans_clean)
    struct_score = 18 if (has_punctuation and word_count >= 25) else 12

    # Technical accuracy & relevance estimates
    tech_acc = min(20, kw_score + 2)
    relevance = 16 if any(k in ans_clean.lower() for k in ["for example", "instance", "used", "built", "implemented", "project", "because", "result"]) else 12

    total_score = tech_acc + kw_score + struct_score + relevance + comp_score
    total_score = min(98, max(30, total_score))

    if total_score >= 80:
        rating = "Excellent Answer"
        color = "#10b981" # Emerald
    elif total_score >= 65:
        rating = "Good Effort"
        color = "#38bdf8" # Cyan
    else:
        rating = "Needs Improvement"
        color = "#f59e0b" # Amber

    strengths = []
    if kw_score >= 14:
        strengths.append("Good technical terminology and relevant domain keywords included.")
    if comp_score >= 16:
        strengths.append("Thorough explanation with good depth and detail.")
    if struct_score >= 16:
        strengths.append("Clear syntax and well-structured response.")
    if not strengths:
        strengths.append("Valid attempt showing foundational understanding.")

    missing_points = []
    if kw_score < 14:
        missing_points.append("Include more specific technical terms, data structures, or algorithmic time/space complexities.")
    if comp_score < 16:
        missing_points.append("Elaborate further with concrete examples or real-world project context.")
    if relevance < 15:
        missing_points.append("State the measurable result or business impact (e.g. reduced latency by X%, improved test coverage).")

    ideal_answer = f"A complete answer for '{question}' should clearly define the problem, state any underlying data structures or algorithm complexities (e.g., O(N)), give a 2-sentence practical example, and mention edge case handling."

    return {
        "status": "success",
        "total_score": total_score,
        "rating": rating,
        "color": color,
        "breakdown": {
            "technical_accuracy": tech_acc,
            "keywords_terminology": kw_score,
            "structure_clarity": struct_score,
            "real_world_relevance": relevance,
            "completeness": comp_score
        },
        "strengths": strengths,
        "missing_points": missing_points,
        "ideal_answer": ideal_answer
    }

