"""
OpenAI service for code evaluation using GPT-4.1-nano model.
Optimized for consistent, concise feedback with token management.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from openai import OpenAI
from django.conf import settings
from cache_utils import cache_llm_response

logger = logging.getLogger(__name__)

class OpenAIService:
    """OpenAI service for code evaluation"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4o-mini"  # Using gpt-4o-mini as nano equivalent
        self.max_tokens = 500
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
        """Evaluate code using specific rubric criteria with caching"""
        try:
            # Create evaluation prompt
            prompt = self._create_evaluation_prompt(code_content, rubric_criteria, filename)
            
            # Get cached or fresh response
            response = self.create_chat_completion([
                {"role": "system", "content": "You are a strict code evaluator. Follow rubrics exactly. Give concise, actionable feedback."},
                {"role": "user", "content": prompt}
            ])
            
            if not response:
                return {
                    "status": "error",
                    "feedback": "Evaluation failed - no response from AI service",
                    "points_lost": 0
                }
            
            # Parse response
            result = self._parse_evaluation_response(response, rubric_criteria)
            return result
            
        except Exception as e:
            logger.error(f"Code evaluation error: {str(e)}")
            return {
                "status": "error",
                "feedback": f"Evaluation failed: {str(e)}",
                "points_lost": 0
            }
    
    def generate_summary_feedback(self, individual_feedback: List[str], lab_name: str) -> str:
        """Generate summary feedback from individual file feedback with caching"""
        try:
            # Combine feedback for analysis
            feedback_text = "\n".join(individual_feedback[:5])  # Limit to 5 feedback items
            
            # Create summary prompt
            prompt = f"""
Analyze these code evaluation feedback items for {lab_name} and provide a 2-3 sentence summary focusing on CORE PROGRAMMING CONCEPTS:

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
Instead say "student shows good understanding of arrays" or "struggles with loops".

Use random student names like Alex, Jordan, Taylor, Casey, Morgan, etc.
Respond with only the concept-based analysis.
"""
            
            response = self.create_chat_completion([
                {"role": "system", "content": "You are an educational analyst. Focus on core programming concepts, not specific lab topics. Be concise and concept-focused."},
                {"role": "user", "content": prompt}
            ])
            
            return response if response else "Summary analysis not available"
            
        except Exception as e:
            logger.error(f"Summary generation error: {str(e)}")
            return "Summary analysis not available"
    
    def _create_evaluation_prompt(self, code_content: str, rubric_criteria: Dict[str, Any], filename: str) -> str:
        """Create evaluation prompt from rubric criteria"""
        criteria_text = ""
        total_points = 0
        
        for criterion, details in rubric_criteria.items():
            points = details.get('points', 0)
            description = details.get('description', '')
            criteria_text += f"- {criterion}: {points} points - {description}\n"
            total_points += points
        
        prompt = f"""
Evaluate this Python code file '{filename}' using the following rubric criteria:

{criteria_text}

Total possible points: {total_points}

Code to evaluate:
{code_content}

Instructions:
1. Check each criterion and deduct points for issues found
2. Provide specific, actionable feedback for each deduction
3. Be strict but fair - no double deductions
4. Give partial credit when appropriate
5. Focus on programming concepts, not just syntax
6. Keep feedback concise and clear

Respond in this exact format:
POINTS_LOST: [total points deducted]
FEEDBACK: [detailed feedback with specific issues and suggestions]
"""
        
        return prompt
    
    def _parse_evaluation_response(self, response: str, rubric_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Parse evaluation response from AI"""
        try:
            lines = response.strip().split('\n')
            points_lost = 0
            feedback = ""
            
            for line in lines:
                line = line.strip()
                if line.startswith('POINTS_LOST:'):
                    try:
                        points_lost = int(line.split(':', 1)[1].strip())
                    except (ValueError, IndexError):
                        points_lost = 0
                elif line.startswith('FEEDBACK:'):
                    feedback = line.split(':', 1)[1].strip()
            
            # If parsing failed, use the entire response as feedback
            if not feedback:
                feedback = response.strip()
            
            return {
                "status": "success",
                "feedback": feedback,
                "points_lost": points_lost
            }
            
        except Exception as e:
            logger.error(f"Response parsing error: {str(e)}")
            return {
                "status": "error",
                "feedback": f"Failed to parse evaluation response: {str(e)}",
                "points_lost": 0
            }

# Global instance
openai_service = OpenAIService()
