"""
File processing utilities for the AI Code Evaluation System.
Handles all file I/O operations with proper error handling.
"""

import json
import re
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

from config import Config


class FileProcessor:
    """Handles file I/O operations for the evaluation system."""

    @staticmethod
    def parse_input(input_text: str) -> Dict[str, str]:
        """
        Parse input text and extract code files.

        Args:
            input_text: Raw input text containing multiple lab files

        Returns:
            Dictionary with lab names as keys and cleaned code as values
        """
        files = {}

        # Remove triple quotes if present
        input_text = input_text.strip()
        if input_text.startswith('"""') and input_text.endswith('"""'):
            input_text = input_text[3:-3].strip()

        # Pattern to match file names followed by "Download" and then code
        pattern = r"(\w+\.py)\s*\n\s*Download\s*\n(.*?)(?=\s*\w+\.py\s*\n\s*Download|$)"
        matches = re.findall(pattern, input_text, re.DOTALL)

        for filename, code in matches:
            cleaned_code = FileProcessor._clean_code_content(code)
            files[filename] = cleaned_code

        return files

    @staticmethod
    def _clean_code_content(code: str) -> str:
        """
        Clean individual code content by removing header comments.

        Args:
            code: Raw code content

        Returns:
            Cleaned code content
        """
        lines = code.split("\n")
        cleaned_lines = []
        skip_header = True

        for line in lines:
            # Check if this is a header comment line
            if (
                skip_header
                and line.strip().startswith("#")
                and any(
                    keyword in line
                    for keyword in [
                        "Class:",
                        "Section:",
                        "Term:",
                        "Instructor:",
                        "Name:",
                        "Lab:",
                    ]
                )
            ):
                continue
            else:
                skip_header = False
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()

    @staticmethod
    def validate_input(input_text: str) -> bool:
        """Check if input has valid format"""
        if not input_text:
            return False
        
        # Check if it has at least one file marker
        if '.py' not in input_text and 'Download' not in input_text:
            return False
        
        return True

    @staticmethod
    def get_file_count(input_text: str) -> int:
        """Count number of files in input"""
        files = FileProcessor.parse_input(input_text)
        return len(files)

    @staticmethod
    def load_and_process_input() -> Tuple[Dict[str, str], Dict[str, Any]]:
        """
        Load and process input files in memory.

        Returns:
            Tuple of (cleaned_codes, rubrics)
        """
        try:
            # Load rubrics
            rubrics = FileProcessor.load_rubrics()
            if not rubrics:
                raise ValueError("No rubrics found")

            # Load and clean input text
            codes = FileProcessor.load_and_clean_input()
            if not codes:
                raise ValueError("No code files found")

            # Validate that we have rubrics for all code files
            missing_rubrics = set(codes.keys()) - set(rubrics.keys())
            if missing_rubrics:
                logger.warning(f"Missing rubrics for files: {missing_rubrics}")

            # Filter codes to only include those with rubrics
            filtered_codes = {k: v for k, v in codes.items() if k in rubrics}

            logger.info(
                f"Successfully loaded {len(filtered_codes)} code files and {len(rubrics)} rubrics"
            )
            return filtered_codes, rubrics

        except Exception as e:
            logger.error(f"Error loading and processing input: {str(e)}")
            raise

    @staticmethod
    def load_and_clean_input() -> Dict[str, str]:
        """
        Load and clean input text from input.txt.

        Returns:
            Dictionary with filename as key and cleaned code as value
        """
        try:
            with open(Config.INPUT_FILE, "r", encoding="utf-8") as file:
                input_text = file.read()

            cleaned_files = FileProcessor.parse_input(input_text)
            logger.info(
                f"Successfully cleaned {len(cleaned_files)} code files from {Config.INPUT_FILE}"
            )
            return cleaned_files

        except FileNotFoundError:
            logger.error(f"File not found: {Config.INPUT_FILE}")
            return {}
        except Exception as e:
            logger.error(f"Error loading input from {Config.INPUT_FILE}: {str(e)}")
            return {}

    @staticmethod
    def load_rubrics() -> Dict[str, Any]:
        """
        Load evaluation rubrics from rubrics.json.

        Returns:
            Dictionary with filename as key and rubric as value
        """
        try:
            with open(Config.RUBRICS_FILE, "r", encoding="utf-8") as file:
                rubrics = json.load(file)

            logger.info(
                f"Successfully loaded rubrics for {len(rubrics)} files from {Config.RUBRICS_FILE}"
            )
            return rubrics

        except FileNotFoundError:
            logger.error(f"File not found: {Config.RUBRICS_FILE}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {Config.RUBRICS_FILE}: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Error loading rubrics from {Config.RUBRICS_FILE}: {str(e)}")
            return {}

    @staticmethod
    def write_feedback_json(feedbacks: Dict[str, Any]) -> bool:
        """
        Write evaluation feedback to feedback.json.

        Args:
            feedbacks: Dictionary with evaluation results

        Returns:
            True if successful, False otherwise
        """
        try:
            feedback_data = {
                "evaluation_results": feedbacks,
                "metadata": {
                    "total_files": len(feedbacks),
                    "evaluation_timestamp": str(Path().stat().st_mtime),
                    "system_version": Config.APP_VERSION,
                },
            }

            with open(Config.FEEDBACK_FILE, "w", encoding="utf-8") as file:
                json.dump(feedback_data, file, indent=2, ensure_ascii=False)

            logger.info(
                f"Successfully wrote feedback for {len(feedbacks)} files to {Config.FEEDBACK_FILE}"
            )
            return True

        except Exception as e:
            logger.error(f"Error writing feedback to {Config.FEEDBACK_FILE}: {str(e)}")
            return False

    @staticmethod
    def ensure_directories() -> None:
        """Ensure all required directories exist."""
        Path("logs").mkdir(exist_ok=True)
        logger.debug("Ensured required directories exist")
