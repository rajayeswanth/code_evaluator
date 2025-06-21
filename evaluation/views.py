from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.utils import timezone
import json
import uuid
import time
from metrics_service.monitor import metrics_monitor
from metrics_service.models import EvaluationMetrics, RequestMetrics
from datetime import datetime, timedelta
import logging
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Sum, Avg
from cache_utils import cache_api_response, get_cache_stats
import random
from django_ratelimit.decorators import ratelimit
from django_ratelimit.core import is_ratelimited

from .serializers import (
    LabRubricSerializer, StudentSerializer, EvaluationSerializer, 
    RubricCreateSerializer, RubricGetSerializer, EvaluationRequestSerializer, EvaluationResponseSerializer
)
from .models import LabRubric, Student, Evaluation, EvaluationSession
from data_service.file_processor import FileProcessor
from evaluator_service.code_evaluator import CodeEvaluator
from evaluator_service.openai_service import openai_service
from .validators import InputValidator
from .services import EvaluationService
from metrics_service.monitor import MetricsMonitor

# Set up logging
logger = logging.getLogger('evaluation')
api_logger = logging.getLogger('api_requests')
db_logger = logging.getLogger('database_operations')
activity_logger = logging.getLogger('user_activity')

# Initialize services
evaluation_service = EvaluationService()
metrics_monitor = MetricsMonitor()

# Simple API views

@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='10/m', method='POST', block=True)  # 10 evaluations per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def create_rubric(request):
    """Create a new rubric for a lab"""
    start_time = time.time()
    try:
        serializer = RubricCreateSerializer(data=request.data)
        if not serializer.is_valid():
            response = Response({
                'error': 'Invalid data',
                'details': serializer.errors
            }, status=400)
            metrics_monitor.track_request(request, response, (time.time() - start_time) * 1000, 0, 0.0, 0, 0, 0)
            return response
        
        data = serializer.validated_data
        
        # Calculate total points from rubrics
        total_points = 0
        for criterion, details in data['rubrics'].items():
            total_points += details.get('points', 0)
        
        rubric = LabRubric.objects.create(
            lab_name=data['lab'],
            semester=f"{data['semester']} {data['year']}",
            section=data['section'],
            total_points=total_points,
            criteria=data['rubrics']
        )
        
        response = Response({
            'message': 'Rubric created successfully',
            'rubric_id': rubric.id
        }, status=201)
        metrics_monitor.track_request(request, response, (time.time() - start_time) * 1000, 0, 0.0, 0, 0, 0)
        return response
        
    except Exception as e:
        response = Response({
            'error': 'Failed to create rubric',
            'details': str(e)
        }, status=500)
        metrics_monitor.track_request(request, response, (time.time() - start_time) * 1000, 0, 0.0, 0, 0, 0)
        return response


@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='10/m', method='POST', block=True)  # 10 evaluations per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def get_rubric_id(request):
    """Get rubric ID by lab details"""
    start_time = time.time()
    try:
        serializer = RubricGetSerializer(data=request.data)
        if not serializer.is_valid():
            response = Response({
                'error': 'Invalid data',
                'details': serializer.errors
            }, status=400)
            metrics_monitor.track_request(request, response, (time.time() - start_time) * 1000, 0, 0.0, 0, 0, 0)
            return response
        
        data = serializer.validated_data
        semester_year = f"{data['semester']} {data['year']}"
        
        rubric = LabRubric.objects.get(
            lab_name=data['lab'],
            semester=semester_year,
            section=data['section'],
            is_active=True
        )
        
        response = Response({
            'rubric_id': rubric.id,
            'lab_name': rubric.lab_name,
            'total_points': rubric.total_points
        })
        metrics_monitor.track_request(request, response, (time.time() - start_time) * 1000, 0, 0.0, 0, 0, 0)
        return response
        
    except LabRubric.DoesNotExist:
        response = Response({
            'error': 'Rubric not found'
        }, status=404)
        metrics_monitor.track_request(request, response, (time.time() - start_time) * 1000, 0, 0.0, 0, 0, 0)
        return response
    except Exception as e:
        response = Response({
            'error': 'Failed to get rubric',
            'details': str(e)
        }, status=500)
        metrics_monitor.track_request(request, response, (time.time() - start_time) * 1000, 0, 0.0, 0, 0, 0)
        return response


@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='10/m', method='POST', block=True)  # 10 evaluations per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def evaluate_submission(request):
    """Evaluate student code submission"""
    start_time = time.time()
    
    # Log API request
    api_logger.info(f"API Request: {request.method} {request.path} - Student: {request.data.get('student_id', 'Unknown')} - Lab: {request.data.get('lab_name', 'Unknown')}")
    
    try:
        serializer = EvaluationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Validation failed: {serializer.errors}")
            response = Response({
                'error': 'Invalid data',
                'details': serializer.errors
            }, status=400)
            metrics_monitor.track_request(request, response, (time.time() - start_time) * 1000, 0, 0.0, 0, 0, 0)
            return response
        
        data = serializer.validated_data
        logger.info(f"Starting evaluation for student {data['student_id']} - Lab: {data['lab_name']}")
        
        # Get or create student
        db_logger.info(f"Database operation: Get or create student {data['student_id']}")
        student, created = Student.objects.get_or_create(
            student_id=data['student_id'],
            defaults={
                'name': data['name'],
                'section': data['section'],
                'semester': data['semester'],
                'instructor_name': data['instructor_name']
            }
        )
        
        if created:
            logger.info(f"Created new student: {data['student_id']}")
            db_logger.info(f"Database operation: Created new student record for {data['student_id']}")
        else:
            db_logger.info(f"Database operation: Retrieved existing student {data['student_id']}")
        
        # Get rubric
        try:
            db_logger.info(f"Database operation: Get rubric by ID {data['rubric_id']}")
            rubric = LabRubric.objects.get(id=data['rubric_id'])
            logger.info(f"Using rubric ID: {data['rubric_id']} for lab: {data['lab_name']}")
        except LabRubric.DoesNotExist:
            logger.error(f"Rubric not found: ID {data['rubric_id']}")
            db_logger.error(f"Database operation: Rubric not found with ID {data['rubric_id']}")
            return Response({
                'error': 'Rubric not found'
            }, status=404)
        
        # Process input
        processor = FileProcessor()
        files = processor.parse_input(data['input'])
        
        if not files:
            logger.error(f"No valid files found in input for student {data['student_id']}")
            return Response({
                'error': 'No valid files found in input'
            }, status=400)
        
        logger.info(f"Processing {len(files)} files for student {data['student_id']}")
        
        # Check for existing evaluation for this student and lab
        db_logger.info(f"Database operation: Check existing evaluation for student {data['student_id']} lab {data['lab_name']}")
        existing_evaluation = Evaluation.objects.filter(
            student=student,
            lab_name=data['lab_name'],
            rubric=rubric
        ).first()
        
        # Check for existing session for this student and lab
        db_logger.info(f"Database operation: Check existing session for student {data['student_id']} lab {data['lab_name']}")
        existing_session = EvaluationSession.objects.filter(
            student=student,
            lab_name=data['lab_name']
        ).first()
        
        if existing_evaluation:
            logger.info(f"Updating existing evaluation for student {data['student_id']} - Lab: {data['lab_name']}")
            db_logger.info(f"Database operation: Found existing evaluation for student {data['student_id']}")
        
        if existing_session:
            db_logger.info(f"Database operation: Found existing session for student {data['student_id']}")
        
        # Evaluate code
        evaluator = CodeEvaluator()
        evaluation_start_time = time.time()
        
        logger.info(f"Starting code evaluation for student {data['student_id']}")
        result = evaluator.evaluate_all_files(files, rubric.criteria)
        
        evaluation_time = time.time() - evaluation_start_time
        logger.info(f"Evaluation completed in {evaluation_time:.2f}s for student {data['student_id']}")
        
        # Get actual token usage and LLM calls from evaluation result
        total_tokens = result.get('total_tokens', 0)
        input_tokens = result.get('total_input_tokens', 0)
        output_tokens = result.get('total_output_tokens', 0)
        llm_calls_count = result.get('llm_calls_count', 0)
        
        logger.info(f"Token usage - Total: {total_tokens}, Input: {input_tokens}, Output: {output_tokens}, LLM calls: {llm_calls_count}")
        
        # Calculate cost based on actual tokens (gpt-4.1-nano pricing)
        estimated_cost = (input_tokens * 0.00015 + output_tokens * 0.0006) / 1000  # Per 1K tokens
        
        # Create session ID first
        session_id = str(uuid.uuid4())
        
        # Track evaluation metrics
        metrics_monitor.track_evaluation(
            session_id=session_id,
            student_id=data['student_id'],
            lab_name=data['lab_name'],
            total_files=len(files),
            successful_files=len(files),
            failed_files=0,
            total_tokens=total_tokens,
            total_cost=estimated_cost,
            evaluation_time=evaluation_time
        )
        
        # Convert lab_feedback to JSON string for storage
        lab_feedback_json = json.dumps(result['lab_feedback'])
        
        # Update existing session or create new one
        if existing_session:
            db_logger.info(f"Database operation: Update existing session {session_id} for student {data['student_id']}")
            existing_session.summary_feedback = result['overall_feedback']
            existing_session.total_files_evaluated = result['files_evaluated']
            existing_session.successful_evaluations = len(files)
            existing_session.error_evaluations = 0
            existing_session.total_points_lost = result['total_points_lost']
            existing_session.total_deductions = result['total_points_lost']
            existing_session.submission_data = {'files': list(files.keys()), 'lab_feedback': result['lab_feedback']}
            existing_session.total_evaluation_time_seconds = evaluation_time
            existing_session.total_tokens_used = total_tokens
            existing_session.save()
            session = existing_session
            logger.info(f"Updated existing session {session_id} for student {data['student_id']}")
        else:
            db_logger.info(f"Database operation: Create new session {session_id} for student {data['student_id']}")
            session = EvaluationSession.objects.create(
                student=student,
                session_id=session_id,
                lab_name=data['lab_name'],
                summary_feedback=result['overall_feedback'],
                total_files_evaluated=result['files_evaluated'],
                successful_evaluations=len(files),
                error_evaluations=0,
                total_points_lost=result['total_points_lost'],
                total_deductions=result['total_points_lost'],
                submission_data={'files': list(files.keys()), 'lab_feedback': result['lab_feedback']},
                total_evaluation_time_seconds=evaluation_time,
                total_tokens_used=total_tokens
            )
            logger.info(f"Created new session {session_id} for student {data['student_id']}")
        
        # Update existing evaluation or create new one
        if existing_evaluation:
            db_logger.info(f"Database operation: Update existing evaluation {evaluation.id} for student {data['student_id']}")
            existing_evaluation.status = 'completed'
            existing_evaluation.feedback = lab_feedback_json
            existing_evaluation.total_points_lost = result['total_points_lost']
            existing_evaluation.deductions = result.get('file_results', [])
            existing_evaluation.code_content = data['input']
            existing_evaluation.save()
            evaluation = existing_evaluation
            logger.info(f"Updated existing evaluation {evaluation.id} for student {data['student_id']}")
        else:
            db_logger.info(f"Database operation: Create new evaluation for student {data['student_id']}")
            evaluation = Evaluation.objects.create(
                student=student,
                rubric=rubric,
                lab_name=data['lab_name'],
                status='completed',
                feedback=lab_feedback_json,
                total_points_lost=result['total_points_lost'],
                deductions=result.get('file_results', []),
                code_content=data['input']
            )
            logger.info(f"Created new evaluation {evaluation.id} for student {data['student_id']}")
        
        response = Response({
            'evaluation_id': evaluation.id,
            'session_id': session_id,
            'lab_feedback': result['lab_feedback'],
            'overall_feedback': result['overall_feedback'],
            'total_files_evaluated': len(files),
            'total_points_lost': result['total_points_lost'],
            'total_evaluation_time_seconds': evaluation_time
        })
        
        total_time = (time.time() - start_time) * 1000
        logger.info(f"Evaluation completed successfully for student {data['student_id']} - Total time: {total_time:.2f}ms - Points lost: {result['total_points_lost']}")
        
        metrics_monitor.track_request(request, response, total_time, total_tokens, estimated_cost, input_tokens, output_tokens, llm_calls_count)
        return response
        
    except Exception as e:
        logger.error(f"Evaluation failed for student {request.data.get('student_id', 'Unknown')}: {str(e)}", exc_info=True)
        response = Response({
            'error': 'Evaluation failed',
            'details': str(e)
        }, status=500)
        metrics_monitor.track_request(request, response, (time.time() - start_time) * 1000, 0, 0.0, 0, 0, 0)
        return response


@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)  # 60 requests per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def get_rubrics(request):
    """Get all rubrics with pagination"""
    start_time = time.time()
    try:
        # Get pagination parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 10
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get total count
        total_count = LabRubric.objects.filter(is_active=True).count()
        
        # Get paginated rubrics
        rubrics = LabRubric.objects.filter(is_active=True).order_by('-created_at')[offset:offset + page_size]
        serializer = LabRubricSerializer(rubrics, many=True)
        
        # Calculate pagination info
        total_pages = (total_count + page_size - 1) // page_size
        has_next = page < total_pages
        has_previous = page > 1
        
        response = Response({
            'total_count': total_count,
            'rubrics': serializer.data,
            'pagination': {
                'current_page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': has_next,
                'has_previous': has_previous,
                'next_page': page + 1 if has_next else None,
                'previous_page': page - 1 if has_previous else None
            }
        })
        metrics_monitor.track_request(request, response, (time.time() - start_time) * 1000, 0, 0.0, 0, 0, 0)
        return response
        
    except Exception as e:
        response = Response({
            'error': 'Failed to get rubrics',
            'details': str(e)
        }, status=500)
        metrics_monitor.track_request(request, response, (time.time() - start_time) * 1000, 0, 0.0, 0, 0, 0)
        return response


@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='120/m', method='GET', block=True)  # 120 requests per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def health_check(request):
    """Simple health check"""
    start_time = time.time()
    response = Response({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat()
    })
    metrics_monitor.track_request(request, response, (time.time() - start_time) * 1000, 0, 0.0, 0, 0, 0)
    return response

@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)  # 60 requests per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def get_all_evaluations(request):
    """Get all evaluations with pagination"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 20
        offset = (page - 1) * page_size
        total_count = Evaluation.objects.count()
        evaluations = Evaluation.objects.all().order_by('-id')[offset:offset + page_size]
        total_pages = (total_count + page_size - 1) // page_size
        has_next = page < total_pages
        has_previous = page > 1
        data = []
        for e in evaluations:
            data.append({
                'id': e.id,
                'student_id': e.student.student_id if e.student else None,
                'student_name': e.student.name if e.student else None,
                'lab_name': e.lab_name,
                'rubric_id': e.rubric.id if e.rubric else None,
                'status': e.status,
                'feedback': e.feedback,
                'total_points_lost': e.total_points_lost,
                'deductions': e.deductions,
                'code_content': e.code_content,
                'created_at': e.created_at.isoformat() if hasattr(e, 'created_at') and e.created_at else None,
                'updated_at': e.updated_at.isoformat() if hasattr(e, 'updated_at') and e.updated_at else None
            })
        return Response({
            'total_count': total_count,
            'evaluations': data,
            'pagination': {
                'current_page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': has_next,
                'has_previous': has_previous,
                'next_page': page + 1 if has_next else None,
                'previous_page': page - 1 if has_previous else None
            }
        })
    except Exception as e:
        return Response({'error': 'Failed to get evaluations', 'details': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)  # 60 requests per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def get_evaluation_by_id(request, evaluation_id):
    """Get a single evaluation by its ID"""
    try:
        e = Evaluation.objects.get(id=evaluation_id)
        data = {
            'id': e.id,
            'student_id': e.student.student_id if e.student else None,
            'student_name': e.student.name if e.student else None,
            'lab_name': e.lab_name,
            'rubric_id': e.rubric.id if e.rubric else None,
            'status': e.status,
            'feedback': e.feedback,
            'total_points_lost': e.total_points_lost,
            'deductions': e.deductions,
            'code_content': e.code_content,
            'created_at': e.created_at.isoformat() if hasattr(e, 'created_at') and e.created_at else None,
            'updated_at': e.updated_at.isoformat() if hasattr(e, 'updated_at') and e.updated_at else None
        }
        return Response(data)
    except Evaluation.DoesNotExist:
        return Response({'error': 'Evaluation not found'}, status=404)
    except Exception as e:
        return Response({'error': 'Failed to get evaluation', 'details': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)  # 60 requests per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def get_llm_metrics_by_evaluation(request, evaluation_id):
    """Get detailed LLM metrics for a specific evaluation"""
    try:
        # Get the evaluation
        evaluation = Evaluation.objects.get(id=evaluation_id)
        
        # Get the session for this evaluation
        session = EvaluationSession.objects.filter(
            student=evaluation.student,
            lab_name=evaluation.lab_name
        ).first()
        
        if not session:
            return Response({
                'error': 'Session not found for this evaluation'
            }, status=404)
        
        # Try to find RequestMetrics using multiple strategies
        request_metrics = None
        
        # Strategy 1: Find by time proximity (within 5 minutes)
        request_metrics = RequestMetrics.objects.filter(
            timestamp__gte=session.created_at - timedelta(minutes=5),
            timestamp__lte=session.created_at + timedelta(minutes=5),
            endpoint='/api/evaluation/evaluate/'
        ).order_by('-timestamp').first()
        
        # Strategy 2: If no time match, find by token usage proximity
        if not request_metrics and session.total_tokens_used:
            request_metrics = RequestMetrics.objects.filter(
                endpoint='/api/evaluation/evaluate/',
                tokens_used__gte=session.total_tokens_used - 100,
                tokens_used__lte=session.total_tokens_used + 100
            ).order_by('-timestamp').first()
        
        # Strategy 3: Get the most recent evaluate metrics if still no match
        if not request_metrics:
            request_metrics = RequestMetrics.objects.filter(
                endpoint='/api/evaluation/evaluate/'
            ).order_by('-timestamp').first()
        
        # Get evaluation metrics
        evaluation_metrics = EvaluationMetrics.objects.filter(
            session_id=session.session_id
        ).first()
        
        # Combine data from all sources
        response_data = {
            'session_id': session.session_id,
            'total_tokens_used': session.total_tokens_used or 0,
            'evaluation_time_seconds': session.total_evaluation_time_seconds or 0,
            'total_cost_usd': 0.0,
            'accuracy_score': 0.0,
            'feedback_quality_score': 0.0
        }
        
        # Add RequestMetrics data if available
        if request_metrics:
            response_data.update({
                'llm_calls_count': request_metrics.llm_calls_count,
                'input_tokens': request_metrics.input_tokens,
                'output_tokens': request_metrics.output_tokens,
                'avg_tokens_per_call': request_metrics.avg_tokens_per_call,
                'estimated_cost_usd': request_metrics.estimated_cost_usd,
                'memory_usage_mb': request_metrics.memory_usage_mb,
                'cpu_usage_percent': request_metrics.cpu_usage_percent,
                'response_time_ms': request_metrics.response_time_ms,
                'total_tokens': request_metrics.tokens_used,
                'total_cost_usd': request_metrics.estimated_cost_usd or 0.0,
                'metrics_source': 'request_metrics_found'
            })
        else:
            # Set default values if no RequestMetrics found
            response_data.update({
                'llm_calls_count': None,
                'input_tokens': None,
                'output_tokens': None,
                'avg_tokens_per_call': None,
                'estimated_cost_usd': None,
                'memory_usage_mb': None,
                'cpu_usage_percent': None,
                'response_time_ms': None,
                'total_tokens': session.total_tokens_used or 0,
                'metrics_source': 'no_request_metrics_found'
            })
        
        # Add EvaluationMetrics data if available
        if evaluation_metrics:
            response_data.update({
                'accuracy_score': evaluation_metrics.accuracy_score,
                'feedback_quality_score': evaluation_metrics.feedback_quality_score,
                'total_cost_usd': evaluation_metrics.total_cost_usd or response_data.get('total_cost_usd', 0.0)
            })
        
        return Response(response_data)
        
    except Evaluation.DoesNotExist:
        return Response({
            'error': 'Evaluation not found'
        }, status=404)
    except Exception as e:
        return Response({
            'error': 'Failed to retrieve metrics',
            'details': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)  # 60 requests per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def get_stats(request):
    """Get evaluation statistics for the last N days"""
    try:
        days = int(request.GET.get('days', 30))
        
        if days < 1 or days > 365:
            return Response({
                'status': 'error',
                'message': 'Invalid days parameter',
                'errors': ['Days must be between 1 and 365'],
                'missing_entities': ['valid_days_parameter']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get statistics
        sessions = EvaluationSession.objects.filter(created_at__range=(start_date, end_date))
        
        total_sessions = sessions.count()
        total_evaluations = Evaluation.objects.filter(created_at__range=(start_date, end_date)).count()
        
        # Get token usage from metrics
        from metrics_service.models import RequestMetrics
        metrics = RequestMetrics.objects.filter(created_at__range=(start_date, end_date))
        total_tokens = metrics.aggregate(total=Sum('total_tokens'))['total'] or 0
        
        # Calculate average processing time
        avg_time = sessions.aggregate(avg_time=Avg('total_evaluation_time_seconds'))['avg_time'] or 0
        
        # Calculate success rate
        successful_sessions = sessions.filter(status='completed').count()
        success_rate = (successful_sessions / total_sessions * 100) if total_sessions > 0 else 0
        
        return Response({
            'status': 'success',
            'message': f'Retrieved evaluation statistics for last {days} days',
            'data': {
                'period_days': days,
                'total_sessions': total_sessions,
                'total_evaluations': total_evaluations,
                'total_tokens_used': total_tokens,
                'average_evaluation_time_seconds': round(avg_time, 2),
                'success_rate': round(success_rate, 1)
            }
        })
        
    except Exception as e:
        logger.error(f"Get stats error: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Failed to retrieve statistics',
            'errors': [str(e)]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)  # 60 requests per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def get_performance(request, student_id):
    """Get performance statistics for a specific student"""
    try:
        if not student_id:
            return Response({
                'status': 'error',
                'message': 'Missing student ID',
                'errors': ['Student ID is required'],
                'missing_entities': ['student_id']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        student = Student.objects.filter(student_id=student_id).first()
        
        if not student:
            return Response({
                'status': 'error',
                'message': 'Student not found',
                'errors': ['Student not found'],
                'missing_entities': ['student']
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get performance data
        evaluations = Evaluation.objects.filter(student=student)
        total_evaluations = evaluations.count()
        total_points_lost = evaluations.aggregate(total=Sum('total_points_lost'))['total'] or 0
        avg_points_lost = evaluations.aggregate(avg=Avg('total_points_lost'))['avg'] or 0
        
        # Get recent evaluations
        recent_evaluations = evaluations.order_by('-created_at')[:5]
        recent_data = []
        for eval in recent_evaluations:
            recent_data.append({
                'filename': eval.filename,
                'status': eval.status,
                'total_points_lost': eval.total_points_lost,
                'created_at': eval.created_at.isoformat()
            })
        
        return Response({
            'status': 'success',
            'message': f'Retrieved performance for student: {student_id}',
            'data': {
                'student_id': student.student_id,
                'student_name': student.name,
                'total_evaluations': total_evaluations,
                'total_points_lost': total_points_lost,
                'average_points_lost': round(avg_points_lost, 2),
                'recent_evaluations': recent_data
            }
        })
        
    except Exception as e:
        logger.error(f"Get performance error: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Failed to retrieve performance',
            'errors': [str(e)]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='120/m', method='GET', block=True)  # 120 requests per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def health_check(request):
    """Check system health and status"""
    try:
        # Check database connection
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Check OpenAI service
        openai_status = "healthy"
        try:
            # Simple test call
            test_response = evaluation_service.openai_service.create_chat_completion([
                {"role": "user", "content": "Hello"}
            ])
            if not test_response:
                openai_status = "unhealthy"
        except:
            openai_status = "unhealthy"
        
        # Get cache stats
        cache_stats = get_cache_stats()
        
        overall_status = "healthy" if openai_status == "healthy" else "degraded"
        
        return Response({
            'status': overall_status,
            'database': 'healthy',
            'openai_service': openai_status,
            'cache_stats': cache_stats,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return Response({
            'status': 'unhealthy',
            'database': 'unhealthy',
            'openai_service': 'unknown',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Legacy endpoint for backward compatibility
@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='10/m', method='POST', block=True)  # 10 evaluations per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def legacy_evaluate(request):
    """Legacy evaluation endpoint for backward compatibility"""
    return evaluate_submission(request)

@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)  # 60 requests per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def test_cache(request):
    return Response({"value": random.randint(1, 1000000)})
