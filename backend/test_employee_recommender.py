# test_employee_recommender.py
import json
from rag.employee_recommender import get_employee_recommendations

def test_recommendation_system():
    """Test the employee recommendation system"""
    
    # Sample SOW data (from your example)
    sample_sow = {
        "billing_type": "time and material",  # matches Horizon JSON
        "budgeted_hours": "250 hours per month",
        "category": "Support",  # valid Horizon category
        "client": "The Client",
        "end_date": "2026-06-30",
        "manager": "Mallory Sterling",
        "partner": "Horizon AI Solutions",
        "practice": "Custom Software Development",  # Horizon-approved practice
        "project_name": "AI-Powered Analytics Platform",
        "start_date": "2026-01-01",
        "status": "In progress",  # valid Horizon status
        "technology": [
            "Python",
            "PyTorch",
            "Azure",
            "Azure DevOps",
            "Docker",
            "Kafka",
            "Elastic Search"
        ]
    }

    print("🧪 Testing Employee Recommendation System...")
    print(f"📋 SOW Data: {json.dumps(sample_sow, indent=2)}")
    
    try:
        # Get recommendations
        result = get_employee_recommendations(sample_sow)
        
        print("\n✅ SUCCESS! Recommendations received:")
        print(json.dumps(result, indent=2, default=str))
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_recommendation_system()
    if success:
        print("\n🎉 All tests passed! Your system is ready to rock!")
    else:
        print("\n💥 Tests failed. Check the error messages above.")
