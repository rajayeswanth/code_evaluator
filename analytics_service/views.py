from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.utils import timezone
from datetime import datetime, timedelta
from cache_utils import cache_api_response
from django_ratelimit.decorators import ratelimit

from .analytics import AnalyticsService
from evaluation.models import Student
from .models import StudentPerformance


@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)  # 60 requests per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def get_student_details(request, student_id):
    """Get detailed student information"""
    try:
        analytics = AnalyticsService()
        result = analytics.get_student_details(student_id)
        
        if "error" in result:
            return Response(result, status=404)
        
        return Response(result)
        
    except Exception as e:
        return Response({
            "error": "Failed to get student details",
            "details": str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)  # 60 requests per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def get_all_students(request):
    """Get all students with pagination"""
    try:
        # Get pagination parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 20
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get total count
        total_count = Student.objects.all().count()
        
        # Get paginated students
        students = Student.objects.all().order_by('-created_at')[offset:offset + page_size]
        
        # Calculate pagination info
        total_pages = (total_count + page_size - 1) // page_size
        has_next = page < total_pages
        has_previous = page > 1
        
        return Response({
            'total_count': total_count,
            'students': [
                {
                    'student_id': student.student_id,
                    'name': student.name,
                    'section': student.section,
                    'semester': student.semester,
                    'instructor_name': student.instructor_name,
                    'created_at': student.created_at.isoformat()
                }
                for student in students
            ],
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
        return Response({
            'error': 'Failed to get students',
            'details': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)  # 60 requests per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def analyze_lab_section(request, lab_name, section):
    """Analyze performance by lab and section"""
    try:
        days = int(request.GET.get('days', 30))
        if days < 1 or days > 365:
            days = 30
        
        analytics = AnalyticsService()
        result = analytics.analyze_performance_by_lab_section(lab_name, section, days)
        
        if "error" in result:
            return Response(result, status=404)
        
        return Response(result)
        
    except Exception as e:
        return Response({
            "error": "Failed to analyze lab-section performance",
            "details": str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)  # 60 requests per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def analyze_lab(request, lab_name):
    """Analyze performance by lab"""
    try:
        days = int(request.GET.get('days', 30))
        if days < 1 or days > 365:
            days = 30
        
        analytics = AnalyticsService()
        result = analytics.analyze_performance_by_lab(lab_name, days)
        
        if "error" in result:
            return Response(result, status=404)
        
        return Response(result)
        
    except Exception as e:
        return Response({
            "error": "Failed to analyze lab performance",
            "details": str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)  # 60 requests per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def analyze_semester(request, semester):
    """Analyze performance by semester"""
    try:
        days = int(request.GET.get('days', 30))
        if days < 1 or days > 365:
            days = 30
        
        analytics = AnalyticsService()
        result = analytics.analyze_performance_by_semester(semester, days)
        
        if "error" in result:
            return Response(result, status=404)
        
        return Response(result)
        
    except Exception as e:
        return Response({
            "error": "Failed to analyze semester performance",
            "details": str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)  # 60 requests per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def analyze_lab_semester(request, lab_name, semester):
    """Analyze performance by lab and semester"""
    try:
        days = int(request.GET.get('days', 30))
        if days < 1 or days > 365:
            days = 30
        
        analytics = AnalyticsService()
        result = analytics.analyze_performance_by_lab_semester(lab_name, semester, days)
        
        if "error" in result:
            return Response(result, status=404)
        
        return Response(result)
        
    except Exception as e:
        return Response({
            "error": "Failed to analyze lab-semester performance",
            "details": str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)  # 60 requests per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def analyze_student_performance(request, student_id):
    """Analyze and summarize student's overall performance"""
    try:
        analytics = AnalyticsService()
        result = analytics.analyze_student_performance(student_id)
        
        if "error" in result:
            return Response(result, status=404)
        
        return Response(result)
        
    except Exception as e:
        return Response({
            "error": "Failed to analyze student performance",
            "details": str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)  # 60 requests per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def get_student_performance_by_lab(request):
    """Get student performance by lab with pagination"""
    try:
        lab_name = request.GET.get('lab_name')
        section = request.GET.get('section')
        semester = request.GET.get('semester')
        
        # Get pagination parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 20
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Build query
        query = StudentPerformance.objects.all()
        if lab_name:
            query = query.filter(lab_name=lab_name)
        if section:
            query = query.filter(section=section)
        if semester:
            query = query.filter(semester=semester)
        
        # Get total count
        total_count = query.count()
        
        # Get paginated results
        performances = query.order_by('-last_evaluation_date')[offset:offset + page_size]
        
        # Calculate pagination info
        total_pages = (total_count + page_size - 1) // page_size
        has_next = page < total_pages
        has_previous = page > 1
        
        return Response({
            'total_count': total_count,
            'performances': [
                {
                    'student_id': perf.student_id,
                    'student_name': perf.student_name,
                    'lab_name': perf.lab_name,
                    'section': perf.section,
                    'semester': perf.semester,
                    'total_evaluations': perf.total_evaluations,
                    'total_points_lost': perf.total_points_lost,
                    'average_points_lost': perf.average_points_lost,
                    'last_evaluation_date': perf.last_evaluation_date.isoformat() if perf.last_evaluation_date else None
                }
                for perf in performances
            ],
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
        return Response({
            'error': 'Failed to get student performance',
            'details': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)  # 60 requests per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def get_student_performance_summary(request, student_id):
    """Get comprehensive performance summary for a student"""
    try:
        analytics = AnalyticsService()
        result = analytics.get_student_details(student_id)
        
        if "error" in result:
            return Response(result, status=404)
        
        return Response(result)
        
    except Exception as e:
        return Response({
            "error": "Failed to get student performance summary",
            "details": str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)  # 60 requests per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def get_summarized_performance_by_lab(request, lab_name):
    """Get summarized performance for a specific lab with optional filters"""
    try:
        section = request.GET.get('section')
        semester = request.GET.get('semester')
        
        analytics = AnalyticsService()
        result = analytics.get_summarized_performance_by_lab(lab_name, section, semester)
        
        if "error" in result:
            return Response(result, status=404)
        
        return Response(result)
        
    except Exception as e:
        return Response({
            "error": "Failed to get lab performance summary",
            "details": str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)  # 60 requests per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def get_summarized_performance_by_section(request, section):
    """Get summarized performance for a specific section with optional filters"""
    try:
        lab_name = request.GET.get('lab_name')
        semester = request.GET.get('semester')
        
        analytics = AnalyticsService()
        result = analytics.get_summarized_performance_by_section(section, lab_name, semester)
        
        if "error" in result:
            return Response(result, status=404)
        
        return Response(result)
        
    except Exception as e:
        return Response({
            "error": "Failed to get section performance summary",
            "details": str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)  # 60 requests per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def get_summarized_performance_by_semester(request, semester):
    """Get summarized performance for a specific semester with optional filters"""
    try:
        lab_name = request.GET.get('lab_name')
        section = request.GET.get('section')
        
        analytics = AnalyticsService()
        result = analytics.get_summarized_performance_by_semester(semester, lab_name, section)
        
        if "error" in result:
            return Response(result, status=404)
        
        return Response(result)
        
    except Exception as e:
        return Response({
            "error": "Failed to get semester performance summary",
            "details": str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)  # 60 requests per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def get_all_labs(request):
    """Get all labs with basic information"""
    try:
        analytics = AnalyticsService()
        result = analytics.get_all_labs()
        
        return Response({
            "labs": result,
            "count": len(result)
        })
        
    except Exception as e:
        return Response({
            "error": "Failed to get labs",
            "details": str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)  # 60 requests per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def get_lab_by_id(request, lab_id):
    """Get detailed information about a specific lab by ID"""
    try:
        analytics = AnalyticsService()
        result = analytics.get_lab_by_id(lab_id)
        
        if "error" in result:
            return Response(result, status=404)
        
        return Response(result)
        
    except Exception as e:
        return Response({
            "error": "Failed to get lab details",
            "details": str(e)
        }, status=500) 