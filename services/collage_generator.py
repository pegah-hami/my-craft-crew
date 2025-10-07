"""
Collage generation service using Pillow.

This module provides collage creation capabilities including
different layout algorithms and image arrangement strategies.
"""

import os
import math
import logging
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
from uuid import UUID

from PIL import Image, ImageDraw, ImageFont

from models.task_models import ImageInfo, ImageFormat
from models.design_models import (
    CollageLayout, CollageElement, ImagePosition, 
    DesignRequest, CollageGenerationResult, ProcessingOptions
)


class CollageGenerator:
    """
    Service for generating collages from multiple images.
    
    Supports various layout algorithms and customization options.
    """
    
    def __init__(self, output_directory: str = "collages"):
        """
        Initialize the collage generator.
        
        Args:
            output_directory: Directory to save generated collages
        """
        self.output_directory = output_directory
        self.logger = logging.getLogger("collage_generator")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_directory, exist_ok=True)
    
    async def generate_collage(
        self,
        request: DesignRequest,
        task_id: UUID
    ) -> CollageGenerationResult:
        """
        Generate a collage from the given design request.
        
        Args:
            request: Design request containing images and specifications
            task_id: ID of the task this collage belongs to
            
        Returns:
            CollageGenerationResult containing the generated collage
            
        Raises:
            Exception: If collage generation fails
        """
        start_time = datetime.utcnow()
        
        try:
            # Process images first
            processed_images = await self._process_images_for_collage(
                request.images, 
                request.processing_options,
                (request.output_width, request.output_height)
            )
            
            # Generate collage based on layout
            if request.layout == CollageLayout.GRID:
                collage_image, elements = await self._create_grid_collage(
                    processed_images, request
                )
            elif request.layout == CollageLayout.STACKED:
                collage_image, elements = await self._create_stacked_collage(
                    processed_images, request
                )
            elif request.layout == CollageLayout.CIRCULAR:
                collage_image, elements = await self._create_circular_collage(
                    processed_images, request
                )
            elif request.layout == CollageLayout.FREEFORM:
                collage_image, elements = await self._create_freeform_collage(
                    processed_images, request
                )
            elif request.layout == CollageLayout.MOSAIC:
                collage_image, elements = await self._create_mosaic_collage(
                    processed_images, request
                )
            else:
                raise ValueError(f"Unsupported layout: {request.layout}")
            
            # Save collage
            output_path = await self._save_collage(
                collage_image, task_id, request.output_width, request.output_height
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return CollageGenerationResult(
                task_id=task_id,
                output_file_path=output_path,
                output_format="jpeg",
                output_width=request.output_width,
                output_height=request.output_height,
                processing_time_seconds=processing_time,
                images_used=[img.id for img in processed_images],
                layout_used=request.layout,
                elements=elements,
                metadata={
                    "background_color": request.background_color,
                    "spacing": request.spacing,
                    "images_count": len(processed_images)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to generate collage for task {task_id}: {str(e)}")
            raise
    
    async def _process_images_for_collage(
        self,
        images: List[ImageInfo],
        options: ProcessingOptions,
        target_size: Tuple[int, int]
    ) -> List[ImageInfo]:
        """
        Process images for collage generation.
        
        Args:
            images: List of images to process
            options: Processing options
            target_size: Target collage size
            
        Returns:
            List of processed ImageInfo objects
        """
        from .image_processor import ImageProcessor
        
        processor = ImageProcessor()
        processed_images = []
        
        # Calculate individual image size based on layout
        num_images = len(images)
        if num_images == 0:
            return processed_images
        
        # Simple sizing strategy - divide canvas by number of images
        canvas_width, canvas_height = target_size
        spacing = 10  # Default spacing
        
        # Calculate approximate size per image
        if num_images <= 4:
            cols = 2
            rows = 2
        elif num_images <= 9:
            cols = 3
            rows = 3
        else:
            cols = int(math.ceil(math.sqrt(num_images)))
            rows = int(math.ceil(num_images / cols))
        
        available_width = canvas_width - (spacing * (cols - 1))
        available_height = canvas_height - (spacing * (rows - 1))
        
        image_width = available_width // cols
        image_height = available_height // rows
        
        # Process each image
        for image_info in images:
            try:
                result = await processor.process_image(
                    image_info,
                    options,
                    (image_width, image_height)
                )
                processed_images.append(result.processed_image)
            except Exception as e:
                self.logger.warning(f"Failed to process image {image_info.id}: {str(e)}")
                continue
        
        return processed_images
    
    async def _create_grid_collage(
        self,
        images: List[ImageInfo],
        request: DesignRequest
    ) -> Tuple[Image.Image, List[CollageElement]]:
        """
        Create a grid-based collage.
        
        Args:
            images: List of processed images
            request: Design request
            
        Returns:
            Tuple of (collage_image, collage_elements)
        """
        width, height = request.output_width, request.output_height
        spacing = request.spacing
        
        # Create canvas
        canvas = Image.new("RGB", (width, height), request.background_color)
        
        if not images:
            return canvas, []
        
        # Calculate grid dimensions
        num_images = len(images)
        cols = int(math.ceil(math.sqrt(num_images)))
        rows = int(math.ceil(num_images / cols))
        
        # Calculate cell size
        available_width = width - (spacing * (cols - 1))
        available_height = height - (spacing * (rows - 1))
        
        cell_width = available_width // cols
        cell_height = available_height // rows
        
        elements = []
        
        # Place images in grid
        for i, image_info in enumerate(images):
            row = i // cols
            col = i % cols
            
            x = col * (cell_width + spacing)
            y = row * (cell_height + spacing)
            
            # Load and resize image - use the processed image path
            try:
                with Image.open(image_info.file_path) as img:
                    # Resize to fit cell
                    img.thumbnail((cell_width, cell_height), Image.Resampling.LANCZOS)
                    
                    # Center image in cell
                    paste_x = x + (cell_width - img.width) // 2
                    paste_y = y + (cell_height - img.height) // 2
                    
                    canvas.paste(img, (paste_x, paste_y))
                    
                    # Create element record
                    element = CollageElement(
                        image_id=image_info.id,
                        position=ImagePosition(
                            x=paste_x,
                            y=paste_y,
                            width=img.width,
                            height=img.height
                        )
                    )
                    elements.append(element)
            except Exception as e:
                self.logger.error(f"Failed to load image {image_info.file_path}: {str(e)}")
                continue
        
        return canvas, elements
    
    async def _create_stacked_collage(
        self,
        images: List[ImageInfo],
        request: DesignRequest
    ) -> Tuple[Image.Image, List[CollageElement]]:
        """
        Create a stacked collage (images arranged vertically).
        
        Args:
            images: List of processed images
            request: Design request
            
        Returns:
            Tuple of (collage_image, collage_elements)
        """
        width, height = request.output_width, request.output_height
        spacing = request.spacing
        
        # Create canvas
        canvas = Image.new("RGB", (width, height), request.background_color)
        
        if not images:
            return canvas, []
        
        # Calculate image height
        available_height = height - (spacing * (len(images) - 1))
        image_height = available_height // len(images)
        
        elements = []
        current_y = 0
        
        # Stack images vertically
        for image_info in images:
            # Load and resize image - use the processed image path
            try:
                with Image.open(image_info.file_path) as img:
                    # Resize to fit width and calculated height
                    img.thumbnail((width, image_height), Image.Resampling.LANCZOS)
                    
                    # Center horizontally
                    paste_x = (width - img.width) // 2
                    
                    canvas.paste(img, (paste_x, current_y))
                    
                    # Create element record
                    element = CollageElement(
                        image_id=image_info.id,
                        position=ImagePosition(
                            x=paste_x,
                            y=current_y,
                            width=img.width,
                            height=img.height
                        )
                    )
                    elements.append(element)
                    
                    current_y += img.height + spacing
            except Exception as e:
                self.logger.error(f"Failed to load image {image_info.file_path}: {str(e)}")
                continue
        
        return canvas, elements
    
    async def _create_circular_collage(
        self,
        images: List[ImageInfo],
        request: DesignRequest
    ) -> Tuple[Image.Image, List[CollageElement]]:
        """
        Create a circular collage (images arranged in a circle).
        
        Args:
            images: List of processed images
            request: Design request
            
        Returns:
            Tuple of (collage_image, collage_elements)
        """
        width, height = request.output_width, request.output_height
        
        # Create canvas
        canvas = Image.new("RGB", (width, height), request.background_color)
        
        if not images:
            return canvas, []
        
        # Calculate circle parameters
        center_x, center_y = width // 2, height // 2
        radius = min(width, height) // 3
        
        # Calculate image size
        image_size = min(radius // 2, 200)  # Max 200px per image
        
        elements = []
        
        # Place images in circle
        for i, image_info in enumerate(images):
            angle = (2 * math.pi * i) / len(images)
            
            # Calculate position
            x = center_x + radius * math.cos(angle) - image_size // 2
            y = center_y + radius * math.sin(angle) - image_size // 2
            
            # Load and resize image - use the processed image path
            try:
                with Image.open(image_info.file_path) as img:
                    img.thumbnail((image_size, image_size), Image.Resampling.LANCZOS)
                    
                    canvas.paste(img, (int(x), int(y)))
                    
                    # Create element record
                    element = CollageElement(
                        image_id=image_info.id,
                        position=ImagePosition(
                            x=int(x),
                            y=int(y),
                            width=img.width,
                            height=img.height
                        )
                    )
                    elements.append(element)
            except Exception as e:
                self.logger.error(f"Failed to load image {image_info.file_path}: {str(e)}")
                continue
        
        return canvas, elements
    
    async def _create_freeform_collage(
        self,
        images: List[ImageInfo],
        request: DesignRequest
    ) -> Tuple[Image.Image, List[CollageElement]]:
        """
        Create a freeform collage (random placement).
        
        Args:
            images: List of processed images
            request: Design request
            
        Returns:
            Tuple of (collage_image, collage_elements)
        """
        import random
        
        width, height = request.output_width, request.output_height
        
        # Create canvas
        canvas = Image.new("RGB", (width, height), request.background_color)
        
        if not images:
            return canvas, []
        
        elements = []
        used_positions = []
        
        # Place images randomly
        for image_info in images:
            # Load image - use the processed image path
            try:
                with Image.open(image_info.file_path) as img:
                    # Random size between 100-300px
                    max_size = random.randint(100, 300)
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                    
                    # Find random position that doesn't overlap too much
                    attempts = 0
                    while attempts < 50:  # Prevent infinite loop
                        x = random.randint(0, width - img.width)
                        y = random.randint(0, height - img.height)
                        
                        # Check for overlap
                        overlaps = False
                        for pos in used_positions:
                            if (abs(x - pos[0]) < img.width and 
                                abs(y - pos[1]) < img.height):
                                overlaps = True
                                break
                        
                        if not overlaps:
                            break
                        attempts += 1
                    
                    canvas.paste(img, (x, y))
                    used_positions.append((x, y))
                    
                    # Create element record
                    element = CollageElement(
                        image_id=image_info.id,
                        position=ImagePosition(
                            x=x,
                            y=y,
                            width=img.width,
                            height=img.height
                        )
                    )
                    elements.append(element)
            except Exception as e:
                self.logger.error(f"Failed to load image {image_info.file_path}: {str(e)}")
                continue
        
        return canvas, elements
    
    async def _create_mosaic_collage(
        self,
        images: List[ImageInfo],
        request: DesignRequest
    ) -> Tuple[Image.Image, List[CollageElement]]:
        """
        Create a mosaic collage (small tiles).
        
        Args:
            images: List of processed images
            request: Design request
            
        Returns:
            Tuple of (collage_image, collage_elements)
        """
        width, height = request.output_width, request.output_height
        
        # Create canvas
        canvas = Image.new("RGB", (width, height), request.background_color)
        
        if not images:
            return canvas, []
        
        # Calculate tile size
        tile_size = min(width, height) // 10  # 10x10 grid
        
        elements = []
        image_index = 0
        
        # Create mosaic pattern
        for y in range(0, height, tile_size):
            for x in range(0, width, tile_size):
                if image_index < len(images):
                    image_info = images[image_index]
                    
                    # Load and resize image - use the processed image path
                    try:
                        with Image.open(image_info.file_path) as img:
                            img.thumbnail((tile_size, tile_size), Image.Resampling.LANCZOS)
                            
                            canvas.paste(img, (x, y))
                            
                            # Create element record
                            element = CollageElement(
                                image_id=image_info.id,
                                position=ImagePosition(
                                    x=x,
                                    y=y,
                                    width=img.width,
                                    height=img.height
                                )
                            )
                            elements.append(element)
                            
                            image_index += 1
                    except Exception as e:
                        self.logger.error(f"Failed to load image {image_info.file_path}: {str(e)}")
                        image_index += 1
                        continue
        
        return canvas, elements
    
    async def _save_collage(
        self,
        collage_image: Image.Image,
        task_id: UUID,
        width: int,
        height: int
    ) -> str:
        """
        Save collage to disk.
        
        Args:
            collage_image: PIL Image object
            task_id: Task ID
            width: Collage width
            height: Collage height
            
        Returns:
            Path to saved collage
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"collage_{task_id}_{timestamp}.jpg"
        file_path = os.path.join(self.output_directory, filename)
        
        # Save with high quality
        collage_image.save(file_path, "JPEG", quality=95, optimize=True)
        
        return file_path
