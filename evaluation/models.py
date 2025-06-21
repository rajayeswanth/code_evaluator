from django.db import models
from django.contrib.auth.models import User
import json
from datetime import datetime
from django.utils import timezone


class Student(models.Model):
    """Simple student model"""
    student_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    section = models.CharField(max_length=10)
    semester = models.CharField(max_length=20)
    instructor_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.student_id})"


class LabRubric(models.Model):
    """Rubric for an entire lab (covers all programs in the lab)"""
    lab_name = models.CharField(max_length=100)
    semester = models.CharField(max_length=20)
    section = models.CharField(max_length=10)
    total_points = models.IntegerField()
    criteria = models.JSONField()  # Store all criteria for the lab
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['lab_name', 'semester', 'section']

    def __str__(self):
        return f"{self.lab_name} - {self.semester} - {self.section}"


class Evaluation(models.Model):
    """Simple evaluation model"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    rubric = models.ForeignKey(LabRubric, on_delete=models.CASCADE)
    lab_name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default='pending')
    feedback = models.TextField()
    total_points_lost = models.IntegerField(default=0)
    deductions = models.JSONField(default=list)
    code_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.name} - {self.lab_name}"


class EvaluationSession(models.Model):
    """Track evaluation sessions"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=50, unique=True)
    lab_name = models.CharField(max_length=100)
    summary_feedback = models.TextField()
    total_files_evaluated = models.IntegerField(default=0)
    successful_evaluations = models.IntegerField(default=0)
    error_evaluations = models.IntegerField(default=0)
    total_points_lost = models.IntegerField(default=0)
    total_deductions = models.IntegerField(default=0)
    submission_data = models.JSONField()
    total_evaluation_time_seconds = models.FloatField(default=0)
    total_tokens_used = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session {self.session_id} - {self.student.name}"


class SystemMetrics(models.Model):
    """Simple system metrics"""
    metric_type = models.CharField(max_length=50)
    metric_name = models.CharField(max_length=50)
    metric_value = models.FloatField()
    metric_unit = models.CharField(max_length=20)
    additional_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.metric_type} - {self.metric_name}"


class ErrorLog(models.Model):
    """Simple error logging"""
    level = models.CharField(max_length=20)
    message = models.TextField()
    error_type = models.CharField(max_length=50)
    user_id = models.CharField(max_length=50, null=True, blank=True)
    session_id = models.CharField(max_length=50, null=True, blank=True)
    request_data = models.JSONField(default=dict)
    stack_trace = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.error_type} - {self.message[:50]}"
