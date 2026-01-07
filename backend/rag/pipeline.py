# rag/pipeline.py
import os
import re
import json
from datetime import datetime
from chromadb import PersistentClient
from dotenv import load_dotenv
from utils.pdf_utils import extract_text_from_pdf, chunk_text, extract_first_n_pages
from utils.validator import load_db_values, fuzzy_match, safe_parse_list, clean_llm_response, extract_dates_from_context
#from rag.prompts import generate_billing_type_prompt, generate_client_prompt, generate_prompt, generate_date_prompt, generate_status_prompt, generate_tech_prompt, generate_practice_prompt, generate_category_prompt, generate_start_date_prompt, generate_end_date_prompt
from rag.prompts import generate_billing_type_prompt, generate_client_prompt, generate_prompt, generate_status_prompt, generate_tech_prompt, generate_practice_prompt, generate_category_prompt, generate_start_date_prompt, generate_end_date_prompt
from rag.query_azure_openai import query_azure_openai
from rag.embedder import get_embedding_function

load_dotenv()
TECHNOLOGY_PAGES = int(os.getenv("TECHNOLOGY_PAGES", 5))
DATE_CONTEXT_PAGES = int(os.getenv("DATE_CONTEXT_PAGES", 3))

embedding_function = get_embedding_function()

FIELDS = ["Project Name", "Practice", "Technology", "Category", "Manager", "Client", "Partner",
          "Billing Type", "Status", "Budgeted Hours", "Start date", "End Date"]

DATE_FIELDS = {"Start date", "End Date"}
FUZZY_MATCH_FIELDS = {"Practice", "Technology"}

def extract_dates_from_chunks(chroma_collection, doc_id: str) -> dict:
    """Extract start and end dates from document chunks using specialized prompts"""
    dates = {"start_date": None, "end_date": None}
    
    # Define date-related keywords for better chunk retrieval
    date_keywords = {
        "start_date": ["start date", "project start", "commencement", "begin", "kick-off", "initiation", "launch", "January", "November"],
        "end_date": ["end date", "completion", "delivery", "final", "conclusion", "project end", "deadline", "due date", "November", "January"]
    }
    
    for date_type, keywords in date_keywords.items():
        # Query for chunks most likely to contain date information
        query_text = f"{' '.join(keywords)} deliverables timelines schedule milestone"
        
        query_result = chroma_collection.query(
            query_texts=[query_text], 
            n_results=5,
            where={"doc_id": doc_id}
        )
        
        if query_result["documents"] and query_result["documents"][0]:
            context_chunks = query_result["documents"][0]
            context = "\n---\n".join(context_chunks)
            
            # Use specialized prompts for each date type
            if date_type == "start_date":
                prompt = generate_start_date_prompt(context)
            else:  # end_date
                prompt = generate_end_date_prompt(context)
            
            raw_response = query_azure_openai(prompt)
            cleaned_date = clean_llm_response(raw_response)
            
            if cleaned_date:
                dates[date_type] = cleaned_date
    
    return dates

def extract_client_from_chunks(chroma_collection, doc_id: str) -> str:
    """
    Extract client information from document chunks using targeted queries
    with multiple synonyms and context-aware retrieval
    """
    
    # Primary client-related keywords (most common and effective)
    primary_keywords = [
        "client", "customer", "organization", "company", "corporation", 
        "enterprise", "contracting party", "service recipient", "sponsor"
    ]
    
    # Secondary context keywords for better retrieval
    context_keywords = ["contact information", "stakeholder", "agreement", "contract"]
    
    # Create a balanced query string (optimized for embedding performance)
    query_text = f"{' '.join(primary_keywords)} {' '.join(context_keywords)}"
    
    # Query for chunks most likely to contain client information
    query_result = chroma_collection.query(
        query_texts=[query_text], 
        n_results=5,  
        where={"doc_id": doc_id}
    )
    
    client_info = ""
    
    if query_result["documents"] and query_result["documents"][0]:
        context_chunks = query_result["documents"][0]
        context = "\n---\n".join(context_chunks)
        
        # Generate focused prompt for client extraction
        prompt = generate_client_prompt(context)
        
        # Query the local LLM
        raw_response = query_azure_openai(prompt)
        client_info = clean_llm_response(raw_response)
    
    return client_info or ""





def extract_fields_from_pdf(file_path: str) -> dict:
    """Extract all fields from PDF with enhanced error handling and specialized logic"""
    text = extract_text_from_pdf(file_path)
    chunks = chunk_text(text)
    db_values = load_db_values()

    client = PersistentClient(path=os.getenv("CHROMA_DB_PATH", "./chroma_store"))
    chroma_collection = client.get_or_create_collection(
        name="sow_docs",
        embedding_function=embedding_function
    )

    doc_id = os.path.basename(file_path)
    chunked_ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
    
    metadatas = [{"doc_id": doc_id, "chunk_index": i} for i in range(len(chunks))]
    existing_ids = chroma_collection.get(include=["metadatas"])["ids"]

    if chunked_ids[0] not in existing_ids:
        chroma_collection.add(
            documents=chunks, 
            ids=chunked_ids,
            metadatas=metadatas
        )

    results = {}

    # Handle dates first using targeted chunk queries
    extracted_dates = extract_dates_from_chunks(chroma_collection, doc_id)
    results["start_date"] = extracted_dates["start_date"] or ""
    results["end_date"] = extracted_dates["end_date"] or ""

    # Handle client extraction with specialized logic
    results["client"] = extract_client_from_chunks(chroma_collection, doc_id)

    # Get context from first n pages for Technology and Practice (single call to avoid repeated file reads)
    early_context = extract_first_n_pages(file_path, TECHNOLOGY_PAGES)
    
    for field in FIELDS:
        match_field = field.lower().replace(" ", "_")
        
        # Skip dates and client as they're already processed
        if field in DATE_FIELDS or field == "Client":
            continue
            
        valid_list = db_values.get(match_field, [])

        # SPECIAL HANDLING FOR TECHNOLOGY
        if field == "Technology":
            prompt = generate_tech_prompt(early_context)
            raw_response = query_azure_openai(prompt) # Make sure the LLM's context length is high enough or you'll get an empty list
            tech_list = safe_parse_list(raw_response)
            results[match_field] = fuzzy_match(tech_list, valid_list) if valid_list else tech_list
            #results[match_field] = tech_list
            continue

        # SPECIAL HANDLING FOR PRACTICE (with fuzzy matching)
        if field == "Practice":
            prompt = generate_practice_prompt(early_context, valid_list)
            raw_response = query_azure_openai(prompt)
            practice_list = safe_parse_list(raw_response) if '[' in raw_response else [clean_llm_response(raw_response)]
            results[match_field] = fuzzy_match(practice_list, valid_list)[0] if valid_list else practice_list[0] if practice_list else ""
            #results[match_field] = practice_list
            continue

        # SPECIAL HANDLING FOR PROJECT NAME
        if field == "Project Name":
            # Use first page for project name (reuse early_context if it's from 1+ pages)
            project_context = extract_first_n_pages(file_path, 2)
            prompt = generate_prompt(field, project_context)
            raw_response = query_azure_openai(prompt)
            results[match_field] = clean_llm_response(raw_response)
            continue

        # SPECIAL HANDLING FOR CATEGORY
        if field == "Category":
            prompt = generate_category_prompt(early_context)
            raw_response = query_azure_openai(prompt)
            results[match_field] = clean_llm_response(raw_response)
            continue

        # REGULAR RAG FLOW WITH DOCUMENT-SPECIFIC FILTERING
        query_text = f"{field}. Possible values: {', '.join(valid_list)}" if valid_list else field
        
        query_result = chroma_collection.query(
            query_texts=[query_text], 
            n_results=5,
            where={"doc_id": doc_id} #Prevent Cross talk between documents
        )
        
        context_chunks = query_result["documents"][0]
        context = "\n---\n".join(context_chunks)

        # Field-specific prompt handling
        
        if field == "Status":
            prompt = generate_status_prompt(context)
        elif field == "Billing Type":
            prompt = generate_billing_type_prompt(context)
        else:
            prompt = generate_prompt(field, context)


        raw_response = query_azure_openai(prompt)
        
        results[match_field] = clean_llm_response(raw_response)

    # Convert to properly formatted JSON structure
    formatted_results = {}
    for field in FIELDS:
        match_field = field.lower().replace(" ", "_")
        formatted_results[field] = results.get(match_field, "")
    
    return formatted_results