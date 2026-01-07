# rag/prompts.py

import os
from dotenv import load_dotenv
load_dotenv()

def generate_prompt(field, context):
    """Enhanced prompt with stricter instructions"""
    return (
        f"Rules:\n"
        f"- Output ONLY the {field} value\n"
        f"- NO explanations, reasoning, or calculations\n"
        f"- If not found, give your best guess\n"
        f"- Be precise and concise\n\n"
        f"EXTRACT ONLY: {field}\n\n"
        f"Document excerpt:\n{context}\n\n"
        f"YOUR TURN:\n{field}:"
    )


def generate_status_prompt(context):
    """Generate strict status extraction prompt"""
    return (
        f"Rules:\n"
        f"- Output ONLY ONE of the following values:\n"
        f"  - In Progress\n"
        f"  - Completed\n"
        f"  - On Hold\n"
        f"  - Not yet started\n"
        f"  - Experimental\n"
        f"- NO explanations, no reasoning\n"
        f"- If not sure, make your best guess\n\n"
        f"Document excerpt:\n{context}\n\n"
        f"Status:"
    )

def generate_client_prompt(context: str) -> str:
    """
    Generate a focused prompt for client extraction with multiple recognition patterns
    """
    prompt = f"""
Based on the following document context, identify the CLIENT or CUSTOMER organization.

Context:
{context}

Instructions:
1. Look for the name of the organization that is receiving the services
2. Return ONLY the organization name, no additional text
3. If multiple organizations are mentioned, return the PRIMARY client/customer
4. If unclear, return the most prominent organization name

Client/Customer Name:"""
    
    return prompt



def generate_billing_type_prompt(context):
    """Generate strict billing type prompt"""
    return (
        f"Rules:\n"
        f"- Output ONLY ONE of the following values:\n"
        f"  - Time and Material\n"
        f"  - Retainer\n"
        f"  - Fixed Fee\n"
        f"  - Staff Augmentation\n"
        f"  - Research Grant\n"
        f"- NO explanations, no reasoning\n"
        f"- Be precise and concise\n\n"
        f"Document excerpt:\n{context}\n\n"
        f"Billing Type:"
    )

def generate_tech_prompt(context):
    """Generate prompt for technology extraction"""
    return (
        f"Rules:\n"
        f"- Output ONLY a Python list format: ['tech1', 'tech2', 'tech3']\n"
        f"- Include programming languages, databases, cloud platforms, tools etc\n"
        f"- NO explanations or extra text\n"
        f"- If none found, output []\n\n"
        f"EXTRACT: List of technologies, tools, platforms, or frameworks mentioned\n\n"
        f"Document excerpt:\n{context}\n\n"
        f"Technologies:"
    )


def generate_practice_prompt(context, valid_practices):
    """Generate prompt for practice extraction with fuzzy matching"""
    practices_hint = f"Common practices: {', '.join(valid_practices[:10])}" if valid_practices else ""

    return (
        f"Rules:\n"
        f"- Output ONLY the main practice/service area\n"
        f"- Examples: Software Development, Artificial Intelligence, Computer Vision, etc.\n"
        f"- NO explanations or extra text\n"
        f"- If not found, output your best guess\n\n"
        f"EXTRACT: Business practice or service area for this project\n\n"
        f"Document excerpt:\n{context}\n\n"
        f"{practices_hint}\n\n"
        f"Practice:"
    )

def generate_category_prompt(context):
    """Generate strict category extraction prompt aligned with Horizon AI Solutions taxonomy"""
    return (
        "Rules:\n"
        "- Output ONLY ONE of the following values:\n"
        "  - Project\n"
        "  - Research\n"
        "  - Pilot\n"
        "  - Support\n"
        "  - Internal Innovation\n"
        "- NO explanations\n"
        "- NO reasoning text\n"
        "- NO additional words or punctuation\n"
        "- Choose the MOST appropriate category based on the document context\n"
        "- If unclear, make your best guess\n\n"
        "Category Guidelines:\n"
        "- Project: Client-facing delivery work, implementation, development, integrations, or defined deliverables\n"
        "- Research: Experimental work, feasibility studies, model experimentation, benchmarking, or R&D activities\n"
        "- Pilot: Proof of concept, MVP, limited-scope trial, or validation phase before full rollout\n"
        "- Support: Ongoing maintenance, monitoring, bug fixes, enhancements, or operational assistance\n"
        "- Internal Innovation: Internal tools, accelerators, frameworks, or Horizon AI internal initiatives\n\n"
        "Document excerpt:\n"
        f"{context}\n\n"
        "Category:"
    )


def generate_start_date_prompt(context):
    """Generate specialized prompt for start date extraction"""
    return (
        f"Rules:\n"
        f"- Output ONLY the start date in MM/DD/YYYY format\n"
        f"- NO explanations or extra text\n"
        f"- Look for project commencement, kick-off, or beginning dates\n"
        f"- If multiple dates exist, choose the earliest project start date\n"
        f"- If unable to decide, give the most appropriate value based on context\n\n"
        f"EXTRACT ONLY: Project start date in MM/DD/YYYY format\n\n"
        f"Document excerpt:\n{context}\n\n"
        f"Start Date:"
    )

def generate_end_date_prompt(context):
    """Generate specialized prompt for end date extraction"""
    return (
        f"Rules:\n"
        f"- Output ONLY the end date in MM/DD/YYYY format\n"
        f"- NO explanations or extra text\n"
        f"- Look for project completion, delivery, or final dates\n"
        f"- If multiple dates exist, choose the final project completion date\n"
        f"- If details about duration are given calculate the end date"
        f"- If unable to decide, give the most apprpriate value based on context\n\n"
        f"EXTRACT ONLY: Project end date in MM/DD/YYYY format\n\n"
        f"Document excerpt:\n{context}\n\n"
        f"End Date:"
    )

#rag/prompts.py (updated with enhanced JSON fields)

def generate_manager_recommendation_prompt(sow_data, manager_candidates):
    """Generate AI prompt specifically for manager recommendations"""
    
    n_managers = int(os.getenv("N_MANAGERS", 1))
    
    sow_summary = f"""
    PROJECT REQUIREMENTS:
    - Project: {sow_data.get('project_name', 'Unknown')}
    - Technologies: {', '.join(sow_data.get('technology', []))}
    - Practice: {sow_data.get('practice', '')}
    - Category: {sow_data.get('category', '')}
    - Duration: {sow_data.get('start_date', '')} to {sow_data.get('end_date', '')}
    - Budget: {sow_data.get('budgeted_hours', '')}
    """

    candidates_text = "AVAILABLE MANAGERS:\n"
    for i, candidate in enumerate(manager_candidates, 1):
        meta = candidate['metadata']
        candidates_text += f"""
        M{i}. {meta['resource_name']}
        - Designation: {meta.get('designation', 'N/A')}
        - Skills: {meta.get('skills', 'N/A')}
        - Experience: {meta.get('experience_months', '0')} months
        - Level: {meta.get('designation_level', 'N/A')}
        - Department: {meta.get('department', 'N/A')}
        - Base Department: {meta.get('base_department', 'N/A')}
        - Hours Worked on Skills: {meta.get('hours_worked', '0')} hours
        - Availability: {meta.get('availability', '0')}%
        - Weekly Hours Available: {meta.get('hours_available_weekly', '0')} hours/week
        - Practice Areas: {meta.get('practices_with_hours', 'N/A')}
        """

    return f"""
    You are an expert consultant selecting PROJECT MANAGERS for a software development project.

    *** CRITICAL REQUIREMENT ***
    You MUST recommend EXACTLY {n_managers} manager(s). NO MORE, NO LESS.

    {sow_summary}

    {candidates_text}

    MANAGER SELECTION CRITERIA:
    1. Leadership and project management experience
    2. Technical understanding of required technologies
    3. Department and practice area alignment
    4. Availability and capacity (both percentage and weekly hours)
    5. Experience level and designation
    6. Communication and coordination skills
    7. Practice area experience that matches project requirements  
    8. Higher proficiency levels (in parentheses) indicate stronger expertise and must be considered when evaluating skills

    ALLOCATION RULES:
    - CRITICAL: Check each candidate's "Weekly Hours Available" field carefully
    - Your allocation suggestion MUST be ≤ their available hours (never exceed!)
    - Consider project needs but respect their capacity limits
    
    SKILLS RECOMMENDATION RULES:
    - Return ONLY technology names, tool names, or methodology keywords
    - NO explanations, descriptions, or full sentences
    - Examples: "Agile", "Scrum", "JIRA", "Azure DevOps", "Risk Management"
    - NOT: "Learn advanced project management frameworks for better coordination"

    EXPERIENCE RECOMMENDATION RULES:
    - Suggest ideal experience level in years for this specific project
    - Consider project complexity, technology stack, team size, and duration
    - Format as a number (e.g., 3 for 3 years, 5 for 5 years)

    STRICT INSTRUCTIONS:
    1. Recommend EXACTLY {n_managers} manager(s) - do not exceed this number
    2. RANK them in DESCENDING ORDER OF PREFERENCE (M1 = best choice, M2 = second best, etc.)
    3. For each recommendation:
    - Explain WHY they're ideal for managing this specific project
    - Point out any concerns or limitations
    - Justify why you picked this person over others
    - Consider their practice area experience and weekly availability
    - Suggest realistic hour allocation as a number (MUST NOT exceed their weekly available hours)
    - Recommend additional skills as simple keywords/technologies only
    - Suggest ideal experience level for this project type
    4. Focus on management capabilities, not just technical skills
    5. Consider their current workload and availability (both % and weekly hours)
    6. Keep the tone executive-summary style, focused and concise.

    Return your response as a JSON object with this structure:
    {{
        "managers": [
            {{
                "rank": "1",
                "name": "Manager Name",
                "designation": "designation of the manager selected",
                "match_score": 0.95,
                "reasons": [
                    "Strong leadership experience in similar projects",
                    "Available capacity aligns with project timeline",
                    "Deep understanding of required technology stack",
                    "Practice area experience matches project needs"
                ],
                "concerns": [
                    "Any potential management challenges",
                    "Current availability/workload considerations"
                ],
                "why_pick": "Clear justification for why this manager was selected over others",
                "allocation_suggestion": 23,
                "recommended_skills": [
                    "Agile",
                    "Scrum Master",
                    "Azure DevOPs",
                    "Project Planning Tools"
                ],
                "recommended_experience": 4,
                "recommendation": "Highly recommended / Recommended / Consider"
            }}
        ]
    }}
    """.strip()

def generate_tester_recommendation_prompt(sow_data, tester_candidates):
    """Generate AI prompt specifically for tester recommendations"""
    
    n_testers = int(os.getenv("N_TESTERS", 1))
    
    sow_summary = f"""
    PROJECT REQUIREMENTS:
    - Project: {sow_data.get('project_name', 'Unknown')}
    - Technologies: {', '.join(sow_data.get('technology', []))}
    - Practice: {sow_data.get('practice', '')}
    - Category: {sow_data.get('category', '')}
    - Duration: {sow_data.get('start_date', '')} to {sow_data.get('end_date', '')}
    - Budget: {sow_data.get('budgeted_hours', '')}
    """

    candidates_text = "AVAILABLE TESTERS:\n"
    for i, candidate in enumerate(tester_candidates, 1):
        meta = candidate['metadata']
        candidates_text += f"""
        T{i}. {meta['resource_name']}
        - Designation: {meta.get('designation', 'N/A')}
        - Skills: {meta.get('skills', 'N/A')}
        - Experience: {meta.get('experience_months', '0')} months
        - Level: {meta.get('designation_level', 'N/A')}
        - Department: {meta.get('department', 'N/A')}
        - Base Department: {meta.get('base_department', 'N/A')}
        - Hours Worked on Skills: {meta.get('hours_worked', '0')} hours
        - Availability: {meta.get('availability', '0')}%
        - Weekly Hours Available: {meta.get('hours_available_weekly', '0')} hours/week
        - Practice Areas: {meta.get('practices_with_hours', 'N/A')}
        """

    return f"""
    You are an expert consultant selecting QUALITY ASSURANCE TESTERS for a software development project.

    *** CRITICAL REQUIREMENT ***
    You MUST recommend EXACTLY {n_testers} tester(s). NO MORE, NO LESS.

    {sow_summary}

    {candidates_text}

    TESTER SELECTION CRITERIA:
    1. Testing expertise and methodologies
    2. Technology stack familiarity
    3. Domain/department experience
    4. Automation vs manual testing skills
    5. Availability and capacity (both percentage and weekly hours)
    6. Previous project success in similar environments
    7. Practice area experience that matches project requirements
    8. Higher proficiency levels (in parentheses) indicate stronger expertise and must be considered when evaluating skills

    ALLOCATION RULES:
    - CRITICAL: Check each candidate's "Weekly Hours Available" field carefully
    - Your allocation suggestion MUST be ≤ their available hours (never exceed!)
    - Consider testing phases but respect their capacity limits
    
    SKILLS RECOMMENDATION RULES:
    - Return ONLY technology names, tool names, or methodology keywords
    - NO explanations, descriptions, or full sentences
    - Examples: "Selenium", "Jest", "Cypress", "JMeter", "Postman", "API Testing"
    - NOT: "Learn automation testing frameworks for better coverage"

    EXPERIENCE RECOMMENDATION RULES:
    - Suggest ideal experience level in years for this specific project
    - Consider testing complexity, automation needs, technology stack, and project duration
    - Format as a number (e.g., 2 for 2 years, 3 for 3 years)

    STRICT INSTRUCTIONS:
    1. Recommend EXACTLY {n_testers} tester(s) - do not exceed this number
    2. RANK them in DESCENDING ORDER OF PREFERENCE (T1 = best choice, T2 = second best, etc.)
    3. For each recommendation:
    - Explain WHY they're perfect for testing this specific project
    - Point out any testing gaps or concerns
    - Justify why you picked this person over others
    - Consider their practice area experience and weekly availability
    - Suggest realistic hour allocation as a number (MUST NOT exceed their weekly available hours)
    - Recommend additional testing skills as simple keywords/technologies only
    - Suggest ideal experience level for this project type
    4. Focus on testing capabilities, automation skills, and quality assurance experience
    5. Consider their current project load and availability (both % and weekly hours)
    6. Keep the tone executive-summary style, focused and concise.

    Return your response as a JSON object with this structure:
    {{
        "testers": [
            {{
                "rank": "1",
                "name": "Tester Name",
                "designation": "designation of the tester selected",
                "match_score": 0.95,
                "reasons": [
                    "Extensive testing experience in similar technology",
                    "Strong automation testing capabilities",
                    "Available capacity matches project testing needs",
                    "Practice area experience aligns with project domain"
                ],
                "concerns": [
                    "Any potential testing challenges",
                    "Current availability/project commitments"
                ],
                "why_pick": "Clear justification for why this tester was selected over others",
                "allocation_suggestion": 18,
                "recommended_skills": [
                    "Selenium",
                    "Jest",
                    "API Testing",
                    "Performance Testing"
                ],
                "recommended_experience": 2.5,
                "recommendation": "Highly recommended / Recommended / Consider"
            }}
        ]
    }}
    """.strip()


def generate_developer_recommendation_prompt(sow_data, developer_candidates):
    """Generate AI prompt specifically for developer recommendations"""
    
    n_developers = int(os.getenv("N_DEVELOPERS", 4))
    
    sow_summary = f"""
    PROJECT REQUIREMENTS:
    - Project: {sow_data.get('project_name', 'Unknown')}
    - Technologies: {', '.join(sow_data.get('technology', []))}
    - Practice: {sow_data.get('practice', '')}
    - Category: {sow_data.get('category', '')}
    - Duration: {sow_data.get('start_date', '')} to {sow_data.get('end_date', '')}
    - Budget: {sow_data.get('budgeted_hours', '')}
    """

    candidates_text = "AVAILABLE DEVELOPERS:\n"
    for i, candidate in enumerate(developer_candidates, 1):
        meta = candidate['metadata']
        candidates_text += f"""
        D{i}. {meta['resource_name']}
        - Designation: {meta.get('designation', 'N/A')}
        - Skills: {meta.get('skills', 'N/A')}
        - Experience: {meta.get('experience_months', '0')} months
        - Level: {meta.get('designation_level', 'N/A')}
        - Department: {meta.get('department', 'N/A')}
        - Base Department: {meta.get('base_department', 'N/A')}
        - Hours Worked on Skills: {meta.get('hours_worked', '0')} hours
        - Availability: {meta.get('availability', '0')}%
        - Weekly Hours Available: {meta.get('hours_available_weekly', '0')} hours/week
        - Practice Areas: {meta.get('practices_with_hours', 'N/A')}
        """

    return f"""
    You are an expert consultant selecting SOFTWARE DEVELOPERS for a development project.

    *** CRITICAL REQUIREMENT ***
    You MUST recommend EXACTLY {n_developers} developer(s). NO MORE, NO LESS.

    {sow_summary}

    {candidates_text}

    DEVELOPER SELECTION CRITERIA:
    1. Technical skills match with required technologies
    2. Experience level and programming expertise
    3. Department and domain knowledge
    4. Availability and capacity (both percentage and weekly hours)
    5. Previous project success in similar tech stacks
    6. Problem-solving and development capabilities
    7. Practice area experience that matches project requirements
    8. Higher proficiency levels (in parentheses) indicate stronger expertise and must be considered when evaluating skills

    ALLOCATION RULES:
    - CRITICAL: Check each candidate's "Weekly Hours Available" field carefully
    - Your allocation suggestion MUST be ≤ their available hours (never exceed!)
    - Consider development phases but respect their capacity limits
    
    SKILLS RECOMMENDATION RULES:
    - Return ONLY technology names, tool names, or methodology keywords
    - NO explanations, descriptions, or full sentences
    - Examples: "React", "Node.js", "Docker", "GraphQL", "TypeScript"
    - NOT: "Learn modern JavaScript frameworks for better performance"

    EXPERIENCE RECOMMENDATION RULES:
    - Suggest ideal experience level in years for this specific project
    - Consider technical complexity, technology stack difficulty, and project scope
    - Format as a number (e.g., 1.5 for 1.5 years, 3 for 3 years)

    STRICT INSTRUCTIONS:
    1. Recommend EXACTLY {n_developers} developer(s) - do not exceed this number
    2. RANK them in DESCENDING ORDER OF PREFERENCE (D1 = best choice, D2 = second best, etc.)
    3. For each recommendation:
    - Explain WHY they're ideal for developing this specific project
    - Point out any technical gaps or concerns
    - Justify why you picked this person over others
    - Consider their practice area experience and weekly availability
    - Suggest realistic hour allocation as a number (MUST NOT exceed their weekly available hours)
    - Recommend additional technical skills as simple keywords/technologies only
    - Suggest ideal experience level for this project type
    4. Focus on technical capabilities, experience, and development skills
    5. Consider their current project load and availability (both % and weekly hours)
    6. Keep the tone executive-summary style, focused and concise.

    Return your response as a JSON object with this structure:
    {{
        "developers": [
            {{
                "rank": "1",
                "name": "Developer Name",
                "designation": "designation of the developer selected",
                "match_score": 0.95,
                "reasons": [
                    "Strong technical skills in required technologies",
                    "Proven experience in similar development projects",
                    "Available capacity aligns with project timeline",
                    "Practice area experience matches project domain"
                ],
                "concerns": [
                    "Any potential technical challenges",
                    "Current availability/project commitments"
                ],
                "why_pick": "Clear justification for why this developer was selected over others",
                "allocation_suggestion": 32,
                "recommended_skills": [
                    "React",
                    "Node.js",
                    "Docker",
                    "GraphQL"
                ],
                "recommended_experience": 2,
                "recommendation": "Highly recommended / Recommended / Consider"
            }}
        ]
    }}
    """.strip()

def generate_employee_search_query(sow_data):
    """Generate search query for employee matching"""
    technology = sow_data.get('technology', [])
    practice = sow_data.get('practice', '')
    category = sow_data.get('category', '')

    tech_str = ', '.join(technology) if isinstance(technology, list) else str(technology)

    return f"""
    Technologies: {tech_str}
    Practice: {practice}
    Category: {category}
    Skills needed: {tech_str}
    """.strip()


def generate_employee_text_summary(row, employee_type="employee"):
    """Generate text summary for employee vectorization - UPDATED FOR NEW SCHEMA"""
    name = str(row.get('ResourceName', 'Unknown'))
    designation = str(row.get('ResourceDesignationName', 'Unknown'))
    skills = str(row.get('ResourceSubSkillWithProficiency', ''))
    experience = str(row.get('ResourceExperienceInMonths', '0'))
    level = str(row.get('ResourceDesignationLevel', 'Unknown'))
    department = str(row.get('ResourceDepartmentName', 'Unknown'))
    base_department = str(row.get('ResourceBaseDepartment', 'Unknown'))
    hours_worked = str(row.get('HoursWorkedOnSkill', '0'))
    availability = str(row.get('ResourceAvailabilityInPercentage', '0'))
    hours_available_weekly = str(row.get('HoursAvailableOutOf40', '0'))  # New field
    practices_with_hours = str(row.get('ResourcePracticesWithHoursWorked', ''))  # New field

    # Customize the role description based on employee type
    if employee_type == "manager":
        role_desc = "Project Manager / Team Lead"
    elif employee_type == "tester":
        role_desc = "Quality Assurance / Software Tester"
    else:  # developer
        role_desc = "Software Developer"

    text = f"""
    {employee_type.title()}: {name}
    Role: {role_desc}
    Designation: {designation}
    Skills: {skills}
    Experience: {experience} months
    Level: {level}
    Department: {department}
    Base Department: {base_department}
    Hours Worked on Skills: {hours_worked} hours
    Availability: {availability}%
    Weekly Hours Available: {hours_available_weekly} hours/week
    Practice Areas with Hours: {practices_with_hours}
    """
    return text.strip()