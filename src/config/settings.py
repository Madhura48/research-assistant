import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration settings for the Research Assistant System"""
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Model Configuration
    LLM_MODEL = "gpt-4-turbo-preview"
    TEMPERATURE = 0.1
    MAX_TOKENS = 4000
    
    # System Configuration
    MAX_SEARCH_RESULTS = 10
    MAX_RETRY_ATTEMPTS = 3
    TIMEOUT_SECONDS = 30
    
    # Memory Configuration
    MEMORY_SIZE = 1000
    CONTEXT_WINDOW = 8000
    
    # Quality Thresholds
    MIN_CONFIDENCE_SCORE = 0.7
    MIN_RELEVANCE_SCORE = 0.6
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")
        return True