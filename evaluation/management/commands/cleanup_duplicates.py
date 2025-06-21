from django.core.management.base import BaseCommand
from django.db.models import Count
from evaluation.models import Evaluation, EvaluationSession


class Command(BaseCommand):
    help = 'Clean up duplicate evaluations and sessions'

    def handle(self, *args, **options):
        self.stdout.write('Starting duplicate cleanup...')
        
        # Clean up duplicate evaluations
        self.cleanup_evaluations()
        
        # Clean up duplicate sessions
        self.cleanup_sessions()
        
        self.stdout.write(self.style.SUCCESS('Duplicate cleanup completed!'))

    def cleanup_evaluations(self):
        """Remove duplicate evaluations, keeping the latest one"""
        self.stdout.write('Cleaning up duplicate evaluations...')
        
        # Find duplicates
        duplicates = Evaluation.objects.values(
            'student', 'lab_name', 'rubric'
        ).annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        for duplicate in duplicates:
            student_id = duplicate['student']
            lab_name = duplicate['lab_name']
            rubric_id = duplicate['rubric']
            
            # Get all evaluations for this combination
            evaluations = Evaluation.objects.filter(
                student_id=student_id,
                lab_name=lab_name,
                rubric_id=rubric_id
            ).order_by('-created_at')
            
            # Keep the latest one, delete the rest
            latest = evaluations.first()
            to_delete = evaluations.exclude(id=latest.id)
            
            deleted_count = to_delete.count()
            to_delete.delete()
            
            self.stdout.write(f'Deleted {deleted_count} duplicate evaluations for student {student_id}, lab {lab_name}')

    def cleanup_sessions(self):
        """Remove duplicate sessions, keeping the latest one"""
        self.stdout.write('Cleaning up duplicate sessions...')
        
        # Find duplicates
        duplicates = EvaluationSession.objects.values(
            'student', 'lab_name'
        ).annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        for duplicate in duplicates:
            student_id = duplicate['student']
            lab_name = duplicate['lab_name']
            
            # Get all sessions for this combination
            sessions = EvaluationSession.objects.filter(
                student_id=student_id,
                lab_name=lab_name
            ).order_by('-created_at')
            
            # Keep the latest one, delete the rest
            latest = sessions.first()
            to_delete = sessions.exclude(id=latest.id)
            
            deleted_count = to_delete.count()
            to_delete.delete()
            
            self.stdout.write(f'Deleted {deleted_count} duplicate sessions for student {student_id}, lab {lab_name}') 