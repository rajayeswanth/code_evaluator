from rest_framework import serializers
from .models import (
    LabRubric, Student, Evaluation, 
    EvaluationSession, SystemMetrics, ErrorLog
)


class LabRubricSerializer(serializers.ModelSerializer):
    """Simple rubric serializer"""
    
    class Meta:
        model = LabRubric
        fields = [
            'id', 'lab_name', 'semester', 'section', 'total_points', 
            'criteria', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class StudentSerializer(serializers.ModelSerializer):
    """Simple student serializer"""
    
    class Meta:
        model = Student
        fields = [
            'id', 'student_id', 'name', 'section', 'semester', 
            'instructor_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class EvaluationSerializer(serializers.ModelSerializer):
    """Simple evaluation serializer"""
    
    student = StudentSerializer(read_only=True)
    rubric = LabRubricSerializer(read_only=True)
    
    class Meta:
        model = Evaluation
        fields = [
            'id', 'student', 'rubric', 'lab_name', 'status',
            'feedback', 'total_points_lost', 'deductions', 'code_content', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class EvaluationSessionSerializer(serializers.ModelSerializer):
    """Simple session serializer"""
    
    student = StudentSerializer(read_only=True)
    evaluations = EvaluationSerializer(many=True, read_only=True)
    
    class Meta:
        model = EvaluationSession
        fields = [
            'id', 'student', 'session_id', 'lab_name', 'summary_feedback',
            'total_files_evaluated', 'successful_evaluations', 'error_evaluations',
            'total_points_lost', 'total_deductions', 'total_evaluation_time_seconds', 
            'total_tokens_used', 'created_at', 'evaluations'
        ]
        read_only_fields = ['id', 'session_id', 'created_at']


# Simple request/response serializers

class RubricCreateSerializer(serializers.Serializer):
    """Create a new rubric"""
    lab = serializers.CharField(max_length=100)
    semester = serializers.CharField(max_length=20)
    year = serializers.CharField(max_length=4)
    section = serializers.CharField(max_length=10)
    rubrics = serializers.JSONField()


class RubricGetSerializer(serializers.Serializer):
    """Get rubric ID"""
    lab = serializers.CharField(max_length=100)
    semester = serializers.CharField(max_length=20)
    year = serializers.CharField(max_length=4)
    section = serializers.CharField(max_length=10)


class EvaluationRequestSerializer(serializers.Serializer):
    """Request to evaluate student code"""
    student_id = serializers.CharField(max_length=20)
    name = serializers.CharField(max_length=100)
    section = serializers.CharField(max_length=10)
    semester = serializers.CharField(max_length=20)
    instructor_name = serializers.CharField(max_length=100)
    lab_name = serializers.CharField(max_length=100)
    rubric_id = serializers.IntegerField()
    input = serializers.CharField()  # Raw input text


class EvaluationResponseSerializer(serializers.Serializer):
    """Response from evaluation"""
    session_id = serializers.CharField()
    feedback = serializers.CharField()
    summary = serializers.CharField()
    total_files_evaluated = serializers.IntegerField()
    total_points_lost = serializers.IntegerField()
    total_evaluation_time_seconds = serializers.FloatField()


class SystemMetricsSerializer(serializers.ModelSerializer):
    """Simple system metrics serializer"""
    
    class Meta:
        model = SystemMetrics
        fields = [
            'id', 'metric_type', 'metric_name', 'metric_value', 
            'metric_unit', 'additional_data', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ErrorLogSerializer(serializers.ModelSerializer):
    """Simple error log serializer"""
    
    class Meta:
        model = ErrorLog
        fields = [
            'id', 'level', 'message', 'error_type', 'stack_trace',
            'user_id', 'session_id', 'request_data', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class MonitoringMetricsSerializer(serializers.Serializer):
    """Serializer for monitoring metrics."""
    
    metric_type = serializers.CharField()
    metric_name = serializers.CharField()
    metric_value = serializers.FloatField()
    metric_unit = serializers.CharField()
    timestamp = serializers.DateTimeField()
    additional_data = serializers.DictField(required=False) 