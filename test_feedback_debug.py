#!/usr/bin/env python3
"""
Test script to debug feedback data in evaluations
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'code_grader_api.settings')
django.setup()

from evaluation.models import Evaluation, Student

def debug_feedback_data():
    """Debug what feedback data is actually stored"""
    print("=== DEBUGGING FEEDBACK DATA ===")
    
    # Get all evaluations
    evaluations = Evaluation.objects.all()
    print(f"Total evaluations: {evaluations.count()}")
    
    if evaluations.exists():
        # Look at first few evaluations
        for i, eval in enumerate(evaluations[:3]):
            print(f"\n--- Evaluation {i+1} ---")
            print(f"ID: {eval.id}")
            print(f"Student: {eval.student.name} ({eval.student.student_id})")
            print(f"Lab: {eval.lab_name}")
            print(f"Feedback type: {type(eval.feedback)}")
            print(f"Feedback content: {repr(eval.feedback)}")
            print(f"Feedback length: {len(str(eval.feedback)) if eval.feedback else 0}")
            
            if eval.feedback:
                feedback_str = str(eval.feedback)
                print(f"First 200 chars: {feedback_str[:200]}")
                
                # Try to parse as JSON
                try:
                    import json
                    feedback_json = json.loads(feedback_str)
                    print(f"JSON parse successful: {type(feedback_json)}")
                    if isinstance(feedback_json, dict):
                        print(f"JSON keys: {list(feedback_json.keys())}")
                        if 'summary' in feedback_json:
                            print(f"Summary: {feedback_json['summary'][:100]}...")
                except json.JSONDecodeError:
                    print("Not valid JSON - plain text")
            else:
                print("No feedback content")
    
    # Check specific student if exists
    try:
        student = Student.objects.first()
        if student:
            print(f"\n--- Checking student {student.student_id} ---")
            student_evals = Evaluation.objects.filter(student=student)
            print(f"Student evaluations: {student_evals.count()}")
            
            for eval in student_evals:
                print(f"Lab: {eval.lab_name}, Feedback: {str(eval.feedback)[:100] if eval.feedback else 'None'}...")
    except Exception as e:
        print(f"Error checking student: {e}")

if __name__ == "__main__":
    debug_feedback_data() 