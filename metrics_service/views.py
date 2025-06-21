from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.utils import timezone
import logging
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Sum, Avg, Count
from cache_utils import cache_api_response, cache_db_query, get_cache_stats
from django_ratelimit.decorators import ratelimit

from .monitor import metrics_monitor
from .models import RequestMetrics, CostMetrics
from .monitor import MetricsMonitor

logger = logging.getLogger(__name__)

# Initialize monitor
metrics_monitor = MetricsMonitor()

@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)  # 60 requests per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def get_cost_analysis(request):
    """Get cost analysis for the last N days"""
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
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get cost metrics
        metrics = RequestMetrics.objects.filter(created_at__range=(start_date, end_date))
        
        if not metrics.exists():
            return Response({
                'status': 'success',
                'message': f'No cost data found for last {days} days',
                'data': {
                    'period_days': days,
                    'total_cost': 0.0,
                    'average_cost_per_day': 0.0,
                    'total_requests': 0,
                    'average_cost_per_request': 0.0,
                    'cost_breakdown': []
                }
            })
        
        # Calculate totals
        total_cost = metrics.aggregate(total=Sum('total_cost'))['total'] or 0.0
        total_requests = metrics.count()
        avg_cost_per_request = total_cost / total_requests if total_requests > 0 else 0.0
        avg_cost_per_day = total_cost / days
        
        # Get daily breakdown
        daily_costs = metrics.extra(
            select={'date': 'DATE(created_at)'}
        ).values('date').annotate(
            daily_cost=Sum('total_cost'),
            daily_requests=Count('id')
        ).order_by('date')
        
        cost_breakdown = []
        for day in daily_costs:
            cost_breakdown.append({
                'date': day['date'],
                'cost': float(day['daily_cost']),
                'requests': day['daily_requests']
            })
        
        return Response({
            'status': 'success',
            'message': f'Retrieved cost analysis for last {days} days',
            'data': {
                'period_days': days,
                'total_cost': float(total_cost),
                'average_cost_per_day': round(avg_cost_per_day, 4),
                'total_requests': total_requests,
                'average_cost_per_request': round(avg_cost_per_request, 4),
                'cost_breakdown': cost_breakdown
            }
        })
        
    except Exception as e:
        logger.error(f"Cost analysis error: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Failed to retrieve cost analysis',
            'errors': [str(e)]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)  # 60 requests per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def get_request_metrics(request):
    """Get request metrics with pagination"""
    try:
        # Get pagination parameters
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 20)), 100)
        
        # Get metrics
        metrics = RequestMetrics.objects.all().order_by('-created_at')
        
        # Paginate
        paginator = Paginator(metrics, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize
        metrics_data = []
        for metric in page_obj:
            metrics_data.append({
                'id': metric.id,
                'session_id': metric.session_id,
                'llm_calls': metric.llm_calls,
                'total_tokens': metric.total_tokens,
                'input_tokens': metric.input_tokens,
                'output_tokens': metric.output_tokens,
                'avg_tokens_per_call': metric.avg_tokens_per_call,
                'total_cost': float(metric.total_cost),
                'avg_cost_per_call': float(metric.avg_cost_per_call),
                'processing_time_ms': metric.processing_time_ms,
                'memory_usage_mb': metric.memory_usage_mb,
                'status': metric.status,
                'created_at': metric.created_at.isoformat()
            })
        
        return Response({
            'status': 'success',
            'message': f'Retrieved {len(metrics_data)} request metrics',
            'data': {
                'metrics': metrics_data,
                'pagination': {
                    'current_page': page_obj.number,
                    'page_size': page_size,
                    'total_count': paginator.count,
                    'total_pages': paginator.num_pages,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                    'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
                    'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Request metrics error: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Failed to retrieve request metrics',
            'errors': [str(e)]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)  # 60 requests per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def get_performance_summary(request):
    """Get overall performance summary"""
    try:
        # Get date range (last 30 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Get metrics for the period
        metrics = RequestMetrics.objects.filter(created_at__range=(start_date, end_date))
        
        if not metrics.exists():
            return Response({
                'status': 'success',
                'message': 'No performance data available',
                'data': {
                    'period_days': 30,
                    'total_requests': 0,
                    'successful_requests': 0,
                    'failed_requests': 0,
                    'success_rate': 0.0,
                    'total_tokens': 0,
                    'average_tokens_per_request': 0,
                    'total_cost': 0.0,
                    'average_cost_per_request': 0.0,
                    'average_processing_time_ms': 0,
                    'average_memory_usage_mb': 0
                }
            })
        
        # Calculate statistics
        total_requests = metrics.count()
        successful_requests = metrics.filter(status='success').count()
        failed_requests = total_requests - successful_requests
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        total_tokens = metrics.aggregate(total=Sum('total_tokens'))['total'] or 0
        avg_tokens_per_request = metrics.aggregate(avg=Avg('total_tokens'))['avg'] or 0
        
        total_cost = metrics.aggregate(total=Sum('total_cost'))['total'] or 0.0
        avg_cost_per_request = metrics.aggregate(avg=Avg('total_cost'))['avg'] or 0.0
        
        avg_processing_time = metrics.aggregate(avg=Avg('processing_time_ms'))['avg'] or 0
        avg_memory_usage = metrics.aggregate(avg=Avg('memory_usage_mb'))['avg'] or 0
        
        return Response({
            'status': 'success',
            'message': 'Retrieved performance summary',
            'data': {
                'period_days': 30,
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'failed_requests': failed_requests,
                'success_rate': round(success_rate, 2),
                'total_tokens': total_tokens,
                'average_tokens_per_request': round(avg_tokens_per_request, 2),
                'total_cost': float(total_cost),
                'average_cost_per_request': float(avg_cost_per_request),
                'average_processing_time_ms': round(avg_processing_time, 2),
                'average_memory_usage_mb': round(avg_memory_usage, 2)
            }
        })
        
    except Exception as e:
        logger.error(f"Performance summary error: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Failed to retrieve performance summary',
            'errors': [str(e)]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)  # 60 requests per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def get_token_usage(request):
    """Get token usage analysis"""
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
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get token metrics
        metrics = RequestMetrics.objects.filter(created_at__range=(start_date, end_date))
        
        if not metrics.exists():
            return Response({
                'status': 'success',
                'message': f'No token data found for last {days} days',
                'data': {
                    'period_days': days,
                    'total_tokens': 0,
                    'input_tokens': 0,
                    'output_tokens': 0,
                    'average_tokens_per_request': 0,
                    'token_breakdown': []
                }
            })
        
        # Calculate totals
        total_tokens = metrics.aggregate(total=Sum('total_tokens'))['total'] or 0
        input_tokens = metrics.aggregate(total=Sum('input_tokens'))['total'] or 0
        output_tokens = metrics.aggregate(total=Sum('output_tokens'))['total'] or 0
        avg_tokens_per_request = metrics.aggregate(avg=Avg('total_tokens'))['avg'] or 0
        
        # Get daily breakdown
        daily_tokens = metrics.extra(
            select={'date': 'DATE(created_at)'}
        ).values('date').annotate(
            daily_tokens=Sum('total_tokens'),
            daily_requests=Count('id')
        ).order_by('date')
        
        token_breakdown = []
        for day in daily_tokens:
            token_breakdown.append({
                'date': day['date'],
                'tokens': day['daily_tokens'],
                'requests': day['daily_requests']
            })
        
        return Response({
            'status': 'success',
            'message': f'Retrieved token usage for last {days} days',
            'data': {
                'period_days': days,
                'total_tokens': total_tokens,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'average_tokens_per_request': round(avg_tokens_per_request, 2),
                'token_breakdown': token_breakdown
            }
        })
        
    except Exception as e:
        logger.error(f"Token usage error: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Failed to retrieve token usage',
            'errors': [str(e)]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)  # 60 requests per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def get_cache_status(request):
    """Get cache status and statistics"""
    try:
        cache_stats = get_cache_stats()
        
        return Response({
            'status': 'success',
            'message': 'Retrieved cache status',
            'data': cache_stats
        })
        
    except Exception as e:
        logger.error(f"Cache status error: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Failed to retrieve cache status',
            'errors': [str(e)]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def system_health_dashboard(request):
    """Get comprehensive system health dashboard"""
    try:
        hours = int(request.GET.get('hours', 24))
        if hours < 1 or hours > 168:  # Max 1 week
            hours = 24
        
        result = metrics_monitor.get_system_health_dashboard(hours)
        
        if "error" in result:
            return Response(result, status=500)
        
        return Response(result)
        
    except Exception as e:
        return Response({
            "error": "Failed to get system health dashboard",
            "details": str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
def cost_analysis(request):
    """Get detailed cost analysis"""
    try:
        days = int(request.GET.get('days', 30))
        if days < 1 or days > 365:  # Max 1 year
            days = 30
        
        result = metrics_monitor.get_cost_analysis(days)
        
        if "error" in result:
            return Response(result, status=500)
        
        return Response(result)
        
    except Exception as e:
        return Response({
            "error": "Failed to get cost analysis",
            "details": str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
def performance_trends(request):
    """Get performance trends over time"""
    try:
        hours = int(request.GET.get('hours', 24))
        if hours < 1 or hours > 168:  # Max 1 week
            hours = 24
        
        result = metrics_monitor.get_performance_trends(hours)
        
        if "error" in result:
            return Response(result, status=500)
        
        return Response(result)
        
    except Exception as e:
        return Response({
            "error": "Failed to get performance trends",
            "details": str(e)
        }, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def update_daily_metrics(request):
    """Manually trigger daily metrics update"""
    try:
        metrics_monitor.update_daily_cost_metrics()
        
        return Response({
            "message": "Daily metrics updated successfully",
            "timestamp": timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response({
            "error": "Failed to update daily metrics",
            "details": str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)  # 60 requests per minute per IP
@cache_api_response(cache_alias="api_cache", timeout=7200)
def get_metrics_summary(request):
    """Get quick metrics summary for dashboard"""
    try:
        # Get last 24 hours summary
        health_dashboard = metrics_monitor.get_system_health_dashboard(24)
        
        # Get last 7 days cost
        cost_analysis = metrics_monitor.get_cost_analysis(7)
        
        # Get last 24 hours performance
        performance_trends = metrics_monitor.get_performance_trends(24)
        
        summary = {
            "last_24_hours": {
                "requests": health_dashboard.get("requests", {}),
                "costs": health_dashboard.get("costs", {}),
                "performance": health_dashboard.get("performance", {}),
                "evaluations": health_dashboard.get("evaluations", {})
            },
            "last_7_days": {
                "cost_summary": cost_analysis.get("summary", {})
            },
            "system_status": {
                "uptime_seconds": health_dashboard.get("performance", {}).get("system_uptime_seconds", 0),
                "success_rate": health_dashboard.get("requests", {}).get("success_rate", 0),
                "avg_response_time": health_dashboard.get("requests", {}).get("avg_response_time_ms", 0)
            }
        }
        
        return Response(summary)
        
    except Exception as e:
        return Response({
            "error": "Failed to get metrics summary",
            "details": str(e)
        }, status=500) 