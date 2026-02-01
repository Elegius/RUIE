"""
Pure Python ASAR extractor - no Node.js required.
ASAR format: Header JSON + File data
"""

import os
import json
import struct
from pathlib import Path

class ASARExtractor:
    """Extract ASAR archives using pure Python."""
    
    HEADER_SIZE = 8  # First 8 bytes contain header size info
    
    @staticmethod
    def extract(asar_path, output_dir):
        """Extract an ASAR file to the specified directory.
        
        ASAR Format:
        - Bytes 0-3: Size of the offset size (always 4)
        - Bytes 4-7: Size of the header
        - Bytes 8+: The actual header (JSON) followed by file data
        
        However, there's a complexity: the header itself contains size metadata
        for each file, so we need to find where the JSON actually starts.
        """
        try:
            print(f"[ASARExtractor] Starting extraction from: {asar_path}")
            print(f"[ASARExtractor] Output directory: {output_dir}")
            
            # Verify asar file exists
            if not os.path.exists(asar_path):
                raise FileNotFoundError(f"ASAR file not found: {asar_path}")
            
            asar_size = os.path.getsize(asar_path)
            print(f"[ASARExtractor] ASAR file size: {asar_size} bytes")
            
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            with open(asar_path, 'rb') as f:
                # Read header metadata (first 8 bytes)
                header_metadata = f.read(8)
                offset_size = struct.unpack('<I', header_metadata[0:4])[0]  # Should be 4
                header_size = struct.unpack('<I', header_metadata[4:8])[0]  # Size of header data
                
                print(f"[ASARExtractor] Offset size: {offset_size}, Header size: {header_size}")
                
                # The header data starts after the 8-byte metadata
                # But it might have inline size values for each file
                header_bytes = f.read(header_size)
                
                # The actual JSON should start somewhere in here
                # Let's search for the opening brace '{'
                json_start = header_bytes.find(b'{')
                print(f"[ASARExtractor] JSON starts at offset: {json_start}")
                
                if json_start < 0:
                    raise ValueError("No JSON object found in ASAR header")
                
                # Extract from the first { to the matching }
                # Count braces to find the end
                json_data = ASARExtractor._extract_json_object(header_bytes[json_start:])
                
                print(f"[ASARExtractor] Extracted {len(json_data)} bytes of JSON")
                print(f"[ASARExtractor] JSON preview: {json_data[:100]}")
                
                try:
                    header = json.loads(json_data.decode('utf-8'))
                except UnicodeDecodeError as e:
                    print(f"[ASARExtractor] Failed to decode JSON: {e}")
                    raise ValueError(f"Failed to decode ASAR header JSON: {e}")
                
                print(f"[ASARExtractor] Header parsed, files: {len(header.get('files', {}))}")
                
                # The data offset is after the metadata and header
                data_offset = 8 + header_size
                
                # Extract files
                ASARExtractor._extract_files(f, header.get('files', {}), output_dir, data_offset)
                
                print(f"[ASARExtractor] Extraction complete")
                return True
                
        except Exception as e:
            print(f"[ASARExtractor] Error: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    @staticmethod
    def _extract_json_object(data):
        """Extract a complete JSON object from bytes, handling braces properly."""
        if data[0:1] != b'{':
            raise ValueError("Data does not start with JSON object")
        
        brace_count = 0
        in_string = False
        escape_next = False
        
        for i, byte in enumerate(data):
            char = chr(byte) if byte < 128 else '?'
            
            if escape_next:
                escape_next = False
                continue
            
            if char == '\\':
                escape_next = True
                continue
                
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            
            if in_string:
                continue
            
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    # Found the end of the object
                    return data[:i+1]
        
        raise ValueError("Could not find end of JSON object")
    
    @staticmethod
    def _extract_files(file_handle, files_dict, output_dir, data_offset, path_prefix=''):
        """Recursively extract files from ASAR header."""
        # Counter for progress logging
        file_count = 0
        for name, file_info in files_dict.items():
            current_path = os.path.join(path_prefix, name) if path_prefix else name
            full_output_path = os.path.join(output_dir, current_path)
            
            if isinstance(file_info, dict):
                # Check if it's a directory or file
                if 'files' in file_info:
                    # It's a directory
                    os.makedirs(full_output_path, exist_ok=True)
                    ASARExtractor._extract_files(
                        file_handle,
                        file_info['files'],
                        output_dir,
                        data_offset,
                        current_path
                    )
                else:
                    # It's a file with offset and size
                    if 'offset' in file_info and 'size' in file_info:
                        offset = int(file_info['offset'])
                        size = int(file_info['size'])
                        
                        # Make sure parent directory exists
                        parent_dir = os.path.dirname(full_output_path)
                        if parent_dir and not os.path.exists(parent_dir):
                            os.makedirs(parent_dir, exist_ok=True)
                        
                        try:
                            # Read file data from ASAR
                            file_handle.seek(data_offset + offset)
                            file_data = file_handle.read(size)
                            
                            # Write to output - write in one go to minimize antimalware scanning
                            with open(full_output_path, 'wb') as out_f:
                                out_f.write(file_data)
                            
                            # Log progress less frequently to reduce overhead
                            file_count += 1
                            if file_count % 100 == 0:
                                print(f"[ASARExtractor] Progress: {file_count} files extracted ({current_path})")
                        except Exception as e:
                            print(f"[ASARExtractor] Failed to extract {current_path}: {e}")
