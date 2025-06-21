from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta


class SystemMetrics(models.Model):
    """Track system-level metrics"""
    metric_type = models.CharField(max_length=50)  # 'performance', 'cost', 'accuracy', 'errors'
    metric_name = models.CharField(max_length=100)
    metric_value = models.FloatField()
    metric_unit = models.CharField(max_length=20)  # 'tokens', 'seconds', 'dollars', 'percentage'
    timestamp = models.DateTimeField(auto_now_add=True)
    additional_data = models.JSONField(default=dict)

    class Meta:
        indexes = [
            models.Index(fields=['metric_type', 'timestamp']),
            models.Index(fields=['metric_name', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.metric_name}: {self.metric_value} {self.metric_unit}"


class RequestMetrics(models.Model):
    """Track individual request metrics"""
    request_id = models.CharField(max_length=50, unique=True)
    endpoint = models.CharField(max_length=100)
    method = models.CharField(max_length=10)
    status_code = models.IntegerField()
    response_time_ms = models.FloatField()
    tokens_used = models.IntegerField(default=0)
    input_tokens = models.IntegerField(default=0)  # Input tokens sent to LLM
    output_tokens = models.IntegerField(default=0)  # Output tokens from LLM
    avg_tokens_per_call = models.FloatField(default=0.0)  # Average tokens per LLM call
    llm_calls_count = models.IntegerField(default=0)  # Number of LLM API calls made
    estimated_cost_usd = models.FloatField(default=0.0)
    memory_usage_mb = models.FloatField(default=0.0)
    cpu_usage_percent = models.FloatField(default=0.0)
    error_message = models.TextField(blank=True, null=True)
    user_agent = models.CharField(max_length=200, blank=True)
    ip_address = models.CharField(max_length=45, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['endpoint', 'timestamp']),
            models.Index(fields=['status_code', 'timestamp']),
            models.Index(fields=['request_id']),
            models.Index(fields=['llm_calls_count', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.request_id} - {self.endpoint} ({self.status_code})"


class EvaluationMetrics(models.Model):
    """Track evaluation-specific metrics"""
    session_id = models.CharField(max_length=50)
    student_id = models.CharField(max_length=20)
    lab_name = models.CharField(max_length=100)
    total_files = models.IntegerField()
    successful_files = models.IntegerField()
    failed_files = models.IntegerField()
    total_tokens = models.IntegerField()
    total_cost_usd = models.FloatField()
    evaluation_time_seconds = models.FloatField()
    accuracy_score = models.FloatField(default=0.0)  # Based on rubric adherence
    feedback_quality_score = models.FloatField(default=0.0)  # Based on feedback usefulness
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['student_id', 'timestamp']),
            models.Index(fields=['lab_name', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.session_id} - {self.lab_name}"


class CostMetrics(models.Model):
    """Track cost-related metrics"""
    date = models.DateField()
    total_requests = models.IntegerField()
    total_tokens = models.IntegerField()
    total_cost_usd = models.FloatField()
    avg_cost_per_request = models.FloatField()
    cost_by_model = models.JSONField(default=dict)  # {'gpt-4.1-nano': 0.50, 'gpt-4': 2.30}
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['date']
        indexes = [
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"{self.date} - ${self.total_cost_usd:.2f}"


class ErrorMetrics(models.Model):
    """Track error patterns and frequencies"""
    error_type = models.CharField(max_length=50)  # 'api_error', 'validation_error', 'timeout'
    error_message = models.TextField()
    endpoint = models.CharField(max_length=100)
    frequency = models.IntegerField(default=1)
    first_occurrence = models.DateTimeField(auto_now_add=True)
    last_occurrence = models.DateTimeField(auto_now=True)
    is_resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['error_type', 'last_occurrence']),
            models.Index(fields=['endpoint', 'last_occurrence']),
        ]

    def __str__(self):
        return f"{self.error_type} - {self.frequency} occurrences"


class PerformanceMetrics(models.Model):
    """Track system performance metrics"""
    metric_name = models.CharField(max_length=100)  # 'avg_response_time', 'throughput', 'memory_usage'
    metric_value = models.FloatField()
    metric_unit = models.CharField(max_length=20)
    period_minutes = models.IntegerField()  # Time period for aggregation
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['metric_name', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.metric_name}: {self.metric_value} {self.metric_unit}" 