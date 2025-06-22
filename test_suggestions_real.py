#!/usr/bin/env python3
"""
Test suggestions with real feedback data
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'code_grader_api.settings')
django.setup()

from evaluation.models import Evaluation, Student
from analytics_service.vector_service import vector_service

def test_suggestions_with_real_data():
    """Test suggestions with real feedback data"""
    print("=== TESTING SUGGESTIONS WITH REAL DATA ===")
    
    # Get a student with evaluations
    student = Student.objects.first()
    if not student:
        print("No students found!")
        return
    
    print(f"Testing with student: {student.name} ({student.student_id})")
    
    # Get their evaluations
    evaluations = Evaluation.objects.filter(student=student)
    print(f"Found {evaluations.count()} evaluations")
    
    # Test with first evaluation that has substantial feedback
    for eval in evaluations:
        if eval.feedback and len(str(eval.feedback)) > 20:
            print(f"\n--- Testing with Lab {eval.lab_name} ---")
            print(f"Feedback: {eval.feedback}")
            
            # Test keyword extraction
            keywords = vector_service._extract_keywords_from_feedback(str(eval.feedback))
            print(f"Extracted keywords: {keywords}")
            
            # Test full suggestions
            suggestions = vector_service.get_suggestions_for_feedback(str(eval.feedback), 3)
            print(f"Suggestions: {suggestions}")
            
            break
    
    # Test with combined feedback from multiple evaluations
    print(f"\n--- Testing with combined feedback ---")
    feedback_texts = []
    for eval in evaluations[:3]:  # First 3 evaluations
        if eval.feedback:
            feedback_texts.append(str(eval.feedback))
    
    if feedback_texts:
        combined_feedback = " ".join(feedback_texts)
        print(f"Combined feedback: {combined_feedback[:200]}...")
        
        keywords = vector_service._extract_keywords_from_feedback(combined_feedback)
        print(f"Extracted keywords: {keywords}")
        
        suggestions = vector_service.get_suggestions_for_feedback(combined_feedback, 3)
        print(f"Suggestions: {suggestions}")

if __name__ == "__main__":
    test_suggestions_with_real_data() 