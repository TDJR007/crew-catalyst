# FILE: utils/validator.py

import json
import re
import ast
from datetime import datetime
from difflib import get_close_matches

def load_db_values():
    with open("data/db_values.json") as f:
        return json.load(f)["data"]


def fuzzy_match(extracted_list, valid_list):
    matched = []
    for tech in extracted_list:
        match = get_close_matches(tech, valid_list, n=1, cutoff=0.7)
        if match:
            matched.append(match[0])
    return matched


def safe_parse_list(raw_response: str) -> list:
    """Safely parse LLM response into a Python list, handling various formats"""
    if not raw_response:
        return []
    
    # Try to find list-like content in the response
    list_patterns = [
        r'\[([^\]]+)\]',  # Standard list format
        r'```(?:python)?\s*(\[.*?\])\s*```',  # Code block format
        r'(\[.*?\])',  # Any bracket content
    ]
    
    for pattern in list_patterns:
        match = re.search(pattern, raw_response, re.DOTALL)
        if match:
            try:
                # Use ast.literal_eval instead of eval for security
                return ast.literal_eval(match.group(1) if len(match.groups()) == 1 else match.group(0))
            except (ValueError, SyntaxError):
                continue
    
    # Fallback: split by common delimiters and clean up
    items = re.split(r'[,\n;]', raw_response.strip())
    return [item.strip().strip('"\'') for item in items if item.strip()]


def clean_llm_response(response: str) -> str:
    """Clean LLM response to extract only the essential information"""
    if not response:
        return ""
    
    # Remove common LLM chattiness patterns
    patterns_to_remove = [
        r"^(Based on|According to|From|In|The|Looking at).*?[,:]",
        r"(the document|the context|the text|above|below|mentioned)",
        r"(appears to be|seems to be|is likely|probably)",
        r"\b(I|me|my|we|our)\b",
        r"^(Answer:|Response:|Result:)",
        r"\.$",  # Remove trailing period
    ]
    
    cleaned = response.strip()
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
    
    return cleaned


def extract_dates_from_context(context: str) -> dict:
    """Extract start and end dates from context using both regex and LLM"""
    dates = {"start_date": None, "end_date": None}
    
    # First, try regex pattern matching for common date formats
    date_patterns = [
        r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',  # MM/DD/YYYY or M/D/YYYY
        r'\b(\d{1,2})-(\d{1,2})-(\d{4})\b',  # MM-DD-YYYY
        r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b',  # YYYY-MM-DD
    ]
    
    found_dates = []
    for pattern in date_patterns:
        matches = re.findall(pattern, context)
        for match in matches:
            try:
                if len(match[0]) == 4:  # YYYY-MM-DD format
                    date_obj = datetime(int(match[0]), int(match[1]), int(match[2]))
                    formatted_date = f"{match[1].zfill(2)}/{match[2].zfill(2)}/{match[0]}"
                else:  # MM/DD/YYYY format
                    date_obj = datetime(int(match[2]), int(match[0]), int(match[1]))
                    formatted_date = f"{match[0].zfill(2)}/{match[1].zfill(2)}/{match[2]}"
                found_dates.append((date_obj, formatted_date))
            except ValueError:
                continue
    
    # Sort dates chronologically
    found_dates.sort(key=lambda x: x[0])
    
    if len(found_dates) >= 2:
        dates["start_date"] = found_dates[0][1]
        dates["end_date"] = found_dates[-1][1]
    elif len(found_dates) == 1:
        # Use LLM to determine if it's start or end date
        from rag.prompts import generate_date_prompt
        from rag.query_local_llm import query_local_llm
        
        prompt = generate_date_prompt("determine", context, found_dates[0][1])
        llm_response = query_local_llm(prompt).lower().strip()
        if "start" in llm_response:
            dates["start_date"] = found_dates[0][1]
        else:
            dates["end_date"] = found_dates[0][1]
    
    # If no dates found with regex, let LLM extract them
    if not any(dates.values()):
        from rag.prompts import generate_date_prompt
        from rag.query_local_llm import query_local_llm
        
        for date_type in ["start", "end"]:
            prompt = generate_date_prompt(date_type, context)
            llm_response = query_local_llm(prompt).strip()
            
            # Extract date from LLM response using regex
            date_match = re.search(r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b', llm_response)
            if date_match:
                dates[f"{date_type}_date"] = f"{date_match.group(1).zfill(2)}/{date_match.group(2).zfill(2)}/{date_match.group(3)}"
    
    return dates


def extract_json_from_text(text: str) -> dict:
    """
    Extracts and sanitizes likely JSON from messy LLM output.
    Handles smart quotes, embedded newlines inside strings, markdown, comments, and weird whitespace.
    Returns a Python dict or raises ValueError.
    """
    # Step 1: Normalize curly quotes and unicode garbage
    text = text.replace('“', '"').replace('”', '"')
    text = text.replace('‘', "'").replace('’', "'")
    text = text.replace("\u2013", "-").replace("\u2014", "-").replace("\xa0", " ")

    # Step 2: Strip markdown-style ```json blocks
    text = re.sub(r"```(?:json)?\n?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)

    # Step 3: Remove comments
    text = re.sub(r'//.*', '', text)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)

    # Step 4: Remove control characters except \n and \t
    text = re.sub(r'[\x00-\x08\x0B-\x1F\x7F]', '', text)

    # Step 5: Fix illegal newlines inside JSON string literals
    def clean_illegal_newlines(s: str) -> str:
        in_string = False
        escaped = False
        result = []

        for c in s:
            if c == '"' and not escaped:
                in_string = not in_string
            if c == '\n' and in_string:
                result.append(' ')
            else:
                result.append(c)
            escaped = (c == '\\' and not escaped)

        return ''.join(result)

    text = clean_illegal_newlines(text)

    # Step 6: Extract and parse the largest valid JSON-ish blob
    json_candidates = re.findall(r'(\{.*\})', text, re.DOTALL)
    json_candidates.sort(key=len, reverse=True)

    for candidate in json_candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    try:
        return json.loads(text.strip())
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to extract valid JSON: {e}\nOriginal text (truncated):\n{text[:300]}...")
