"""
config.py - Configuration management for Sentinel-Vision agent.

Centralized configuration using dataclasses for API keys, model parameters,
and runtime settings. Loads configuration from environment variables with
sensible defaults and validation.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """
    Configuration parameters for Sentinel-Vision agent.
    
    Loads settings from environment variables with fallback defaults.
    All required values are validated during instantiation.
    """
    
    # API Configuration
    GEMINI_API_KEY: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    GEMINI_MODEL: str = "gemini-1.5-pro"
    
    # Video Processing
    FRAME_EXTRACTION_INTERVAL: int = field(
        default_factory=lambda: int(os.getenv("FRAME_EXTRACTION_INTERVAL", "2"))
    )
    MAX_FRAMES_PER_VIDEO: int = field(
        default_factory=lambda: int(os.getenv("MAX_FRAMES_PER_VIDEO", "300"))
    )
    VIDEO_TIMEOUT_SECONDS: int = field(
        default_factory=lambda: int(os.getenv("VIDEO_TIMEOUT_SECONDS", "600"))
    )
    
    # Analysis Settings
    ANALYSIS_TEMPERATURE: float = 0.3
    ANALYSIS_MAX_TOKENS: int = 2048
    
    # Output Configuration
    OUTPUT_DIR: str = field(
        default_factory=lambda: os.getenv("OUTPUT_DIR", "./outputs")
    )
    REPORT_FORMAT: str = "PDF"
    
    # Logging
    LOG_LEVEL: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO")
    )
    LOG_DIR: str = field(
        default_factory=lambda: os.getenv("LOG_DIR", "./logs")
    )
    
    def __post_init__(self) -> None:
        """
        Validate configuration after instantiation.
        
        Raises:
            ValueError: If required configuration is missing or invalid
        """
        self._validate_config()
    
    def _validate_config(self) -> None:
        """
        Validate all required configuration parameters.
        
        Raises:
            ValueError: If required parameters are missing or invalid
        """
        if not self.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY environment variable is not set. "
                "Please set GEMINI_API_KEY to your Google Generative AI API key."
            )
        
        if self.FRAME_EXTRACTION_INTERVAL < 1:
            raise ValueError(
                f"FRAME_EXTRACTION_INTERVAL must be >= 1, got {self.FRAME_EXTRACTION_INTERVAL}"
            )
        
        if self.MAX_FRAMES_PER_VIDEO < 1:
            raise ValueError(
                f"MAX_FRAMES_PER_VIDEO must be >= 1, got {self.MAX_FRAMES_PER_VIDEO}"
            )
        
        if self.VIDEO_TIMEOUT_SECONDS < 1:
            raise ValueError(
                f"VIDEO_TIMEOUT_SECONDS must be >= 1, got {self.VIDEO_TIMEOUT_SECONDS}"
            )
        
        if not 0 <= self.ANALYSIS_TEMPERATURE <= 1:
            raise ValueError(
                f"ANALYSIS_TEMPERATURE must be between 0 and 1, got {self.ANALYSIS_TEMPERATURE}"
            )
        
        if self.LOG_LEVEL not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError(
                f"LOG_LEVEL must be one of DEBUG, INFO, WARNING, ERROR, CRITICAL, "
                f"got {self.LOG_LEVEL}"
            )
        
        logger.debug("Configuration validation passed")
    
    @classmethod
    def from_env(cls) -> "Config":
        """
        Create a Config instance from environment variables.
        
        Returns:
            Initialized Config instance
            
        Raises:
            ValueError: If required environment variables are missing
        """
        try:
            return cls()
        except ValueError as e:
            logger.error(f"Configuration error: {str(e)}")
            raise
    
    def to_dict(self) -> dict:
        """
        Convert configuration to dictionary (excluding sensitive values).
        
        Returns:
            Dictionary representation of configuration with API key masked
        """
        config_dict = {
            "GEMINI_MODEL": self.GEMINI_MODEL,
            "FRAME_EXTRACTION_INTERVAL": self.FRAME_EXTRACTION_INTERVAL,
            "MAX_FRAMES_PER_VIDEO": self.MAX_FRAMES_PER_VIDEO,
            "VIDEO_TIMEOUT_SECONDS": self.VIDEO_TIMEOUT_SECONDS,
            "ANALYSIS_TEMPERATURE": self.ANALYSIS_TEMPERATURE,
            "ANALYSIS_MAX_TOKENS": self.ANALYSIS_MAX_TOKENS,
            "OUTPUT_DIR": self.OUTPUT_DIR,
            "REPORT_FORMAT": self.REPORT_FORMAT,
            "LOG_LEVEL": self.LOG_LEVEL,
            "LOG_DIR": self.LOG_DIR,
            "GEMINI_API_KEY": "***MASKED***" if self.GEMINI_API_KEY else "NOT_SET"
        }
        return config_dict
