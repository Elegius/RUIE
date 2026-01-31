import shutil
import os
from pathlib import Path

class MediaReplacer:
    """Replace media files in extracted launcher."""
    
    @staticmethod
    def copy_media(source_dir, dest_dir, media_type):
        """Copy media files from source to destination."""
        success_count = 0
        
        if not os.path.exists(source_dir):
            return 0
        
        dest_media_dir = os.path.join(dest_dir, 'assets', media_type)
        os.makedirs(dest_media_dir, exist_ok=True)
        
        try:
            for file in os.listdir(source_dir):
                source_file = os.path.join(source_dir, file)
                dest_file = os.path.join(dest_media_dir, file)
                
                if os.path.isfile(source_file):
                    shutil.copy2(source_file, dest_file)
                    success_count += 1
        except Exception as e:
            print(f"Error copying {media_type}: {e}")
        
        return success_count
    
    @staticmethod
    def apply_media(extracted_dir, media_mappings):
        """Apply media replacements."""
        results = {}
        
        for media_type, source_dir in media_mappings.items():
            if source_dir and os.path.exists(source_dir):
                count = MediaReplacer.copy_media(source_dir, extracted_dir, media_type)
                results[media_type] = count
        
        return results
