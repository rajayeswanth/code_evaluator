from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta


class StudentPerformance(models.Model):
    """Track student performance analytics"""
    student_id = models.CharField(max_length=20)
    student_name = models.CharField(max_length=100)
    lab_name = models.CharField(max_length=100)
    section = models.CharField(max_length=10)
    semester = models.CharField(max_length=20)
    total_evaluations = models.IntegerField(default=0)
    total_points_lost = models.IntegerField(default=0)
    average_points_lost = models.FloatField(default=0.0)
    last_evaluation_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student_id', 'lab_name', 'section', 'semester']

    def __str__(self):
        return f"{self.student_name} - {self.lab_name}"


class LabAnalytics(models.Model):
    """Track lab-level analytics"""
    lab_name = models.CharField(max_length=100)
    section = models.CharField(max_length=10)
    semester = models.CharField(max_length=20)
    total_students = models.IntegerField(default=0)
    total_evaluations = models.IntegerField(default=0)
    average_points_lost = models.FloatField(default=0.0)
    common_issues = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['lab_name', 'section', 'semester']

    def __str__(self):
        return f"{self.lab_name} - {self.section} - {self.semester}" 