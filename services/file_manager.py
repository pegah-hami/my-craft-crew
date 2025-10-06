"""
File management service for handling uploads and downloads.

This module provides functionality for managing file uploads,
downloads, and storage operations.
"""

import os
import shutil
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pathlib import Path

from fastapi import UploadFile
from PIL import Image

from models.task_models import ImageInfo, ImageFormat


class FileManager:
    """
    Service for managing file operations including uploads and downloads.
    """
    
    def __init__(
        self,
        upload_directory: str = "uploads",
        max_file_size_mb: int = 10,
        allowed_extensions: List[str] = None
    ):
        """
        Initialize the file manager.
        
        Args:
            upload_directory: Directory for uploaded files
            max_file_size_mb: Maximum file size in MB
            allowed_extensions: List of allowed file extensions
        """
        self.upload_directory = upload_directory
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.allowed_extensions = allowed_extensions or [".jpg", ".jpeg", ".png", ".gif", ".webp"]
        
        self.logger = logging.getLogger("file_manager")
        
        # Create upload directory if it doesn't exist
        os.makedirs(upload_directory, exist_ok=True)
        
        # Extension to format mapping
        self.extension_to_format = {
            ".jpg": ImageFormat.JPEG,
            ".jpeg": ImageFormat.JPEG,
            ".png": ImageFormat.PNG,
            ".gif": ImageFormat.GIF,
            ".webp": ImageFormat.WEBP
        }
    
    async def save_uploaded_file(
        self,
        file: UploadFile,
        user_id: Optional[str] = None
    ) -> ImageInfo:
        """
        Save an uploaded file and return image information.
        
        Args:
            file: Uploaded file
            user_id: Optional user ID for organization
            
        Returns:
            ImageInfo object with file details
            
        Raises:
            ValueError: If file is invalid or too large
            Exception: If file saving fails
        """
        # Validate file
        await self._validate_file(file)
        
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_id = UUID()
        
        # Get file extension
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in self.allowed_extensions:
            raise ValueError(f"File extension {file_extension} not allowed")
        
        # Generate filename
        filename = f"{file_id}_{timestamp}{file_extension}"
        
        # Create user-specific directory if user_id provided
        if user_id:
            user_dir = os.path.join(self.upload_directory, user_id)
            os.makedirs(user_dir, exist_ok=True)
            file_path = os.path.join(user_dir, filename)
        else:
            file_path = os.path.join(self.upload_directory, filename)
        
        try:
            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Get image information
            image_info = await self._get_image_info(file_path, filename)
            
            self.logger.info(f"Saved uploaded file: {filename}")
            return image_info
            
        except Exception as e:
            # Clean up file if saving failed
            if os.path.exists(file_path):
                os.remove(file_path)
            raise Exception(f"Failed to save uploaded file: {str(e)}")
    
    async def save_multiple_files(
        self,
        files: List[UploadFile],
        user_id: Optional[str] = None
    ) -> List[ImageInfo]:
        """
        Save multiple uploaded files.
        
        Args:
            files: List of uploaded files
            user_id: Optional user ID for organization
            
        Returns:
            List of ImageInfo objects
            
        Raises:
            Exception: If any file saving fails
        """
        saved_files = []
        failed_files = []
        
        for file in files:
            try:
                image_info = await self.save_uploaded_file(file, user_id)
                saved_files.append(image_info)
            except Exception as e:
                self.logger.error(f"Failed to save file {file.filename}: {str(e)}")
                failed_files.append(file.filename)
        
        if failed_files:
            self.logger.warning(f"Failed to save {len(failed_files)} files: {failed_files}")
        
        return saved_files
    
    async def get_file_path(self, image_info: ImageInfo) -> str:
        """
        Get the full file path for an image.
        
        Args:
            image_info: Image information
            
        Returns:
            Full file path
        """
        return image_info.file_path
    
    async def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file exists, False otherwise
        """
        return os.path.exists(file_path)
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file.
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if file was deleted, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                self.logger.info(f"Deleted file: {file_path}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to delete file {file_path}: {str(e)}")
            return False
    
    async def cleanup_old_files(self, days_old: int = 7) -> int:
        """
        Clean up files older than specified days.
        
        Args:
            days_old: Number of days after which files should be deleted
            
        Returns:
            Number of files deleted
        """
        deleted_count = 0
        cutoff_time = datetime.utcnow().timestamp() - (days_old * 24 * 60 * 60)
        
        try:
            for root, dirs, files in os.walk(self.upload_directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.getmtime(file_path) < cutoff_time:
                        if await self.delete_file(file_path):
                            deleted_count += 1
            
            self.logger.info(f"Cleaned up {deleted_count} old files")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old files: {str(e)}")
            return deleted_count
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with storage statistics
        """
        total_files = 0
        total_size = 0
        
        try:
            for root, dirs, files in os.walk(self.upload_directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_files += 1
                    total_size += os.path.getsize(file_path)
            
            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "upload_directory": self.upload_directory,
                "max_file_size_mb": self.max_file_size_bytes // (1024 * 1024)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get storage stats: {str(e)}")
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "upload_directory": self.upload_directory,
                "max_file_size_mb": self.max_file_size_bytes // (1024 * 1024)
            }
    
    async def _validate_file(self, file: UploadFile) -> None:
        """
        Validate uploaded file.
        
        Args:
            file: Uploaded file
            
        Raises:
            ValueError: If file is invalid
        """
        # Check file size
        if hasattr(file, 'size') and file.size > self.max_file_size_bytes:
            raise ValueError(f"File too large. Maximum size: {self.max_file_size_bytes} bytes")
        
        # Check file extension
        if file.filename:
            file_extension = Path(file.filename).suffix.lower()
            if file_extension not in self.allowed_extensions:
                raise ValueError(f"File extension {file_extension} not allowed")
        
        # Check if it's a valid image
        try:
            # Read first few bytes to check image header
            file.file.seek(0)
            header = file.file.read(10)
            file.file.seek(0)  # Reset position
            
            # Check for common image file signatures
            if not (header.startswith(b'\xff\xd8\xff') or  # JPEG
                    header.startswith(b'\x89PNG\r\n\x1a\n') or  # PNG
                    header.startswith(b'GIF87a') or  # GIF
                    header.startswith(b'GIF89a') or  # GIF
                    header.startswith(b'RIFF') and b'WEBP' in header):  # WEBP
                raise ValueError("File does not appear to be a valid image")
                
        except Exception as e:
            raise ValueError(f"Invalid image file: {str(e)}")
    
    async def _get_image_info(self, file_path: str, filename: str) -> ImageInfo:
        """
        Get image information from file.
        
        Args:
            file_path: Path to image file
            filename: Original filename
            
        Returns:
            ImageInfo object
        """
        try:
            with Image.open(file_path) as img:
                # Get file extension
                file_extension = Path(filename).suffix.lower()
                image_format = self.extension_to_format.get(file_extension, ImageFormat.JPEG)
                
                # Get file size
                file_size = os.path.getsize(file_path)
                
                return ImageInfo(
                    filename=filename,
                    format=image_format,
                    width=img.width,
                    height=img.height,
                    size_bytes=file_size,
                    file_path=file_path
                )
                
        except Exception as e:
            raise Exception(f"Failed to get image info: {str(e)}")
    
    async def create_thumbnail(
        self,
        image_info: ImageInfo,
        thumbnail_size: tuple = (150, 150)
    ) -> str:
        """
        Create a thumbnail for an image.
        
        Args:
            image_info: Image information
            thumbnail_size: Size of thumbnail (width, height)
            
        Returns:
            Path to thumbnail file
        """
        thumbnail_dir = os.path.join(self.upload_directory, "thumbnails")
        os.makedirs(thumbnail_dir, exist_ok=True)
        
        thumbnail_filename = f"thumb_{image_info.id}.jpg"
        thumbnail_path = os.path.join(thumbnail_dir, thumbnail_filename)
        
        try:
            with Image.open(image_info.file_path) as img:
                img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
                img.save(thumbnail_path, "JPEG", quality=85)
            
            return thumbnail_path
            
        except Exception as e:
            self.logger.error(f"Failed to create thumbnail: {str(e)}")
            raise
