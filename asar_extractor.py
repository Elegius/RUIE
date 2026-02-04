"""
ASAR Extractor Module
====================

This module provides pure Python extraction of ASAR archives.
No Node.js or external tools required!

ASAR (Atom Shell Archive) is a simple tar-like archive format used by
Electron applications to store application resources. The RSI Launcher
uses ASAR to store its UI files.

ASAR Format Overview:
- Bytes 0-3: Offset size (always 4 in practice)
- Bytes 4-7: Header size
- Bytes 8+: JSON header describing file structure + binary file data

The JSON header contains:
- Directory structure
- File offsets (relative to start of file data)
- File sizes

Implementation Notes:
- No external dependencies needed (pure Python)
- Handles escape sequences in JSON
- Recursively extracts nested directories
- Progress logging to show extraction status
"""

import os
import json
import struct
from pathlib import Path

class ASARExtractor:
    """Extract ASAR archives using pure Python.
    
    This class handles the low-level ASAR format parsing and file extraction.
    It doesn't require Node.js or any Electron tools.
    """
    
    # Constant for ASAR header metadata size (8 bytes)
    HEADER_SIZE = 8  # First 8 bytes contain header size info
    
    @staticmethod
    def extract(asar_path, output_dir):
        """Extract an ASAR file to the specified directory.
        
        Main entry point for ASAR extraction. This method:
        1. Reads the ASAR header (which is JSON)
        2. Parses the JSON to get file structure and offsets
        3. Recursively extracts all files to the output directory
        
        ASAR Format Layout:
        [0-3]   Offset size (always 4)
        [4-7]   Header size
        [8+]    Header (JSON)
        [end]   File data (referenced by offsets in JSON)
        
        Args:
            asar_path (str): Path to the .asar file to extract
            output_dir (str): Directory where files should be extracted
            
        Returns:
            bool: True if extraction succeeded
            
        Raises:
            FileNotFoundError: If asar_path doesn't exist
            ValueError: If ASAR header is invalid or corrupt
        """
        try:
            print(f"[ASARExtractor] Starting extraction from: {asar_path}")
            print(f"[ASARExtractor] Output directory: {output_dir}")
            
            # Verify asar file exists before attempting extraction
            if not os.path.exists(asar_path):
                raise FileNotFoundError(f"ASAR file not found: {asar_path}")
            
            # Get file size for informational logging
            asar_size = os.path.getsize(asar_path)
            print(f"[ASARExtractor] ASAR file size: {asar_size} bytes")
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            with open(asar_path, 'rb') as f:
                # Read and parse the header metadata (first 8 bytes)
                # Format: [offset_size (4 bytes)][header_size (4 bytes)]
                header_metadata = f.read(8)
                offset_size = struct.unpack('<I', header_metadata[0:4])[0]  # Little-endian unsigned int
                header_size = struct.unpack('<I', header_metadata[4:8])[0]  # Size of header data
                
                print(f"[ASARExtractor] Offset size: {offset_size}, Header size: {header_size}")
                
                # Read the header data (JSON containing file structure and offsets)
                header_bytes = f.read(header_size)
                
                # Find where the JSON object starts
                # We search for the first '{' character to locate the JSON
                json_start = header_bytes.find(b'{')
                print(f"[ASARExtractor] JSON starts at offset: {json_start}")
                
                if json_start < 0:
                    raise ValueError("No JSON object found in ASAR header")
                
                # Extract the complete JSON object from the header
                # This is non-trivial because we need to handle escaped characters
                json_data = ASARExtractor._extract_json_object(header_bytes[json_start:])
                
                print(f"[ASARExtractor] Extracted {len(json_data)} bytes of JSON")
                print(f"[ASARExtractor] JSON preview: {json_data[:100]}")
                
                # Parse the JSON to get the file structure
                try:
                    header = json.loads(json_data.decode('utf-8'))
                except UnicodeDecodeError as e:
                    print(f"[ASARExtractor] Failed to decode JSON: {e}")
                    raise ValueError(f"Failed to decode ASAR header JSON: {e}")
                
                print(f"[ASARExtractor] Header parsed, files: {len(header.get('files', {}))}")
                
                # Calculate where the actual file data starts
                # It comes after the 8-byte metadata and the header
                data_offset = 8 + header_size
                
                # Extract all files from the archive
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
        """Extract a complete JSON object from bytes, handling escapes.
        
        This helper method finds the end of a JSON object by counting
        braces and handling escape sequences properly.
        
        Args:
            data (bytes): Byte data starting with '{'
            
        Returns:
            bytes: Complete JSON object from first { to matching }
            
        Raises:
            ValueError: If input doesn't start with '{' or object is incomplete
        """
        if data[0:1] != b'{':
            raise ValueError("Data does not start with JSON object")
        
        # Track bracket nesting level
        brace_count = 0
        in_string = False  # Whether we're inside a JSON string
        escape_next = False  # Whether the next character is escaped
        
        for i, byte in enumerate(data):
            char = chr(byte) if byte < 128 else '?'
            
            # Handle escape sequences in strings
            if escape_next:
                escape_next = False
                continue
            
            # Check for escape character
            if char == '\\':
                escape_next = True
                continue
            
            # Toggle string state on unescaped quotes
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            
            # Only count braces when not inside a string
            if in_string:
                continue
            
            # Count braces to find the matching closing brace
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    # Found the matching closing brace!
                    return data[:i+1]
        
        # If we get here, the JSON object was incomplete
        raise ValueError("Could not find end of JSON object")
    
    @staticmethod
    def _extract_files(file_handle, files_dict, output_dir, data_offset, path_prefix=''):
        """Recursively extract files and directories from ASAR.
        
        This method traverses the file structure described in the ASAR header
        and extracts all files to disk. It handles nested directories by
        recursively calling itself.
        
        Args:
            file_handle (file): Open file handle for the ASAR file
            files_dict (dict): Dictionary of files/dirs from ASAR header
            output_dir (str): Root output directory
            data_offset (int): Offset where file data starts in ASAR
            path_prefix (str): Current directory path for recursion
        """
        # Counter for progress logging
        file_count = 0
        
        # Process each file/directory in the current level
        for name, file_info in files_dict.items():
            # Build the full relative path
            current_path = os.path.join(path_prefix, name) if path_prefix else name
            # Build the full output filesystem path
            full_output_path = os.path.join(output_dir, current_path)
            
            if isinstance(file_info, dict):
                # Check if this entry is a directory or a file
                if 'files' in file_info:
                    # It's a directory - create it and recursively extract contents
                    os.makedirs(full_output_path, exist_ok=True)
                    ASARExtractor._extract_files(
                        file_handle,
                        file_info['files'],
                        output_dir,
                        data_offset,
                        current_path
                    )
                else:
                    # It's a file with offset and size metadata
                    if 'offset' in file_info and 'size' in file_info:
                        offset = int(file_info['offset'])
                        size = int(file_info['size'])
                        
                        # Ensure parent directory exists
                        parent_dir = os.path.dirname(full_output_path)
                        if parent_dir and not os.path.exists(parent_dir):
                            os.makedirs(parent_dir, exist_ok=True)
                        
                        try:
                            # Seek to the file data and read it
                            file_handle.seek(data_offset + offset)
                            file_data = file_handle.read(size)
                            
                            # Write extracted file to disk
                            # We write all data at once to minimize antimalware scanning delays
                            with open(full_output_path, 'wb') as out_f:
                                out_f.write(file_data)
                            
                            # Log progress (less frequently to reduce overhead)
                            file_count += 1
                            if file_count % 100 == 0:
                                print(f"[ASARExtractor] Progress: {file_count} files extracted ({current_path})")
                        except Exception as e:
                            print(f"[ASARExtractor] Failed to extract {current_path}: {e}")
