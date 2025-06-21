#!/usr/bin/env python
"""
Comprehensive Database Population Script
Populates all tables with realistic data for testing and demonstration
"""

import os
import sys
import django
import random
import uuid
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'code_grader_api.settings')
django.setup()

from evaluation.models import Student, LabRubric, Evaluation, EvaluationSession
from metrics_service.models import (
    RequestMetrics, EvaluationMetrics, SystemMetrics, 
    CostMetrics, ErrorMetrics, PerformanceMetrics
)
from analytics_service.models import StudentPerformance, LabAnalytics


def create_diverse_rubrics():
    """Create 10 different rubrics for various programming topics"""
    print("Creating diverse rubrics...")
    
    # Different programming topics and their criteria
    lab_topics = {
        "Lab1": {
            "topic": "Basic Variables and Input/Output",
            "files": ["Lab1A.py", "Lab1B.py"],
            "criteria": {
                "Lab1A.py": {
                    "variable_declaration": {"points": 5, "description": "Properly declares variables with appropriate types"},
                    "input_handling": {"points": 5, "description": "Correctly handles user input with proper prompts"},
                    "basic_calculations": {"points": 8, "description": "Performs basic arithmetic operations correctly"},
                    "output_formatting": {"points": 4, "description": "Formats output according to specifications"},
                    "code_structure": {"points": 3, "description": "Code is well-structured and readable"}
                },
                "Lab1B.py": {
                    "string_operations": {"points": 6, "description": "Correctly manipulates strings"},
                    "type_conversion": {"points": 5, "description": "Properly converts between data types"},
                    "conditional_logic": {"points": 7, "description": "Implements basic if-else statements"},
                    "output_accuracy": {"points": 4, "description": "Produces correct output format"},
                    "error_handling": {"points": 3, "description": "Handles basic error cases"}
                }
            }
        },
        "Lab2": {
            "topic": "Arrays and Lists",
            "files": ["Lab2A.py", "Lab2B.py", "Lab2C.py"],
            "criteria": {
                "Lab2A.py": {
                    "array_initialization": {"points": 4, "description": "Properly initializes arrays/lists"},
                    "array_operations": {"points": 6, "description": "Correctly performs array operations"},
                    "loop_implementation": {"points": 5, "description": "Uses loops to process arrays"},
                    "array_indexing": {"points": 4, "description": "Correctly accesses array elements"},
                    "output_validation": {"points": 3, "description": "Validates and displays array results"}
                },
                "Lab2B.py": {
                    "array_searching": {"points": 7, "description": "Implements search algorithms in arrays"},
                    "array_sorting": {"points": 8, "description": "Implements basic sorting algorithms"},
                    "algorithm_efficiency": {"points": 3, "description": "Uses efficient algorithms"},
                    "edge_cases": {"points": 4, "description": "Handles edge cases properly"}
                },
                "Lab2C.py": {
                    "multi_dimensional_arrays": {"points": 8, "description": "Works with 2D arrays correctly"},
                    "nested_loops": {"points": 6, "description": "Implements nested loops properly"},
                    "array_manipulation": {"points": 5, "description": "Manipulates array structures"},
                    "complex_operations": {"points": 3, "description": "Performs complex array operations"}
                }
            }
        },
        "Lab3": {
            "topic": "Functions and Methods",
            "files": ["Lab3A.py", "Lab3B.py"],
            "criteria": {
                "Lab3A.py": {
                    "function_definition": {"points": 5, "description": "Properly defines functions with parameters"},
                    "function_calls": {"points": 4, "description": "Correctly calls functions"},
                    "return_values": {"points": 5, "description": "Returns appropriate values from functions"},
                    "parameter_handling": {"points": 4, "description": "Handles function parameters correctly"},
                    "function_documentation": {"points": 2, "description": "Includes function documentation"}
                },
                "Lab3B.py": {
                    "recursive_functions": {"points": 8, "description": "Implements recursive functions correctly"},
                    "algorithm_implementation": {"points": 7, "description": "Implements algorithms using functions"},
                    "error_handling": {"points": 4, "description": "Handles errors in functions"},
                    "code_reusability": {"points": 3, "description": "Creates reusable function code"}
                }
            }
        },
        "Lab4": {
            "topic": "Object-Oriented Programming",
            "files": ["Lab4A.py", "Lab4B.py"],
            "criteria": {
                "Lab4A.py": {
                    "class_definition": {"points": 6, "description": "Properly defines classes"},
                    "constructor_implementation": {"points": 5, "description": "Implements constructors correctly"},
                    "method_definition": {"points": 5, "description": "Defines class methods properly"},
                    "object_creation": {"points": 4, "description": "Creates objects correctly"},
                    "attribute_access": {"points": 2, "description": "Accesses class attributes properly"}
                },
                "Lab4B.py": {
                    "inheritance": {"points": 8, "description": "Implements inheritance correctly"},
                    "method_overriding": {"points": 6, "description": "Overrides methods properly"},
                    "polymorphism": {"points": 5, "description": "Demonstrates polymorphism"},
                    "encapsulation": {"points": 3, "description": "Uses encapsulation principles"}
                }
            }
        },
        "Lab5": {
            "topic": "File Handling and I/O",
            "files": ["Lab5A.py", "Lab5B.py"],
            "criteria": {
                "Lab5A.py": {
                    "file_reading": {"points": 6, "description": "Correctly reads from files"},
                    "file_writing": {"points": 6, "description": "Correctly writes to files"},
                    "file_operations": {"points": 4, "description": "Performs file operations safely"},
                    "data_parsing": {"points": 5, "description": "Parses file data correctly"},
                    "error_handling": {"points": 3, "description": "Handles file operation errors"}
                },
                "Lab5B.py": {
                    "csv_processing": {"points": 7, "description": "Processes CSV files correctly"},
                    "data_analysis": {"points": 6, "description": "Performs basic data analysis"},
                    "report_generation": {"points": 5, "description": "Generates reports from file data"},
                    "data_validation": {"points": 4, "description": "Validates file data"}
                }
            }
        },
        "Lab6": {
            "topic": "Data Structures",
            "files": ["Lab6A.py", "Lab6B.py"],
            "criteria": {
                "Lab6A.py": {
                    "stack_implementation": {"points": 8, "description": "Implements stack data structure"},
                    "queue_implementation": {"points": 8, "description": "Implements queue data structure"},
                    "basic_operations": {"points": 5, "description": "Performs basic stack/queue operations"},
                    "algorithm_usage": {"points": 3, "description": "Uses appropriate algorithms"}
                },
                "Lab6B.py": {
                    "linked_list": {"points": 10, "description": "Implements linked list correctly"},
                    "tree_structure": {"points": 8, "description": "Implements basic tree structure"},
                    "traversal_algorithms": {"points": 6, "description": "Implements traversal algorithms"},
                    "complex_operations": {"points": 4, "description": "Performs complex data structure operations"}
                }
            }
        },
        "Lab7": {
            "topic": "Graph Algorithms",
            "files": ["Lab7A.py", "Lab7B.py"],
            "criteria": {
                "Lab7A.py": {
                    "graph_representation": {"points": 8, "description": "Correctly represents graphs"},
                    "graph_traversal": {"points": 10, "description": "Implements graph traversal algorithms"},
                    "adjacency_structures": {"points": 6, "description": "Uses appropriate adjacency structures"},
                    "basic_algorithms": {"points": 4, "description": "Implements basic graph algorithms"}
                },
                "Lab7B.py": {
                    "shortest_path": {"points": 12, "description": "Implements shortest path algorithms"},
                    "minimum_spanning_tree": {"points": 10, "description": "Implements MST algorithms"},
                    "algorithm_complexity": {"points": 5, "description": "Considers algorithm complexity"},
                    "optimization": {"points": 3, "description": "Optimizes graph algorithms"}
                }
            }
        },
        "Lab8": {
            "topic": "Dynamic Programming",
            "files": ["Lab8A.py", "Lab8B.py"],
            "criteria": {
                "Lab8A.py": {
                    "memoization": {"points": 8, "description": "Implements memoization correctly"},
                    "recursive_solutions": {"points": 7, "description": "Converts recursive to dynamic programming"},
                    "state_management": {"points": 6, "description": "Manages state properly"},
                    "optimization": {"points": 5, "description": "Optimizes solutions using DP"}
                },
                "Lab8B.py": {
                    "complex_dp_problems": {"points": 12, "description": "Solves complex DP problems"},
                    "algorithm_design": {"points": 8, "description": "Designs efficient DP algorithms"},
                    "space_optimization": {"points": 5, "description": "Optimizes space complexity"},
                    "problem_analysis": {"points": 3, "description": "Analyzes problems for DP approach"}
                }
            }
        },
        "Lab9": {
            "topic": "Advanced Algorithms",
            "files": ["Lab9A.py", "Lab9B.py"],
            "criteria": {
                "Lab9A.py": {
                    "sorting_algorithms": {"points": 10, "description": "Implements advanced sorting algorithms"},
                    "searching_algorithms": {"points": 8, "description": "Implements efficient searching"},
                    "algorithm_analysis": {"points": 6, "description": "Analyzes algorithm performance"},
                    "optimization_techniques": {"points": 4, "description": "Uses optimization techniques"}
                },
                "Lab9B.py": {
                    "divide_and_conquer": {"points": 10, "description": "Implements divide and conquer algorithms"},
                    "greedy_algorithms": {"points": 8, "description": "Implements greedy algorithms"},
                    "backtracking": {"points": 8, "description": "Implements backtracking algorithms"},
                    "complex_problem_solving": {"points": 4, "description": "Solves complex algorithmic problems"}
                }
            }
        },
        "Lab10": {
            "topic": "System Programming",
            "files": ["Lab10A.py", "Lab10B.py"],
            "criteria": {
                "Lab10A.py": {
                    "process_management": {"points": 8, "description": "Manages processes correctly"},
                    "thread_handling": {"points": 8, "description": "Handles threads properly"},
                    "synchronization": {"points": 6, "description": "Implements synchronization mechanisms"},
                    "resource_management": {"points": 4, "description": "Manages system resources"}
                },
                "Lab10B.py": {
                    "network_programming": {"points": 10, "description": "Implements network programming"},
                    "socket_programming": {"points": 8, "description": "Uses sockets correctly"},
                    "protocol_implementation": {"points": 6, "description": "Implements network protocols"},
                    "error_handling": {"points": 4, "description": "Handles network errors properly"}
                }
            }
        }
    }
    
    semesters = ["Spring 2024", "Fall 2024", "Spring 2025", "Fall 2025", "Summer 2024"]
    sections = ["14", "15", "16", "17", "18", "19", "20", "21", "22", "23"]
    
    rubrics_created = []
    
    for i, (lab_name, lab_data) in enumerate(lab_topics.items()):
        semester = semesters[i % len(semesters)]
        section = sections[i % len(sections)]
        
        # Calculate total points
        total_points = 0
        for file_criteria in lab_data["criteria"].values():
            for criterion in file_criteria.values():
                total_points += criterion["points"]
        
        rubric = LabRubric.objects.create(
            lab_name=lab_name,
            semester=semester,
            section=section,
            total_points=total_points,
            criteria=lab_data["criteria"],
            is_active=True
        )
        rubrics_created.append(rubric)
        print(f"Created rubric: {lab_name} ({lab_data['topic']}) - {semester} - {section} - {total_points} points")
    
    return rubrics_created


def create_students():
    """Create 100,000+ students across different semesters and sections"""
    print("Creating students...")
    
    # Sample names for variety
    first_names = [
        "John", "Jane", "Michael", "Sarah", "David", "Emily", "James", "Jessica", "Robert", "Amanda",
        "William", "Ashley", "Richard", "Stephanie", "Joseph", "Nicole", "Thomas", "Elizabeth", "Christopher", "Helen",
        "Charles", "Deborah", "Daniel", "Rachel", "Matthew", "Carolyn", "Anthony", "Janet", "Mark", "Catherine",
        "Donald", "Maria", "Steven", "Heather", "Paul", "Diane", "Andrew", "Ruth", "Joshua", "Julie",
        "Kenneth", "Joyce", "Kevin", "Virginia", "Brian", "Victoria", "George", "Kelly", "Edward", "Lauren",
        "Ronald", "Christine", "Timothy", "Joan", "Jason", "Evelyn", "Jeffrey", "Judith", "Ryan", "Megan",
        "Jacob", "Cheryl", "Gary", "Andrea", "Nicholas", "Hannah", "Eric", "Jacqueline", "Jonathan", "Martha",
        "Stephen", "Gloria", "Larry", "Teresa", "Justin", "Ann", "Scott", "Sara", "Brandon", "Madison",
        "Benjamin", "Frances", "Samuel", "Kathryn", "Frank", "Janice", "Gregory", "Jean", "Raymond", "Abigail",
        "Alexander", "Alice", "Patrick", "Julia", "Jack", "Judy", "Dennis", "Sophia", "Jerry", "Grace",
        "Alex", "Jordan", "Taylor", "Casey", "Morgan", "Riley", "Avery", "Quinn", "Blake", "Hayden",
        "Parker", "Dakota", "Reese", "Sage", "Rowan", "Phoenix", "River", "Skylar", "Emery", "Finley",
        "Cameron", "Drew", "Jamie", "Kendall", "Logan", "Peyton", "Reagan", "Spencer", "Tatum", "Winter"
    ]
    
    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
        "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
        "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
        "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
        "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts",
        "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker", "Cruz", "Edwards", "Collins", "Reyes",
        "Stewart", "Morris", "Morales", "Murphy", "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper",
        "Peterson", "Bailey", "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson",
        "Watson", "Brooks", "Chavez", "Wood", "James", "Bennett", "Gray", "Mendoza", "Ruiz", "Hughes",
        "Price", "Alvarez", "Castillo", "Sanders", "Patel", "Myers", "Long", "Ross", "Foster", "Jimenez",
        "Chen", "Wang", "Li", "Zhang", "Liu", "Yang", "Huang", "Wu", "Zhou", "Zhao",
        "Kumar", "Singh", "Patel", "Sharma", "Gupta", "Verma", "Kaur", "Malhotra", "Kapoor", "Joshi"
    ]
    
    semesters = ["Spring 2024", "Fall 2024", "Spring 2025", "Fall 2025", "Summer 2024"]
    sections = ["14", "15", "16", "17", "18", "19", "20", "21", "22", "23"]
    instructors = [
        "Dr. Raja Yeswanth Nalamati", "Dr. Sarah Johnson", "Dr. Michael Chen", "Dr. Emily Rodriguez",
        "Prof. David Thompson", "Dr. Lisa Wang", "Prof. Robert Kim", "Dr. Amanda Davis", "Prof. James Wilson",
        "Dr. Jennifer Lee", "Prof. Christopher Brown", "Dr. Maria Garcia", "Prof. Daniel Martinez",
        "Dr. Alex Thompson", "Prof. Rachel Kim", "Dr. Marcus Johnson", "Prof. Sophia Chen", "Dr. Kevin Park"
    ]
    
    students_created = []
    
    for i in range(100000):  # Create 1 lakh students
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        name = f"{first_name} {last_name}"
        student_id = f"STU{100000 + i:06d}"
        semester = random.choice(semesters)
        section = random.choice(sections)
        instructor = random.choice(instructors)
        
        student = Student.objects.create(
            student_id=student_id,
            name=name,
            section=section,
            semester=semester,
            instructor_name=instructor
        )
        students_created.append(student)
        
        if i % 1000 == 0:
            print(f"Created {i} students...")
    
    print(f"Created {len(students_created)} students")
    return students_created


def generate_realistic_feedback(lab_name, topic):
    """Generate realistic feedback based on lab topic"""
    
    # Programming concept feedback templates
    concept_feedback = {
        "Basic Variables and Input/Output": {
            "strengths": [
                "demonstrates good understanding of variable declaration",
                "shows proficiency in basic input/output operations",
                "excellent use of data type conversion",
                "well-structured code with clear variable names"
            ],
            "weaknesses": [
                "struggles with proper variable initialization",
                "has difficulty with input validation",
                "needs improvement in output formatting",
                "lacks proper error handling for user input"
            ]
        },
        "Arrays and Lists": {
            "strengths": [
                "excellent array manipulation skills",
                "shows strong understanding of array indexing",
                "good implementation of array operations",
                "demonstrates proficiency in loop-based array processing"
            ],
            "weaknesses": [
                "struggles with array boundary conditions",
                "has difficulty implementing search algorithms",
                "needs improvement in array sorting techniques",
                "lacks understanding of multi-dimensional arrays"
            ]
        },
        "Functions and Methods": {
            "strengths": [
                "excellent function design and implementation",
                "shows strong understanding of parameter passing",
                "good use of return values and function calls",
                "demonstrates proper function documentation"
            ],
            "weaknesses": [
                "struggles with recursive function implementation",
                "has difficulty with function scope and variables",
                "needs improvement in error handling within functions",
                "lacks understanding of function overloading"
            ]
        },
        "Object-Oriented Programming": {
            "strengths": [
                "excellent class design and implementation",
                "shows strong understanding of inheritance concepts",
                "good use of encapsulation and data hiding",
                "demonstrates proper method implementation"
            ],
            "weaknesses": [
                "struggles with polymorphism implementation",
                "has difficulty with constructor design",
                "needs improvement in class relationships",
                "lacks understanding of abstract classes"
            ]
        },
        "File Handling and I/O": {
            "strengths": [
                "excellent file reading and writing skills",
                "shows strong understanding of file operations",
                "good implementation of data parsing",
                "demonstrates proper error handling for file operations"
            ],
            "weaknesses": [
                "struggles with CSV file processing",
                "has difficulty with large file handling",
                "needs improvement in file path management",
                "lacks understanding of binary file operations"
            ]
        },
        "Data Structures": {
            "strengths": [
                "excellent implementation of basic data structures",
                "shows strong understanding of stack and queue operations",
                "good use of linked list concepts",
                "demonstrates proper tree structure implementation"
            ],
            "weaknesses": [
                "struggles with complex data structure operations",
                "has difficulty with traversal algorithms",
                "needs improvement in memory management",
                "lacks understanding of advanced data structures"
            ]
        },
        "Graph Algorithms": {
            "strengths": [
                "excellent graph representation skills",
                "shows strong understanding of graph traversal",
                "good implementation of basic graph algorithms",
                "demonstrates proper adjacency structure usage"
            ],
            "weaknesses": [
                "struggles with shortest path algorithms",
                "has difficulty with minimum spanning tree implementation",
                "needs improvement in algorithm optimization",
                "lacks understanding of graph complexity analysis"
            ]
        },
        "Dynamic Programming": {
            "strengths": [
                "excellent problem analysis for DP approach",
                "shows strong understanding of memoization",
                "good implementation of recursive to DP conversion",
                "demonstrates proper state management"
            ],
            "weaknesses": [
                "struggles with complex DP problem formulation",
                "has difficulty with space optimization",
                "needs improvement in algorithm design",
                "lacks understanding of DP optimization techniques"
            ]
        },
        "Advanced Algorithms": {
            "strengths": [
                "excellent implementation of sorting algorithms",
                "shows strong understanding of divide and conquer",
                "good use of greedy algorithm concepts",
                "demonstrates proper backtracking implementation"
            ],
            "weaknesses": [
                "struggles with algorithm complexity analysis",
                "has difficulty with optimization techniques",
                "needs improvement in problem-solving approach",
                "lacks understanding of advanced algorithmic concepts"
            ]
        },
        "System Programming": {
            "strengths": [
                "excellent process management skills",
                "shows strong understanding of threading concepts",
                "good implementation of synchronization mechanisms",
                "demonstrates proper resource management"
            ],
            "weaknesses": [
                "struggles with network programming concepts",
                "has difficulty with socket programming",
                "needs improvement in protocol implementation",
                "lacks understanding of system-level programming"
            ]
        }
    }
    
    # Student names for personalization
    student_names = [
        "Alex", "Jordan", "Taylor", "Casey", "Morgan", "Riley", "Avery", "Quinn", "Blake", "Hayden",
        "Parker", "Dakota", "Reese", "Sage", "Rowan", "Phoenix", "River", "Skylar", "Emery", "Finley",
        "Cameron", "Drew", "Jamie", "Kendall", "Logan", "Peyton", "Reagan", "Spencer", "Tatum", "Winter"
    ]
    
    topic_data = concept_feedback.get(topic, {
        "strengths": ["shows good programming fundamentals", "demonstrates logical thinking"],
        "weaknesses": ["needs improvement in implementation", "requires more practice"]
    })
    
    # Generate personalized feedback
    student_name = random.choice(student_names)
    strength = random.choice(topic_data["strengths"])
    weakness = random.choice(topic_data["weaknesses"])
    
    feedback_templates = [
        f"{student_name} performed well in {lab_name}, demonstrating {strength}. However, {weakness}. Overall good work with room for improvement.",
        f"In {lab_name}, {student_name} shows {strength}. Areas for improvement include {weakness}. Keep practicing these concepts.",
        f"{student_name} has completed {lab_name} with {strength}. To improve further, focus on {weakness}. Good effort overall.",
        f"Excellent work by {student_name} in {lab_name}! {strength} is clearly demonstrated. For future labs, work on {weakness}.",
        f"{student_name} shows promise in {lab_name} with {strength}. To excel, address {weakness}. Continue this good work."
    ]
    
    return random.choice(feedback_templates)


def create_evaluations_and_sessions(students, rubrics):
    """Create evaluations and sessions with realistic feedback"""
    print("Creating evaluations and sessions...")
    
    # Lab topics mapping
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
    
    # Realistic feedback templates for specific issues
    feedback_templates = {
        "perfect": "correct",
        "minor_issues": [
            "1. Missing variable initialization --> -4 points\n2. Incorrect output formatting --> -3 points",
            "1. Wrong calculation method --> -7 points\n2. Missing comments --> -1 points",
            "1. Incorrect input type conversion --> -4 points\n2. Poor variable naming --> -1 points",
            "1. Array index out of bounds --> -5 points\n2. Incomplete loop implementation --> -3 points",
            "1. Function parameter mismatch --> -6 points\n2. Missing return statement --> -4 points"
        ],
        "major_issues": [
            "1. Missing main calculation logic --> -15 points\n2. Incorrect variable types --> -8 points\n3. No output statements --> -10 points",
            "1. Wrong algorithm implementation --> -20 points\n2. Missing input validation --> -5 points\n3. Incorrect data types --> -8 points",
            "1. Incomplete function implementation --> -25 points\n2. Wrong mathematical formula --> -12 points\n3. Missing error handling --> -5 points",
            "1. Failed to implement array operations --> -18 points\n2. Incorrect loop structure --> -10 points\n3. Missing array bounds checking --> -7 points",
            "1. Class definition errors --> -20 points\n2. Missing method implementations --> -15 points\n3. Inheritance not properly used --> -10 points"
        ],
        "errors": [
            "Error - Syntax errors in code structure",
            "Error - Missing required functions",
            "Error - Incorrect file format",
            "Error - Array index out of bounds",
            "Error - Function not defined"
        ]
    }
    
    evaluations_created = []
    sessions_created = []
    
    for student in students:
        # Each student gets 1-3 evaluations
        num_evaluations = random.randint(1, 3)
        
        for i in range(num_evaluations):
            rubric = random.choice(rubrics)
            topic = lab_topics.get(rubric.lab_name, "Programming Fundamentals")
            
            # Generate realistic feedback
            feedback_type = random.choices(
                ["perfect", "minor_issues", "major_issues", "errors"],
                weights=[0.15, 0.45, 0.35, 0.05]
            )[0]
            
            if feedback_type == "perfect":
                feedback = feedback_templates["perfect"]
                points_lost = 0
            elif feedback_type == "minor_issues":
                feedback = random.choice(feedback_templates["minor_issues"])
                points_lost = random.randint(5, 15)
            elif feedback_type == "major_issues":
                feedback = random.choice(feedback_templates["major_issues"])
                points_lost = random.randint(20, 40)
            else:  # errors
                feedback = random.choice(feedback_templates["errors"])
                points_lost = random.randint(25, 50)
            
            # Generate personalized overall feedback
            overall_feedback = generate_realistic_feedback(rubric.lab_name, topic)
            
            # Create evaluation session
            session_id = str(uuid.uuid4())
            session = EvaluationSession.objects.create(
                student=student,
                session_id=session_id,
                lab_name=rubric.lab_name,
                summary_feedback=overall_feedback,
                total_files_evaluated=random.randint(2, 4),
                successful_evaluations=random.randint(1, 3),
                error_evaluations=random.randint(0, 1),
                total_points_lost=points_lost,
                total_deductions=points_lost,
                submission_data={
                    "files": [f"{rubric.lab_name}A.py", f"{rubric.lab_name}B.py", f"{rubric.lab_name}C.py"],
                    "lab_feedback": {f"{rubric.lab_name}A.py": feedback}
                },
                total_evaluation_time_seconds=random.uniform(2.0, 8.0),
                total_tokens_used=random.randint(800, 2500)
            )
            sessions_created.append(session)
            
            # Create evaluation
            evaluation = Evaluation.objects.create(
                student=student,
                rubric=rubric,
                lab_name=rubric.lab_name,
                status='completed',
                feedback=feedback,
                total_points_lost=points_lost,
                deductions=[{"criteria": "calculation", "points_lost": points_lost}],
                code_content=f"# Sample code for {rubric.lab_name}\nprint('Hello World')"
            )
            evaluations_created.append(evaluation)
    
    print(f"Created {len(evaluations_created)} evaluations and {len(sessions_created)} sessions")
    return evaluations_created, sessions_created


def create_request_metrics():
    """Create realistic request metrics data"""
    print("Creating request metrics...")
    
    endpoints = [
        "/api/evaluation/evaluate/",
        "/api/evaluation/create-rubric/",
        "/api/evaluation/get-rubric-id/",
        "/api/evaluation/rubrics/",
        "/api/metrics/dashboard/",
        "/api/metrics/cost-analysis/",
        "/api/metrics/performance-trends/",
        "/api/analytics/student-performance/",
        "/api/analytics/lab-analytics/"
    ]
    
    methods = ["GET", "POST"]
    status_codes = [200, 201, 400, 404, 500]
    
    metrics_created = []
    
    # Create metrics for the last 30 days
    for i in range(30):
        date = timezone.now() - timedelta(days=i)
        
        # Create 20-50 requests per day
        daily_requests = random.randint(20, 50)
        
        for j in range(daily_requests):
            # Random time during the day
            hour = random.randint(0, 23)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            
            timestamp = date.replace(hour=hour, minute=minute, second=second)
            
            endpoint = random.choice(endpoints)
            method = random.choice(methods)
            status_code = random.choices(status_codes, weights=[0.7, 0.1, 0.1, 0.05, 0.05])[0]
            
            # Token usage based on endpoint
            if "evaluate" in endpoint:
                input_tokens = random.randint(800, 2000)
                output_tokens = random.randint(200, 600)
                llm_calls = random.randint(2, 6)
            else:
                input_tokens = random.randint(50, 200)
                output_tokens = random.randint(20, 100)
                llm_calls = 0
            
            total_tokens = input_tokens + output_tokens
            avg_tokens_per_call = total_tokens / llm_calls if llm_calls > 0 else 0
            
            # Cost calculation (gpt-4.1-nano pricing)
            estimated_cost = (input_tokens * 0.00015 + output_tokens * 0.0006) / 1000
            
            metric = RequestMetrics.objects.create(
                request_id=str(uuid.uuid4()),
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time_ms=random.uniform(100, 3000),
                tokens_used=total_tokens,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                avg_tokens_per_call=avg_tokens_per_call,
                llm_calls_count=llm_calls,
                estimated_cost_usd=estimated_cost,
                memory_usage_mb=random.uniform(30, 80),
                cpu_usage_percent=random.uniform(5, 25),
                error_message="" if status_code < 400 else "Sample error message",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                ip_address=f"192.168.1.{random.randint(1, 255)}",
                timestamp=timestamp
            )
            metrics_created.append(metric)
    
    print(f"Created {len(metrics_created)} request metrics")
    return metrics_created


def create_evaluation_metrics(sessions):
    """Create evaluation metrics data"""
    print("Creating evaluation metrics...")
    
    metrics_created = []
    
    for session in sessions:
        metric = EvaluationMetrics.objects.create(
            session_id=session.session_id,
            student_id=session.student.student_id,
            lab_name=session.lab_name,
            total_files=session.total_files_evaluated,
            successful_files=session.successful_evaluations,
            failed_files=session.error_evaluations,
            total_tokens=session.total_tokens_used,
            total_cost_usd=(session.total_tokens_used * 0.00015) / 1000,  # Rough cost estimation
            evaluation_time_seconds=session.total_evaluation_time_seconds,
            accuracy_score=random.uniform(0.6, 1.0),
            feedback_quality_score=random.uniform(0.7, 1.0)
        )
        metrics_created.append(metric)
    
    print(f"Created {len(metrics_created)} evaluation metrics")
    return metrics_created


def create_system_metrics():
    """Create system metrics data"""
    print("Creating system metrics...")
    
    metric_types = ["performance", "cost", "accuracy", "errors"]
    metric_names = [
        "avg_response_time", "memory_usage", "cpu_usage", "throughput",
        "error_rate", "success_rate", "token_efficiency", "cost_per_request"
    ]
    units = ["milliseconds", "megabytes", "percentage", "requests_per_second", "percentage", "percentage", "tokens_per_dollar", "dollars"]
    
    metrics_created = []
    
    # Create metrics for the last 30 days
    for i in range(30):
        date = timezone.now() - timedelta(days=i)
        
        # Create 5-10 system metrics per day
        daily_metrics = random.randint(5, 10)
        
        for j in range(daily_metrics):
            metric_type = random.choice(metric_types)
            metric_name = random.choice(metric_names)
            unit = random.choice(units)
            
            # Realistic values based on metric type
            if "response_time" in metric_name:
                value = random.uniform(500, 2500)
            elif "memory" in metric_name:
                value = random.uniform(40, 90)
            elif "cpu" in metric_name:
                value = random.uniform(10, 40)
            elif "error" in metric_name or "success" in metric_name:
                value = random.uniform(85, 99)
            else:
                value = random.uniform(1, 100)
            
            metric = SystemMetrics.objects.create(
                metric_type=metric_type,
                metric_name=metric_name,
                metric_value=value,
                metric_unit=unit,
                additional_data={"source": "system_monitor", "period": "daily"},
                timestamp=date
            )
            metrics_created.append(metric)
    
    print(f"Created {len(metrics_created)} system metrics")
    return metrics_created


def create_error_metrics():
    """Create error metrics data"""
    print("Creating error metrics...")
    
    error_types = ["api_error", "validation_error", "timeout", "database_error", "authentication_error"]
    error_messages = [
        "OpenAI API rate limit exceeded",
        "Invalid input format provided",
        "Request timeout after 30 seconds",
        "Database connection failed",
        "Authentication token expired",
        "Invalid rubric ID provided",
        "Student ID format incorrect",
        "File parsing error occurred"
    ]
    endpoints = [
        "/api/evaluation/evaluate/",
        "/api/evaluation/create-rubric/",
        "/api/metrics/dashboard/",
        "/api/analytics/student-performance/"
    ]
    
    metrics_created = []
    
    for error_type in error_types:
        for endpoint in endpoints:
            # Create 1-5 occurrences of each error type per endpoint
            frequency = random.randint(1, 5)
            
            if frequency > 0:
                metric = ErrorMetrics.objects.create(
                    error_type=error_type,
                    error_message=random.choice(error_messages),
                    endpoint=endpoint,
                    frequency=frequency,
                    is_resolved=random.choice([True, False]),
                    resolution_notes="Issue resolved by system administrator" if random.choice([True, False]) else ""
                )
                metrics_created.append(metric)
    
    print(f"Created {len(metrics_created)} error metrics")
    return metrics_created


def create_performance_metrics():
    """Create performance metrics data"""
    print("Creating performance metrics...")
    
    metric_names = ["avg_response_time", "throughput", "memory_usage", "cpu_usage", "error_rate"]
    units = ["milliseconds", "requests_per_second", "megabytes", "percentage", "percentage"]
    
    metrics_created = []
    
    # Create metrics for different time periods
    periods = [5, 15, 30, 60]  # minutes
    
    for period in periods:
        for i in range(20):  # 20 metrics per period
            metric_name = random.choice(metric_names)
            unit = random.choice(units)
            
            # Realistic values
            if "response_time" in metric_name:
                value = random.uniform(800, 3000)
            elif "throughput" in metric_name:
                value = random.uniform(10, 100)
            elif "memory" in metric_name:
                value = random.uniform(50, 120)
            elif "cpu" in metric_name:
                value = random.uniform(15, 50)
            else:  # error_rate
                value = random.uniform(1, 10)
            
            metric = PerformanceMetrics.objects.create(
                metric_name=metric_name,
                metric_value=value,
                metric_unit=unit,
                period_minutes=period
            )
            metrics_created.append(metric)
    
    print(f"Created {len(metrics_created)} performance metrics")
    return metrics_created


def create_analytics_data(students, rubrics):
    """Create analytics data for students and labs"""
    print("Creating analytics data...")
    
    performance_data = []
    lab_analytics = []
    
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
    
    for student in students:
        # Each student gets 1-3 lab performances (unique per lab)
        num_labs = random.randint(1, 3)
        selected_labs = random.sample(list(lab_topics.keys()), num_labs)
        
        for lab_name in selected_labs:
            topic = lab_topics[lab_name]
            student_name = random.choice(student_names)
            
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
    
    # Create lab analytics (keep summary logic here)
    for rubric in rubrics:
        topic = lab_topics.get(rubric.lab_name, "Programming Fundamentals")
        total_students = random.randint(20, 50)
        total_evaluations = total_students * random.randint(1, 3)
        average_points_lost = random.uniform(3.0, 12.0)
        # ... summary and concept_analysis logic unchanged ...
        # (omitted for brevity)
        # ...
        # (use the same summary and concept_analysis logic as before)
        # ...
        # Generate concept-based analysis
        if topic == "Arrays and Lists":
            concept_analysis = {
                "array_operations": {
                    "strength": "Students show excellent array manipulation skills",
                    "weakness": "Many struggle with array boundary conditions",
                    "improvement_needed": "Focus on array bounds checking and edge cases"
                },
                "loop_implementation": {
                    "strength": "Good understanding of basic loop structures",
                    "weakness": "Difficulty with nested loops and complex iterations",
                    "improvement_needed": "Practice with multi-dimensional array processing"
                }
            }
        elif topic == "Functions and Methods":
            concept_analysis = {
                "function_design": {
                    "strength": "Students demonstrate good function design principles",
                    "weakness": "Many struggle with recursive function implementation",
                    "improvement_needed": "Focus on recursive thinking and function scope"
                },
                "parameter_handling": {
                    "strength": "Good understanding of parameter passing",
                    "weakness": "Difficulty with complex parameter types",
                    "improvement_needed": "Practice with different parameter types and return values"
                }
            }
        elif topic == "Object-Oriented Programming":
            concept_analysis = {
                "class_design": {
                    "strength": "Students show good class design principles",
                    "weakness": "Many struggle with inheritance and polymorphism",
                    "improvement_needed": "Focus on inheritance hierarchies and method overriding"
                },
                "encapsulation": {
                    "strength": "Good understanding of basic encapsulation",
                    "weakness": "Difficulty with advanced OOP concepts",
                    "improvement_needed": "Practice with abstract classes and interfaces"
                }
            }
        else:
            concept_analysis = {
                "fundamentals": {
                    "strength": f"Students show good understanding of {topic.lower()} basics",
                    "weakness": f"Many struggle with advanced {topic.lower()} concepts",
                    "improvement_needed": f"Focus on advanced {topic.lower()} techniques and best practices"
                }
            }
        student_name1 = random.choice(student_names)
        student_name2 = random.choice(student_names)
        if topic == "Arrays and Lists":
            summary = f"Students in {rubric.section} demonstrate strong fundamentals in array operations but need improvement in handling edge cases and complex loop structures. {student_name1} shows particular promise in algorithm implementation while {student_name2} needs additional support with array boundary conditions."
        elif topic == "Functions and Methods":
            summary = f"Students in {rubric.section} show good function design skills but struggle with recursive implementation. {student_name1} demonstrates excellent parameter handling while {student_name2} needs help with function scope and return values."
        elif topic == "Object-Oriented Programming":
            summary = f"Students in {rubric.section} demonstrate good class design but need work on inheritance and polymorphism. {student_name1} shows strong encapsulation skills while {student_name2} needs support with abstract class concepts."
        else:
            summary = f"Students in {rubric.section} show good progress in {topic.lower()} with {student_name1} demonstrating strong fundamentals and {student_name2} needing additional practice with advanced concepts."
        lab_analytics_obj = LabAnalytics.objects.create(
            lab_name=rubric.lab_name,
            section=rubric.section,
            semester=rubric.semester,
            total_students=total_students,
            total_evaluations=total_evaluations,
            average_points_lost=average_points_lost,
            concept_performance=concept_analysis,
            performance_summary=summary,
            analysis_date=timezone.now()
        )
        lab_analytics.append(lab_analytics_obj)
    print(f"Created {len(performance_data)} student performance records and {len(lab_analytics)} lab analytics")
    return performance_data, lab_analytics


def main():
    """Main function to populate all databases"""
    print("Starting database population...")
    
    # Clear existing data (optional - comment out if you want to keep existing data)
    print("Clearing existing data...")
    Student.objects.all().delete()
    LabRubric.objects.all().delete()
    Evaluation.objects.all().delete()
    EvaluationSession.objects.all().delete()
    RequestMetrics.objects.all().delete()
    EvaluationMetrics.objects.all().delete()
    SystemMetrics.objects.all().delete()
    ErrorMetrics.objects.all().delete()
    PerformanceMetrics.objects.all().delete()
    StudentPerformance.objects.all().delete()
    LabAnalytics.objects.all().delete()
    
    # Create data
    rubrics = create_diverse_rubrics()
    students = create_students()
    evaluations, sessions = create_evaluations_and_sessions(students, rubrics)
    request_metrics = create_request_metrics()
    evaluation_metrics = create_evaluation_metrics(sessions)
    system_metrics = create_system_metrics()
    error_metrics = create_error_metrics()
    performance_metrics = create_performance_metrics()
    performance_data, lab_analytics = create_analytics_data(students, rubrics)
    
    print("\n" + "="*50)
    print("DATABASE POPULATION COMPLETE!")
    print("="*50)
    print(f"Created:")
    print(f"  - {len(rubrics)} rubrics")
    print(f"  - {len(students)} students")
    print(f"  - {len(evaluations)} evaluations")
    print(f"  - {len(sessions)} evaluation sessions")
    print(f"  - {len(request_metrics)} request metrics")
    print(f"  - {len(evaluation_metrics)} evaluation metrics")
    print(f"  - {len(system_metrics)} system metrics")
    print(f"  - {len(error_metrics)} error metrics")
    print(f"  - {len(performance_metrics)} performance metrics")
    print(f"  - {len(performance_data)} student performance records")
    print(f"  - {len(lab_analytics)} lab analytics")
    print("\nYour database is now populated with realistic test data!")
    print("You can now test all your API endpoints with this data.")


if __name__ == "__main__":
    main() 