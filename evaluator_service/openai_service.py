"""
OpenAI service for handling LLM interactions.
Provides centralized OpenAI API communication with proper error handling.
"""

import json
from typing import Dict, Any, Optional
from openai import OpenAI
from openai.types.chat import ChatCompletion

from config import Config


class OpenAIService:
    """Service class for OpenAI API interactions."""

    def __init__(self):
        """Initialize OpenAI client."""
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)

    def create_chat_completion(
        self,
        messages: list,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Create a chat completion with the OpenAI API.

        Args:
            messages: List of message dictionaries
            model: Model to use (defaults to config)
            max_tokens: Maximum tokens (defaults to config)
            temperature: Temperature setting (defaults to config)

        Returns:
            Dictionary with response content and token usage or None if error
        """
        try:
            # Use config defaults if not provided
            model = model or Config.OPENAI_MODEL
            max_tokens = max_tokens or Config.OPENAI_MAX_TOKENS
            temperature = temperature or Config.OPENAI_TEMPERATURE

            completion: ChatCompletion = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            response_content = completion.choices[0].message.content
            
            # Extract token usage
            usage = completion.usage
            token_info = {
                'content': response_content,
                'input_tokens': usage.prompt_tokens if usage else 0,
                'output_tokens': usage.completion_tokens if usage else 0,
                'total_tokens': usage.total_tokens if usage else 0
            }
            
            return token_info

        except Exception as e:
            return None

    def evaluate_code(
        self,
        filename: str,
        code: str,
        rubric: Dict[str, Any],
        evaluation_type: str = "initial",
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluate code using LLM with enhanced prompts for edge cases.

        Args:
            filename: Name of the file being evaluated
            code: Code content to evaluate
            rubric: Evaluation rubric
            evaluation_type: Type of evaluation ("initial" or "double_check")

        Returns:
            Evaluation result dictionary with token usage or None if error
        """
        try:
            # Validate inputs
            if not code or not code.strip():
                return self._create_error_response(
                    "EMPTY_CODE", "No code content provided"
                )

            if not isinstance(rubric, dict):
                return self._create_error_response(
                    "INVALID_RUBRIC", "Invalid rubric format"
                )

            system_message = self._get_system_message(evaluation_type)
            user_message = self._build_enhanced_evaluation_prompt(
                filename, code, rubric, evaluation_type
            )

            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ]

            response = self.create_chat_completion(messages)

            if not response:
                return self._create_error_response(
                    "API_ERROR", "Failed to get evaluation from LLM"
                )

            # Parse response
            result = self._parse_evaluation_response(response['content'], filename)
            
            # Add token usage to result
            result['input_tokens'] = response['input_tokens']
            result['output_tokens'] = response['output_tokens']
            result['total_tokens'] = response['total_tokens']
            
            return result

        except Exception as e:
            return self._create_error_response("EVALUATION_ERROR", str(e))

    def _get_system_message(self, evaluation_type: str) -> str:
        """Get appropriate system message based on evaluation type."""
        if evaluation_type == "initial":
            return """You are a coding instructor evaluating student code. Follow these STRICT rules:

EVALUATION RULES:
- ONLY evaluate against the provided rubric criteria
- NO deductions for extra code not in rubric
- NO deductions for missing input validation
- Give PARTIAL credit if student attempted but didn't complete correctly
- Give PARTIAL credit if student tried but didn't meet rubric exactly
- If failure is due to previously deducted rubric, DO NOT deduct again
- Be LENIENT - students are learning
- Output SHORT, CONCISE feedback - only what's wrong, no explanations

FORMAT RULES:
- Perfect code: "correct"
- Issues: "1. [SHORT issue] --> -[points] points"
- Use EXACT format: "Missing array implementation --> -2 points"
- Calculate total points_lost correctly
- Always respond with valid JSON"""
        else:
            return """You are reviewing grading for consistency. Follow these STRICT rules:

EVALUATION RULES:
- ONLY evaluate against the provided rubric criteria
- NO deductions for extra code not in rubric
- NO deductions for missing input validation
- Give PARTIAL credit if student attempted but didn't complete correctly
- Give PARTIAL credit if student tried but didn't meet rubric exactly
- If failure is due to previously deducted rubric, DO NOT deduct again
- Be LENIENT - students are learning
- Output SHORT, CONCISE feedback - only what's wrong, no explanations

FORMAT RULES:
- Perfect code: "correct"
- Issues: "1. [SHORT issue] --> -[points] points"
- Use EXACT format: "Missing array implementation --> -2 points"
- Calculate total points_lost correctly
- Always respond with valid JSON"""

    def _build_enhanced_evaluation_prompt(
        self, filename: str, code: str, rubric: Dict[str, Any], evaluation_type: str
    ) -> str:
        """
        Build enhanced evaluation prompt with strict, specific format in JSON.
        """
        base_prompt = f"""
Evaluate this code against the provided rubric. Output ONLY valid JSON with this EXACT format:

If perfect: {{"feedback": "correct", "points_lost": 0}}

If issues: {{"feedback": "1. [SHORT issue] --> -[points] points\\n2. [SHORT issue] --> -[points] points", "points_lost": [total_points_lost]}}

CRITICAL RULES:
- ONLY evaluate rubric criteria - ignore extra code
- NO deductions for missing input validation
- Give PARTIAL credit for attempts (if they tried but didn't complete correctly)
- Give PARTIAL credit if they tried but didn't meet rubric exactly
- If failure is due to previously deducted rubric, DO NOT deduct again
- Be LENIENT - students are learning
- Use EXACT format: "Missing array implementation --> -2 points"
- SHORT and CONCISE - only what's wrong, no explanations

Code file: {filename}
Code:
{code}

Rubric:
{json.dumps(rubric, indent=2)}

Output ONLY the JSON response, nothing else.
"""
        return base_prompt

    def _parse_evaluation_response(
        self, response: str, filename: str
    ) -> Dict[str, Any]:
        """
        Parse evaluation response and extract feedback.

        Args:
            response: Raw response from LLM
            filename: Name of the file being evaluated

        Returns:
            Parsed evaluation result
        """
        try:
            # Clean response
            response = response.strip()
            
            # Try to parse as JSON
            try:
                parsed = json.loads(response)
                feedback = parsed.get("feedback", "")
                points_lost = parsed.get("points_lost", 0)
                
                # Ensure points_lost is an integer
                if isinstance(points_lost, str):
                    try:
                        points_lost = int(points_lost)
                    except ValueError:
                        points_lost = 0
                elif not isinstance(points_lost, (int, float)):
                    points_lost = 0
                    
            except json.JSONDecodeError:
                # If not valid JSON, treat as plain text
                feedback = response
                points_lost = 0

            return {
                "filename": filename,
                "status": "success",
                "feedback": feedback,
                "total_points_lost": int(points_lost),
                "deductions": [],
                "raw_response": response,
            }

        except Exception as e:
            return self._create_error_response("PARSE_ERROR", str(e))

    def _create_error_response(self, error_type: str, message: str) -> Dict[str, Any]:
        """
        Create standardized error response.

        Args:
            error_type: Type of error
            message: Error message

        Returns:
            Error response dictionary
        """
        return {
            "status": "error",
            "error_type": error_type,
            "feedback": f"Error: {message}",
            "total_points_lost": 0,
            "deductions": [],
        }

    def summarize_feedback(self, feedback_json: dict) -> str:
        """
        Create a summary of all feedback.

        Args:
            feedback_json: Dictionary of feedback results

        Returns:
            Summary string
        """
        try:
            total_files = len(feedback_json)
            total_points_lost = sum(
                result.get("total_points_lost", 0) for result in feedback_json.values()
            )
            
            return f"Evaluated {total_files} files. Total points lost: {total_points_lost}"
            
        except Exception:
            return "Evaluation completed"


# Global service instance
openai_service = OpenAIService()
