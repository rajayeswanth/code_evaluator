from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.utils import timezone

from .monitor import metrics_monitor
from .models import RequestMetrics


@api_view(['GET'])
@permission_classes([AllowAny])
def get_request_metrics(request):
    """Get request metrics with pagination"""
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
        total_count = RequestMetrics.objects.all().count()
        
        # Get paginated request metrics
        metrics = RequestMetrics.objects.all().order_by('-timestamp')[offset:offset + page_size]
        
        # Calculate pagination info
        total_pages = (total_count + page_size - 1) // page_size
        has_next = page < total_pages
        has_previous = page > 1
        
        # Format response
        metrics_data = []
        for metric in metrics:
            metrics_data.append({
                'id': metric.id,
                'endpoint': metric.endpoint,
                'method': metric.method,
                'response_time_ms': metric.response_time_ms,
                'status_code': metric.status_code,
                'tokens_used': metric.tokens_used,
                'estimated_cost_usd': metric.estimated_cost_usd,
                'success': metric.status_code < 400,
                'error_message': metric.error_message,
                'timestamp': metric.timestamp.isoformat(),
                'input_tokens': metric.input_tokens,
                'output_tokens': metric.output_tokens,
                'avg_tokens_per_call': metric.avg_tokens_per_call,
                'llm_calls_count': metric.llm_calls_count
            })
        
        return Response({
            'total_count': total_count,
            'request_metrics': metrics_data,
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
            'error': 'Failed to get request metrics',
            'details': str(e)
        }, status=500)


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
def metrics_summary(request):
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