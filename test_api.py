#!/usr/bin/env python3
"""
Simple test script for the Code Grader API
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/evaluation"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_create_rubric():
    """Test creating a rubric"""
    print("Testing create rubric endpoint...")
    
    rubric_data = {
        "lab_name": "Lab 1 - Basic Python",
        "semester": "Spring 2025",
        "section": "CS101",
        "total_points": 100,
        "criteria": {
            "syntax": {"points": 20, "description": "Correct Python syntax"},
            "logic": {"points": 30, "description": "Correct program logic"},
            "output": {"points": 25, "description": "Correct output format"},
            "comments": {"points": 15, "description": "Proper comments"},
            "style": {"points": 10, "description": "Code style and formatting"}
        }
    }
    
    response = requests.post(f"{BASE_URL}/create-rubric/", json=rubric_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    
    return response.json().get('rubric_id')

def test_get_rubric_id():
    """Test getting rubric ID"""
    print("Testing get rubric ID endpoint...")
    
    params = {
        "lab_name": "Lab 1 - Basic Python",
        "semester": "Spring 2025", 
        "section": "CS101"
    }
    
    response = requests.get(f"{BASE_URL}/get-rubric-id/", params=params)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    
    return response.json().get('rubric_id')

def test_evaluate_submission(rubric_id):
    """Test evaluating a submission"""
    print("Testing evaluate submission endpoint...")
    
    submission_data = {
        "student_id": "12345",
        "name": "John Doe",
        "section": "CS101",
        "semester": "Spring 2025",
        "instructor_name": "Dr. Smith",
        "lab_name": "Lab 1 - Basic Python",
        "rubric_id": rubric_id,
        "input": """
hello.py
Download

# Class: CS101
# Section: A
# Term: Spring 2025
# Instructor: Dr. Smith
# Name: John Doe
# Lab: Lab 1

print("Hello, World!")
"""
    }
    
    response = requests.post(f"{BASE_URL}/evaluate/", json=submission_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_get_rubrics():
    """Test getting all rubrics"""
    print("Testing get rubrics endpoint...")
    response = requests.get(f"{BASE_URL}/rubrics/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

if __name__ == "__main__":
    print("=== Code Grader API Test ===\n")
    
    # Test health endpoint
    test_health()
    
    # Test creating a rubric
    rubric_id = test_create_rubric()
    
    if rubric_id:
        # Test getting rubric ID
        test_get_rubric_id()
        
        # Test evaluation
        test_evaluate_submission(rubric_id)
    
    # Test getting all rubrics
    test_get_rubrics()
    
    print("=== Test Complete ===") 