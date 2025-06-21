#!/usr/bin/env python
"""
Analytics Data Creation Script
Only creates analytics data without re-creating other data
"""

import os
import sys
import django
import random
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'code_grader_api.settings')
django.setup()

from evaluation.models import Student, LabRubric
from analytics_service.models import StudentPerformance, LabAnalytics


def create_analytics_data_only():
    """Create only analytics data using existing students and rubrics"""
    print("Creating analytics data only...")
    
    # Get existing data
    students = Student.objects.all()
    rubrics = LabRubric.objects.all()
    
    print(f"Found {students.count()} existing students")
    print(f"Found {rubrics.count()} existing rubrics")
    
    # Lab topics for concept-based summaries
    lab_topics = {
        "Lab1": "Basic Variables and Input/Output",
        "Lab2": "Arrays and Lists", 
        "Lab3": "Functions and Methods",
        "Lab4": "Object-Oriented Programming",
        "Lab5": "File Handling and I/O",
        "Lab6": "Data Structures",
        "Lab7": "Graph Algorithms",
        "Lab8": "Dynamic Programming",
        "Lab9": "Advanced Algorithms",
        "Lab10": "System Programming"
    }
    
    # Student names for personalization
    student_names = [
        "Alex", "Jordan", "Taylor", "Casey", "Morgan", "Riley", "Avery", "Quinn", "Blake", "Hayden",
        "Parker", "Dakota", "Reese", "Sage", "Rowan", "Phoenix", "River", "Skylar", "Emery", "Finley"
    ]
    
    performance_data = []
    lab_analytics = []
    
    # Create student performance data
    print("Creating student performance records...")
    for student in students:
        # Each student gets 1-3 lab performances (unique per lab)
        num_labs = random.randint(1, 3)
        selected_labs = random.sample(list(lab_topics.keys()), num_labs)
        
        for lab_name in selected_labs:
            # Generate realistic performance data
            total_evaluations = random.randint(1, 5)
            total_points_lost = random.randint(0, 30)
            average_points_lost = total_points_lost / total_evaluations if total_evaluations > 0 else 0
            
            # Use get_or_create to avoid unique constraint violations
            performance, created = StudentPerformance.objects.get_or_create(
                student_id=student.student_id,
                lab_name=lab_name,
                section=student.section,
                semester=student.semester,
                defaults={
                    'student_name': student.name,
                    'total_evaluations': total_evaluations,
                    'total_points_lost': total_points_lost,
                    'average_points_lost': average_points_lost,
                    'last_evaluation_date': timezone.now() - timedelta(days=random.randint(1, 30))
                }
            )
            if created:
                performance_data.append(performance)
    
    # Create lab analytics
    print("Creating lab analytics...")
    for rubric in rubrics:
        topic = lab_topics.get(rubric.lab_name, "Programming Fundamentals")
        
        # Generate lab-specific analytics
        total_students = random.randint(20, 50)
        total_evaluations = total_students * random.randint(1, 3)
        average_points_lost = random.uniform(3.0, 12.0)
        
        # Generate common issues based on topic
        if topic == "Arrays and Lists":
            common_issues = {
                "array_boundary_errors": random.randint(10, 30),
                "loop_implementation": random.randint(15, 40),
                "array_indexing": random.randint(5, 20),
                "search_algorithms": random.randint(20, 35)
            }
        elif topic == "Functions and Methods":
            common_issues = {
                "parameter_handling": random.randint(10, 30),
                "return_values": random.randint(15, 40),
                "recursive_functions": random.randint(5, 20),
                "function_scope": random.randint(20, 35)
            }
        elif topic == "Object-Oriented Programming":
            common_issues = {
                "class_definition": random.randint(10, 30),
                "inheritance": random.randint(15, 40),
                "polymorphism": random.randint(5, 20),
                "encapsulation": random.randint(20, 35)
            }
        else:
            common_issues = {
                "basic_concepts": random.randint(10, 30),
                "implementation": random.randint(15, 40),
                "error_handling": random.randint(5, 20),
                "documentation": random.randint(20, 35)
            }
        
        # Use get_or_create to avoid unique constraint violations
        lab_analytics_obj, created = LabAnalytics.objects.get_or_create(
            lab_name=rubric.lab_name,
            section=rubric.section,
            semester=rubric.semester,
            defaults={
                'total_students': total_students,
                'total_evaluations': total_evaluations,
                'average_points_lost': average_points_lost,
                'common_issues': common_issues
            }
        )
        if created:
            lab_analytics.append(lab_analytics_obj)
    
    print(f"Created {len(performance_data)} student performance records and {len(lab_analytics)} lab analytics")
    return performance_data, lab_analytics


def main():
    """Main function to create analytics data only"""
    print("Starting analytics data creation...")
    
    # Clear existing analytics data only
    print("Clearing existing analytics data...")
    StudentPerformance.objects.all().delete()
    LabAnalytics.objects.all().delete()
    
    # Create analytics data
    performance_data, lab_analytics = create_analytics_data_only()
    
    print("\n" + "="*50)
    print("ANALYTICS DATA CREATION COMPLETE!")
    print("="*50)
    print(f"Created:")
    print(f"  - {len(performance_data)} student performance records")
    print(f"  - {len(lab_analytics)} lab analytics")
    print("\nYour analytics data is now populated!")


if __name__ == "__main__":
    main() 