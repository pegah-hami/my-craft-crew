"""
Design generation agent for creating collages and product designs.

This agent specializes in processing images and generating collages
using various layout algorithms and customization options.
"""

import logging
from typing import Dict, List, Any
from uuid import UUID

from agents.base_agent import BaseAgent
from models.task_models import Task, TaskStatus, AgentType
from models.design_models import DesignRequest, CollageGenerationResult
from services.collage_generator import CollageGenerator
from services.image_processor import ImageProcessor


class DesignAgent(BaseAgent):
    """
    Agent specialized in design generation and collage creation.
    
    This agent handles tasks related to:
    - Image collage generation
    - Product design creation
    - Image processing and optimization
    - Layout arrangement
    """
    
    def __init__(self, agent_id: str = "design_agent_001"):
        """
        Initialize the design agent.
        
        Args:
            agent_id: Unique identifier for this agent
        """
        capabilities = [
            "collage_generation",
            "image_processing",
            "layout_arrangement",
            "grid_layout",
            "stacked_layout",
            "circular_layout",
            "freeform_layout",
            "mosaic_layout",
            "image_optimization",
            "format_conversion"
        ]
        
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.DESIGN,
            capabilities=capabilities,
            max_concurrent_tasks=3
        )
        
        # Initialize services
        self.collage_generator = CollageGenerator()
        self.image_processor = ImageProcessor()
        
        self.logger = logging.getLogger(f"design_agent.{agent_id}")
    
    async def validate_task(self, task: Task) -> bool:
        """
        Validate if this agent can handle the given task.
        
        Args:
            task: The task to validate
            
        Returns:
            True if the agent can handle the task, False otherwise
        """
        # Check if task is for design agent
        if task.agent_type != AgentType.DESIGN:
            return False
        
        # Check if task has images
        if not task.images or len(task.images) == 0:
            self.logger.warning(f"Task {task.id} has no images")
            return False
        
        # Check if task has design specification
        if not task.design_spec:
            self.logger.warning(f"Task {task.id} has no design specification")
            return False
        
        # Validate image count (reasonable limits)
        if len(task.images) > 20:
            self.logger.warning(f"Task {task.id} has too many images: {len(task.images)}")
            return False
        
        # Check if images are valid
        for image_info in task.images:
            if not await self.image_processor.validate_image(image_info.file_path):
                self.logger.warning(f"Task {task.id} has invalid image: {image_info.filename}")
                return False
        
        return True
    
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """
        Process a design generation task.
        
        Args:
            task: The task to process
            
        Returns:
            Dictionary containing the result of task processing
            
        Raises:
            Exception: If task processing fails
        """
        self.logger.info(f"Processing design task {task.id}")
        
        try:
            # Create design request from task
            design_request = await self._create_design_request(task)
            
            # Generate collage
            result = await self.collage_generator.generate_collage(design_request, task.id)
            
            # Update task with result
            task.result = {
                "collage_result": result.dict(),
                "output_file_path": result.output_file_path,
                "processing_time": result.processing_time_seconds,
                "images_used": result.images_used,
                "layout_used": result.layout_used.value
            }
            
            self.logger.info(f"Successfully processed design task {task.id}")
            
            return task.result
            
        except Exception as e:
            self.logger.error(f"Failed to process design task {task.id}: {str(e)}")
            raise
    
    async def _create_design_request(self, task: Task) -> DesignRequest:
        """
        Create a design request from a task.
        
        Args:
            task: The task to convert
            
        Returns:
            DesignRequest object
        """
        from ..models.design_models import ProcessingOptions
        
        # Create processing options
        processing_options = ProcessingOptions(
            resize_mode="fit",
            quality=95,
            optimize=True,
            preserve_aspect_ratio=True,
            max_file_size_mb=10
        )
        
        # Create design request
        design_request = DesignRequest(
            images=task.images,
            layout=task.design_spec.layout,
            output_width=task.design_spec.output_width,
            output_height=task.design_spec.output_height,
            background_color=task.design_spec.background_color,
            spacing=task.design_spec.spacing,
            processing_options=processing_options
        )
        
        return design_request
    
    async def get_capabilities(self) -> List[str]:
        """
        Get list of capabilities this agent provides.
        
        Returns:
            List of capability strings
        """
        return self.capabilities.copy()
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics for this agent.
        
        Returns:
            Dictionary with performance metrics
        """
        status = self.get_status()
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "status": status.status,
            "current_tasks": len(self._current_tasks),
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "capabilities": self.capabilities,
            "performance_metrics": status.performance_metrics,
            "last_heartbeat": status.last_heartbeat.isoformat()
        }
    
    async def process_batch_tasks(self, tasks: List[Task]) -> List[Dict[str, Any]]:
        """
        Process multiple tasks in batch.
        
        Args:
            tasks: List of tasks to process
            
        Returns:
            List of results for each task
        """
        results = []
        
        for task in tasks:
            try:
                if await self.validate_task(task):
                    result = await self.process_task(task)
                    results.append({
                        "task_id": task.id,
                        "success": True,
                        "result": result
                    })
                else:
                    results.append({
                        "task_id": task.id,
                        "success": False,
                        "error": "Task validation failed"
                    })
            except Exception as e:
                results.append({
                    "task_id": task.id,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    async def optimize_images_for_collage(
        self,
        images: List[Any],
        target_size: tuple,
        layout_type: str
    ) -> List[Any]:
        """
        Optimize images specifically for collage generation.
        
        Args:
            images: List of images to optimize
            target_size: Target size for optimization
            layout_type: Type of layout being used
            
        Returns:
            List of optimized images
        """
        optimized_images = []
        
        for image_info in images:
            try:
                # Determine optimal size based on layout
                if layout_type == "grid":
                    optimal_size = self._calculate_grid_image_size(target_size, len(images))
                elif layout_type == "stacked":
                    optimal_size = self._calculate_stacked_image_size(target_size, len(images))
                else:
                    optimal_size = target_size
                
                # Process image
                result = await self.image_processor.process_image(
                    image_info,
                    ProcessingOptions(),
                    optimal_size
                )
                
                optimized_images.append(result.processed_image)
                
            except Exception as e:
                self.logger.warning(f"Failed to optimize image {image_info.id}: {str(e)}")
                # Use original image if optimization fails
                optimized_images.append(image_info)
        
        return optimized_images
    
    def _calculate_grid_image_size(self, canvas_size: tuple, num_images: int) -> tuple:
        """
        Calculate optimal image size for grid layout.
        
        Args:
            canvas_size: Canvas size (width, height)
            num_images: Number of images
            
        Returns:
            Optimal image size (width, height)
        """
        import math
        
        canvas_width, canvas_height = canvas_size
        
        # Calculate grid dimensions
        cols = int(math.ceil(math.sqrt(num_images)))
        rows = int(math.ceil(num_images / cols))
        
        # Calculate cell size
        cell_width = canvas_width // cols
        cell_height = canvas_height // rows
        
        return (cell_width, cell_height)
    
    def _calculate_stacked_image_size(self, canvas_size: tuple, num_images: int) -> tuple:
        """
        Calculate optimal image size for stacked layout.
        
        Args:
            canvas_size: Canvas size (width, height)
            num_images: Number of images
            
        Returns:
            Optimal image size (width, height)
        """
        canvas_width, canvas_height = canvas_size
        
        # For stacked layout, images should fill the width
        image_height = canvas_height // num_images
        
        return (canvas_width, image_height)
    
    async def preview_collage_layout(
        self,
        images: List[Any],
        layout_type: str,
        canvas_size: tuple
    ) -> Dict[str, Any]:
        """
        Generate a preview of how images would be arranged.
        
        Args:
            images: List of images
            layout_type: Type of layout
            canvas_size: Canvas size
            
        Returns:
            Preview information
        """
        preview_info = {
            "layout_type": layout_type,
            "canvas_size": canvas_size,
            "num_images": len(images),
            "image_positions": [],
            "estimated_processing_time": 0
        }
        
        if layout_type == "grid":
            preview_info["image_positions"] = self._calculate_grid_positions(
                images, canvas_size
            )
        elif layout_type == "stacked":
            preview_info["image_positions"] = self._calculate_stacked_positions(
                images, canvas_size
            )
        
        # Estimate processing time
        preview_info["estimated_processing_time"] = len(images) * 0.5  # 0.5 seconds per image
        
        return preview_info
    
    def _calculate_grid_positions(self, images: List[Any], canvas_size: tuple) -> List[Dict[str, Any]]:
        """Calculate positions for grid layout."""
        import math
        
        positions = []
        canvas_width, canvas_height = canvas_size
        num_images = len(images)
        
        cols = int(math.ceil(math.sqrt(num_images)))
        rows = int(math.ceil(num_images / cols))
        
        cell_width = canvas_width // cols
        cell_height = canvas_height // rows
        
        for i in range(num_images):
            row = i // cols
            col = i % cols
            
            x = col * cell_width
            y = row * cell_height
            
            positions.append({
                "image_index": i,
                "x": x,
                "y": y,
                "width": cell_width,
                "height": cell_height
            })
        
        return positions
    
    def _calculate_stacked_positions(self, images: List[Any], canvas_size: tuple) -> List[Dict[str, Any]]:
        """Calculate positions for stacked layout."""
        positions = []
        canvas_width, canvas_height = canvas_size
        num_images = len(images)
        
        image_height = canvas_height // num_images
        
        for i in range(num_images):
            y = i * image_height
            
            positions.append({
                "image_index": i,
                "x": 0,
                "y": y,
                "width": canvas_width,
                "height": image_height
            })
        
        return positions
