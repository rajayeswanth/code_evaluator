#!/usr/bin/env python3
"""
Mock test for suggestions process without OpenAI API
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'code_grader_api.settings')
django.setup()

from evaluation.models import Evaluation, Student

def mock_suggestions_test():
    """Mock test showing what suggestions would do"""
    print("=== MOCK SUGGESTIONS TEST ===")
    
    # Get a student with evaluations
    student = Student.objects.first()
    if not student:
        print("No students found!")
        return
    
    print(f"Testing with student: {student.name} ({student.student_id})")
    
    # Get their evaluations
    evaluations = Evaluation.objects.filter(student=student)
    print(f"Found {evaluations.count()} evaluations")
    
    # Show what feedback we have
    feedback_texts = []
    for eval in evaluations[:3]:  # First 3 evaluations
        if eval.feedback:
            feedback_text = str(eval.feedback)
            feedback_texts.append(feedback_text)
            print(f"\nLab {eval.lab_name}: {feedback_text}")
    
    if feedback_texts:
        combined_feedback = " ".join(feedback_texts)
        print(f"\n=== COMBINED FEEDBACK ===")
        print(combined_feedback)
        
        print(f"\n=== WHAT THE SYSTEM WOULD DO ===")
        print("1. LLM would extract 3 keywords from this feedback")
        print("   Expected keywords: ['calculation', 'variables', 'output']")
        
        print("\n2. FAISS would search for materials using these keywords")
        print("   Search query: 'calculation variables output'")
        
        print("\n3. LLM would generate suggestions like:")
        print("   - 'for calculation → refer math_basics.pdf'")
        print("   - 'for variables → refer variable_tutorial.pdf'")
        print("   - 'for output → refer io_examples.pdf'")
        
        print(f"\n=== CURRENT ISSUE ===")
        print("OpenAI API key not set, so LLM calls fail")
        print("Need to set OPENAI_API_KEY environment variable")

if __name__ == "__main__":
    mock_suggestions_test() 