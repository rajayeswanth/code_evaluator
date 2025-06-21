"""
Analytics service for student and lab performance analysis.
Uses simple aggregation and nano model for summaries.
"""

from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg, Count, Sum
from typing import Dict, Any, List

from evaluation.models import Student, Evaluation, EvaluationSession, LabRubric
from analytics_service.models import StudentPerformance, LabAnalytics
from evaluator_service.openai_service import openai_service


class AnalyticsService:
    """Simple analytics service for performance tracking"""

    def __init__(self):
        self.openai_service = openai_service

    def get_student_details(self, student_id: str) -> Dict[str, Any]:
        """Get detailed student information with comprehensive performance summary"""
        try:
            student = Student.objects.get(student_id=student_id)
            evaluations = Evaluation.objects.filter(student=student)
            sessions = EvaluationSession.objects.filter(student=student)
            
            if not evaluations.exists():
                return {"error": "No evaluations found for this student"}
            
            # Basic stats
            total_evaluations = evaluations.count()
            total_points_lost = evaluations.aggregate(total=Sum('total_points_lost'))['total'] or 0
            avg_points_lost = evaluations.aggregate(avg=Avg('total_points_lost'))['avg'] or 0.0
            
            # Lab breakdown
            lab_stats = sessions.values('lab_name').annotate(
                count=Count('id'),
                avg_points=Avg('total_points_lost'),
                total_points=Sum('total_points_lost')
            ).order_by('lab_name')
            
            # Recent performance (last 5 evaluations)
            recent_evaluations = evaluations.order_by('-created_at')[:5]
            recent_data = []
            for eval in recent_evaluations:
                recent_data.append({
                    "lab_name": eval.lab_name,
                    "points_lost": eval.total_points_lost,
                    "date": eval.created_at.isoformat()
                })
            
            # Performance trend analysis
            performance_summary = self._analyze_student_trend(student_id, sessions)
            
            return {
                "student_id": student.student_id,
                "name": student.name,
                "section": student.section,
                "semester": student.semester,
                "instructor_name": student.instructor_name,
                "total_evaluations": total_evaluations,
                "total_points_lost": total_points_lost,
                "average_points_lost": round(avg_points_lost, 2),
                "lab_breakdown": list(lab_stats),
                "recent_evaluations": recent_data,
                "performance_summary": performance_summary,
                "first_evaluation": evaluations.order_by('created_at').first().created_at.isoformat(),
                "last_evaluation": evaluations.order_by('-created_at').first().created_at.isoformat()
            }
        except Student.DoesNotExist:
            return {"error": "Student not found"}

    def get_all_students(self) -> List[Dict[str, Any]]:
        """Get all students with basic stats"""
        students = Student.objects.all()
        result = []
        
        for student in students:
            evaluations = Evaluation.objects.filter(student=student)
            result.append({
                "student_id": student.student_id,
                "name": student.name,
                "section": student.section,
                "semester": student.semester,
                "total_evaluations": evaluations.count(),
                "total_points_lost": evaluations.aggregate(total=Sum('total_points_lost'))['total'] or 0
            })
        
        return result

    def analyze_performance_by_lab_section(self, lab_name: str, section: str, days: int = 30) -> Dict[str, Any]:
        """Analyze performance for specific lab and section"""
        start_date = timezone.now() - timedelta(days=days)
        
        sessions = EvaluationSession.objects.filter(
            lab_name=lab_name,
            student__section=section,
            created_at__gte=start_date
        )
        
        if not sessions.exists():
            return {"error": "No data found for this lab and section"}
        
        total_sessions = sessions.count()
        total_points_lost = sessions.aggregate(total=Sum('total_points_lost'))['total'] or 0
        avg_points_lost = sessions.aggregate(avg=Avg('total_points_lost'))['avg'] or 0.0
        
        # Get common issues using nano model
        common_issues = self._analyze_common_issues(sessions)
        
        return {
            "lab_name": lab_name,
            "section": section,
            "period_days": days,
            "total_sessions": total_sessions,
            "total_points_lost": total_points_lost,
            "average_points_lost": round(avg_points_lost, 2),
            "common_issues": common_issues
        }

    def analyze_performance_by_lab(self, lab_name: str, days: int = 30) -> Dict[str, Any]:
        """Analyze performance for specific lab across all sections"""
        start_date = timezone.now() - timedelta(days=days)
        
        sessions = EvaluationSession.objects.filter(
            lab_name=lab_name,
            created_at__gte=start_date
        )
        
        if not sessions.exists():
            return {"error": "No data found for this lab"}
        
        total_sessions = sessions.count()
        total_points_lost = sessions.aggregate(total=Sum('total_points_lost'))['total'] or 0
        avg_points_lost = sessions.aggregate(avg=Avg('total_points_lost'))['avg'] or 0.0
        
        # Get section breakdown
        section_stats = sessions.values('student__section').annotate(
            count=Count('id'),
            avg_points=Avg('total_points_lost')
        )
        
        common_issues = self._analyze_common_issues(sessions)
        
        return {
            "lab_name": lab_name,
            "period_days": days,
            "total_sessions": total_sessions,
            "total_points_lost": total_points_lost,
            "average_points_lost": round(avg_points_lost, 2),
            "section_breakdown": list(section_stats),
            "common_issues": common_issues
        }

    def analyze_performance_by_semester(self, semester: str, days: int = 30) -> Dict[str, Any]:
        """Analyze performance for specific semester"""
        start_date = timezone.now() - timedelta(days=days)
        
        sessions = EvaluationSession.objects.filter(
            student__semester=semester,
            created_at__gte=start_date
        )
        
        if not sessions.exists():
            return {"error": "No data found for this semester"}
        
        total_sessions = sessions.count()
        total_points_lost = sessions.aggregate(total=Sum('total_points_lost'))['total'] or 0
        avg_points_lost = sessions.aggregate(avg=Avg('total_points_lost'))['avg'] or 0.0
        
        # Get lab breakdown
        lab_stats = sessions.values('lab_name').annotate(
            count=Count('id'),
            avg_points=Avg('total_points_lost')
        )
        
        common_issues = self._analyze_common_issues(sessions)
        
        return {
            "semester": semester,
            "period_days": days,
            "total_sessions": total_sessions,
            "total_points_lost": total_points_lost,
            "average_points_lost": round(avg_points_lost, 2),
            "lab_breakdown": list(lab_stats),
            "common_issues": common_issues
        }

    def analyze_performance_by_lab_semester(self, lab_name: str, semester: str, days: int = 30) -> Dict[str, Any]:
        """Analyze performance for specific lab and semester"""
        start_date = timezone.now() - timedelta(days=days)
        
        sessions = EvaluationSession.objects.filter(
            lab_name=lab_name,
            student__semester=semester,
            created_at__gte=start_date
        )
        
        if not sessions.exists():
            return {"error": "No data found for this lab and semester"}
        
        total_sessions = sessions.count()
        total_points_lost = sessions.aggregate(total=Sum('total_points_lost'))['total'] or 0
        avg_points_lost = sessions.aggregate(avg=Avg('total_points_lost'))['avg'] or 0.0
        
        # Get section breakdown
        section_stats = sessions.values('student__section').annotate(
            count=Count('id'),
            avg_points=Avg('total_points_lost')
        )
        
        common_issues = self._analyze_common_issues(sessions)
        
        return {
            "lab_name": lab_name,
            "semester": semester,
            "period_days": days,
            "total_sessions": total_sessions,
            "total_points_lost": total_points_lost,
            "average_points_lost": round(avg_points_lost, 2),
            "section_breakdown": list(section_stats),
            "common_issues": common_issues
        }

    def _analyze_common_issues(self, sessions) -> str:
        """Use nano model to analyze common issues from session data focusing on programming concepts"""
        try:
            # Get recent feedback for analysis
            recent_feedback = []
            for session in sessions[:10]:  # Limit to 10 recent sessions
                if session.summary_feedback:
                    recent_feedback.append(session.summary_feedback)
            
            if not recent_feedback:
                return "No feedback data available"
            
            # Create simple prompt for nano model
            feedback_text = "\n".join(recent_feedback[:5])  # Limit to 5 feedback items
            
            prompt = f"""
Analyze these student feedback items and identify the most common PROGRAMMING CONCEPT issues in 1-2 sentences:

{feedback_text}

Focus on core programming concepts:
- Arrays/Lists handling
- Loops (for, while)
- Dictionaries/Objects
- Functions/Methods
- Variables/Data types
- Input/Output handling
- Calculations/Logic
- Error handling
- Code structure/Formatting

DO NOT mention specific lab topics like "GPA calculations" or "time calculations".
Instead say "students struggle with loops" or "good understanding of arrays".

Respond with only the concept-based common issues.
"""
            
            response = self.openai_service.create_chat_completion([
                {"role": "system", "content": "You are an educational analyst. Focus on core programming concepts, not specific lab topics. Be concise and concept-focused."},
                {"role": "user", "content": prompt}
            ])
            
            return response if response else "Analysis not available"
            
        except Exception as e:
            return "Analysis not available"

    def analyze_student_performance(self, student_id: str) -> Dict[str, Any]:
        """Analyze and summarize student's overall performance"""
        try:
            student = Student.objects.get(student_id=student_id)
            evaluations = Evaluation.objects.filter(student=student)
            sessions = EvaluationSession.objects.filter(student=student)
            
            if not evaluations.exists():
                return {"error": "No evaluations found for this student"}
            
            # Basic stats
            total_evaluations = evaluations.count()
            total_points_lost = evaluations.aggregate(total=Sum('total_points_lost'))['total'] or 0
            avg_points_lost = evaluations.aggregate(avg=Avg('total_points_lost'))['avg'] or 0.0
            
            # Lab breakdown
            lab_stats = sessions.values('lab_name').annotate(
                count=Count('id'),
                avg_points=Avg('total_points_lost'),
                total_points=Sum('total_points_lost')
            ).order_by('lab_name')
            
            # Recent performance (last 5 evaluations)
            recent_evaluations = evaluations.order_by('-created_at')[:5]
            recent_data = []
            for eval in recent_evaluations:
                recent_data.append({
                    "lab_name": eval.lab_name,
                    "points_lost": eval.total_points_lost,
                    "date": eval.created_at.isoformat()
                })
            
            # Performance trend analysis
            performance_summary = self._analyze_student_trend(student_id, sessions)
            
            return {
                "student_id": student.student_id,
                "name": student.name,
                "section": student.section,
                "semester": student.semester,
                "instructor_name": student.instructor_name,
                "total_evaluations": total_evaluations,
                "total_points_lost": total_points_lost,
                "average_points_lost": round(avg_points_lost, 2),
                "lab_breakdown": list(lab_stats),
                "recent_evaluations": recent_data,
                "performance_summary": performance_summary,
                "first_evaluation": evaluations.order_by('created_at').first().created_at.isoformat(),
                "last_evaluation": evaluations.order_by('-created_at').first().created_at.isoformat()
            }
            
        except Student.DoesNotExist:
            return {"error": "Student not found"}

    def _analyze_student_trend(self, student_id: str, sessions) -> str:
        """Use nano model to analyze student's performance trend by programming concepts"""
        try:
            # Get recent feedback for trend analysis
            recent_feedback = []
            for session in sessions.order_by('-created_at')[:10]:
                if session.summary_feedback:
                    recent_feedback.append(f"Lab: {session.lab_name}, Points Lost: {session.total_points_lost}, Feedback: {session.summary_feedback}")
            
            if not recent_feedback:
                return "No recent feedback available for trend analysis"
            
            # Create simple prompt for nano model focused on programming concepts
            feedback_text = "\n".join(recent_feedback[:5])
            
            prompt = f"""
Analyze this student's performance data and provide a 2-3 sentence summary focusing on CORE PROGRAMMING CONCEPTS (not specific lab topics):

{feedback_text}

Focus on programming concepts like:
- Arrays/Lists handling
- Loops (for, while)
- Dictionaries/Objects
- Functions/Methods
- Variables/Data types
- Input/Output handling
- Calculations/Logic
- Error handling
- Code structure/Formatting

DO NOT mention specific lab topics like "GPA calculations" or "time calculations".
Instead say "student is comfortable with arrays" or "struggles with loops".

Respond with only the concept-based analysis.
"""
            
            response = self.openai_service.create_chat_completion([
                {"role": "system", "content": "You are an educational analyst. Focus on core programming concepts, not specific lab topics. Be concise and concept-focused."},
                {"role": "user", "content": prompt}
            ])
            
            return response if response else "Performance trend analysis not available"
            
        except Exception as e:
            return "Performance trend analysis not available"

    def get_summarized_performance_by_lab(self, lab_name: str, section: str = None, semester: str = None) -> Dict[str, Any]:
        """Get summarized performance for a specific lab with optional filters"""
        try:
            # Build query
            sessions = EvaluationSession.objects.filter(lab_name=lab_name)
            if section:
                sessions = sessions.filter(student__section=section)
            if semester:
                sessions = sessions.filter(student__semester=semester)
            
            if not sessions.exists():
                return {"error": "No data found for this lab"}
            
            # Basic stats
            total_sessions = sessions.count()
            total_points_lost = sessions.aggregate(total=Sum('total_points_lost'))['total'] or 0
            avg_points_lost = sessions.aggregate(avg=Avg('total_points_lost'))['avg'] or 0.0
            
            # Section breakdown (if not already filtered by section)
            section_breakdown = []
            if not section:
                section_stats = sessions.values('student__section').annotate(
                    count=Count('id'),
                    avg_points=Avg('total_points_lost')
                ).order_by('student__section')
                section_breakdown = list(section_stats)
            
            # Semester breakdown (if not already filtered by semester)
            semester_breakdown = []
            if not semester:
                semester_stats = sessions.values('student__semester').annotate(
                    count=Count('id'),
                    avg_points=Avg('total_points_lost')
                ).order_by('student__semester')
                semester_breakdown = list(semester_stats)
            
            # Performance summary with token limit check
            performance_summary = self._get_performance_summary_with_limit(sessions, f"lab {lab_name}")
            
            return {
                "lab_name": lab_name,
                "section": section,
                "semester": semester,
                "total_sessions": total_sessions,
                "total_points_lost": total_points_lost,
                "average_points_lost": round(avg_points_lost, 2),
                "section_breakdown": section_breakdown,
                "semester_breakdown": semester_breakdown,
                "performance_summary": performance_summary
            }
            
        except Exception as e:
            return {"error": f"Failed to analyze lab performance: {str(e)}"}

    def get_summarized_performance_by_section(self, section: str, lab_name: str = None, semester: str = None) -> Dict[str, Any]:
        """Get summarized performance for a specific section with optional filters"""
        try:
            # Build query
            sessions = EvaluationSession.objects.filter(student__section=section)
            if lab_name:
                sessions = sessions.filter(lab_name=lab_name)
            if semester:
                sessions = sessions.filter(student__semester=semester)
            
            if not sessions.exists():
                return {"error": "No data found for this section"}
            
            # Basic stats
            total_sessions = sessions.count()
            total_points_lost = sessions.aggregate(total=Sum('total_points_lost'))['total'] or 0
            avg_points_lost = sessions.aggregate(avg=Avg('total_points_lost'))['avg'] or 0.0
            
            # Lab breakdown (if not already filtered by lab)
            lab_breakdown = []
            if not lab_name:
                lab_stats = sessions.values('lab_name').annotate(
                    count=Count('id'),
                    avg_points=Avg('total_points_lost')
                ).order_by('lab_name')
                lab_breakdown = list(lab_stats)
            
            # Semester breakdown (if not already filtered by semester)
            semester_breakdown = []
            if not semester:
                semester_stats = sessions.values('student__semester').annotate(
                    count=Count('id'),
                    avg_points=Avg('total_points_lost')
                ).order_by('student__semester')
                semester_breakdown = list(semester_stats)
            
            # Performance summary with token limit check
            performance_summary = self._get_performance_summary_with_limit(sessions, f"section {section}")
            
            return {
                "section": section,
                "lab_name": lab_name,
                "semester": semester,
                "total_sessions": total_sessions,
                "total_points_lost": total_points_lost,
                "average_points_lost": round(avg_points_lost, 2),
                "lab_breakdown": lab_breakdown,
                "semester_breakdown": semester_breakdown,
                "performance_summary": performance_summary
            }
            
        except Exception as e:
            return {"error": f"Failed to analyze section performance: {str(e)}"}

    def get_summarized_performance_by_semester(self, semester: str, lab_name: str = None, section: str = None) -> Dict[str, Any]:
        """Get summarized performance for a specific semester with optional filters"""
        try:
            # Build query
            sessions = EvaluationSession.objects.filter(student__semester=semester)
            if lab_name:
                sessions = sessions.filter(lab_name=lab_name)
            if section:
                sessions = sessions.filter(student__section=section)
            
            if not sessions.exists():
                return {"error": "No data found for this semester"}
            
            # Basic stats
            total_sessions = sessions.count()
            total_points_lost = sessions.aggregate(total=Sum('total_points_lost'))['total'] or 0
            avg_points_lost = sessions.aggregate(avg=Avg('total_points_lost'))['avg'] or 0.0
            
            # Lab breakdown (if not already filtered by lab)
            lab_breakdown = []
            if not lab_name:
                lab_stats = sessions.values('lab_name').annotate(
                    count=Count('id'),
                    avg_points=Avg('total_points_lost')
                ).order_by('lab_name')
                lab_breakdown = list(lab_stats)
            
            # Section breakdown (if not already filtered by section)
            section_breakdown = []
            if not section:
                section_stats = sessions.values('student__section').annotate(
                    count=Count('id'),
                    avg_points=Avg('total_points_lost')
                ).order_by('student__section')
                section_breakdown = list(section_stats)
            
            # Performance summary with token limit check
            performance_summary = self._get_performance_summary_with_limit(sessions, f"semester {semester}")
            
            return {
                "semester": semester,
                "lab_name": lab_name,
                "section": section,
                "total_sessions": total_sessions,
                "total_points_lost": total_points_lost,
                "average_points_lost": round(avg_points_lost, 2),
                "lab_breakdown": lab_breakdown,
                "section_breakdown": section_breakdown,
                "performance_summary": performance_summary
            }
            
        except Exception as e:
            return {"error": f"Failed to analyze semester performance: {str(e)}"}

    def _get_performance_summary_with_limit(self, sessions, context: str) -> str:
        """Get performance summary with token limit check (400 tokens total)"""
        try:
            # Get recent feedback for analysis
            recent_feedback = []
            for session in sessions.order_by('-created_at')[:20]:  # Limit to 20 recent sessions
                if session.summary_feedback:
                    recent_feedback.append(session.summary_feedback)
            
            if not recent_feedback:
                return "No feedback data available"
            
            # Check token length before processing
            feedback_text = "\n".join(recent_feedback[:5])  # Limit to 5 feedback items
            estimated_tokens = len(feedback_text.split()) * 1.3  # Rough token estimation
            
            if estimated_tokens > 300:  # Leave room for prompt (400 - 100 for prompt)
                return "MAX_LIMIT_EXCEEDED: Too much data to analyze. Please use more specific filters."
            
            # Create simple prompt for nano model
            prompt = f"""
Analyze these student feedback items for {context} and identify the most common PROGRAMMING CONCEPT issues in 2-3 sentences:

{feedback_text}

Focus on core programming concepts:
- Arrays/Lists handling
- Loops (for, while)
- Dictionaries/Objects
- Functions/Methods
- Variables/Data types
- Input/Output handling
- Calculations/Logic
- Error handling
- Code structure/Formatting

DO NOT mention specific lab topics like "GPA calculations" or "time calculations".
Instead say "students struggle with loops" or "good understanding of arrays".

Respond with only the concept-based analysis.
"""
            
            response = self.openai_service.create_chat_completion([
                {"role": "system", "content": "You are an educational analyst. Focus on core programming concepts, not specific lab topics. Be concise and concept-focused."},
                {"role": "user", "content": prompt}
            ])
            
            return response if response else "Analysis not available"
            
        except Exception as e:
            return "Analysis not available"

    def get_all_labs(self) -> List[Dict[str, Any]]:
        """Get all labs with basic information"""
        try:
            labs = LabRubric.objects.filter(is_active=True).order_by('lab_name', 'semester', 'section')
            result = []
            
            for lab in labs:
                # Get basic stats for this lab
                evaluations = Evaluation.objects.filter(lab_name=lab.lab_name)
                total_evaluations = evaluations.count()
                avg_points_lost = evaluations.aggregate(avg=Avg('total_points_lost'))['avg'] or 0.0
                
                result.append({
                    "id": lab.id,
                    "lab_name": lab.lab_name,
                    "semester": lab.semester,
                    "section": lab.section,
                    "total_points": lab.total_points,
                    "is_active": lab.is_active,
                    "total_evaluations": total_evaluations,
                    "average_points_lost": round(avg_points_lost, 2),
                    "created_at": lab.created_at.isoformat(),
                    "updated_at": lab.updated_at.isoformat()
                })
            
            return result
            
        except Exception as e:
            return []

    def get_lab_by_id(self, lab_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific lab by ID"""
        try:
            lab = LabRubric.objects.get(id=lab_id)
            
            # Get detailed stats for this lab
            evaluations = Evaluation.objects.filter(lab_name=lab.lab_name)
            sessions = EvaluationSession.objects.filter(lab_name=lab.lab_name)
            
            total_evaluations = evaluations.count()
            total_sessions = sessions.count()
            avg_points_lost = evaluations.aggregate(avg=Avg('total_points_lost'))['avg'] or 0.0
            
            # Get section breakdown
            section_stats = sessions.values('student__section').annotate(
                count=Count('id'),
                avg_points=Avg('total_points_lost')
            ).order_by('student__section')
            
            # Get semester breakdown
            semester_stats = sessions.values('student__semester').annotate(
                count=Count('id'),
                avg_points=Avg('total_points_lost')
            ).order_by('student__semester')
            
            # Get recent evaluations (last 5)
            recent_evaluations = evaluations.order_by('-created_at')[:5]
            recent_data = []
            for eval in recent_evaluations:
                recent_data.append({
                    "student_id": eval.student.student_id,
                    "student_name": eval.student.name,
                    "points_lost": eval.total_points_lost,
                    "status": eval.status,
                    "date": eval.created_at.isoformat()
                })
            
            return {
                "id": lab.id,
                "lab_name": lab.lab_name,
                "semester": lab.semester,
                "section": lab.section,
                "total_points": lab.total_points,
                "criteria": lab.criteria,
                "is_active": lab.is_active,
                "total_evaluations": total_evaluations,
                "total_sessions": total_sessions,
                "average_points_lost": round(avg_points_lost, 2),
                "section_breakdown": list(section_stats),
                "semester_breakdown": list(semester_stats),
                "recent_evaluations": recent_data,
                "created_at": lab.created_at.isoformat(),
                "updated_at": lab.updated_at.isoformat()
            }
            
        except LabRubric.DoesNotExist:
            return {"error": "Lab not found"}
        except Exception as e:
            return {"error": f"Failed to get lab details: {str(e)}"} 