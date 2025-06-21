"""
Comprehensive metrics monitoring service for real-world insights.
Tracks performance, cost, accuracy, errors, and system health.
"""

import time
import psutil
import uuid
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg, Count, Sum, Q
from typing import Dict, Any, List, Optional

from .models import (
    SystemMetrics, RequestMetrics, EvaluationMetrics, 
    CostMetrics, ErrorMetrics, PerformanceMetrics
)


class MetricsMonitor:
    """Comprehensive metrics monitoring service"""

    def __init__(self):
        self.start_time = time.time()

    def track_request(self, request, response, response_time_ms: float, 
                     tokens_used: int = 0, estimated_cost: float = 0.0,
                     input_tokens: int = 0, output_tokens: int = 0, 
                     llm_calls_count: int = 0):
        """Track individual request metrics"""
        try:
            # Get system metrics
            memory_usage = psutil.virtual_memory().percent
            cpu_usage = psutil.cpu_percent()
            
            # Generate request ID
            request_id = str(uuid.uuid4())
            
            # Calculate average tokens per call
            avg_tokens_per_call = (input_tokens + output_tokens) / llm_calls_count if llm_calls_count > 0 else 0.0
            
            # Create request metrics
            RequestMetrics.objects.create(
                request_id=request_id,
                endpoint=request.path,
                method=request.method,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                tokens_used=tokens_used,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                avg_tokens_per_call=avg_tokens_per_call,
                llm_calls_count=llm_calls_count,
                estimated_cost_usd=estimated_cost,
                memory_usage_mb=memory_usage,
                cpu_usage_percent=cpu_usage,
                error_message=response.data.get('error', '') if hasattr(response, 'data') else '',
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                ip_address=self._get_client_ip(request)
            )
            
            return request_id
            
        except Exception as e:
            print(f"Error tracking request metrics: {e}")

    def track_evaluation(self, session_id: str, student_id: str, lab_name: str,
                        total_files: int, successful_files: int, failed_files: int,
                        total_tokens: int, total_cost: float, evaluation_time: float,
                        accuracy_score: float = 0.0, feedback_quality_score: float = 0.0):
        """Track evaluation-specific metrics"""
        try:
            EvaluationMetrics.objects.create(
                session_id=session_id,
                student_id=student_id,
                lab_name=lab_name,
                total_files=total_files,
                successful_files=successful_files,
                failed_files=failed_files,
                total_tokens=total_tokens,
                total_cost_usd=total_cost,
                evaluation_time_seconds=evaluation_time,
                accuracy_score=accuracy_score,
                feedback_quality_score=feedback_quality_score
            )
        except Exception as e:
            print(f"Error tracking evaluation metrics: {e}")

    def track_error(self, error_type: str, error_message: str, endpoint: str):
        """Track error patterns"""
        try:
            error, created = ErrorMetrics.objects.get_or_create(
                error_type=error_type,
                error_message=error_message,
                endpoint=endpoint,
                defaults={'frequency': 1}
            )
            
            if not created:
                error.frequency += 1
                error.last_occurrence = timezone.now()
                error.save()
                
        except Exception as e:
            print(f"Error tracking error metrics: {e}")

    def track_system_metric(self, metric_type: str, metric_name: str, 
                           metric_value: float, metric_unit: str, 
                           additional_data: Dict = None):
        """Track system-level metrics"""
        try:
            SystemMetrics.objects.create(
                metric_type=metric_type,
                metric_name=metric_name,
                metric_value=metric_value,
                metric_unit=metric_unit,
                additional_data=additional_data or {}
            )
        except Exception as e:
            print(f"Error tracking system metric: {e}")

    def update_daily_cost_metrics(self):
        """Update daily cost aggregation"""
        try:
            today = timezone.now().date()
            
            # Get today's request metrics
            today_requests = RequestMetrics.objects.filter(
                timestamp__date=today
            )
            
            total_requests = today_requests.count()
            total_tokens = today_requests.aggregate(total=Sum('tokens_used'))['total'] or 0
            total_cost = today_requests.aggregate(total=Sum('estimated_cost_usd'))['total'] or 0.0
            avg_cost = total_cost / total_requests if total_requests > 0 else 0.0
            
            # Update or create daily cost metrics
            cost_metric, created = CostMetrics.objects.get_or_create(
                date=today,
                defaults={
                    'total_requests': total_requests,
                    'total_tokens': total_tokens,
                    'total_cost_usd': total_cost,
                    'avg_cost_per_request': avg_cost,
                    'cost_by_model': {'gpt-4.1-nano': total_cost}  # Simplified for now
                }
            )
            
            if not created:
                cost_metric.total_requests = total_requests
                cost_metric.total_tokens = total_tokens
                cost_metric.total_cost_usd = total_cost
                cost_metric.avg_cost_per_request = avg_cost
                cost_metric.save()
                
        except Exception as e:
            print(f"Error updating daily cost metrics: {e}")

    def get_system_health_dashboard(self, hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive system health dashboard"""
        try:
            start_time = timezone.now() - timedelta(hours=hours)
            
            # Request metrics
            total_requests = RequestMetrics.objects.filter(
                timestamp__gte=start_time
            ).count()
            
            successful_requests = RequestMetrics.objects.filter(
                timestamp__gte=start_time,
                status_code__lt=400
            ).count()
            
            error_requests = total_requests - successful_requests
            success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
            
            avg_response_time = RequestMetrics.objects.filter(
                timestamp__gte=start_time
            ).aggregate(avg=Avg('response_time_ms'))['avg'] or 0
            
            # Cost metrics
            total_cost = RequestMetrics.objects.filter(
                timestamp__gte=start_time
            ).aggregate(total=Sum('estimated_cost_usd'))['total'] or 0.0
            
            total_tokens = RequestMetrics.objects.filter(
                timestamp__gte=start_time
            ).aggregate(total=Sum('tokens_used'))['total'] or 0
            
            total_input_tokens = RequestMetrics.objects.filter(
                timestamp__gte=start_time
            ).aggregate(total=Sum('input_tokens'))['total'] or 0
            
            total_output_tokens = RequestMetrics.objects.filter(
                timestamp__gte=start_time
            ).aggregate(total=Sum('output_tokens'))['total'] or 0
            
            total_llm_calls = RequestMetrics.objects.filter(
                timestamp__gte=start_time
            ).aggregate(total=Sum('llm_calls_count'))['total'] or 0
            
            avg_tokens_per_call = RequestMetrics.objects.filter(
                timestamp__gte=start_time,
                llm_calls_count__gt=0
            ).aggregate(avg=Avg('avg_tokens_per_call'))['avg'] or 0.0
            
            # Performance metrics
            avg_memory = RequestMetrics.objects.filter(
                timestamp__gte=start_time
            ).aggregate(avg=Avg('memory_usage_mb'))['avg'] or 0
            
            avg_cpu = RequestMetrics.objects.filter(
                timestamp__gte=start_time
            ).aggregate(avg=Avg('cpu_usage_percent'))['avg'] or 0
            
            # Error analysis
            top_errors = ErrorMetrics.objects.filter(
                last_occurrence__gte=start_time
            ).order_by('-frequency')[:5]
            
            # Evaluation metrics
            total_evaluations = EvaluationMetrics.objects.filter(
                timestamp__gte=start_time
            ).count()
            
            avg_evaluation_time = EvaluationMetrics.objects.filter(
                timestamp__gte=start_time
            ).aggregate(avg=Avg('evaluation_time_seconds'))['avg'] or 0
            
            avg_accuracy = EvaluationMetrics.objects.filter(
                timestamp__gte=start_time
            ).aggregate(avg=Avg('accuracy_score'))['avg'] or 0
            
            return {
                "period_hours": hours,
                "requests": {
                    "total": total_requests,
                    "successful": successful_requests,
                    "errors": error_requests,
                    "success_rate": round(success_rate, 2),
                    "avg_response_time_ms": round(avg_response_time, 2)
                },
                "costs": {
                    "total_cost_usd": round(total_cost, 4),
                    "total_tokens": total_tokens,
                    "total_input_tokens": total_input_tokens,
                    "total_output_tokens": total_output_tokens,
                    "total_llm_calls": total_llm_calls,
                    "avg_cost_per_request": round(total_cost / total_requests, 4) if total_requests > 0 else 0,
                    "avg_tokens_per_call": round(avg_tokens_per_call, 2)
                },
                "performance": {
                    "avg_memory_usage_mb": round(avg_memory, 2),
                    "avg_cpu_usage_percent": round(avg_cpu, 2),
                    "system_uptime_seconds": time.time() - self.start_time
                },
                "evaluations": {
                    "total": total_evaluations,
                    "avg_evaluation_time_seconds": round(avg_evaluation_time, 2),
                    "avg_accuracy_score": round(avg_accuracy, 2)
                },
                "top_errors": [
                    {
                        "error_type": error.error_type,
                        "frequency": error.frequency,
                        "endpoint": error.endpoint,
                        "last_occurrence": error.last_occurrence.isoformat()
                    }
                    for error in top_errors
                ]
            }
            
        except Exception as e:
            print(f"Error getting system health dashboard: {e}")
            return {"error": str(e)}

    def get_cost_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Get detailed cost analysis"""
        try:
            start_date = timezone.now().date() - timedelta(days=days)
            
            # Get cost data from RequestMetrics instead of CostMetrics
            request_metrics = RequestMetrics.objects.filter(
                timestamp__date__gte=start_date
            )
            
            total_cost = request_metrics.aggregate(total=Sum('estimated_cost_usd'))['total'] or 0.0
            total_requests = request_metrics.count()
            total_tokens = request_metrics.aggregate(total=Sum('tokens_used'))['total'] or 0
            
            # Group by date for daily breakdown
            daily_costs = request_metrics.extra(
                select={'date': "date(timestamp)"}
            ).values('date').annotate(
                daily_cost=Sum('estimated_cost_usd'),
                daily_requests=Count('id'),
                daily_tokens=Sum('tokens_used'),
                daily_input_tokens=Sum('input_tokens'),
                daily_output_tokens=Sum('output_tokens'),
                daily_llm_calls=Sum('llm_calls_count')
            ).order_by('date')
            
            # Cost trends
            cost_trend = [
                {
                    "date": cost['date'],
                    "cost_usd": float(cost['daily_cost'] or 0.0),
                    "requests": cost['daily_requests'],
                    "tokens": cost['daily_tokens'] or 0,
                    "input_tokens": cost['daily_input_tokens'] or 0,
                    "output_tokens": cost['daily_output_tokens'] or 0,
                    "llm_calls": cost['daily_llm_calls'] or 0
                }
                for cost in daily_costs
            ]
            
            # Calculate additional totals
            total_input_tokens = request_metrics.aggregate(total=Sum('input_tokens'))['total'] or 0
            total_output_tokens = request_metrics.aggregate(total=Sum('output_tokens'))['total'] or 0
            total_llm_calls = request_metrics.aggregate(total=Sum('llm_calls_count'))['total'] or 0
            avg_tokens_per_call = request_metrics.filter(llm_calls_count__gt=0).aggregate(avg=Avg('avg_tokens_per_call'))['avg'] or 0.0
            
            return {
                "period_days": days,
                "summary": {
                    "total_cost_usd": round(total_cost, 4),
                    "total_requests": total_requests,
                    "total_tokens": total_tokens,
                    "total_input_tokens": total_input_tokens,
                    "total_output_tokens": total_output_tokens,
                    "total_llm_calls": total_llm_calls,
                    "avg_daily_cost": round(total_cost / days, 4),
                    "avg_cost_per_request": round(total_cost / total_requests, 4) if total_requests > 0 else 0,
                    "avg_tokens_per_call": round(avg_tokens_per_call, 2)
                },
                "daily_breakdown": cost_trend
            }
            
        except Exception as e:
            print(f"Error getting cost analysis: {e}")
            return {"error": str(e)}

    def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance trends over time"""
        try:
            start_time = timezone.now() - timedelta(hours=hours)
            
            # Get all metrics in the time period
            metrics = RequestMetrics.objects.filter(
                timestamp__gte=start_time
            ).values('timestamp', 'response_time_ms', 'memory_usage_mb', 'cpu_usage_percent')
            
            # Group by hour manually
            hourly_data = {}
            for metric in metrics:
                hour = metric['timestamp'].hour
                if hour not in hourly_data:
                    hourly_data[hour] = {
                        'response_times': [],
                        'memory_usage': [],
                        'cpu_usage': [],
                        'request_count': 0
                    }
                
                hourly_data[hour]['response_times'].append(metric['response_time_ms'])
                hourly_data[hour]['memory_usage'].append(metric['memory_usage_mb'])
                hourly_data[hour]['cpu_usage'].append(metric['cpu_usage_percent'])
                hourly_data[hour]['request_count'] += 1
            
            # Calculate averages for each hour
            hourly_trends = []
            for hour in sorted(hourly_data.keys()):
                data = hourly_data[hour]
                hourly_trends.append({
                    'hour': hour,
                    'avg_response_time': sum(data['response_times']) / len(data['response_times']) if data['response_times'] else 0,
                    'total_requests': data['request_count'],
                    'avg_memory': sum(data['memory_usage']) / len(data['memory_usage']) if data['memory_usage'] else 0,
                    'avg_cpu': sum(data['cpu_usage']) / len(data['cpu_usage']) if data['cpu_usage'] else 0
                })
            
            return {
                "period_hours": hours,
                "hourly_trends": hourly_trends
            }
            
        except Exception as e:
            print(f"Error getting performance trends: {e}")
            return {"error": str(e)}

    def _get_client_ip(self, request) -> str:
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# Global metrics monitor instance
metrics_monitor = MetricsMonitor() 