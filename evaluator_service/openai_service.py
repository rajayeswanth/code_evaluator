"""
OpenAI service for code evaluation using GPT-4.1-nano model.
Optimized for beginner-friendly evaluation with topic-focused feedback.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from openai import OpenAI
from django.conf import settings
from cache_utils import cache_llm_response
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

class OpenAIService:
    """OpenAI service for code evaluation"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4o-mini"
        self.max_tokens = 800
        self.temperature = 0.1
        
    @cache_llm_response(cache_alias="llm_cache", timeout=3600)
    def create_chat_completion(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """Create chat completion with caching"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            if response.choices and response.choices[0].message:
                return response.choices[0].message.content.strip()
            
            return None
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return None
    
    def evaluate_code_with_rubric(self, code_content: str, rubric_criteria: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """Evaluate code using three parallel LLMs with beginner-friendly approach"""
        try:
            # Create evaluation prompt
            prompt = self._create_beginner_evaluation_prompt(code_content, rubric_criteria, filename)
            
            # Run three parallel evaluations
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = []
                for i in range(3):
                    future = executor.submit(self._single_evaluation, prompt, f"evaluator_{i+1}")
                    futures.append(future)
                
                # Collect all results
                results = []
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        results.append(result)
            
            # Use evaluator model to combine results
            final_result = self._evaluate_with_evaluator_model(results, filename)
            return final_result
            
        except Exception as e:
            logger.error(f"Code evaluation error: {str(e)}")
            return {
                "status": "error",
                "feedback": f"Evaluation failed: {str(e)}",
                "points_lost": 0
            }
    
    def _single_evaluation(self, prompt: str, evaluator_name: str) -> Optional[Dict[str, Any]]:
        """Single LLM evaluation"""
        try:
            response = self.create_chat_completion([
                {"role": "system", "content": f"You are {evaluator_name}, a beginner-friendly code evaluator. Focus on core programming concepts only."},
                {"role": "user", "content": prompt}
            ])
            
            if response:
                return self._parse_json_response(response)
            return None
            
        except Exception as e:
            logger.error(f"Single evaluation error: {str(e)}")
            return None
    
    def _evaluate_with_evaluator_model(self, results: List[Dict[str, Any]], filename: str) -> Dict[str, Any]:
        """Use evaluator model to combine and finalize results"""
        try:
            # Create evaluator prompt
            evaluator_prompt = f"""
You are the final evaluator. Review these three evaluations for '{filename}' and provide the final result.

Evaluations:
{json.dumps(results, indent=2)}

Provide the final evaluation in this exact JSON format:
{{
    "status": "success",
    "result": "correct" OR {{
        "issues": [
            {{"issue": "specific programming issue description", "points": -X}},
            {{"issue": "another specific issue description", "points": -X}}
        ]
    }},
    "topics_lacking": ["array_handling", "loop_control", "variable_scope", etc.],
    "summary": "2-3 sentence summary focusing on programming topics student needs to improve"
}}

Focus on core programming topics like: arrays, loops, variables, functions, conditionals, input/output.
Combine the evaluations and identify the specific programming issues found in the code.
"""
            
            response = self.create_chat_completion([
                {"role": "system", "content": "You are the final evaluator. Combine evaluations and focus on programming topics."},
                {"role": "user", "content": evaluator_prompt}
            ])
            
            if response:
                return self._parse_json_response(response)
            else:
                return {"status": "error", "feedback": "Evaluator model failed"}
                
        except Exception as e:
            logger.error(f"Evaluator model error: {str(e)}")
            return {"status": "error", "feedback": f"Evaluator failed: {str(e)}"}
    
    def _create_beginner_evaluation_prompt(self, code_content: str, rubric_criteria: Dict[str, Any], filename: str) -> str:
        """Create beginner-friendly evaluation prompt"""
        criteria_text = ""
        total_points = 0
        
        for criterion, details in rubric_criteria.items():
            points = details.get('points', 0)
            description = details.get('description', '')
            criteria_text += f"- {criterion}: {points} points - {description}\n"
            total_points += points
        
        prompt = f"""
Evaluate this Python code file '{filename}' for BEGINNERS using these criteria:

{criteria_text}

Total possible points: {total_points}

Code to evaluate:
{code_content}

BEGINNER-FRIENDLY EVALUATION RULES:
1. NO deductions for missing input validation
2. NO deductions for extra code or preprocessing steps
3. NO deductions for code formatting or comments
4. Focus ONLY on core programming concepts
5. Be encouraging and constructive
6. Only deduct points for fundamental programming errors

Core programming topics to evaluate:
- Array/List handling and manipulation
- Loop implementation and control
- Variable declaration and usage
- Function definition and calls
- Conditional statements (if/else)
- Basic calculations and logic
- Input/Output operations

Respond in this exact JSON format:
{{
    "status": "success",
    "result": "correct" OR {{
        "issues": [
            {{"issue": "specific programming issue found", "points": -X}},
            {{"issue": "another specific issue found", "points": -X}}
        ]
    }},
    "topics_lacking": ["array_handling", "loop_control", "variable_scope", etc.],
    "summary": "2-3 sentence summary focusing on programming topics student needs to improve"
}}

If code is correct, use "correct". If there are issues, list the specific programming concept problems you find in the actual code.
"""
        
        return prompt
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from AI"""
        try:
            # Clean the response
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            # Parse JSON
            result = json.loads(response.strip())
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            # Fallback parsing
            return self._fallback_parse(response)
        except Exception as e:
            logger.error(f"Response parsing error: {str(e)}")
            return {"status": "error", "feedback": f"Failed to parse response: {str(e)}"}
    
    def _fallback_parse(self, response: str) -> Dict[str, Any]:
        """Fallback parsing for non-JSON responses"""
        try:
            # Look for "correct" in response
            if "correct" in response.lower():
                return {
                    "status": "success",
                    "result": "correct",
                    "topics_lacking": [],
                    "summary": "Code is correct"
                }
            
            # Try to extract issues
            issues = []
            topics = []
            
            lines = response.split('\n')
            for line in lines:
                line = line.strip()
                if 'points' in line.lower() or '-' in line:
                    # Extract issue description
                    if ':' in line:
                        issue = line.split(':', 1)[1].strip()
                        issues.append({"issue": issue, "points": -2})
            
            return {
                "status": "success",
                "result": {"issues": issues} if issues else "correct",
                "topics_lacking": topics,
                "summary": "Evaluation completed"
            }
            
        except Exception as e:
            
            return {"status": "error", "feedback": f"Fallback parsing failed: {str(e)}"}

# Global instance
openai_service = OpenAIService()
