"""
Configuration settings for the AI Code Evaluation System.
Centralizes all settings, API keys, and constants.
"""

import os
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables
load_dotenv()


class Config:
    """Central configuration class for the application."""

    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = "gpt-4.1-nano"
    OPENAI_MAX_TOKENS = 200
    OPENAI_TEMPERATURE = 0.1

    # Application Configuration
    APP_NAME = "AI Code Evaluation System"
    APP_VERSION = "1.0.0"

    # File Paths (only essential files)
    INPUT_FILE = "input.txt"
    RUBRICS_FILE = "rubrics.json"
    FEEDBACK_FILE = "feedback.json"  # Changed to JSON

    # Logging Configuration
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = "logs/app.log"

    # Evaluation Configuration
    MAX_WORKERS = 3  # Number of parallel LLM workers
    EVALUATION_TIMEOUT = 30  # seconds

    # Database Configuration (for future use)
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///evaluations.db")

    # Validation
    @classmethod
    def validate(cls) -> bool:
        """Validate that all required configuration is present."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required in .env file")
        return True

    @classmethod
    def get_openai_config(cls) -> Dict[str, Any]:
        """Get OpenAI configuration as a dictionary."""
        return {
            "api_key": cls.OPENAI_API_KEY,
            "model": cls.OPENAI_MODEL,
            "max_tokens": cls.OPENAI_MAX_TOKENS,
            "temperature": cls.OPENAI_TEMPERATURE,
        }
