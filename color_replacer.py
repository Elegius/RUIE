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
    def _read_text(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()

    @staticmethod
    def _write_text(file_path, content):
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    @staticmethod
    def _hex_to_rgb_string(hex_color):
        if not hex_color or not hex_color.startswith('#'):
            return None
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c * 2 for c in hex_color])
        if len(hex_color) != 6:
            return None
        r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"{r} {g} {b}"

    @staticmethod
    def _extract_default_values(content, variable_names):
        defaults = {}
        for var_name in variable_names:
            # More robust pattern that handles CSS variable definitions
            # Looks for: variableName: value; (or variableName:value with optional whitespace)
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
        """Apply color replacements by targeting main.*.js and replacing default theme values."""
        success_count = 0
        error_count = 0

        try:
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
                    
                    defaults = ColorReplacer._extract_default_values(content, variable_names)
                    print(f"Found {len(defaults)} default values")

                    if not defaults:
                        print(f"⚠ No default values found in {main_file}")
                        continue

                    file_modified = False

                    for var_name, new_color in color_mappings.items():
                        old_value = defaults.get(var_name)
                        if not old_value:
                            print(f"  ⚠ {var_name}: old value not found in defaults")
                            continue

                        new_value = new_color.strip()
                        if not new_value:
                            print(f"  ⚠ {var_name}: new value is empty")
                            continue

                        # Validate new color format
                        if not (new_value.startswith('#') or re.match(r'^\d{1,3}\s+\d{1,3}\s+\d{1,3}$', new_value)):
                            print(f"  ⚠ {var_name}: invalid new color format '{new_value}'")
                            continue

                        print(f"  → {var_name}: '{old_value}' → '{new_value}'")
                        
                        # Replace direct color values
                        if old_value in content:
                            old_count = content.count(old_value)
                            content = content.replace(old_value, new_value)
                            print(f"    ✓ Replaced {old_count} occurrence(s) of '{old_value}'")
                            file_modified = True
                        else:
                            print(f"    ⚠ Old value '{old_value}' not found in file")

                        # Also try RGB conversion if applicable
                        if old_value.startswith('#'):
                            old_rgb = ColorReplacer._hex_to_rgb_string(old_value)
                            if new_value.startswith('#'):
                                new_rgb = ColorReplacer._hex_to_rgb_string(new_value)
                            else:
                                new_rgb = new_value
                                
                            if old_rgb and new_rgb:
                                rgb_patterns = [
                                    (old_rgb, new_rgb),  # Space-separated
                                    (old_rgb.replace(' ', ','), new_rgb.replace(' ', ',')),  # Comma-separated
                                    (f"rgb({old_rgb.replace(' ', ',')})", f"rgb({new_rgb.replace(' ', ',')})"),  # rgb() function
                                ]
                                for old_pattern, new_pattern in rgb_patterns:
                                    if old_pattern in content:
                                        old_count = content.count(old_pattern)
                                        content = content.replace(old_pattern, new_pattern)
                                        print(f"    ✓ Replaced {old_count} RGB occurrence(s)")
                                        file_modified = True

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
