"""
Image processing service using Pillow.

This module provides image processing capabilities including
resizing, cropping, format conversion, and quality optimization.
"""

import os
import logging
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
from uuid import UUID

from PIL import Image, ImageOps, ImageEnhance
from PIL.Image import Resampling

from models.task_models import ImageInfo, ImageFormat
from models.design_models import ProcessingOptions, ImageProcessingResult


class ImageProcessor:
    """
    Service for processing images using Pillow.
    
    Provides functionality for resizing, cropping, format conversion,
    and quality optimization of images.
    """
    
    def __init__(self, output_directory: str = "processed_images"):
        """
        Initialize the image processor.
        
        Args:
            output_directory: Directory to save processed images
        """
        self.output_directory = output_directory
        self.logger = logging.getLogger("image_processor")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_directory, exist_ok=True)
        
        # Supported formats mapping
        self.format_mapping = {
            ImageFormat.JPEG: "JPEG",
            ImageFormat.PNG: "PNG",
            ImageFormat.WEBP: "WEBP",
            ImageFormat.GIF: "GIF"
        }
    
    async def process_image(
        self,
        image_info: ImageInfo,
        options: ProcessingOptions,
        target_size: Optional[Tuple[int, int]] = None
    ) -> ImageProcessingResult:
        """
        Process a single image according to the given options.
        
        Args:
            image_info: Information about the image to process
            options: Processing options
            target_size: Optional target size (width, height)
            
        Returns:
            ImageProcessingResult containing processed image info
            
        Raises:
            Exception: If image processing fails
        """
        start_time = datetime.utcnow()
        operations_applied = []
        
        try:
            # Open the image
            with Image.open(image_info.file_path) as img:
                original_size = img.size
                
                # Convert to RGB if necessary (for JPEG output)
                if options.resize_mode in ["fit", "fill", "crop"] and img.mode in ["RGBA", "LA"]:
                    # Create white background for transparent images
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "RGBA":
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background
                    operations_applied.append("convert_to_rgb")
                
                # Resize image if target size is specified
                if target_size:
                    img = await self._resize_image(img, target_size, options)
                    operations_applied.append(f"resize_to_{target_size[0]}x{target_size[1]}")
                
                # Apply quality optimization
                if options.optimize:
                    img = await self._optimize_image(img, options)
                    operations_applied.append("optimize")
                
                # Save processed image
                processed_path = await self._save_processed_image(img, image_info, options)
                
                # Get processed image info
                processed_info = await self._get_image_info(processed_path)
                
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                
                return ImageProcessingResult(
                    original_image=image_info,
                    processed_image=processed_info,
                    processing_time_seconds=processing_time,
                    operations_applied=operations_applied,
                    quality_score=await self._calculate_quality_score(img)
                )
                
        except Exception as e:
            self.logger.error(f"Failed to process image {image_info.id}: {str(e)}")
            raise
    
    async def process_multiple_images(
        self,
        images: List[ImageInfo],
        options: ProcessingOptions,
        target_size: Optional[Tuple[int, int]] = None
    ) -> List[ImageProcessingResult]:
        """
        Process multiple images with the same options.
        
        Args:
            images: List of images to process
            options: Processing options
            target_size: Optional target size (width, height)
            
        Returns:
            List of ImageProcessingResult objects
        """
        results = []
        
        for image_info in images:
            try:
                result = await self.process_image(image_info, options, target_size)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to process image {image_info.id}: {str(e)}")
                # Continue with other images
                continue
        
        return results
    
    async def _resize_image(
        self,
        img: Image.Image,
        target_size: Tuple[int, int],
        options: ProcessingOptions
    ) -> Image.Image:
        """
        Resize image according to the resize mode.
        
        Args:
            img: PIL Image object
            target_size: Target size (width, height)
            options: Processing options
            
        Returns:
            Resized PIL Image object
        """
        width, height = target_size
        
        if options.resize_mode == "fit":
            # Fit image within target size while preserving aspect ratio
            img.thumbnail((width, height), Resampling.LANCZOS)
            
        elif options.resize_mode == "fill":
            # Fill target size, cropping if necessary
            img = ImageOps.fit(img, (width, height), Resampling.LANCZOS)
            
        elif options.resize_mode == "crop":
            # Crop to target size from center
            img = ImageOps.fit(img, (width, height), Resampling.LANCZOS)
            
        elif options.resize_mode == "stretch":
            # Stretch to exact target size
            img = img.resize((width, height), Resampling.LANCZOS)
        
        return img
    
    async def _optimize_image(
        self,
        img: Image.Image,
        options: ProcessingOptions
    ) -> Image.Image:
        """
        Optimize image quality and file size.
        
        Args:
            img: PIL Image object
            options: Processing options
            
        Returns:
            Optimized PIL Image object
        """
        # Enhance sharpness slightly
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.1)
        
        # Enhance contrast slightly
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.05)
        
        return img
    
    async def _save_processed_image(
        self,
        img: Image.Image,
        original_info: ImageInfo,
        options: ProcessingOptions
    ) -> str:
        """
        Save processed image to disk.
        
        Args:
            img: PIL Image object
            original_info: Original image information
            options: Processing options
            
        Returns:
            Path to saved image
        """
        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"processed_{original_info.id}_{timestamp}.jpg"
        file_path = os.path.join(self.output_directory, filename)
        
        # Save with quality settings
        save_kwargs = {
            "format": "JPEG",
            "quality": options.quality,
            "optimize": options.optimize
        }
        
        img.save(file_path, **save_kwargs)
        
        return file_path
    
    async def _get_image_info(self, file_path: str) -> ImageInfo:
        """
        Get image information from file.
        
        Args:
            file_path: Path to image file
            
        Returns:
            ImageInfo object
        """
        with Image.open(file_path) as img:
            # Determine format
            format_name = img.format.lower() if img.format else "jpeg"
            image_format = ImageFormat(format_name)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            return ImageInfo(
                filename=os.path.basename(file_path),
                format=image_format,
                width=img.width,
                height=img.height,
                size_bytes=file_size,
                file_path=file_path
            )
    
    async def _calculate_quality_score(self, img: Image.Image) -> float:
        """
        Calculate a quality score for the image.
        
        Args:
            img: PIL Image object
            
        Returns:
            Quality score between 0 and 1
        """
        # Simple quality metrics
        width, height = img.size
        
        # Aspect ratio score (closer to 1:1 is better for collages)
        aspect_ratio = min(width, height) / max(width, height)
        
        # Resolution score (higher resolution is better)
        resolution_score = min(1.0, (width * height) / (1024 * 1024))
        
        # Combined score
        quality_score = (aspect_ratio * 0.3 + resolution_score * 0.7)
        
        return round(quality_score, 3)
    
    async def validate_image(self, file_path: str) -> bool:
        """
        Validate if file is a valid image.
        
        Args:
            file_path: Path to image file
            
        Returns:
            True if valid image, False otherwise
        """
        try:
            with Image.open(file_path) as img:
                img.verify()
            return True
        except Exception:
            return False
    
    async def get_image_dimensions(self, file_path: str) -> Tuple[int, int]:
        """
        Get image dimensions without loading full image.
        
        Args:
            file_path: Path to image file
            
        Returns:
            Tuple of (width, height)
        """
        with Image.open(file_path) as img:
            return img.size
    
    async def convert_format(
        self,
        image_info: ImageInfo,
        target_format: ImageFormat,
        options: ProcessingOptions
    ) -> ImageProcessingResult:
        """
        Convert image to different format.
        
        Args:
            image_info: Original image information
            target_format: Target format
            options: Processing options
            
        Returns:
            ImageProcessingResult
        """
        start_time = datetime.utcnow()
        
        with Image.open(image_info.file_path) as img:
            # Convert format
            pil_format = self.format_mapping[target_format]
            
            # Generate output filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"converted_{image_info.id}_{timestamp}.{target_format.value}"
            file_path = os.path.join(self.output_directory, filename)
            
            # Save in new format
            save_kwargs = {"format": pil_format}
            if target_format == ImageFormat.JPEG:
                save_kwargs.update({
                    "quality": options.quality,
                    "optimize": options.optimize
                })
            
            img.save(file_path, **save_kwargs)
            
            # Get new image info
            processed_info = await self._get_image_info(file_path)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return ImageProcessingResult(
                original_image=image_info,
                processed_image=processed_info,
                processing_time_seconds=processing_time,
                operations_applied=[f"convert_to_{target_format.value}"],
                quality_score=await self._calculate_quality_score(img)
            )
