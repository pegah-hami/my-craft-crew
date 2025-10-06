"""
Design-specific data models.

This module contains models specific to design generation,
image processing, and collage creation.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator

from .task_models import ImageInfo, CollageLayout


class ImagePosition(BaseModel):
    """Position and size of an image in a collage."""
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    rotation: float = Field(default=0.0, ge=-180.0, le=180.0)
    opacity: float = Field(default=1.0, ge=0.0, le=1.0)


class CollageElement(BaseModel):
    """An element in a collage (image with position)."""
    image_id: UUID
    position: ImagePosition
    layer: int = Field(default=0, ge=0)  # For layering/z-index


class CollageTemplate(BaseModel):
    """A predefined collage template."""
    name: str
    layout: CollageLayout
    description: str
    default_width: int = Field(default=1024, ge=100)
    default_height: int = Field(default=1024, ge=100)
    slots: List[ImagePosition] = Field(default_factory=list)
    background_color: str = Field(default="#FFFFFF")
    spacing: int = Field(default=10, ge=0)


class ProcessingOptions(BaseModel):
    """Options for image processing."""
    resize_mode: str = Field(default="fit", pattern=r"^(fit|fill|crop|stretch)$")
    quality: int = Field(default=95, ge=1, le=100)
    optimize: bool = Field(default=True)
    preserve_aspect_ratio: bool = Field(default=True)
    max_file_size_mb: int = Field(default=10, ge=1, le=100)


class DesignRequest(BaseModel):
    """Request for design generation."""
    images: List[ImageInfo]
    layout: CollageLayout = CollageLayout.GRID
    template: Optional[str] = None
    output_width: int = Field(default=1024, ge=100, le=4096)
    output_height: int = Field(default=1024, ge=100, le=4096)
    background_color: str = Field(default="#FFFFFF")
    spacing: int = Field(default=10, ge=0, le=100)
    processing_options: ProcessingOptions = Field(default_factory=ProcessingOptions)
    
    # Future: Add support for text overlays, effects, etc.
    text_overlays: List[Dict[str, Any]] = Field(default_factory=list)
    effects: List[str] = Field(default_factory=list)


class DesignProgress(BaseModel):
    """Progress information for design generation."""
    task_id: UUID
    stage: str  # "uploading", "processing", "generating", "finalizing"
    progress_percentage: float = Field(ge=0.0, le=100.0)
    current_operation: str
    estimated_completion: Optional[datetime] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class ImageProcessingResult(BaseModel):
    """Result of image processing operations."""
    original_image: ImageInfo
    processed_image: ImageInfo
    processing_time_seconds: float
    operations_applied: List[str]
    quality_score: Optional[float] = None


class CollageGenerationResult(BaseModel):
    """Result of collage generation."""
    task_id: UUID
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    output_file_path: str
    output_format: str
    output_width: int
    output_height: int
    processing_time_seconds: float
    images_used: List[UUID]
    layout_used: CollageLayout
    elements: List[CollageElement]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BatchProcessingRequest(BaseModel):
    """Request for batch processing multiple designs."""
    requests: List[DesignRequest]
    batch_id: UUID
    priority: str = Field(default="normal", pattern=r"^(low|normal|high|urgent)$")
    notify_on_completion: bool = Field(default=True)


class BatchProcessingResult(BaseModel):
    """Result of batch processing."""
    batch_id: UUID
    total_requests: int
    completed_requests: int
    failed_requests: int
    results: List[CollageGenerationResult]
    total_processing_time_seconds: float
    completed_at: datetime = Field(default_factory=datetime.utcnow)
