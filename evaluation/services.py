import uuid
import time
import traceback
import logging
from typing import Dict, Any, List, Optional
from django.db import transaction, models
from django.utils import timezone

from .models import (
    LabRubric, Student, Evaluation, EvaluationSession, SystemMetrics, ErrorLog
)
from .validators import InputValidator, ValidationError
from data_service.file_processor import FileProcessor
from evaluator_service.code_evaluator import CodeEvaluator
from evaluator_service.openai_service import openai_service

logger = logging.getLogger(__name__)


class RubricService:
    """Service for managing rubrics with strict validation."""
    
    @staticmethod
    def create_rubric(data: Dict[str, Any]) -> LabRubric:
        """Create a new rubric with validation."""
        logger.info(f"Creating rubric: {data.get('filename', 'unknown')}")
        
        try:
            # Sanitize input
            sanitized_data = InputValidator.sanitize_input(data)
            
            # Validate rubric data
            is_valid, errors = InputValidator.validate_rubric_data(sanitized_data)
            if not is_valid:
                logger.error(f"Rubric validation failed: {errors}")
                raise ValidationError(errors, 'rubric_data')
            
            with transaction.atomic():
                rubric = LabRubric.objects.create(
                    name=sanitized_data['name'],
                    filename=sanitized_data['filename'],
                    total_points=sanitized_data['total_points'],
                    criteria=sanitized_data['criteria']
                )
                logger.info(f"Successfully created rubric: {rubric.filename} (ID: {rubric.id})")
                return rubric
                
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating rubric: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            raise
    
    @staticmethod
    def get_rubric_by_filename(filename: str) -> Optional[LabRubric]:
        """Get rubric by filename with logging."""
        logger.debug(f"Looking up rubric for filename: {filename}")
        
        try:
            rubric = LabRubric.objects.filter(filename=filename, is_active=True).first()
            if rubric:
                logger.debug(f"Found rubric: {rubric.filename} (ID: {rubric.id})")
            else:
                logger.warning(f"No active rubric found for filename: {filename}")
            return rubric
            
        except Exception as e:
            logger.error(f"Error getting rubric {filename}: {str(e)}")
            return None
    
    @staticmethod
    def get_all_rubrics() -> List[LabRubric]:
        """Get all active rubrics with logging."""
        logger.debug("Fetching all active rubrics")
        
        try:
            rubrics = list(LabRubric.objects.filter(is_active=True).order_by('filename'))
            logger.info(f"Retrieved {len(rubrics)} active rubrics")
            return rubrics
            
        except Exception as e:
            logger.error(f"Error getting all rubrics: {str(e)}")
            return []
    
    @staticmethod
    def update_rubric(rubric_id: int, data: Dict[str, Any]) -> Optional[LabRubric]:
        """Update an existing rubric with validation."""
        logger.info(f"Updating rubric ID: {rubric_id}")
        
        try:
            # Sanitize input
            sanitized_data = InputValidator.sanitize_input(data)
            
            # Validate rubric data if provided
            if 'name' in sanitized_data or 'filename' in sanitized_data or 'criteria' in sanitized_data:
                validation_data = {
                    'name': sanitized_data.get('name', ''),
                    'filename': sanitized_data.get('filename', ''),
                    'total_points': sanitized_data.get('total_points', 1),
                    'criteria': sanitized_data.get('criteria', {})
                }
                is_valid, errors = InputValidator.validate_rubric_data(validation_data)
                if not is_valid:
                    logger.error(f"Rubric update validation failed: {errors}")
                    raise ValidationError(errors, 'rubric_update')
            
            with transaction.atomic():
                rubric = LabRubric.objects.get(id=rubric_id)
                for key, value in sanitized_data.items():
                    if hasattr(rubric, key):
                        setattr(rubric, key, value)
                rubric.save()
                logger.info(f"Successfully updated rubric: {rubric.filename} (ID: {rubric.id})")
                return rubric
                
        except LabRubric.DoesNotExist:
            logger.warning(f"Rubric {rubric_id} not found")
            return None
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error updating rubric {rubric_id}: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            return None


class StudentService:
    """Service for managing students with strict validation."""
    
    @staticmethod
    def get_or_create_student(data: Dict[str, Any]) -> Student:
        """Get existing student or create new one with validation."""
        logger.info(f"Processing student: {data.get('student_id', 'unknown')}")
        
        try:
            # Sanitize input
            sanitized_data = InputValidator.sanitize_input(data)
            
            # Validate student data
            is_valid, errors = InputValidator.validate_student_data(sanitized_data)
            if not is_valid:
                logger.error(f"Student validation failed: {errors}")
                raise ValidationError(errors, 'student_data')
            
            student, created = Student.objects.get_or_create(
                student_id=sanitized_data['student_id'],
                defaults={
                    'name': sanitized_data['name'],
                    'section': sanitized_data['section'],
                    'term': sanitized_data['term'],
                    'instructor_name': sanitized_data['instructor_name']
                }
            )
            
            if created:
                logger.info(f"Created new student: {student.name} ({student.student_id})")
            else:
                # Update existing student info
                student.name = sanitized_data['name']
                student.section = sanitized_data['section']
                student.term = sanitized_data['term']
                student.instructor_name = sanitized_data['instructor_name']
                student.save()
                logger.info(f"Updated existing student: {student.name} ({student.student_id})")
            
            return student
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting/creating student: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            raise


class EvaluationService:
    """Service for handling evaluations with comprehensive validation and logging."""
    
    def __init__(self):
        self.code_evaluator = CodeEvaluator()
        logger.info("EvaluationService initialized")
    
    def evaluate_submission(self, student_data: Dict[str, Any], lab_name: str, 
                          input_text: str, submission_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Evaluate a complete submission with comprehensive validation and logging."""
        start_time = time.time()
        session_id = str(uuid.uuid4())
        
        logger.info(f"Starting evaluation session: {session_id}")
        logger.info(f"Student: {student_data.get('student_id', 'unknown')}")
        logger.info(f"Lab: {lab_name}")
        logger.info(f"Input length: {len(input_text)} characters")
        
        try:
            # Validate student data
            is_valid, errors = InputValidator.validate_student_data(student_data)
            if not is_valid:
                logger.error(f"Student data validation failed: {errors}")
                raise ValidationError(errors, 'student_data')
            
            # Validate evaluation request
            eval_request = {
                'student_id': student_data['student_id'],
                'name': student_data['name'],
                'section': student_data['section'],
                'term': student_data['term'],
                'instructor_name': student_data['instructor_name'],
                'lab_name': lab_name,
                'input': input_text,
                'submission_metadata': submission_metadata or {}
            }
            
            is_valid, errors = InputValidator.validate_evaluation_request(eval_request)
            if not is_valid:
                logger.error(f"Evaluation request validation failed: {errors}")
                raise ValidationError(errors, 'evaluation_request')
            
            # Get or create student
            student = StudentService.get_or_create_student(student_data)
            logger.info(f"Student processed: {student.name} (ID: {student.id})")
            
            # Process input files
            logger.info("Processing input files...")
            codes = FileProcessor.clean_text(input_text)
            logger.info(f"Detected {len(codes)} files: {list(codes.keys())}")
            
            # Validate extracted code content
            is_valid, errors = InputValidator.validate_code_content(codes)
            if not is_valid:
                logger.error(f"Code content validation failed: {errors}")
                raise ValidationError(errors, 'code_content')
            
            # Get rubrics from database
            logger.info("Retrieving rubrics from database...")
            rubrics = {}
            missing_rubrics = []
            
            for filename in codes.keys():
                rubric = RubricService.get_rubric_by_filename(filename)
                if rubric:
                    rubrics[filename] = {
                        'total_points': rubric.total_points,
                        'criteria': rubric.criteria
                    }
                    logger.debug(f"Found rubric for {filename}")
                else:
                    missing_rubrics.append(filename)
                    logger.warning(f"No rubric found for {filename}")
            
            if missing_rubrics:
                logger.warning(f"Missing rubrics for files: {missing_rubrics}")
            
            # Validate evaluation setup
            logger.info("Validating evaluation setup...")
            if not self.code_evaluator.validate_evaluation_setup(codes, rubrics):
                error_msg = "Invalid evaluation setup - missing rubrics or empty codes"
                logger.error(error_msg)
                raise ValidationError([error_msg], 'evaluation_setup')
            
            # Perform evaluations
            logger.info("Starting code evaluation...")
            evaluation_results = self.code_evaluator.evaluate_all_files(codes, rubrics)
            logger.info(f"Evaluation completed. Results: {list(evaluation_results.keys())}")
            
            # Create evaluation session
            logger.info("Creating evaluation session...")
            session = self._create_evaluation_session(
                student, session_id, lab_name, codes, evaluation_results, 
                submission_metadata, start_time
            )
            
            # Create individual evaluations
            logger.info("Creating individual evaluation records...")
            evaluations = self._create_evaluations(
                student, session, codes, evaluation_results, rubrics, submission_metadata
            )
            logger.info(f"Created {len(evaluations)} evaluation records")
            
            # Generate summary
            logger.info("Generating summary feedback...")
            summary = self._generate_summary(evaluation_results, session)
            
            total_time = time.time() - start_time
            logger.info(f"Total evaluation time: {total_time:.2f} seconds")
            
            # Log metrics
            self._log_evaluation_metrics(session, total_time)
            
            # Log successful completion
            logger.info(f"Evaluation session {session_id} completed successfully")
            
            return {
                'session_id': session_id,
                'feedback': {k: v for k, v in evaluation_results.items() if k != '_summary'},
                'summary': summary,
                'total_files_evaluated': session.total_files_evaluated,
                'successful_evaluations': session.successful_evaluations,
                'error_evaluations': session.error_evaluations,
                'total_points_lost': session.total_points_lost,
                'total_evaluation_time_seconds': total_time,
                'total_tokens_used': session.total_tokens_used
            }
            
        except ValidationError:
            logger.error(f"Validation error in evaluation session {session_id}")
            self._log_error("VALIDATION_ERROR", str(ValidationError), student_data.get('student_id'), session_id)
            raise
        except Exception as e:
            logger.error(f"Error in evaluation session {session_id}: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            self._log_error("EVALUATION_ERROR", str(e), student_data.get('student_id'), session_id)
            raise
    
    def _create_evaluation_session(self, student: Student, session_id: str, lab_name: str,
                                 codes: Dict[str, str], evaluation_results: Dict[str, Any],
                                 submission_metadata: Dict[str, Any], start_time: float) -> EvaluationSession:
        """Create evaluation session record with logging."""
        logger.debug(f"Creating evaluation session: {session_id}")
        
        try:
            summary = evaluation_results.get('_summary', {})
            
            session = EvaluationSession.objects.create(
                student=student,
                session_id=session_id,
                lab_name=lab_name,
                summary_feedback="",  # Will be updated later
                total_files_evaluated=summary.get('total_files_evaluated', 0),
                successful_evaluations=summary.get('successful_evaluations', 0),
                error_evaluations=summary.get('error_evaluations', 0),
                total_points_lost=summary.get('total_points_lost', 0),
                total_deductions=summary.get('total_deductions', 0),
                submission_data={
                    'codes': codes,
                    'metadata': submission_metadata or {}
                },
                total_evaluation_time_seconds=0,  # Will be updated
                total_tokens_used=0  # Will be updated
            )
            
            logger.debug(f"Created evaluation session: {session_id} (ID: {session.id})")
            return session
            
        except Exception as e:
            logger.error(f"Error creating evaluation session: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            raise
    
    def _create_evaluations(self, student: Student, session: EvaluationSession,
                          codes: Dict[str, str], evaluation_results: Dict[str, Any],
                          rubrics: Dict[str, Any], submission_metadata: Dict[str, Any]) -> List[Evaluation]:
        """Create individual evaluation records with logging."""
        evaluations = []
        
        logger.debug(f"Creating evaluations for session: {session.session_id}")
        
        try:
            for filename, result in evaluation_results.items():
                if filename == '_summary':
                    continue
                
                logger.debug(f"Processing evaluation for: {filename}")
                
                rubric = RubricService.get_rubric_by_filename(filename)
                if not rubric:
                    logger.warning(f"No rubric found for {filename}, skipping evaluation record")
                    continue
                
                evaluation = Evaluation.objects.create(
                    student=student,
                    rubric=rubric,
                    lab_name=session.lab_name,
                    filename=filename,
                    status=result.get('status', 'error'),
                    feedback=result.get('feedback', ''),
                    total_points_lost=result.get('total_points_lost', 0),
                    deductions=result.get('deductions', []),
                    code_content=codes.get(filename, ''),
                    submission_metadata=submission_metadata or {},
                    evaluation_time_seconds=result.get('evaluation_time_seconds', 0)
                )
                
                evaluations.append(evaluation)
                logger.debug(f"Created evaluation record for {filename} (ID: {evaluation.id})")
                
                # Store LLM responses if available
                if 'llm_responses' in result:
                    for llm_response_data in result['llm_responses']:
                        LLMResponse.objects.create(
                            evaluation=evaluation,
                            evaluation_type=llm_response_data.get('evaluation_type', 'unknown'),
                            prompt_tokens=llm_response_data.get('prompt_tokens', 0),
                            completion_tokens=llm_response_data.get('completion_tokens', 0),
                            total_tokens=llm_response_data.get('total_tokens', 0),
                            model_used=llm_response_data.get('model_used', ''),
                            temperature=llm_response_data.get('temperature', 0.0),
                            max_tokens=llm_response_data.get('max_tokens', 0),
                            raw_response=llm_response_data.get('raw_response', ''),
                            parsed_response=llm_response_data.get('parsed_response', {}),
                            response_time_seconds=llm_response_data.get('response_time_seconds', 0)
                        )
                        logger.debug(f"Stored LLM response for {filename}")
            
            logger.info(f"Successfully created {len(evaluations)} evaluation records")
            return evaluations
            
        except Exception as e:
            logger.error(f"Error creating evaluations: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            raise
    
    def _generate_summary(self, evaluation_results: Dict[str, Any], session: EvaluationSession) -> str:
        """Generate summary feedback with logging."""
        logger.debug(f"Generating summary for session: {session.session_id}")
        
        try:
            feedback_for_summary = {k: v for k, v in evaluation_results.items() if k != '_summary'}
            summary = openai_service.summarize_feedback(feedback_for_summary)
            
            # Update session with summary
            session.summary_feedback = summary
            session.save()
            
            logger.debug(f"Generated summary: {summary[:100]}...")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return "Summary not available."
    
    def _log_evaluation_metrics(self, session: EvaluationSession, total_time: float):
        """Log evaluation metrics with detailed logging."""
        logger.debug(f"Logging metrics for session: {session.session_id}")
        
        try:
            # Update session with final metrics
            session.total_evaluation_time_seconds = total_time
            session.total_tokens_used = sum(
                llm.total_tokens for eval in session.evaluations.all() 
                for llm in eval.llm_responses.all()
            )
            session.save()
            
            logger.info(f"Session metrics - Time: {total_time:.2f}s, Tokens: {session.total_tokens_used}")
            
            # Log system metrics
            SystemMetrics.objects.create(
                metric_type='evaluation',
                metric_name='total_time',
                metric_value=total_time,
                metric_unit='seconds',
                additional_data={'session_id': session.session_id}
            )
            
            SystemMetrics.objects.create(
                metric_type='evaluation',
                metric_name='total_tokens',
                metric_value=session.total_tokens_used,
                metric_unit='tokens',
                additional_data={'session_id': session.session_id}
            )
            
            logger.debug("System metrics logged successfully")
            
        except Exception as e:
            logger.error(f"Error logging metrics: {str(e)}")
    
    def _log_error(self, error_type: str, message: str, user_id: str = None, session_id: str = None):
        """Log error to database with comprehensive details."""
        logger.error(f"Logging error: {error_type} - {message}")
        
        try:
            ErrorLog.objects.create(
                level='ERROR',
                message=message,
                error_type=error_type,
                user_id=user_id,
                session_id=session_id,
                request_data={},
                stack_trace=traceback.format_exc()
            )
            logger.debug("Error logged to database successfully")
        except Exception as e:
            logger.error(f"Error logging error: {str(e)}")


class MonitoringService:
    """Service for monitoring and insights with enhanced logging."""
    
    @staticmethod
    def get_evaluation_stats(days: int = 30) -> Dict[str, Any]:
        """Get evaluation statistics for the last N days with logging."""
        logger.info(f"Getting evaluation stats for last {days} days")
        
        try:
            from django.utils import timezone
            from datetime import timedelta
            
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            sessions = EvaluationSession.objects.filter(created_at__range=[start_date, end_date])
            
            total_sessions = sessions.count()
            total_evaluations = sum(session.total_files_evaluated for session in sessions)
            total_tokens = sum(session.total_tokens_used for session in sessions)
            avg_time = sessions.aggregate(avg_time=models.Avg('total_evaluation_time_seconds'))['avg_time'] or 0
            
            stats = {
                'period_days': days,
                'total_sessions': total_sessions,
                'total_evaluations': total_evaluations,
                'total_tokens_used': total_tokens,
                'average_evaluation_time_seconds': avg_time,
                'success_rate': (sum(session.successful_evaluations for session in sessions) / 
                               max(sum(session.total_files_evaluated for session in sessions), 1)) * 100
            }
            
            logger.info(f"Retrieved stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting evaluation stats: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            return {}
    
    @staticmethod
    def get_student_performance(student_id: str) -> Dict[str, Any]:
        """Get performance statistics for a specific student with logging."""
        logger.info(f"Getting performance stats for student: {student_id}")
        
        try:
            student = Student.objects.get(student_id=student_id)
            evaluations = Evaluation.objects.filter(student=student)
            
            total_evaluations = evaluations.count()
            total_points_lost = sum(eval.total_points_lost for eval in evaluations)
            avg_points_lost = total_points_lost / max(total_evaluations, 1)
            
            performance = {
                'student_id': student_id,
                'student_name': student.name,
                'total_evaluations': total_evaluations,
                'total_points_lost': total_points_lost,
                'average_points_lost': avg_points_lost,
                'recent_evaluations': list(evaluations.order_by('-created_at')[:5].values(
                    'filename', 'status', 'total_points_lost', 'created_at'
                ))
            }
            
            logger.info(f"Retrieved performance for {student_id}: {performance}")
            return performance
            
        except Student.DoesNotExist:
            logger.warning(f"Student {student_id} not found")
            return {'error': 'Student not found'}
        except Exception as e:
            logger.error(f"Error getting student performance: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            return {'error': str(e)} 