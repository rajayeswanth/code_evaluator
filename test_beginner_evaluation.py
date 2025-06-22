#!/usr/bin/env python3
"""
Test script for the new beginner-friendly evaluation system
"""

import requests
import json
import time

# Test data
test_data = {
    "student_id": "test_student_001",
    "lab_name": "Lab3",
    "input": {
        "Lab3A.py": """
amount_owed = int(input("Enter amount owed: "))
apr = float(input("Enter APR: "))
minimum_payment = amount_owed * 0.02
print(f"Minimum payment: ${minimum_payment}")
""",
        "Lab3B.py": """
course1_hours = int(input("Enter course 1 hours: "))
course1_grade = int(input("Enter course 1 grade: "))
course2_hours = int(input("Enter course 2 hours: "))
course2_grade = int(input("Enter course 2 grade: "))

total_hours = course1_hours + course2_hours
total_points = (course1_hours * course1_grade) + (course2_hours * course2_grade)
gpa = total_points / total_hours
print(f"GPA: {gpa:.2f}")
""",
        "Lab3C.py": """
cooking_time = int(input("Enter cooking time in minutes: "))
print(f"Cooking time: {cooking_time} minutes")
"""
    }
}

def test_evaluation():
    """Test the evaluation endpoint"""
    print("🧪 Testing Beginner-Friendly Evaluation System")
    print("=" * 50)
    
    # API endpoint
    url = "http://localhost:8000/api/evaluate/"
    
    try:
        print("📤 Sending evaluation request...")
        start_time = time.time()
        
        response = requests.post(url, json=test_data, timeout=60)
        
        end_time = time.time()
        print(f"⏱️  Response time: {end_time - start_time:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Evaluation successful!")
            print("\n📊 Results:")
            print(f"Evaluation ID: {result.get('evaluation_id')}")
            print(f"Session ID: {result.get('session_id')}")
            print(f"Total files evaluated: {result.get('total_files_evaluated')}")
            print(f"Total points lost: {result.get('total_points_lost')}")
            print(f"Evaluation time: {result.get('total_evaluation_time_seconds', 0):.2f} seconds")
            
            print("\n📝 Lab Feedback:")
            lab_feedback = result.get('lab_feedback', {})
            for filename, feedback in lab_feedback.items():
                print(f"\n{filename}:")
                if isinstance(feedback, dict):
                    # New JSON format
                    for issue, points in feedback.items():
                        print(f"  • {issue}: {points}")
                else:
                    # Old format (should not happen with new system)
                    print(f"  {feedback}")
            
            print(f"\n📋 Overall Feedback:")
            print(f"  {result.get('overall_feedback', 'No feedback')}")
            
            # Check cache insights
            cache_insights = result.get('cache_insights', {})
            if cache_insights:
                print(f"\n💾 Cache: {'HIT' if cache_insights.get('cache_hit') else 'MISS'}")
            
        else:
            print(f"❌ Evaluation failed with status {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - evaluation took too long")
    except requests.exceptions.ConnectionError:
        print("🔌 Connection error - make sure the server is running")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    test_evaluation() 