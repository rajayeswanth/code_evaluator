"""
Code evaluation module for the AI Code Evaluation System.
Handles the evaluation logic and parallel processing.
"""

import time
from typing import Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import Config
from .openai_service import openai_service


class CodeEvaluator:
    """Handles code evaluation using LLMs with parallel processing."""

    def __init__(self):
        """Initialize the code evaluator."""
        self.openai_service = openai_service

    def evaluate_single_file(
        self, filename: str, code: str, rubric: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Evaluate a single file with initial and double-check evaluations.

        Args:
            filename: Name of the file to evaluate
            code: Code content to evaluate
            rubric: Evaluation rubric

        Returns:
            Tuple of (filename, evaluation_result)
        """
        start_time = time.time()

        try:
            # Initial evaluation
            initial_result = self.openai_service.evaluate_code(
                filename=filename, code=code, rubric=rubric, evaluation_type="initial"
            )

            if not initial_result:
                return filename, self._create_error_result(
                    filename, "Failed to get initial evaluation"
                )

            # Double-check evaluation
            double_check_result = self.openai_service.evaluate_code(
                filename=filename,
                code=code,
                rubric=rubric,
                evaluation_type="double_check",
            )

            if not double_check_result:
                final_result = initial_result
            else:
                # Use double-check result if it's more detailed or if initial had errors
                if (
                    initial_result.get("status") == "error"
                    and double_check_result.get("status") != "error"
                ):
                    final_result = double_check_result
                elif len(double_check_result.get("deductions", [])) > len(
                    initial_result.get("deductions", [])
                ):
                    final_result = double_check_result
                else:
                    final_result = initial_result

            evaluation_time = time.time() - start_time

            # Add timing information to result
            final_result["evaluation_time_seconds"] = evaluation_time

            return filename, final_result

        except Exception as e:
            return filename, self._create_error_result(filename, str(e))

    def evaluate_all_files(
        self, codes: Dict[str, str], rubrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate all files in parallel.

        Args:
            codes: Dictionary of filename to code content
            rubrics: Dictionary of filename to rubric (already structured per-file)

        Returns:
            Simple result dictionary with feedback and stats including token usage
        """
        start_time = time.time()

        evaluation_results = {}
        total_input_tokens = 0
        total_output_tokens = 0
        total_tokens = 0
        llm_calls_count = 0

        with ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
            # Submit all evaluation tasks
            future_to_filename = {}

            for filename, code in codes.items():
                # The rubrics parameter is already structured per-file
                # So we can access it directly by filename
                file_rubric = rubrics.get(filename, {})
                
                future = executor.submit(
                    self.evaluate_single_file, filename, code, file_rubric
                )
                future_to_filename[future] = filename

            # Collect results as they complete
            for future in as_completed(future_to_filename):
                filename = future_to_filename[future]
                try:
                    filename, result = future.result()
                    evaluation_results[filename] = result
                    
                    # Aggregate token usage
                    if result.get('status') != 'error':
                        total_input_tokens += result.get('input_tokens', 0)
                        total_output_tokens += result.get('output_tokens', 0)
                        total_tokens += result.get('total_tokens', 0)
                        llm_calls_count += 2  # Each file gets 2 calls (initial + double-check)
                    
                except Exception as e:
                    evaluation_results[filename] = self._create_error_result(
                        filename, str(e)
                    )

        total_time = time.time() - start_time

        # Combine all feedback into one string with strict formatting
        lab_feedback = {}
        total_points_lost = 0
        
        for filename, result in evaluation_results.items():
            if result.get('status') != 'error':
                feedback = result.get('feedback', '')
                points_lost = result.get('total_points_lost', 0)
                total_points_lost += points_lost
                
                # Format feedback consistently
                if feedback.strip() == "correct":
                    lab_feedback[filename] = "correct"
                else:
                    lab_feedback[filename] = feedback
            else:
                lab_feedback[filename] = f"Error - {result.get('feedback', 'Unknown error')}"

        # Create summarized feedback without using another LLM
        overall_feedback = self._create_overall_feedback(lab_feedback, total_points_lost, len(codes))

        return {
            'lab_feedback': lab_feedback,
            'overall_feedback': overall_feedback,
            'total_points_lost': total_points_lost,
            'file_results': list(evaluation_results.values()),
            'evaluation_time': total_time,
            'files_evaluated': len(codes),
            'total_input_tokens': total_input_tokens,
            'total_output_tokens': total_output_tokens,
            'total_tokens': total_tokens,
            'llm_calls_count': llm_calls_count
        }

    def _create_overall_feedback(self, lab_feedback: dict, total_points_lost: int, total_files: int) -> str:
        """
        Create analytical overall feedback from individual lab results.
        
        Args:
            lab_feedback: Dictionary of lab feedback
            total_points_lost: Total points lost
            total_files: Total number of files evaluated
            
        Returns:
            Analytical overall feedback string
        """
        # Count different types of results
        perfect_labs = sum(1 for feedback in lab_feedback.values() if feedback == "correct")
        error_labs = sum(1 for feedback in lab_feedback.values() if "Error" in feedback)
        
        if error_labs > 0:
            return f"Student has evaluation errors in {error_labs} labs. Total points lost: {total_points_lost}."
        
        if perfect_labs == total_files:
            return "Student has completed all labs perfectly. Excellent work!"
        elif perfect_labs == 0:
            return f"Student needs improvement in all labs. Total points lost: {total_points_lost}."
        else:
            # Analyze patterns in the feedback more specifically
            strengths = []
            weaknesses = []
            specific_issues = []
            
            for lab, feedback in lab_feedback.items():
                if feedback == "correct":
                    # Identify strengths based on lab content
                    if "Lab3A" in lab:
                        strengths.append("financial calculations")
                    elif "Lab3B" in lab:
                        strengths.append("GPA calculations")
                    elif "Lab3C" in lab:
                        strengths.append("time calculations")
                else:
                    # Extract specific issues from feedback
                    feedback_lower = feedback.lower()
                    
                    if "calculation" in feedback_lower:
                        if "minimum payment" in feedback_lower:
                            specific_issues.append("minimum payment calculation")
                        elif "monthly rate" in feedback_lower:
                            specific_issues.append("monthly rate calculation")
                        elif "gpa" in feedback_lower:
                            specific_issues.append("GPA calculation")
                        else:
                            specific_issues.append("mathematical calculations")
                    
                    if "input" in feedback_lower:
                        if "prompt" in feedback_lower:
                            specific_issues.append("input prompts")
                        else:
                            specific_issues.append("input handling")
                    
                    if "output" in feedback_lower:
                        if "format" in feedback_lower:
                            specific_issues.append("output formatting")
                        else:
                            specific_issues.append("output display")
                    
                    if "variable" in feedback_lower:
                        if "naming" in feedback_lower:
                            specific_issues.append("variable naming")
                        elif "initialization" in feedback_lower:
                            specific_issues.append("variable initialization")
                        else:
                            specific_issues.append("variable usage")
                    
                    if "loop" in feedback_lower:
                        if "exit" in feedback_lower:
                            specific_issues.append("loop exit conditions")
                        else:
                            specific_issues.append("loop implementation")
                    
                    if "array" in feedback_lower:
                        specific_issues.append("array handling")
                    
                    if "function" in feedback_lower:
                        specific_issues.append("function implementation")
                    
                    if "syntax" in feedback_lower:
                        specific_issues.append("syntax errors")
            
            # Create detailed analytical feedback
            if strengths and specific_issues:
                strength_summary = ", ".join(list(set(strengths)))
                issue_summary = ", ".join(list(set(specific_issues)))
                return f"Student demonstrates comfort with {strength_summary} but struggles with {issue_summary}. Focus on improving these specific areas. Total points lost: {total_points_lost}."
            elif specific_issues:
                issue_summary = ", ".join(list(set(specific_issues)))
                return f"Student needs improvement in {issue_summary}. Practice these concepts to strengthen understanding. Total points lost: {total_points_lost}."
            else:
                return f"Student has done well in {perfect_labs} labs but needs improvement in {total_files - perfect_labs} labs. Total points lost: {total_points_lost}."

    def _create_error_result(self, filename: str, error_message: str) -> Dict[str, Any]:
        """
        Create standardized error result.

        Args:
            filename: Name of the file
            error_message: Error message

        Returns:
            Error result dictionary
        """
        return {
            "filename": filename,
            "status": "error",
            "feedback": f"Error evaluating {filename}: {error_message}",
            "total_points_lost": 0,
            "deductions": [],
            "evaluation_time_seconds": 0,
        }

    def _create_evaluation_summary(
        self, results: Dict[str, Dict[str, Any]], total_time: float
    ) -> Dict[str, Any]:
        """
        Create summary statistics for all evaluations.

        Args:
            results: Dictionary of evaluation results
            total_time: Total evaluation time

        Returns:
            Summary dictionary
        """
        successful_evaluations = sum(
            1 for r in results.values() if r.get("status") != "error"
        )
        error_evaluations = len(results) - successful_evaluations
        total_points_lost = sum(r.get("total_points_lost", 0) for r in results.values())

        return {
            "total_files_evaluated": len(results),
            "successful_evaluations": successful_evaluations,
            "error_evaluations": error_evaluations,
            "total_points_lost": total_points_lost,
            "total_evaluation_time_seconds": total_time,
        }
