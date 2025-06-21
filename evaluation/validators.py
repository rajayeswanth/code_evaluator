import re
from typing import Dict, Any, List, Tuple
from django.core.exceptions import ValidationError
from utils.logger import logger


class InputValidator:
    """Comprehensive input validation for all API endpoints."""
    
    @staticmethod
    def validate_student_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate student data with strict requirements.
        
        Args:
            data: Student data dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        required_fields = ['student_id', 'name', 'section', 'term', 'instructor_name']
        
        # Check required fields
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"Missing required field: {field}")
                continue
            
            # Validate field types and formats
            if not isinstance(data[field], str):
                errors.append(f"Field {field} must be a string")
                continue
            
            # Trim whitespace
            data[field] = data[field].strip()
            
            if not data[field]:
                errors.append(f"Field {field} cannot be empty")
                continue
        
        # Validate specific field formats
        if 'student_id' in data and data['student_id']:
            if not re.match(r'^[A-Z0-9_-]{3,20}$', data['student_id']):
                errors.append("student_id must be 3-20 characters, alphanumeric with hyphens/underscores only")
        
        if 'name' in data and data['name']:
            if len(data['name']) < 2 or len(data['name']) > 100:
                errors.append("name must be 2-100 characters")
            if not re.match(r'^[a-zA-Z\s\.\'-]+$', data['name']):
                errors.append("name contains invalid characters")
        
        if 'section' in data and data['section']:
            if not re.match(r'^[A-Z0-9]{1,10}$', data['section']):
                errors.append("section must be 1-10 alphanumeric characters")
        
        if 'term' in data and data['term']:
            if not re.match(r'^(Spring|Summer|Fall|Winter)\s+\d{4}$', data['term']):
                errors.append("term must be in format: 'Spring 2025', 'Fall 2024', etc.")
        
        if 'instructor_name' in data and data['instructor_name']:
            if len(data['instructor_name']) < 2 or len(data['instructor_name']) > 100:
                errors.append("instructor_name must be 2-100 characters")
            if not re.match(r'^[a-zA-Z\s\.\'-]+$', data['instructor_name']):
                errors.append("instructor_name contains invalid characters")
        
        logger.info(f"Student data validation: {len(errors)} errors found")
        if errors:
            logger.warning(f"Student validation errors: {errors}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_rubric_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate rubric data with strict requirements.
        
        Args:
            data: Rubric data dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        required_fields = ['name', 'filename', 'total_points', 'criteria']
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
                continue
            
            if field == 'total_points':
                if not isinstance(data[field], int) or data[field] <= 0:
                    errors.append("total_points must be a positive integer")
            elif field == 'criteria':
                if not isinstance(data[field], (dict, list)):
                    errors.append("criteria must be a dictionary or list")
            else:
                if not isinstance(data[field], str) or not data[field].strip():
                    errors.append(f"Field {field} must be a non-empty string")
        
        # Validate filename format
        if 'filename' in data and data['filename']:
            if not re.match(r'^[a-zA-Z0-9_\-\.]+\.py$', data['filename']):
                errors.append("filename must be a valid Python filename ending in .py")
        
        # Validate criteria structure
        if 'criteria' in data and isinstance(data['criteria'], dict):
            for key, value in data['criteria'].items():
                if not isinstance(value, dict):
                    errors.append(f"Criteria item '{key}' must be a dictionary")
                    continue
                
                if 'points' not in value or not isinstance(value['points'], (int, float)):
                    errors.append(f"Criteria item '{key}' must have numeric 'points' field")
                
                if 'description' not in value or not isinstance(value['description'], str):
                    errors.append(f"Criteria item '{key}' must have string 'description' field")
        
        logger.info(f"Rubric data validation: {len(errors)} errors found")
        if errors:
            logger.warning(f"Rubric validation errors: {errors}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_evaluation_request(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate evaluation request data with strict requirements.
        
        Args:
            data: Evaluation request data dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        required_fields = ['student_id', 'name', 'section', 'term', 'instructor_name', 'lab_name', 'input']
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
                continue
            
            if field == 'input':
                if not isinstance(data[field], str) or not data[field].strip():
                    errors.append("input must be a non-empty string")
            elif field == 'lab_name':
                if not isinstance(data[field], str) or not data[field].strip():
                    errors.append("lab_name must be a non-empty string")
                if not re.match(r'^[a-zA-Z0-9\s\-_]{1,50}$', data[field]):
                    errors.append("lab_name contains invalid characters")
            else:
                if not isinstance(data[field], str) or not data[field].strip():
                    errors.append(f"Field {field} must be a non-empty string")
        
        # Validate input content
        if 'input' in data and data['input']:
            input_text = data['input'].strip()
            if len(input_text) < 10:
                errors.append("input must be at least 10 characters")
            
            if len(input_text) > 50000:
                errors.append("input too large (max 50,000 characters)")
            
            # Check for basic code structure
            if 'Download' not in input_text:
                errors.append("input must contain 'Download' keyword for file separation")
            
            if '.py' not in input_text:
                errors.append("input must contain Python files (.py)")
        
        # Validate submission metadata if provided
        if 'submission_metadata' in data:
            if not isinstance(data['submission_metadata'], dict):
                errors.append("submission_metadata must be a dictionary")
            else:
                # Validate metadata keys and values
                for key, value in data['submission_metadata'].items():
                    if not isinstance(key, str):
                        errors.append("submission_metadata keys must be strings")
                    if not isinstance(value, (str, int, float, bool, list, dict)):
                        errors.append(f"submission_metadata value for '{key}' has invalid type")
        
        logger.info(f"Evaluation request validation: {len(errors)} errors found")
        if errors:
            logger.warning(f"Evaluation validation errors: {errors}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_code_content(codes: Dict[str, str]) -> Tuple[bool, List[str]]:
        """
        Validate extracted code content.
        
        Args:
            codes: Dictionary of filename to code content
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not codes:
            errors.append("No code files found in input")
            return False, errors
        
        for filename, code in codes.items():
            # Validate filename
            if not re.match(r'^[a-zA-Z0-9_\-\.]+\.py$', filename):
                errors.append(f"Invalid filename format: {filename}")
            
            # Validate code content
            if not code or not code.strip():
                errors.append(f"Empty code content for file: {filename}")
                continue
            
            code_lines = code.strip().split('\n')
            if len(code_lines) < 3:
                errors.append(f"Code file {filename} too short (minimum 3 lines)")
            
            # Check for basic Python syntax indicators
            python_keywords = ['def ', 'class ', 'import ', 'from ', 'if ', 'for ', 'while ', 'print(', 'input(']
            has_python_content = any(keyword in code for keyword in python_keywords)
            
            if not has_python_content:
                errors.append(f"File {filename} doesn't appear to contain Python code")
        
        logger.info(f"Code content validation: {len(errors)} errors found")
        if errors:
            logger.warning(f"Code validation errors: {errors}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def sanitize_input(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize input data to prevent injection attacks.
        
        Args:
            data: Raw input data
            
        Returns:
            Sanitized data dictionary
        """
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                # Remove potentially dangerous characters
                sanitized_value = re.sub(r'[<>"\']', '', value.strip())
                sanitized[key] = sanitized_value
            elif isinstance(value, dict):
                sanitized[key] = InputValidator.sanitize_input(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    InputValidator.sanitize_input(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        logger.debug(f"Input sanitization completed for {len(data)} fields")
        return sanitized


class ValidationError(Exception):
    """Custom validation error with detailed error messages."""
    
    def __init__(self, errors: List[str], field: str = None):
        self.errors = errors
        self.field = field
        super().__init__(f"Validation failed: {', '.join(errors)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for API response."""
        return {
            'status': 'error',
            'message': 'Validation failed',
            'errors': self.errors,
            'field': self.field
        } 