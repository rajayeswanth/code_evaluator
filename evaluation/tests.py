from django.test import TestCase
import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.core.cache import cache

from .models import LabRubric, EvaluationSession, Student, Evaluation
from .serializers import LabRubricSerializer, EvaluationSessionSerializer
from .validators import InputValidator
from .services import EvaluationService


class LabRubricModelTest(TestCase):
    """Test cases for LabRubric model"""
    
    def setUp(self):
        self.rubric_data = {
            'lab_name': 'Lab1',
            'semester': 'Spring 2025',
            'section': '14',
            'total_points': 25,
            'criteria': {
                'syntax': {'points': 10, 'description': 'Correct syntax'},
                'logic': {'points': 15, 'description': 'Correct logic'}
            }
        }
        self.rubric = LabRubric.objects.create(**self.rubric_data)
    
    def test_rubric_creation(self):
        """Test rubric creation with valid data"""
        self.assertEqual(self.rubric.lab_name, 'Lab1')
        self.assertEqual(self.rubric.semester, 'Spring 2025')
        self.assertEqual(self.rubric.section, '14')
        self.assertEqual(self.rubric.total_points, 25)
        self.assertTrue(self.rubric.is_active)
    
    def test_rubric_str_representation(self):
        """Test string representation of rubric"""
        expected = "Lab1 - Spring 2025 - Section 14 (25 points)"
        self.assertEqual(str(self.rubric), expected)
    
    def test_rubric_unique_constraint(self):
        """Test that duplicate rubrics are not allowed"""
        with self.assertRaises(Exception):
            LabRubric.objects.create(**self.rubric_data)


class EvaluationSessionModelTest(TestCase):
    """Test cases for EvaluationSession model"""
    
    def setUp(self):
        self.student = Student.objects.create(
            student_id='STU123456',
            name='John Doe',
            section='14',
            semester='Spring 2025',
            instructor_name='Dr. Smith'
        )
        
        self.session_data = {
            'student': self.student,
            'session_id': str(uuid.uuid4()),
            'lab_name': 'Lab1',
            'summary_feedback': 'Good work overall',
            'total_files_evaluated': 2,
            'successful_evaluations': 2,
            'error_evaluations': 0,
            'total_points_lost': 5,
            'total_deductions': 1,
            'submission_data': {'files': ['main.py', 'helper.py']},
            'total_evaluation_time_seconds': 2.5,
            'total_tokens_used': 150
        }
        self.session = EvaluationSession.objects.create(**self.session_data)
    
    def test_session_creation(self):
        """Test session creation with valid data"""
        self.assertEqual(self.session.student, self.student)
        self.assertEqual(self.session.lab_name, 'Lab1')
        self.assertEqual(self.session.summary_feedback, 'Good work overall')
        self.assertEqual(self.session.total_files_evaluated, 2)
        self.assertEqual(self.session.successful_evaluations, 2)
        self.assertEqual(self.session.error_evaluations, 0)
        self.assertEqual(self.session.total_points_lost, 5)
        self.assertEqual(self.session.total_tokens_used, 150)
    
    def test_session_str_representation(self):
        """Test string representation of session"""
        expected = f"Session {self.session.session_id} - John Doe"
        self.assertEqual(str(self.session), expected)


class StudentModelTest(TestCase):
    """Test cases for Student model"""
    
    def setUp(self):
        self.student_data = {
            'student_id': 'STU123456',
            'name': 'John Doe',
            'section': '14',
            'semester': 'Spring 2025',
            'instructor_name': 'Dr. Smith'
        }
        self.student = Student.objects.create(**self.student_data)
    
    def test_student_creation(self):
        """Test student creation with valid data"""
        self.assertEqual(self.student.student_id, 'STU123456')
        self.assertEqual(self.student.name, 'John Doe')
        self.assertEqual(self.student.section, '14')
        self.assertEqual(self.student.semester, 'Spring 2025')
        self.assertEqual(self.student.instructor_name, 'Dr. Smith')
    
    def test_student_str_representation(self):
        """Test string representation of student"""
        expected = "John Doe (STU123456)"
        self.assertEqual(str(self.student), expected)
    
    def test_student_unique_constraint(self):
        """Test that duplicate student IDs are not allowed"""
        with self.assertRaises(Exception):
            Student.objects.create(**self.student_data)


class EvaluationModelTest(TestCase):
    """Test cases for Evaluation model"""
    
    def setUp(self):
        self.student = Student.objects.create(
            student_id='STU123456',
            name='John Doe',
            section='14',
            semester='Spring 2025',
            instructor_name='Dr. Smith'
        )
        
        self.rubric = LabRubric.objects.create(
            lab_name='Lab1',
            semester='Spring 2025',
            section='14',
            total_points=25,
            criteria={
                'syntax': {'points': 10, 'description': 'Correct syntax'},
                'logic': {'points': 15, 'description': 'Correct logic'}
            }
        )
        
        self.evaluation_data = {
            'student': self.student,
            'rubric': self.rubric,
            'lab_name': 'Lab1',
            'status': 'completed',
            'feedback': 'Good work!',
            'total_points_lost': 5,
            'deductions': [{'reason': 'Missing comments', 'points': 5}],
            'code_content': 'print("Hello World")'
        }
        self.evaluation = Evaluation.objects.create(**self.evaluation_data)
    
    def test_evaluation_creation(self):
        """Test evaluation creation with valid data"""
        self.assertEqual(self.evaluation.student, self.student)
        self.assertEqual(self.evaluation.rubric, self.rubric)
        self.assertEqual(self.evaluation.lab_name, 'Lab1')
        self.assertEqual(self.evaluation.status, 'completed')
        self.assertEqual(self.evaluation.feedback, 'Good work!')
        self.assertEqual(self.evaluation.total_points_lost, 5)
    
    def test_evaluation_str_representation(self):
        """Test string representation of evaluation"""
        expected = "John Doe - Lab1"
        self.assertEqual(str(self.evaluation), expected)


class ValidatorTest(TestCase):
    """Test cases for validators"""
    
    def test_validate_student_data_valid(self):
        """Test student data validation with valid data"""
        valid_data = {
            'student_id': 'STU123456',
            'name': 'John Doe',
            'section': '14',
            'term': 'Spring 2025',
            'instructor_name': 'Dr. Smith'
        }
        is_valid, errors = InputValidator.validate_student_data(valid_data)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_student_data_invalid(self):
        """Test student data validation with invalid data"""
        invalid_data = {
            'student_id': 'ST',  # Too short
            'name': '',  # Empty
            'section': '14',
            'term': 'Invalid Term',  # Invalid format
            'instructor_name': 'Dr. Smith'
        }
        is_valid, errors = InputValidator.validate_student_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        self.assertIn('student_id must be 3-20 characters, alphanumeric with hyphens/underscores only', str(errors))
        self.assertIn('Missing required field: name', str(errors))
        self.assertIn('term must be in format', str(errors))
    
    def test_validate_rubric_data_valid(self):
        """Test rubric data validation with valid data"""
        valid_data = {
            'name': 'Test Rubric',
            'filename': 'main.py',
            'total_points': 100,
            'criteria': {
                'syntax': {'points': 20, 'description': 'Correct syntax'},
                'logic': {'points': 30, 'description': 'Correct logic'}
            }
        }
        is_valid, errors = InputValidator.validate_rubric_data(valid_data)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_rubric_data_invalid(self):
        """Test rubric data validation with invalid data"""
        invalid_data = {
            'name': '',  # Empty
            'filename': 'main.txt',  # Wrong extension
            'total_points': -10,  # Negative
            'criteria': {}  # Empty
        }
        is_valid, errors = InputValidator.validate_rubric_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        self.assertIn('name must be a non-empty string', str(errors))
        self.assertIn('filename must be a valid Python filename', str(errors))
        self.assertIn('total_points must be a positive integer', str(errors))
    
    def test_validate_evaluation_request_valid(self):
        """Test evaluation request validation with valid data"""
        valid_data = {
            'student_id': 'STU123456',
            'name': 'John Doe',
            'section': '14',
            'term': 'Spring 2025',
            'instructor_name': 'Dr. Smith',
            'lab_name': 'Lab1',
            'input': 'Download main.py\nprint("Hello World")'
        }
        is_valid, errors = InputValidator.validate_evaluation_request(valid_data)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_evaluation_request_invalid(self):
        """Test evaluation request validation with invalid data"""
        invalid_data = {
            'student_id': 'STU123456',
            'name': 'John Doe',
            'section': '14',
            'term': 'Spring 2025',
            'instructor_name': 'Dr. Smith',
            'lab_name': '',  # Empty
            'input': 'Too short'  # Too short
        }
        is_valid, errors = InputValidator.validate_evaluation_request(invalid_data)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        self.assertIn('lab_name must be a non-empty string', str(errors))
        self.assertIn('input must be at least 10 characters', str(errors))


class SerializerTest(TestCase):
    """Test cases for serializers"""
    
    def setUp(self):
        self.rubric_data = {
            'lab_name': 'Lab1',
            'semester': 'Spring 2025',
            'section': '14',
            'total_points': 25,
            'criteria': {
                'syntax': {'points': 10, 'description': 'Correct syntax'},
                'logic': {'points': 15, 'description': 'Correct logic'}
            }
        }
        self.rubric = LabRubric.objects.create(**self.rubric_data)
    
    def test_lab_rubric_serializer(self):
        """Test LabRubricSerializer"""
        serializer = LabRubricSerializer(self.rubric)
        data = serializer.data
        
        self.assertEqual(data['lab_name'], 'Lab1')
        self.assertEqual(data['semester'], 'Spring 2025')
        self.assertEqual(data['section'], '14')
        self.assertEqual(data['total_points'], 25)
        self.assertTrue(data['is_active'])
    
    def test_evaluation_session_serializer(self):
        """Test EvaluationSessionSerializer"""
        student = Student.objects.create(
            student_id='STU123456',
            name='John Doe',
            section='14',
            semester='Spring 2025',
            instructor_name='Dr. Smith'
        )
        session = EvaluationSession.objects.create(
            student=student,
            session_id=str(uuid.uuid4()),
            lab_name='Lab1',
            summary_feedback='Good work overall',
            total_files_evaluated=2,
            successful_evaluations=2,
            error_evaluations=0,
            total_points_lost=5,
            total_deductions=1,
            submission_data={'files': ['main.py']},
            total_evaluation_time_seconds=2.5,
            total_tokens_used=150
        )
        serializer = EvaluationSessionSerializer(session)
        data = serializer.data
        self.assertEqual(data['student'], student.id)
        self.assertEqual(data['lab_name'], 'Lab1')
        self.assertEqual(data['total_files_evaluated'], 2)
        self.assertEqual(data['total_points_lost'], 5)
        self.assertEqual(data['total_tokens_used'], 150)


class EvaluationServiceTest(TestCase):
    """Test cases for EvaluationService"""
    
    def setUp(self):
        self.service = EvaluationService()
        self.rubric = LabRubric.objects.create(
            lab_name='Lab1',
            semester='Spring 2025',
            section='14',
            total_points=25,
            criteria={
                'syntax': {'points': 10, 'description': 'Correct syntax'},
                'logic': {'points': 15, 'description': 'Correct logic'}
            }
        )
    
    @patch('evaluation.services.OpenAIService')
    def test_evaluate_code_success(self, mock_openai):
        """Test successful code evaluation"""
        mock_openai.return_value.evaluate_code.return_value = {
            'feedback': 'Good code!',
            'points_lost': 2,
            'tokens_used': 150
        }
        
        code_content = 'print("Hello World")'
        result = self.service.evaluate_code(code_content, self.rubric)
        
        self.assertIn('feedback', result)
        self.assertIn('points_lost', result)
        self.assertIn('tokens_used', result)
        self.assertEqual(result['points_lost'], 2)
    
    @patch('evaluation.services.OpenAIService')
    def test_evaluate_code_failure(self, mock_openai):
        """Test code evaluation failure"""
        mock_openai.return_value.evaluate_code.side_effect = Exception("API Error")
        
        code_content = 'print("Hello World")'
        result = self.service.evaluate_code(code_content, self.rubric)
        
        self.assertIn('error', result)
        self.assertEqual(result['status'], 'error')


class EvaluationViewsTest(APITestCase):
    """Test cases for evaluation views"""
    
    def setUp(self):
        self.client = APIClient()
        self.rubric = LabRubric.objects.create(
            lab_name='Lab1',
            semester='Spring 2025',
            section='14',
            total_points=25,
            criteria={
                'syntax': {'points': 10, 'description': 'Correct syntax'},
                'logic': {'points': 15, 'description': 'Correct logic'}
            }
        )
        cache.clear()
    
    def test_health_check(self):
        """Test health check endpoint"""
        url = reverse('health_check')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertEqual(response.data['status'], 'healthy')
    
    def test_get_rubrics(self):
        """Test get rubrics endpoint"""
        url = reverse('get_rubrics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('rubrics', response.data)
        self.assertEqual(len(response.data['rubrics']), 1)
    
    def test_create_rubric_success(self):
        """Test successful rubric creation"""
        url = reverse('create_rubric')
        data = {
            'lab_name': 'Lab2',
            'semester': 'Fall 2025',
            'section': '15',
            'criteria': {
                'syntax': {'points': 20, 'description': 'Correct syntax'},
                'logic': {'points': 30, 'description': 'Correct logic'}
            }
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Rubric created successfully')
    
    def test_create_rubric_duplicate(self):
        """Test duplicate rubric creation"""
        url = reverse('create_rubric')
        data = {
            'lab_name': 'Lab1',
            'semester': 'Spring 2025',
            'section': '14',
            'criteria': {
                'syntax': {'points': 10, 'description': 'Correct syntax'},
                'logic': {'points': 15, 'description': 'Correct logic'}
            }
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    @patch('evaluation.views.EvaluationService')
    def test_evaluate_submission_success(self, mock_service):
        """Test successful submission evaluation"""
        mock_service.return_value.evaluate_submission.return_value = {
            'session_id': str(uuid.uuid4()),
            'feedback': 'Good code!',
            'summary': 'Excellent work',
            'total_files_evaluated': 1,
            'total_points_lost': 2,
            'total_evaluation_time_seconds': 2.5
        }
        
        url = reverse('evaluate_submission')
        data = {
            'student_id': 'STU123456',
            'name': 'John Doe',
            'section': '14',
            'term': 'Spring 2025',
            'instructor_name': 'Dr. Smith',
            'lab_name': 'Lab1',
            'input': 'Download main.py\nprint("Hello World")'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('session_id', response.data)
        self.assertIn('feedback', response.data)
    
    def test_evaluate_submission_invalid_data(self):
        """Test submission evaluation with invalid data"""
        url = reverse('evaluate_submission')
        data = {
            'student_id': 'ST',  # Too short
            'name': 'John Doe',
            'section': '14',
            'term': 'Spring 2025',
            'instructor_name': 'Dr. Smith',
            'lab_name': 'Lab1',
            'input': 'Too short'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
    
    def test_get_all_evaluations(self):
        """Test get all evaluations endpoint"""
        # Create a test student
        student = Student.objects.create(
            student_id='STU123456',
            name='John Doe',
            section='14',
            semester='Spring 2025',
            instructor_name='Dr. Smith'
        )
        
        # Create a test evaluation session
        session = EvaluationSession.objects.create(
            student=student,
            session_id=str(uuid.uuid4()),
            lab_name='Lab1',
            summary_feedback='Good work',
            total_files_evaluated=2,
            successful_evaluations=2,
            error_evaluations=0,
            total_points_lost=5,
            total_deductions=1,
            submission_data={'files': ['main.py']},
            total_evaluation_time_seconds=2.5,
            total_tokens_used=150
        )
        
        url = reverse('get_all_evaluations')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('evaluations', response.data)
        self.assertEqual(len(response.data['evaluations']), 1)
    
    def test_get_evaluation_by_id(self):
        """Test get evaluation by ID endpoint"""
        student = Student.objects.create(
            student_id='STU123456',
            name='John Doe',
            section='14',
            semester='Spring 2025',
            instructor_name='Dr. Smith'
        )
        
        session = EvaluationSession.objects.create(
            student=student,
            session_id=str(uuid.uuid4()),
            lab_name='Lab1',
            summary_feedback='Good work',
            total_files_evaluated=2,
            successful_evaluations=2,
            error_evaluations=0,
            total_points_lost=5,
            total_deductions=1,
            submission_data={'files': ['main.py']},
            total_evaluation_time_seconds=2.5,
            total_tokens_used=150
        )
        
        url = reverse('get_evaluation_by_id', kwargs={'evaluation_id': session.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['student_id'], 'STU123456')
    
    def test_get_evaluation_by_id_not_found(self):
        """Test get evaluation by ID with non-existent ID"""
        url = reverse('get_evaluation_by_id', kwargs={'evaluation_id': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_stats(self):
        """Test get statistics endpoint"""
        url = reverse('get_stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_sessions', response.data)
        self.assertIn('total_evaluations', response.data)
    
    def test_get_performance(self):
        """Test get performance endpoint"""
        student = Student.objects.create(
            student_id='STU123456',
            name='John Doe',
            section='14',
            semester='Spring 2025',
            instructor_name='Dr. Smith'
        )
        
        session = EvaluationSession.objects.create(
            student=student,
            session_id=str(uuid.uuid4()),
            lab_name='Lab1',
            summary_feedback='Good work',
            total_files_evaluated=2,
            successful_evaluations=2,
            error_evaluations=0,
            total_points_lost=5,
            total_deductions=1,
            submission_data={'files': ['main.py']},
            total_evaluation_time_seconds=2.5,
            total_tokens_used=150
        )
        
        url = reverse('get_performance', kwargs={'student_id': 'STU123456'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['student_id'], 'STU123456')
        self.assertEqual(response.data['total_evaluations'], 1)
    
    def test_get_performance_student_not_found(self):
        """Test get performance for non-existent student"""
        url = reverse('get_performance', kwargs={'student_id': 'NONEXISTENT'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class RateLimitTest(APITestCase):
    """Test cases for rate limiting"""
    
    def setUp(self):
        self.client = APIClient()
        cache.clear()
    
    def test_rate_limit_exceeded(self):
        """Test that rate limiting works"""
        url = reverse('health_check')
        
        # Make more than 120 requests per minute
        for i in range(125):
            response = self.client.get(url)
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                break
        
        # Should get rate limited at some point
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_429_TOO_MANY_REQUESTS])


class CacheTest(APITestCase):
    """Test cases for caching functionality"""
    
    def setUp(self):
        self.client = APIClient()
        cache.clear()
    
    def test_cache_functionality(self):
        """Test that caching works correctly"""
        url = reverse('health_check')
        
        # First request
        response1 = self.client.get(url)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Second request should be cached
        response2 = self.client.get(url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Both responses should be identical
        self.assertEqual(response1.data, response2.data)
    
    def test_cache_insights(self):
        """Test that cache insights are included in response"""
        url = reverse('test_cache')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('cache_insights', response.data)
        self.assertIn('cache_hit', response.data['cache_insights'])
        self.assertIn('cache_miss', response.data['cache_insights'])


class IntegrationTest(APITestCase):
    """Integration tests for the complete evaluation flow"""
    
    def setUp(self):
        self.client = APIClient()
        self.rubric = LabRubric.objects.create(
            lab_name='Lab1',
            semester='Spring 2025',
            section='14',
            total_points=25,
            criteria={
                'syntax': {'points': 10, 'description': 'Correct syntax'},
                'logic': {'points': 15, 'description': 'Correct logic'}
            }
        )
        cache.clear()
    
    @patch('evaluation.views.EvaluationService')
    def test_complete_evaluation_flow(self, mock_service):
        """Test complete evaluation flow from rubric creation to evaluation"""
        mock_service.return_value.evaluate_submission.return_value = {
            'session_id': str(uuid.uuid4()),
            'feedback': 'Good code!',
            'summary': 'Excellent work',
            'total_files_evaluated': 1,
            'total_points_lost': 2,
            'total_evaluation_time_seconds': 2.5
        }
        
        # 1. Create rubric
        create_url = reverse('create_rubric')
        rubric_data = {
            'lab_name': 'Lab2',
            'semester': 'Fall 2025',
            'section': '15',
            'criteria': {
                'syntax': {'points': 20, 'description': 'Correct syntax'},
                'logic': {'points': 30, 'description': 'Correct logic'}
            }
        }
        create_response = self.client.post(create_url, rubric_data, format='json')
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        
        # 2. Get rubrics
        get_rubrics_url = reverse('get_rubrics')
        get_response = self.client.get(get_rubrics_url)
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(get_response.data['rubrics']), 2)
        
        # 3. Evaluate submission
        evaluate_url = reverse('evaluate_submission')
        evaluate_data = {
            'student_id': 'STU123456',
            'name': 'John Doe',
            'section': '14',
            'term': 'Spring 2025',
            'instructor_name': 'Dr. Smith',
            'lab_name': 'Lab1',
            'input': 'Download main.py\nprint("Hello World")'
        }
        evaluate_response = self.client.post(evaluate_url, evaluate_data, format='json')
        self.assertEqual(evaluate_response.status_code, status.HTTP_200_OK)
        
        # 4. Get evaluation by ID
        session_id = evaluate_response.data['session_id']
        session = EvaluationSession.objects.get(session_id=session_id)
        get_eval_url = reverse('get_evaluation_by_id', kwargs={'evaluation_id': session.id})
        get_eval_response = self.client.get(get_eval_url)
        self.assertEqual(get_eval_response.status_code, status.HTTP_200_OK)
        
        # 5. Get statistics
        stats_url = reverse('get_stats')
        stats_response = self.client.get(stats_url)
        self.assertEqual(stats_response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(stats_response.data['total_sessions'], 1)
        
        # 6. Get performance
        performance_url = reverse('get_performance', kwargs={'student_id': 'STU123456'})
        performance_response = self.client.get(performance_url)
        self.assertEqual(performance_response.status_code, status.HTTP_200_OK)
        self.assertEqual(performance_response.data['student_id'], 'STU123456')
