import json
import os
import re
from pathlib import Path

class ColorReplacer:
    """Replace colors in theme JSON files."""
    
    @staticmethod
    def hex_to_rgb(hex_color):
        """Convert hex to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    @staticmethod
    def rgb_to_hex(r, g, b):
        """Convert RGB to hex."""
        return f'#{r:02x}{g:02x}{b:02x}'
    
    @staticmethod
    def replace_in_file(file_path, color_mappings):
        """Replace colors in a JSON file."""
        if not os.path.exists(file_path):
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace each color mapping
            for old_color, new_color in color_mappings.items():
                if old_color.startswith('--sol-color-'):
                    pattern = re.compile(rf'({re.escape(old_color)}\s*:\s*)([^;]+)', re.IGNORECASE)
                    content = pattern.sub(rf'\1{new_color}', content)
                    continue

                # Case-insensitive replacement
                content = content.replace(f'"{old_color}"', f'"{new_color}"')
                content = content.replace(f"'{old_color}'", f"'{new_color}'")
                content = content.replace(old_color, new_color)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        except Exception as e:
            print(f"Error replacing colors in {file_path}: {e}")
            return False
    
    @staticmethod
    def apply_colors(extracted_dir, color_mappings):
        """Apply color replacements to all relevant files."""
        success_count = 0
        
        # Find all JSON/CSS/JS files
        for root, dirs, files in os.walk(extracted_dir):
            for file in files:
                if file.endswith('.json') or file.endswith('.css') or file.endswith('.js'):
                    file_path = os.path.join(root, file)
                    if ColorReplacer.replace_in_file(file_path, color_mappings):
                        success_count += 1
        
        return success_count
