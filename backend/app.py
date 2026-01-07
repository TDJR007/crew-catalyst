#app.py (flask app with API key authentication)
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask_httpauth import HTTPTokenAuth
import os
from werkzeug.utils import secure_filename
from rag.pipeline import extract_fields_from_pdf
from rag.employee_recommender import get_employee_recommendations
from flask_cors import CORS
import uuid

load_dotenv()

# Point Flask to the frontend build
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "../frontend/dist/")

app = Flask(__name__)

CORS(app)
auth = HTTPTokenAuth(scheme='Bearer')

UPLOAD_FOLDER = "data/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
N_RECOMMENDATIONS = int(os.getenv("N_RECOMMENDATIONS", 5))

# Load single API key from environment
API_KEY = os.getenv('API_KEY')
if not API_KEY:
    raise ValueError("API_KEY not found in environment variables. Please check your .env file.")

@auth.verify_token
def verify_token(token):
    if not token:
        return None
    return 'user' if token == API_KEY else None

@auth.error_handler
def auth_error(status):
    return jsonify({'error': 'Invalid or missing API key'}), status

# Serve frontend static files (catch-all route)
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    full_path = os.path.join(FRONTEND_DIST, path)
    if path != "" and os.path.exists(full_path):
        return send_from_directory(FRONTEND_DIST, path)
    else:
        # fallback to index.html for SPA routing
        return send_from_directory(FRONTEND_DIST, "index.html")

@app.route("/extract_sow", methods=["POST"])
@auth.login_required
def extract_sow():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        result = extract_fields_from_pdf(filepath)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/recommend_employees_clean", methods=["POST"])
@auth.login_required
def recommend_employees_clean():
    """
    Clean employee recommendations endpoint for UI consumption.
    Takes SOW JSON data, returns only clean recommendation data.
    Perfect for the underpaid frontend guy (who is also me!).
    """
    try:
        sow_data = request.get_json()

        if not sow_data:
            return jsonify({"error": "No SOW data provided"}), 400

        # Get full employee recommendations
        full_recommendations = get_employee_recommendations(sow_data)

        # Clean up the response - recommendations only
        clean_response = {
            "recommendations": [],
            "summary": {
                "initial_shortlisted_candidates": full_recommendations.get("candidates_found", 0),
                "status": "success"
            },
            # Add SOW data to the response
            "sow_data": sow_data
        }

        # Extract clean recommendations from the AI response
        ai_recommendations = full_recommendations.get("recommendations", {})

        if isinstance(ai_recommendations, dict) and "recommendations" in ai_recommendations:
            # If AI returned proper JSON structure
            for rec in ai_recommendations["recommendations"][:N_RECOMMENDATIONS]:  
                clean_rec = {
                    "rank": rec.get("rank", 0),
                    "name": rec.get("name", "Unknown"),
                    "designation": rec.get("designation", "Unknown"),
                    "match_score": round(rec.get("match_score", 0), 2),
                    "recommendation_level": rec.get("recommendation", "Consider"),
                    "key_strengths": rec.get("reasons", [])[:3],  # Top 3 reasons only
                    "concerns": rec.get("concerns", [])[:2],      # Top 2 concerns only
                    "why_pick": rec.get("why_pick", "No justification provided."),
                    "allocation_suggestion": rec.get("allocation_suggestion", 0),
                    "recommended_skills": rec.get("recommended_skills", []),  # Now using consistent field name
                    "recommended_experience": rec.get("recommended_experience", 0)  # Added new field
                }
                clean_response["recommendations"].append(clean_rec)
        else:
            # Fallback: extract from raw candidates if AI parsing failed
            raw_candidates = full_recommendations.get("raw_candidates", [])[:5]
            for i, candidate in enumerate(raw_candidates, 1):
                meta = candidate.get("metadata", {})
                clean_rec = {
                    "rank": i,
                    "name": meta.get("resource_name", "Unknown"),
                    "designation": meta.get("designation", "Unknown"),
                    "match_score": round(candidate.get("similarity_score", 0), 2),
                    "recommendation_level": "Consider",
                    "key_strengths": [
                        f"Skills: {meta.get('skills', 'Not specified')}",
                        f"Experience: {meta.get('experience_months', '0')} months",
                        f"Capacity: {meta.get('capacity', '0')} hours"
                    ],
                    "concerns": ["Check availability"],
                    "why_pick": "Fallback recommendation based on vector similarity.",
                    "allocation_suggestion": int(meta.get('hours_available_weekly', 0)),
                    "recommended_skills": [],
                    "recommended_experience": 0  # Added fallback for new field
                }
                clean_response["recommendations"].append(clean_rec)

        return jsonify(clean_response)

    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "failed",
            "recommendations": [],
            "summary": {
                "total_candidates_analyzed": 0,
                "status": "error"
            },
            "sow_data": {}  # Include empty SOW data even in error case
        }), 500
    
# Health check endpoint - no auth required for monitoring
@app.route("/health", methods=["GET"])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy", "message": "Employee recommendation API is running!"})

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)