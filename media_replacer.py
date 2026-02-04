"""
Media Replacer Module
====================

This module handles the replacement of media files in the extracted launcher.
It supports replacing:
- Images (logos, backgrounds, icons)
- Videos (trailers, promotional content)
- Audio files (background music, sound effects)

The module copies media files from user-provided directories into the
appropriate locations within the extracted launcher structure.
"""

import shutil
import os
from pathlib import Path

class MediaReplacer:
    """Handle media file replacement in extracted launcher.
    
    This class manages copying user-provided media files (images, videos, audio)
    into the extracted launcher directory structure, overwriting the default media.
    """
    
    @staticmethod
    def copy_media(source_dir, dest_dir, media_type):
        """Copy media files from source directory to launcher destination.
        
        Args:
            source_dir (str): Directory containing user's media files
            dest_dir (str): Root directory of extracted launcher
            media_type (str): Type of media ('images', 'videos', 'audio', etc.)
            
        Returns:
            int: Number of files successfully copied
        """
        success_count = 0
        
        # Skip if source directory doesn't exist
        if not os.path.exists(source_dir):
            return 0
        
        # Create destination directory if it doesn't exist
        # The launcher uses assets/{media_type}/ directory structure
        dest_media_dir = os.path.join(dest_dir, 'assets', media_type)
        os.makedirs(dest_media_dir, exist_ok=True)
        
        try:
            # Copy all files from source to destination
            for file in os.listdir(source_dir):
                source_file = os.path.join(source_dir, file)
                dest_file = os.path.join(dest_media_dir, file)
                
                # Only copy files, skip subdirectories
                if os.path.isfile(source_file):
                    shutil.copy2(source_file, dest_file)  # copy2 preserves metadata
                    success_count += 1
        except Exception as e:
            print(f"Error copying {media_type}: {e}")
        
        return success_count
    
    @staticmethod
    def apply_media(extracted_dir, media_mappings):
        """Apply all media replacements to the extracted launcher.
        
        Args:
            extracted_dir (str): Root directory of extracted launcher
            media_mappings (dict): Dictionary mapping media types to source directories
                Example: {
                    'images': '/path/to/my/images',
                    'videos': '/path/to/my/videos',
                    'audio': '/path/to/my/audio'
                }
                
        Returns:
            dict: Dictionary with results for each media type
                Example: {
                    'images': 5,  # 5 image files copied
                    'videos': 2,
                    'audio': 1
                }
        """
        results = {}
        
        # Process each media type that the user provided
        for media_type, source_dir in media_mappings.items():
            # Only process if source directory is provided and exists
            if source_dir and os.path.exists(source_dir):
                # Copy media files and record count
                count = MediaReplacer.copy_media(source_dir, extracted_dir, media_type)
                results[media_type] = count
        
        return results
