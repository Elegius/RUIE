#!/usr/bin/env python3
import urllib.request
import json
import time
import os

# Call the extract API
print("Calling /api/extract endpoint...")
try:
    req = urllib.request.Request('http://localhost:5000/api/extract', method='POST')
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read())
        print(f"Response: {data}")
except Exception as e:
    print(f"Error: {e}")

# Check if extraction directory was created
time.sleep(2)
docs_dir = os.path.expanduser('~/Documents/RUIE')
print(f"\nChecking {docs_dir}...")

# Get all directories in docs_dir
if os.path.exists(docs_dir):
    dirs = [d for d in os.listdir(docs_dir) if os.path.isdir(os.path.join(docs_dir, d))]
    dirs.sort(reverse=True)
    print(f"Directories in {docs_dir} (latest 3):")
    for d in dirs[:3]:
        full_path = os.path.join(docs_dir, d)
        file_count = len([f for f in os.listdir(full_path) if os.path.isfile(os.path.join(full_path, f))])
        dir_count = len([f for f in os.listdir(full_path) if os.path.isdir(os.path.join(full_path, f))])
        print(f"  {d}: {file_count} files, {dir_count} directories")
        
        # List first few files/dirs in the decompiled directory
        if 'app-decompiled' in d and dir_count > 0:
            items = os.listdir(full_path)[:10]
            for item in items:
                print(f"    - {item}")
