#!/usr/bin/env python3
"""
Test script for Lab3 code submission evaluation
"""

import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:8000/api/evaluation"

def test_lab3_evaluation():
    """Test the complete Lab3 evaluation workflow"""
    
    # Step 1: Create the rubric for Lab3
    print("Step 1: Creating rubric for Lab3...")
    
    rubric_data = {
        "lab": "Lab3",
        "semester": "spring",
        "year": "2025",
        "section": "14",
        "rubrics": {
            "Lab3A.py": {
                "variable_initialization": {"points": 4, "description": "All variables are initialized before use"},
                "input_prompt": {"points": 4, "description": "Prompts for amount owed and APR with clear messages"},
                "input_type": {"points": 4, "description": "Correctly uses int and float for inputs"},
                "calculation_monthly_rate": {"points": 7, "description": "Correctly calculates monthly percentage rate"},
                "calculation_min_payment": {"points": 7, "description": "Correctly calculates minimum payment"},
                "output_monthly_rate": {"points": 3, "description": "Prints monthly percentage rate with correct rounding"},
                "output_min_payment": {"points": 3, "description": "Prints minimum payment with correct rounding and $ sign"},
                "variable_naming": {"points": 1, "description": "Uses clear and appropriate variable names"},
                "formatting": {"points": 1, "description": "Code is neatly formatted and readable"},
                "comments": {"points": 1, "description": "Includes helpful comments if needed"}
            },
            "Lab3B.py": {
                "variable_initialization": {"points": 4, "description": "All variables are initialized before use"},
                "input_prompts": {"points": 4, "description": "Prompts for all course hours and grades with clear messages"},
                "input_type": {"points": 4, "description": "Correctly uses int for all inputs"},
                "calculation_total_hours": {"points": 4, "description": "Correctly calculates total hours"},
                "calculation_quality_points": {"points": 7, "description": "Correctly calculates total quality points"},
                "calculation_gpa": {"points": 7, "description": "Correctly calculates GPA"},
                "output_total_hours": {"points": 2, "description": "Prints total hours in correct format"},
                "output_quality_points": {"points": 2, "description": "Prints total quality points in correct format"},
                "output_gpa": {"points": 3, "description": "Prints GPA rounded to 2 decimals"},
                "variable_naming": {"points": 1, "description": "Uses clear and appropriate variable names"},
                "formatting": {"points": 1, "description": "Code is neatly formatted and readable"},
                "comments": {"points": 1, "description": "Includes helpful comments if needed"}
            },
            "Lab3C.py": {
                "variable_initialization": {"points": 3, "description": "All variables are initialized before use"},
                "input_prompts": {"points": 3, "description": "Prompts for all sandwich sizes with clear messages"},
                "input_type": {"points": 3, "description": "Correctly uses int for all inputs"},
                "calculation_cooking_time": {"points": 7, "description": "Correctly calculates total cooking time in seconds"},
                "conversion_minutes_seconds": {"points": 6, "description": "Correctly converts total time to minutes and seconds"},
                "output_sandwich_counts": {"points": 2, "description": "Prints entered sandwich counts in correct format"},
                "output_total_time": {"points": 3, "description": "Prints total cooking time in correct format"},
                "variable_naming": {"points": 1, "description": "Uses clear and appropriate variable names"},
                "formatting": {"points": 1, "description": "Code is neatly formatted and readable"},
                "comments": {"points": 1, "description": "Includes helpful comments if needed"}
            }
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/create-rubric/", json=rubric_data)
        if response.status_code == 201:
            rubric_response = response.json()
            print(f"✅ Rubric created successfully! Rubric ID: {rubric_response['rubric_id']}")
            rubric_id = rubric_response['rubric_id']
        else:
            print(f"❌ Failed to create rubric: {response.status_code}")
            print(response.text)
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ Error creating rubric: {e}")
        return
    
    # Step 2: Get the rubric ID (alternative method)
    print("\nStep 2: Getting rubric ID...")
    
    get_rubric_data = {
        "lab": "Lab3",
        "semester": "spring",
        "year": "2025",
        "section": "14"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/get-rubric-id/", json=get_rubric_data)
        if response.status_code == 200:
            rubric_info = response.json()
            print(f"✅ Found rubric: ID {rubric_info['rubric_id']}, Total points: {rubric_info['total_points']}")
            rubric_id = rubric_info['rubric_id']
        else:
            print(f"❌ Failed to get rubric ID: {response.status_code}")
            print(response.text)
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting rubric ID: {e}")
        return
    
    # Step 3: Evaluate the submission
    print("\nStep 3: Evaluating submission...")
    
    # The code submission you provided
    code_input = """Lab3A.py
Download
# Class: CSE 1321L
# Section: 14
# Term: Spring 2025
# Instructor: Raja Yeswanth Nalamati
# Name: Zachery James Moon Jr.
# Lab: 3

amount_owed = int(input("Amount owed: $"))
apr = float(input("APR: "))
monthly_percentage_rate = apr/12
minimum_payment = amount_owed * (monthly_percentage_rate/100)
print(f"Monthly percentage rate: {round(monthly_percentage_rate, 3)}")
print(f"Minimum payment: ${round(minimum_payment, 2)}")

Lab3B.py
Download
# Class: CSE 1321L
# Section: 14
# Term: Spring 2025
# Instructor: Raja Yeswanth Nalamati
# Name: Zachery James Moon Jr.
# Lab: 3

course_one_hours = int(input("Course 1 hours: "))
course_one_grade = int(input("Grade for course 1: "))
course_two_hours = int(input("Course 2 hours: "))
course_two_grade = int(input("Grade for course 2: "))
course_three_hours = int(input("Course 3 hours: "))
course_three_grade = int(input("Grade for course 3: "))
course_four_hours = int(input("Course 4 hours: "))
course_four_grade = int(input("Grade for course 4: "))
total_hours = course_one_hours + course_two_hours + course_three_hours + course_four_hours
total_quality_points = course_one_grade*course_one_hours + course_two_grade*course_two_hours + course_three_grade*course_three_hours + course_four_grade*course_four_hours
gpa = total_quality_points / total_hours
print(f"Total hours: {total_hours}")
print(f"Total quality points: {total_quality_points}")
print(f"Your GPA for this semester is {round(gpa, 2)}")

Lab3C.py
Download
# Class: CSE 1321L
# Section: 14
# Term: Spring 2025
# Instructor: Raja Yeswanth Nalamati
# Name: Zachery James Moon Jr.
# Lab: 3

small_sandwiches = int(input("Enter the number of small sandwiches: "))
medium_sandwiches = int(input("Enter the number of medium sandwiches: "))
large_sandwiches = int(input("Enter the number of large sandwiches: "))
extra_large_sandwiches = int(input("Enter the number of extra-large sandwiches: "))
print("")
print(f"You've entered {small_sandwiches} small sandwiches.")
print(f"You've entered {medium_sandwiches} medium sandwiches.")
print(f"You've entered {large_sandwiches} large sandwiches.")
print(f"You've entered {extra_large_sandwiches} extra-large sandwiches.")
print("")
cooking_time = (small_sandwiches*30) + (medium_sandwiches*60) + (large_sandwiches*75) + (extra_large_sandwiches*135)
cooking_time_minutes = cooking_time // 60
cooking_time_seconds = cooking_time % 60
print(f"Total cooking time is {cooking_time_minutes} minutes and {cooking_time_seconds} seconds.")"""
    
    evaluation_data = {
        "student_id": "STU123456",
        "name": "Zachery James Moon Jr.",
        "section": "14",
        "semester": "spring 2025",
        "instructor_name": "Raja Yeswanth Nalamati",
        "lab_name": "Lab3",
        "rubric_id": rubric_id,
        "input": code_input
    }
    
    try:
        response = requests.post(f"{BASE_URL}/evaluate/", json=evaluation_data)
        if response.status_code == 200:
            result = response.json()
            print("✅ Evaluation completed successfully!")
            print(f"Session ID: {result['session_id']}")
            print(f"Total files evaluated: {result['total_files_evaluated']}")
            print(f"Total points lost: {result['total_points_lost']}")
            print(f"Evaluation time: {result['total_evaluation_time_seconds']:.2f} seconds")
            print(f"\nSummary: {result['summary']}")
            print(f"\nDetailed Feedback:\n{result['feedback']}")
        else:
            print(f"❌ Evaluation failed: {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"❌ Error during evaluation: {e}")

if __name__ == "__main__":
    print("🚀 Starting Lab3 Code Evaluation Test")
    print("=" * 50)
    test_lab3_evaluation()
    print("\n" + "=" * 50)
    print("🏁 Test completed!") 