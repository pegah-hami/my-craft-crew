"""
Configuration management for the multi-agent design system.

This module handles application settings, environment variables,
and configuration validation.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    """
    
    # Application Settings
    app_name: str = Field(default="Multi-Agent Design System", env="APP_NAME")
    app_version: str = Field(default="0.1.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Server Settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    reload: bool = Field(default=False, env="RELOAD")
    
    # File Management
    upload_directory: str = Field(default="uploads", env="UPLOAD_DIRECTORY")
    processed_directory: str = Field(default="processed_images", env="PROCESSED_DIRECTORY")
    collage_directory: str = Field(default="collages", env="COLLAGE_DIRECTORY")
    max_file_size_mb: int = Field(default=10, env="MAX_FILE_SIZE_MB")
    allowed_extensions: List[str] = Field(
        default=[".jpg", ".jpeg", ".png", ".gif", ".webp"],
        env="ALLOWED_EXTENSIONS"
    )
    
    # Image Processing
    default_image_quality: int = Field(default=95, env="DEFAULT_IMAGE_QUALITY")
    default_output_width: int = Field(default=1024, env="DEFAULT_OUTPUT_WIDTH")
    default_output_height: int = Field(default=1024, env="DEFAULT_OUTPUT_HEIGHT")
    default_background_color: str = Field(default="#FFFFFF", env="DEFAULT_BACKGROUND_COLOR")
    default_spacing: int = Field(default=10, env="DEFAULT_SPACING")
    
    # Agent Settings
    max_concurrent_tasks_per_agent: int = Field(default=3, env="MAX_CONCURRENT_TASKS_PER_AGENT")
    agent_heartbeat_interval: int = Field(default=30, env="AGENT_HEARTBEAT_INTERVAL")
    task_timeout_seconds: int = Field(default=300, env="TASK_TIMEOUT_SECONDS")
    
    # Coordinator Settings
    coordinator_enabled: bool = Field(default=True, env="COORDINATOR_ENABLED")
    task_queue_size: int = Field(default=100, env="TASK_QUEUE_SIZE")
    max_retry_attempts: int = Field(default=3, env="MAX_RETRY_ATTEMPTS")
    
    # Database Settings (for future use)
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    # Redis Settings (for future use)
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    
    # Security
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Monitoring
    enable_metrics: bool = Field(default=False, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    
    # Future: Hugging Face Integration
    huggingface_token: Optional[str] = Field(default=None, env="HUGGINGFACE_TOKEN")
    huggingface_model: str = Field(default="runwayml/stable-diffusion-v1-5", env="HUGGINGFACE_MODEL")
    enable_diffusion: bool = Field(default=False, env="ENABLE_DIFFUSION")
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of {valid_levels}')
        return v.upper()
    
    @validator('max_file_size_mb')
    def validate_max_file_size(cls, v):
        if v <= 0 or v > 100:
            raise ValueError('Max file size must be between 1 and 100 MB')
        return v
    
    @validator('default_image_quality')
    def validate_image_quality(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Image quality must be between 1 and 100')
        return v
    
    @validator('allowed_extensions')
    def validate_extensions(cls, v):
        if isinstance(v, str):
            # Handle comma-separated string from environment
            v = [ext.strip() for ext in v.split(',')]
        
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        for ext in v:
            if ext not in valid_extensions:
                raise ValueError(f'Extension {ext} not supported. Valid: {valid_extensions}')
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class AgentConfig:
    """
    Configuration for individual agents.
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
    
    def get_design_agent_config(self) -> Dict[str, Any]:
        """Get configuration for design agent."""
        return {
            "agent_id": "design_agent_001",
            "agent_type": "design",
            "max_concurrent_tasks": self.settings.max_concurrent_tasks_per_agent,
            "capabilities": [
                "collage_generation",
                "image_processing",
                "layout_arrangement",
                "grid_layout",
                "stacked_layout",
                "circular_layout",
                "freeform_layout",
                "mosaic_layout"
            ],
            "processing_options": {
                "default_quality": self.settings.default_image_quality,
                "default_resize_mode": "fit",
                "optimize": True,
                "preserve_aspect_ratio": True
            }
        }
    
    def get_coordinator_config(self) -> Dict[str, Any]:
        """Get configuration for coordinator."""
        return {
            "coordinator_id": "coordinator_001",
            "enabled": self.settings.coordinator_enabled,
            "task_queue_size": self.settings.task_queue_size,
            "max_retry_attempts": self.settings.max_retry_attempts,
            "heartbeat_interval": self.settings.agent_heartbeat_interval,
            "task_timeout": self.settings.task_timeout_seconds
        }


class FileConfig:
    """
    Configuration for file management.
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
    
    def get_upload_config(self) -> Dict[str, Any]:
        """Get upload configuration."""
        return {
            "upload_directory": self.settings.upload_directory,
            "max_file_size_bytes": self.settings.max_file_size_mb * 1024 * 1024,
            "allowed_extensions": self.settings.allowed_extensions,
            "create_thumbnails": True,
            "thumbnail_size": (150, 150)
        }
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Get image processing configuration."""
        return {
            "processed_directory": self.settings.processed_directory,
            "collage_directory": self.settings.collage_directory,
            "default_quality": self.settings.default_image_quality,
            "default_output_size": (
                self.settings.default_output_width,
                self.settings.default_output_height
            ),
            "background_color": self.settings.default_background_color,
            "spacing": self.settings.default_spacing
        }


def setup_logging(settings: Settings) -> None:
    """
    Setup logging configuration.
    
    Args:
        settings: Application settings
    """
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('design_system.log')
        ]
    )
    
    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)


def create_directories(settings: Settings) -> None:
    """
    Create necessary directories.
    
    Args:
        settings: Application settings
    """
    directories = [
        settings.upload_directory,
        settings.processed_directory,
        settings.collage_directory,
        "logs",
        "temp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

# Configuration instances
agent_config = AgentConfig(settings)
file_config = FileConfig(settings)
