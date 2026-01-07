# rag/employee_recommender.py

import pandas as pd
import chromadb
from chromadb.config import Settings
import os
import json
from typing import List, Dict, Any
from rag.query_azure_openai import query_azure_openai
from rag.embedder import get_embedding_function  #  Don't break my embedder.py 🤣
from rag.prompts import (
    generate_manager_recommendation_prompt,
    generate_tester_recommendation_prompt,
    generate_developer_recommendation_prompt,
    generate_employee_search_query,
    generate_employee_text_summary
)
from utils.validator import extract_json_from_text
from dotenv import load_dotenv

load_dotenv()

# File paths from environment - updated for new structure
DEVELOPER_CSV_PATH = os.getenv("DEVELOPER_CSV_PATH", "Data/DeveloperDetails.csv")
MANAGER_CSV_PATH = os.getenv("MANAGER_CSV_PATH", "Data/ManagerDetails.csv")
TESTER_CSV_PATH = os.getenv("TESTER_CSV_PATH", "Data/TesterDetails.csv")

# Query limits for each employee type - configurable via env
N_MANAGERS_QUERY = int(os.getenv("N_MANAGERS_QUERY", 5))
N_TESTERS_QUERY = int(os.getenv("N_TESTERS_QUERY", 5))
N_DEVELOPERS_QUERY = int(os.getenv("N_DEVELOPERS_QUERY", 10))

class EmployeeRecommender:
    def __init__(self, 
                 developer_csv_path: str = DEVELOPER_CSV_PATH,
                 manager_csv_path: str = MANAGER_CSV_PATH,
                 tester_csv_path: str = TESTER_CSV_PATH,
                 chroma_path: str = "chroma_store"):
        
        self.developer_csv_path = developer_csv_path
        self.manager_csv_path = manager_csv_path
        self.tester_csv_path = tester_csv_path
        self.chroma_path = chroma_path
        
        # Processed file paths
        self.processed_developer_path = developer_csv_path.replace("DeveloperDetails.csv", "_developer_cache.csv") if developer_csv_path else None
        self.processed_manager_path = manager_csv_path.replace("ManagerDetails.csv", "_manager_cache.csv") if manager_csv_path else None
        self.processed_tester_path = tester_csv_path.replace("TesterDetails.csv", "_tester_cache.csv") if tester_csv_path else None
        
        # ChromaDB clients and collections
        self.client = None
        self.developer_collection = None
        self.manager_collection = None
        self.tester_collection = None
        
        # DataFrames
        self.developer_df = None
        self.manager_df = None
        self.tester_df = None
        
        self.embedding_function = get_embedding_function()  # Use our own embedder

    def preprocess_csv(self, csv_path: str, employee_type: str = "employee"):
        """Preprocess CSV with updated schema including new fields"""
        print(f"📂 Loading {employee_type} data from: {csv_path}")
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"❌ ERROR: {employee_type} file not found -> {csv_path}")
        
        df = pd.read_csv(csv_path)
        df.columns = [col.strip() for col in df.columns]
        
        # Drop rows with invalid or empty names
        df = df.dropna(subset=['ResourceName'])
        df = df[df['ResourceName'].str.strip() != '']
        
        # Remove duplicates by ResourceId (keeping last occurrence)
        df = df.drop_duplicates(subset=['ResourceId'], keep='last')
        
        # Updated required fields to include new schema columns
        required_fields = [
            'ResourceName', 'ResourceDesignationName', 'ResourceExperienceInMonths',
            'ResourceDesignationLevel', 'ResourceDepartmentName', 'ResourceBaseDepartment',
            'ResourceSubSkillWithProficiency', 'HoursWorkedOnSkill', 'ResourceAvailabilityInPercentage',
            'HoursAvailableOutOf40', 'ResourcePracticesWithHoursWorked'  # New fields added
        ]
        
        for field in required_fields:
            if field in df.columns:
                df[field] = df[field].fillna('').astype(str)
            else:
                df[field] = ''
        
        # Convert experience to numeric (handle non-numeric values)
        df['ResourceExperienceInMonths'] = pd.to_numeric(df['ResourceExperienceInMonths'], errors='coerce').fillna(0)
        
        # Convert availability percentage to numeric
        df['ResourceAvailabilityInPercentage'] = df['ResourceAvailabilityInPercentage'].str.replace('%', '').astype(str)
        df['ResourceAvailabilityInPercentage'] = pd.to_numeric(df['ResourceAvailabilityInPercentage'], errors='coerce').fillna(0)
        
        # Convert hours available to numeric
        df['HoursAvailableOutOf40'] = pd.to_numeric(df['HoursAvailableOutOf40'], errors='coerce').fillna(0)
        
        print(f"✅ {employee_type} data for {len(df)} unique employees processed")
        return df

    def preprocess_developer_csv(self):
        """Preprocess the developer CSV"""
        df = self.preprocess_csv(self.developer_csv_path, "developer")
        df.to_csv(self.processed_developer_path, index=False)
        return df

    def preprocess_manager_csv(self):
        """Preprocess the manager CSV"""
        df = self.preprocess_csv(self.manager_csv_path, "manager")
        df.to_csv(self.processed_manager_path, index=False)
        return df

    def preprocess_tester_csv(self):
        """Preprocess the tester CSV"""
        df = self.preprocess_csv(self.tester_csv_path, "tester")
        df.to_csv(self.processed_tester_path, index=False)
        return df

    def initialize_chroma(self):
        """Initialize ChromaDB with separate collections for each employee type"""
        print("🔧 Initializing ChromaDB for employee data...")
        self.client = chromadb.PersistentClient(path=self.chroma_path)
        
        # Initialize developer collection
        try:
            self.developer_collection = self.client.get_collection("developers")
            print("✅ Found existing developer collection")
        except:
            self.developer_collection = self.client.create_collection("developers")
            print("✅ Created new developer collection")
        
        # Initialize manager collection
        try:
            self.manager_collection = self.client.get_collection("managers")
            print("✅ Found existing manager collection")
        except:
            self.manager_collection = self.client.create_collection("managers")
            print("✅ Created new manager collection")
        
        # Initialize tester collection
        try:
            self.tester_collection = self.client.get_collection("testers")
            print("✅ Found existing tester collection")
        except:
            self.tester_collection = self.client.create_collection("testers")
            print("✅ Created new tester collection")

    def load_and_process_all_csvs(self):
        """Load and process all three CSV files"""
        print("📊 Loading all employee data from CSVs...")
        
        # Load developer data
        if (os.path.exists(self.processed_developer_path) and 
            os.path.exists(self.developer_csv_path) and
            os.path.getmtime(self.processed_developer_path) > os.path.getmtime(self.developer_csv_path)):
            print("📈 Using existing processed developer CSV...")
            self.developer_df = pd.read_csv(self.processed_developer_path)
        else:
            print("🔄 Processing developer CSV data...")
            self.developer_df = self.preprocess_developer_csv()
        
        # Load manager data
        if (os.path.exists(self.processed_manager_path) and 
            os.path.exists(self.manager_csv_path) and
            os.path.getmtime(self.processed_manager_path) > os.path.getmtime(self.manager_csv_path)):
            print("📈 Using existing processed manager CSV...")
            self.manager_df = pd.read_csv(self.processed_manager_path)
        else:
            print("🔄 Processing manager CSV data...")
            self.manager_df = self.preprocess_manager_csv()
        
        # Load tester data
        if (os.path.exists(self.processed_tester_path) and 
            os.path.exists(self.tester_csv_path) and
            os.path.getmtime(self.processed_tester_path) > os.path.getmtime(self.tester_csv_path)):
            print("📈 Using existing processed tester CSV...")
            self.tester_df = pd.read_csv(self.processed_tester_path)
        else:
            print("🔄 Processing tester CSV data...")
            self.tester_df = self.preprocess_tester_csv()
        
        print(f"📈 Loaded {len(self.developer_df)} developers, {len(self.manager_df)} managers, {len(self.tester_df)} testers")

    def create_employee_vectors(self):
        """Create vectors for all employee types"""
        if self.developer_df is None:
            self.load_and_process_all_csvs()

        self._create_developer_vectors()
        self._create_manager_vectors()
        self._create_tester_vectors()

    def _create_developer_vectors(self):
        """Create vectors for developers"""
        print("🔍 Creating developer vectors...")
        
        if self.developer_collection.count() > 0:
            print("📦 Developer vectors already exist, skipping creation...")
            return

        documents = []
        metadatas = []
        ids = []

        for idx, row in self.developer_df.iterrows():
            doc_text = generate_employee_text_summary(row, "developer")
            documents.append(doc_text)

            metadata = {
                'resource_id': str(row.get('ResourceId', '')),
                'resource_name': str(row.get('ResourceName', 'Unknown')),
                'designation': str(row.get('ResourceDesignationName', 'Unknown')),
                'experience_months': str(row.get('ResourceExperienceInMonths', '0')),
                'designation_level': str(row.get('ResourceDesignationLevel', 'Unknown')),
                'department': str(row.get('ResourceDepartmentName', 'Unknown')),
                'base_department': str(row.get('ResourceBaseDepartment', 'Unknown')),
                'skills': str(row.get('ResourceSubSkillWithProficiency', '')),
                'hours_worked': str(row.get('HoursWorkedOnSkill', '0')),
                'availability': str(row.get('ResourceAvailabilityInPercentage', '0')),
                'hours_available_weekly': str(row.get('HoursAvailableOutOf40', '0')),  # New field
                'practices_with_hours': str(row.get('ResourcePracticesWithHoursWorked', '')),  # New field
                'employee_type': 'developer'
            }
            metadatas.append(metadata)
            ids.append(f"developer_{row.get('ResourceId', idx)}")

        self._add_vectors_to_collection(self.developer_collection, documents, metadatas, ids, "developers")

    def _create_manager_vectors(self):
        """Create vectors for managers"""
        print("🔍 Creating manager vectors...")
        
        if self.manager_collection.count() > 0:
            print("📦 Manager vectors already exist, skipping creation...")
            return

        documents = []
        metadatas = []
        ids = []

        for idx, row in self.manager_df.iterrows():
            doc_text = generate_employee_text_summary(row, "manager")
            documents.append(doc_text)

            metadata = {
                'resource_id': str(row.get('ResourceId', '')),
                'resource_name': str(row.get('ResourceName', 'Unknown')),
                'designation': str(row.get('ResourceDesignationName', 'Unknown')),
                'experience_months': str(row.get('ResourceExperienceInMonths', '0')),
                'designation_level': str(row.get('ResourceDesignationLevel', 'Unknown')),
                'department': str(row.get('ResourceDepartmentName', 'Unknown')),
                'base_department': str(row.get('ResourceBaseDepartment', 'Unknown')),
                'skills': str(row.get('ResourceSubSkillWithProficiency', '')),
                'hours_worked': str(row.get('HoursWorkedOnSkill', '0')),
                'availability': str(row.get('ResourceAvailabilityInPercentage', '0')),
                'hours_available_weekly': str(row.get('HoursAvailableOutOf40', '0')),  # New field
                'practices_with_hours': str(row.get('ResourcePracticesWithHoursWorked', '')),  # New field
                'employee_type': 'manager'
            }
            metadatas.append(metadata)
            ids.append(f"manager_{row.get('ResourceId', idx)}")

        self._add_vectors_to_collection(self.manager_collection, documents, metadatas, ids, "managers")

    def _create_tester_vectors(self):
        """Create vectors for testers"""
        print("🔍 Creating tester vectors...")
        
        if self.tester_collection.count() > 0:
            print("📦 Tester vectors already exist, skipping creation...")
            return

        documents = []
        metadatas = []
        ids = []

        for idx, row in self.tester_df.iterrows():
            doc_text = generate_employee_text_summary(row, "tester")
            documents.append(doc_text)

            metadata = {
                'resource_id': str(row.get('ResourceId', '')),
                'resource_name': str(row.get('ResourceName', 'Unknown')),
                'designation': str(row.get('ResourceDesignationName', 'Unknown')),
                'experience_months': str(row.get('ResourceExperienceInMonths', '0')),
                'designation_level': str(row.get('ResourceDesignationLevel', 'Unknown')),
                'department': str(row.get('ResourceDepartmentName', 'Unknown')),
                'base_department': str(row.get('ResourceBaseDepartment', 'Unknown')),
                'skills': str(row.get('ResourceSubSkillWithProficiency', '')),
                'hours_worked': str(row.get('HoursWorkedOnSkill', '0')),
                'availability': str(row.get('ResourceAvailabilityInPercentage', '0')),
                'hours_available_weekly': str(row.get('HoursAvailableOutOf40', '0')),  # New field
                'practices_with_hours': str(row.get('ResourcePracticesWithHoursWorked', '')),  # New field
                'employee_type': 'tester'
            }
            metadatas.append(metadata)
            ids.append(f"tester_{row.get('ResourceId', idx)}")

        self._add_vectors_to_collection(self.tester_collection, documents, metadatas, ids, "testers")

    def _add_vectors_to_collection(self, collection, documents, metadatas, ids, collection_type):
        """Helper method to add vectors to a collection in batches"""
        embeddings = self.embedding_function(documents)
        
        MAX_BATCH = 5000
        total = len(documents)
        for i in range(0, total, MAX_BATCH):
            end = min(i + MAX_BATCH, total)
            print(f"➡️ Adding {collection_type} batch {i//MAX_BATCH + 1} to vector db")
            collection.add(
                documents=documents[i:end],
                metadatas=metadatas[i:end],
                ids=ids[i:end],
                embeddings=embeddings[i:end]
            )
        
        print(f"✅ Created vectors for {len(documents)} {collection_type}")

    def search_employees_by_type(self, sow_data: Dict[str, Any], employee_type: str, n_results: int = 5) -> List[Dict]:
        """Search for employees of a specific type"""
        print(f"🔎 Searching for {employee_type}s matching SOW requirements...")
        
        search_query = generate_employee_search_query(sow_data)
        print(f"🔸 Search query for {employee_type}s: {search_query}")

        # Select appropriate collection
        if employee_type == 'manager':
            collection = self.manager_collection
        elif employee_type == 'tester':
            collection = self.tester_collection
        else:
            collection = self.developer_collection

        # Get embedding and query
        embedding = self.embedding_function([search_query])[0]
        results = collection.query(
            query_embeddings=[embedding],
            n_results=n_results
        )

        candidates = []
        for i in range(len(results['ids'][0])):
            candidate = {
                'id': results['ids'][0][i],
                'similarity_score': 1 - results['distances'][0][i],
                'metadata': results['metadatas'][0][i],
                'document': results['documents'][0][i],
                'employee_type': employee_type
            }
            candidates.append(candidate)

        print(f"✅ Retrieved {len(candidates)} candidate {employee_type}s")
        return candidates

    def search_all_employees(self, sow_data: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Search for all employee types based on SOW requirements"""
        print("🔍 Searching for all employee types...")
        
        # Use configurable query limits
        managers = self.search_employees_by_type(sow_data, 'manager', N_MANAGERS_QUERY)
        testers = self.search_employees_by_type(sow_data, 'tester', N_TESTERS_QUERY)
        developers = self.search_employees_by_type(sow_data, 'developer', N_DEVELOPERS_QUERY)
        
        return {
            'managers': managers,
            'testers': testers,
            'developers': developers
        }

    def get_manager_recommendations(self, sow_data: Dict[str, Any], manager_candidates: List[Dict]) -> Dict:
        """Get AI recommendations specifically for managers"""
        print("🤖 Getting AI recommendations for managers...")
        
        prompt = generate_manager_recommendation_prompt(sow_data, manager_candidates)
        response = query_azure_openai(prompt)

        try:
            result = extract_json_from_text(response)
            return result
        
        except ValueError as e:
            print(f"⚠️ Manager JSON extraction failed: {e}")
            return {"managers": []}

    def get_tester_recommendations(self, sow_data: Dict[str, Any], tester_candidates: List[Dict]) -> Dict:
        """Get AI recommendations specifically for testers"""
        print("🤖 Getting AI recommendations for testers...")
        
        prompt = generate_tester_recommendation_prompt(sow_data, tester_candidates)
        response = query_azure_openai(prompt)

        try:
            result = extract_json_from_text(response)
            return result
        
        except ValueError as e:
            print(f"⚠️ Tester JSON extraction failed: {e}")
            return {"testers": []}

    def get_developer_recommendations(self, sow_data: Dict[str, Any], developer_candidates: List[Dict]) -> Dict:
        """Get AI recommendations specifically for developers"""
        print("🤖 Getting AI recommendations for developers...")
        
        prompt = generate_developer_recommendation_prompt(sow_data, developer_candidates)
        response = query_azure_openai(prompt)

        try:
            result = extract_json_from_text(response)
            return result
        
        except ValueError as e:
            print(f"⚠️ Developer JSON extraction failed: {e}")
            return {"developers": []}

    def combine_recommendations(self, manager_recs: Dict, tester_recs: Dict, developer_recs: Dict) -> Dict:
        """Combine all recommendations into a single structured response"""
        print("🔗 Combining all employee recommendations...")
        
        # Extract individual recommendations
        managers = manager_recs.get('managers', [])
        testers = tester_recs.get('testers', [])
        developers = developer_recs.get('developers', [])
        
        # Combine all recommendations into one list
        all_recommendations = []
        all_recommendations.extend(managers)
        all_recommendations.extend(testers)
        all_recommendations.extend(developers)
        
        # Calculate team composition
        team_composition = {
            "managers": len(managers),
            "testers": len(testers),
            "developers": len(developers),
            "total": len(all_recommendations),
            "rationale": f"Selected {len(managers)} manager(s) for project leadership, {len(testers)} tester(s) for quality assurance, and {len(developers)} developer(s) for implementation."
        }
        
        return {
            "recommendations": all_recommendations,
            "team_composition": team_composition,
            "breakdown": {
                "managers": managers,
                "testers": testers,
                "developers": developers
            }
        }

    def get_ai_recommendations(self, sow_data: Dict[str, Any], all_candidates: Dict[str, List[Dict]]) -> Dict:
        """Get AI recommendations for all employee types using separate prompts"""
        print("🤖 Getting AI recommendations for all employee types (separate prompts)...")
        
        # Get recommendations for each employee type separately
        manager_recs = self.get_manager_recommendations(sow_data, all_candidates['managers'])
        tester_recs = self.get_tester_recommendations(sow_data, all_candidates['testers'])
        developer_recs = self.get_developer_recommendations(sow_data, all_candidates['developers'])
        
        # Combine all recommendations
        combined_recommendations = self.combine_recommendations(manager_recs, tester_recs, developer_recs)
        
        print(f"✅ Generated {len(combined_recommendations['recommendations'])} total recommendations")
        return combined_recommendations
    
    def recommend_employees(self, sow_data: Dict[str, Any]) -> Dict:
        """Main method to recommend employees from all types"""
        print("🎯 Starting comprehensive employee recommendation process...")
        
        if self.client is None:
            self.initialize_chroma()
            self.create_employee_vectors()

        all_candidates = self.search_all_employees(sow_data)
        recommendations = self.get_ai_recommendations(sow_data, all_candidates)

        total_candidates = len(all_candidates['managers']) + len(all_candidates['testers']) + len(all_candidates['developers'])

        return {
            'sow_data': sow_data,
            'candidates_found': {
                'managers': len(all_candidates['managers']),
                'testers': len(all_candidates['testers']),
                'developers': len(all_candidates['developers']),
                'total': total_candidates
            },
            'recommendations': recommendations,
            'raw_candidates': all_candidates
        }

# Utility function
def get_employee_recommendations(sow_data: Dict[str, Any]) -> Dict:
    """Get recommendations for all employee types"""
    recommender = EmployeeRecommender()
    return recommender.recommend_employees(sow_data)