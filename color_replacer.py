"""
Color Replacer Module
====================

This module handles color replacement in the launcher's JavaScript files.
It works by:

1. Finding the main JavaScript file (main.*.js) in the extracted launcher
2. Locating CSS variable definitions and their default color values
3. Replacing those default values with user-selected colors
4. Supporting both hex (#RRGGBB) and RGB (R G B) color formats

The color replacement is done by literal string replacement, so it modifies
the actual default values in the JavaScript code.

Color Format Support:
- Hex: #FF5733
- RGB: 255 87 51
- RGB function: rgb(255, 87, 51)
"""

import json
import os
import re
from pathlib import Path

class ColorReplacer:
    """Replace colors in launcher theme JavaScript files.
    
    This class handles finding CSS color variables in the launcher's
    JavaScript and replacing them with user-selected colors.
    """
    
    @staticmethod
    def hex_to_rgb(hex_color):
        """Convert hex color code to RGB tuple.
        
        Args:
            hex_color (str): Color in hex format, e.g., '#FF5733'
            
        Returns:
            tuple: (red, green, blue) values 0-255
            
        Example:
            >>> ColorReplacer.hex_to_rgb('#FF5733')
            (255, 87, 51)
        """
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    @staticmethod
    def rgb_to_hex(r, g, b):
        """Convert RGB tuple to hex color code.
        
        Args:
            r (int): Red channel value 0-255
            g (int): Green channel value 0-255
            b (int): Blue channel value 0-255
            
        Returns:
            str: Color in hex format, e.g., '#FF5733'
            
        Example:
            >>> ColorReplacer.rgb_to_hex(255, 87, 51)
            '#ff5733'
        """
        return f'#{r:02x}{g:02x}{b:02x}'
    
    @staticmethod
    def _read_text(file_path):
        """Read text file with fallback encoding support.
        
        Tries UTF-8 first, falls back to Latin-1 if that fails.
        
        Args:
            file_path (str): Path to file to read
            
        Returns:
            str: File contents
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Fallback for files with unusual encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()

    @staticmethod
    def _write_text(file_path, content):
        """Write text file with UTF-8 encoding.
        
        Args:
            file_path (str): Path to file to write
            content (str): Content to write
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    @staticmethod
    def _hex_to_rgb_string(hex_color):
        """Convert hex color to space-separated RGB string.
        
        Supports both 3-digit and 6-digit hex colors.
        
        Args:
            hex_color (str): Color in hex format
            
        Returns:
            str: RGB as space-separated string, e.g., '255 87 51'
            None: If conversion fails
            
        Example:
            >>> ColorReplacer._hex_to_rgb_string('#FF5733')
            '255 87 51'
        """
        if not hex_color or not hex_color.startswith('#'):
            return None
        
        hex_color = hex_color.lstrip('#')
        
        # Support 3-digit hex (#RGB -> #RRGGBB)
        if len(hex_color) == 3:
            hex_color = ''.join([c * 2 for c in hex_color])
        
        # Validate 6-digit hex
        if len(hex_color) != 6:
            return None
        
        # Convert to RGB values
        r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"{r} {g} {b}"

    @staticmethod
    def _extract_default_values(content, variable_names):
        """Extract default values for CSS variables from file content.
        
        Searches for variable definitions like:
        - variableName: #FF5733;
        - variableName: 255 87 51;
        - variableName: rgb(255, 87, 51);
        
        Args:
            content (str): File content to search
            variable_names (list): List of variable names to find
            
        Returns:
            dict: Mapping of variable names to their default values
        """
        defaults = {}
        for var_name in variable_names:
            # Pattern matches: variableName: value; (with flexible whitespace)
            # Looks for patterns like "colorVariable: #FFFFFF;"
            pattern = re.compile(rf'{re.escape(var_name)}\s*:\s*([^;]+?)(?:\s*;|\s*,|\s*}}|\s*$)', re.IGNORECASE)
            match = pattern.search(content)
            if match:
                value = match.group(1).strip().strip('"\'')
                defaults[var_name] = value
                print(f"  Found {var_name}: {value}")
            else:
                print(f"  Variable {var_name} not found in content")
        return defaults
    
    @staticmethod
    def apply_colors(extracted_dir, color_mappings, progress_callback=None):
        """Apply color replacements to launcher JavaScript files.
        
        This is the main entry point for color replacement. It:
        1. Finds main.*.js files in the extracted launcher
        2. Extracts current default color values
        3. Replaces them with user-selected colors
        4. Supports multiple color formats (hex, RGB, rgb() function)
        
        Args:
            extracted_dir (str): Root directory of extracted launcher
            color_mappings (dict): Dictionary mapping color variable names to new colors
                Example: {
                    'primaryColor': '#FF5733',
                    'secondaryColor': '255 87 51'
                }
            progress_callback (function): Optional callback for progress updates
                Called as: progress_callback(current, total, status_message)
                
        Returns:
            int: Number of files successfully modified
        """
        success_count = 0
        error_count = 0

        try:
            # Validate extracted directory
            if not os.path.exists(extracted_dir):
                print(f"Error: extracted_dir doesn't exist: {extracted_dir}")
                return 0

            print(f"Scanning for main.*.js in: {extracted_dir}")
            print(f"Color mappings (variables -> new colors): {color_mappings}")
            print(f"Total color mappings: {len(color_mappings)}")

            extracted_root = Path(extracted_dir)
            main_files = list(extracted_root.glob('**/main.*.js'))

            if not main_files:
                print("❌ No main.*.js files found")
                print(f"Searched in: {extracted_dir}")
                if os.path.isdir(extracted_dir):
                    print(f"Directory contents sample: {os.listdir(extracted_dir)[:10]}")
                return 0

            print(f"✓ Found {len(main_files)} main.*.js file(s)")
            total_files = len(main_files)
            if progress_callback:
                progress_callback(0, total_files, f"Found {total_files} file(s) to process...")

            # Process each main.*.js file
            for index, main_file in enumerate(main_files):
                try:
                    if progress_callback:
                        progress_callback(index, total_files, f"Processing {main_file.name}...")
                    
                    print(f"\n--- Processing {main_file.name} ---")
                    content = ColorReplacer._read_text(main_file)
                    print(f"File size: {len(content)} bytes")
                    
                    # Extract all variable names from the color mappings
                    variable_names = list(color_mappings.keys())
                    print(f"Looking for {len(variable_names)} variables...")
                    
                    # Get current default values for each variable
                    defaults = ColorReplacer._extract_default_values(content, variable_names)
                    print(f"Found {len(defaults)} default values")

                    if not defaults:
                        print(f"⚠ No default values found in {main_file}")
                        continue

                    file_modified = False

                    # Replace each color variable
                    for var_name, new_color in color_mappings.items():
                        old_value = defaults.get(var_name)
                        if not old_value:
                            print(f"  ⚠ {var_name}: old value not found in defaults")
                            continue

                        new_value = new_color.strip()
                        if not new_value:
                            print(f"  ⚠ {var_name}: new value is empty")
                            continue

                        # Validate new color format (hex or RGB)
                        if not (new_value.startswith('#') or re.match(r'^\d{1,3}\s+\d{1,3}\s+\d{1,3}$', new_value)):
                            print(f"  ⚠ {var_name}: invalid new color format '{new_value}'")
                            continue

                        print(f"  → {var_name}: '{old_value}' → '{new_value}'")
                        
                        # Replace direct color values in the file
                        if old_value in content:
                            old_count = content.count(old_value)
                            content = content.replace(old_value, new_value)
                            print(f"    ✓ Replaced {old_count} occurrence(s) of '{old_value}'")
                            file_modified = True
                        else:
                            print(f"    ⚠ Old value '{old_value}' not found in file")

                        # Also try RGB conversion if applicable (hex color to RGB format)
                        if old_value.startswith('#'):
                            old_rgb = ColorReplacer._hex_to_rgb_string(old_value)
                            if new_value.startswith('#'):
                                new_rgb = ColorReplacer._hex_to_rgb_string(new_value)
                            else:
                                new_rgb = new_value
                                
                            if old_rgb and new_rgb:
                                # Try different RGB patterns (spaces, commas, rgb() function)
                                rgb_patterns = [
                                    (old_rgb, new_rgb),  # Space-separated: 255 87 51
                                    (old_rgb.replace(' ', ','), new_rgb.replace(' ', ',')),  # Comma-separated: 255,87,51
                                    (f"rgb({old_rgb.replace(' ', ',')})", f"rgb({new_rgb.replace(' ', ',')})"),  # rgb() function
                                ]
                                for old_pattern, new_pattern in rgb_patterns:
                                    if old_pattern in content:
                                        old_count = content.count(old_pattern)
                                        content = content.replace(old_pattern, new_pattern)
                                        print(f"    ✓ Replaced {old_count} RGB occurrence(s)")
                                        file_modified = True

                    # Save modified file if changes were made
                    if file_modified:
                        ColorReplacer._write_text(main_file, content)
                        success_count += 1
                        print(f"✓ Modified: {main_file.name}")
                    else:
                        print(f"⚠ No modifications made to {main_file.name}")

                except PermissionError as e:
                    error_count += 1
                    print(f"✗ Permission denied: {main_file} - {e}")
                except Exception as e:
                    error_count += 1
                    print(f"✗ Error processing {main_file}: {e}")
                    import traceback
                    traceback.print_exc()

            if progress_callback:
                progress_callback(total_files, total_files, f"Completed - {success_count} file(s) modified")

            print(f"\n=== Summary ===")
            print(f"Total files modified: {success_count}")
            if error_count > 0:
                print(f"Errors encountered: {error_count}")

            return success_count
        except Exception as e:
            print(f"Exception in apply_colors: {e}")
            import traceback
            traceback.print_exc()
            return 0
