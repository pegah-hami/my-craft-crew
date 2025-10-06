"""
FastAPI routes for the multi-agent design system.

This module provides REST API endpoints for image upload,
design generation, and system management.
"""

import os
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer

from models.task_models import (
    Task, TaskStatus, AgentType, TaskPriority, 
    UploadResponse, TaskResponse, ImageInfo, DesignSpecification
)
from models.design_models import (
    DesignRequest, CollageLayout,
    ProcessingOptions, CollageGenerationResult
)
from services.file_manager import FileManager
from services.image_processor import ImageProcessor
from services.collage_generator import CollageGenerator
from agents.design_agent import DesignAgent
from config.settings import settings, file_config

# Initialize router
router = APIRouter(prefix="/api/v1", tags=["design-system"])

# Initialize services
file_manager = FileManager(
    upload_directory=settings.upload_directory,
    max_file_size_mb=settings.max_file_size_mb,
    allowed_extensions=settings.allowed_extensions
)

image_processor = ImageProcessor()
collage_generator = CollageGenerator()

# Initialize design agent
design_agent = DesignAgent()

# Security
security = HTTPBearer()

# In-memory task storage (replace with database in production)
task_storage: Dict[UUID, Task] = {}


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "service": "multi-agent-design-system"
    }


@router.post("/upload/images", response_model=UploadResponse)
async def upload_images(
    files: List[UploadFile] = File(...),
    user_id: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Upload multiple images for design generation.
    
    Args:
        files: List of image files to upload
        user_id: Optional user ID for organization
        background_tasks: Background task handler
        
    Returns:
        UploadResponse with uploaded image information
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        if len(files) > 20:
            raise HTTPException(status_code=400, detail="Too many files. Maximum 20 files allowed.")
        
        # Save uploaded files
        uploaded_images = await file_manager.save_multiple_files(files, user_id)
        
        if not uploaded_images:
            raise HTTPException(status_code=400, detail="No valid images were uploaded")
        
        # Create task for design generation
        task = Task(
            agent_type=AgentType.DESIGN,
            images=uploaded_images,
            design_spec=DesignSpecification(),
            user_id=user_id,
            description=f"Design generation for {len(uploaded_images)} images"
        )
        
        # Store task
        task_storage[task.id] = task
        
        # Schedule background processing
        background_tasks.add_task(process_design_task, task.id)
        
        return UploadResponse(
            success=True,
            message=f"Successfully uploaded {len(uploaded_images)} images",
            uploaded_images=uploaded_images,
            task_id=task.id
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/design/generate", response_model=TaskResponse)
async def generate_design(
    images: List[ImageInfo],
    layout: CollageLayout = CollageLayout.GRID,
    output_width: int = 1024,
    output_height: int = 1024,
    background_color: str = "#FFFFFF",
    spacing: int = 10,
    user_id: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Generate a design with specific parameters.
    
    Args:
        images: List of images to use
        layout: Collage layout type
        output_width: Output width in pixels
        output_height: Output height in pixels
        background_color: Background color (hex)
        spacing: Spacing between images
        user_id: Optional user ID
        background_tasks: Background task handler
        
    Returns:
        TaskResponse with task information
    """
    try:
        # Validate images exist
        for image_info in images:
            if not await file_manager.file_exists(image_info.file_path):
                raise HTTPException(
                    status_code=404, 
                    detail=f"Image not found: {image_info.filename}"
                )
        
        # Create design specification
        design_spec = DesignSpecification(
            layout=layout,
            output_width=output_width,
            output_height=output_height,
            background_color=background_color,
            spacing=spacing
        )
        
        # Create task
        task = Task(
            agent_type=AgentType.DESIGN,
            images=images,
            design_spec=design_spec,
            user_id=user_id,
            description=f"Design generation with {layout.value} layout"
        )
        
        # Store task
        task_storage[task.id] = task
        
        # Schedule background processing
        background_tasks.add_task(process_design_task, task.id)
        
        return TaskResponse(
            success=True,
            message="Design generation task created successfully",
            task=task
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Design generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/task/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: UUID):
    """
    Get the status of a task.
    
    Args:
        task_id: Task ID
        
    Returns:
        TaskResponse with task status
    """
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = task_storage[task_id]
    
    return TaskResponse(
        success=True,
        message="Task retrieved successfully",
        task=task
    )


@router.get("/task/{task_id}/result")
async def get_task_result(task_id: UUID):
    """
    Get the result of a completed task.
    
    Args:
        task_id: Task ID
        
    Returns:
        Task result or file download
    """
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = task_storage[task_id]
    
    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=400, 
            detail=f"Task not completed. Status: {task.status}"
        )
    
    if not task.result:
        raise HTTPException(status_code=404, detail="Task result not available")
    
    # Check if result contains file path
    if "output_file_path" in task.result:
        file_path = task.result["output_file_path"]
        if os.path.exists(file_path):
            return FileResponse(
                file_path,
                media_type="image/jpeg",
                filename=f"design_{task_id}.jpg"
            )
    
    return task.result


@router.delete("/task/{task_id}")
async def cancel_task(task_id: UUID):
    """
    Cancel a task.
    
    Args:
        task_id: Task ID
        
    Returns:
        Success message
    """
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = task_storage[task_id]
    
    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel task with status: {task.status}"
        )
    
    task.update_status(TaskStatus.CANCELLED)
    
    return {"message": "Task cancelled successfully"}


@router.get("/tasks")
async def list_tasks(
    user_id: Optional[str] = None,
    status: Optional[TaskStatus] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    List tasks with optional filtering.
    
    Args:
        user_id: Filter by user ID
        status: Filter by status
        limit: Maximum number of tasks to return
        offset: Number of tasks to skip
        
    Returns:
        List of tasks
    """
    tasks = list(task_storage.values())
    
    # Apply filters
    if user_id:
        tasks = [task for task in tasks if task.user_id == user_id]
    
    if status:
        tasks = [task for task in tasks if task.status == status]
    
    # Apply pagination
    tasks = tasks[offset:offset + limit]
    
    return {
        "tasks": tasks,
        "total": len(task_storage),
        "limit": limit,
        "offset": offset
    }


@router.get("/agents/status")
async def get_agents_status():
    """
    Get status of all agents.
    
    Returns:
        Agent status information
    """
    return {
        "agents": [
            {
                "agent_id": design_agent.agent_id,
                "agent_type": design_agent.agent_type.value,
                "status": design_agent.get_status().status,
                "capabilities": design_agent.capabilities,
                "current_tasks": design_agent.current_task_count,
                "max_concurrent_tasks": design_agent.max_concurrent_tasks,
                "is_available": design_agent.is_available
            }
        ]
    }


@router.get("/storage/stats")
async def get_storage_stats():
    """
    Get storage statistics.
    
    Returns:
        Storage statistics
    """
    stats = await file_manager.get_storage_stats()
    return stats


@router.post("/storage/cleanup")
async def cleanup_storage(days_old: int = 7):
    """
    Clean up old files.
    
    Args:
        days_old: Delete files older than this many days
        
    Returns:
        Cleanup results
    """
    deleted_count = await file_manager.cleanup_old_files(days_old)
    return {
        "message": f"Cleaned up {deleted_count} files older than {days_old} days",
        "deleted_count": deleted_count
    }


async def process_design_task(task_id: UUID):
    """
    Background task to process design generation.
    
    Args:
        task_id: Task ID to process
    """
    try:
        if task_id not in task_storage:
            logging.error(f"Task {task_id} not found in storage")
            return
        
        task = task_storage[task_id]
        
        # Validate task
        if not await design_agent.validate_task(task):
            task.update_status(TaskStatus.FAILED, "Task validation failed")
            return
        
        # Process task
        result = await design_agent.process_task(task)
        
        logging.info(f"Task {task_id} completed successfully")
        
    except Exception as e:
        logging.error(f"Task {task_id} failed: {str(e)}")
        if task_id in task_storage:
            task_storage[task_id].update_status(TaskStatus.FAILED, str(e))


# Error handlers removed - they should be handled at the app level
