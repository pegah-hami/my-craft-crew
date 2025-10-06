"""
Data models for the multi-agent design system.

This module contains Pydantic models for task management,
design specifications, and agent communication.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class TaskStatus(str, Enum):
    """Status of a task in the system."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentType(str, Enum):
    """Types of agents in the system."""
    DESIGN = "design"
    EFFECTS = "effects"
    OPTIMIZATION = "optimization"
    # Future agent types can be added here


class TaskPriority(str, Enum):
    """Priority levels for tasks."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ImageFormat(str, Enum):
    """Supported image formats."""
    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"
    GIF = "gif"


class CollageLayout(str, Enum):
    """Available collage layouts."""
    GRID = "grid"
    STACKED = "stacked"
    CIRCULAR = "circular"
    FREEFORM = "freeform"
    MOSAIC = "mosaic"


class ImageInfo(BaseModel):
    """Information about an uploaded image."""
    id: UUID = Field(default_factory=uuid4)
    filename: str
    format: ImageFormat
    width: int
    height: int
    size_bytes: int
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)
    file_path: str
    
    @validator('width', 'height')
    def validate_dimensions(cls, v):
        if v <= 0:
            raise ValueError('Dimensions must be positive')
        return v
    
    @validator('size_bytes')
    def validate_size(cls, v):
        if v <= 0:
            raise ValueError('File size must be positive')
        return v


class DesignSpecification(BaseModel):
    """Specification for design generation."""
    layout: CollageLayout = CollageLayout.GRID
    output_width: int = Field(default=1024, ge=100, le=4096)
    output_height: int = Field(default=1024, ge=100, le=4096)
    background_color: str = Field(default="#FFFFFF", pattern=r"^#[0-9A-Fa-f]{6}$")
    spacing: int = Field(default=10, ge=0, le=100)
    border_radius: int = Field(default=0, ge=0, le=50)
    
    # Future: Add support for effects, filters, etc.
    effects: Optional[Dict[str, Any]] = None


class Task(BaseModel):
    """A task to be processed by agents."""
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    
    # Task content
    agent_type: AgentType
    images: List[ImageInfo] = Field(default_factory=list)
    design_spec: Optional[DesignSpecification] = None
    
    # Task metadata
    user_id: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Results
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    def update_status(self, status: TaskStatus, error_message: Optional[str] = None):
        """Update task status and timestamp."""
        self.status = status
        self.updated_at = datetime.utcnow()
        if error_message:
            self.error_message = error_message


class AgentMessage(BaseModel):
    """Message for inter-agent communication."""
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sender: str
    recipient: str
    message_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    task_id: Optional[UUID] = None


class AgentStatus(BaseModel):
    """Status information about an agent."""
    agent_id: str
    agent_type: AgentType
    status: str  # "online", "offline", "busy", "error"
    last_heartbeat: datetime
    current_tasks: List[UUID] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)


class DesignResult(BaseModel):
    """Result of a design generation task."""
    task_id: UUID
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    output_file_path: str
    output_format: ImageFormat
    output_width: int
    output_height: int
    processing_time_seconds: float
    images_used: List[UUID]
    design_spec_used: DesignSpecification
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UploadResponse(BaseModel):
    """Response for image upload."""
    success: bool
    message: str
    uploaded_images: List[ImageInfo]
    task_id: Optional[UUID] = None


class TaskResponse(BaseModel):
    """Response for task operations."""
    success: bool
    message: str
    task: Optional[Task] = None
    result: Optional[DesignResult] = None


class AgentRegistration(BaseModel):
    """Registration information for new agents."""
    agent_id: str
    agent_type: AgentType
    capabilities: List[str]
    max_concurrent_tasks: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)
