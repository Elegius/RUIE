#!/usr/bin/env python3
"""
Test script for ASAR extraction - simulates button clicks
"""
import urllib.request
import json
import time
import os
import sys

def make_request(endpoint, method='GET', data=None):
    """Make HTTP request to server."""
    url = f'http://localhost:5000{endpoint}'
    try:
        if method == 'POST':
            if data:
                data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=data, method='POST')
            req.add_header('Content-Type', 'application/json')
        else:
            req = urllib.request.Request(url, method='GET')
        
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as e:
        try:
            error_data = json.loads(e.read())
        except:
            error_data = {'error': e.reason}
        return e.code, error_data
    except Exception as e:
        return 500, {'error': str(e)}

print("=== RUIE ASAR Extraction Test ===\n")

# Step 1: Initialize launcher
print("Step 1: Initializing launcher...")
status, response = make_request('/api/init', 'POST', {
    'asarPath': 'C:\\Program Files\\Roberts Space Industries\\RSI Launcher\\resources\\app.asar'
})
print(f"  Status: {status}")
print(f"  Response: {response}\n")

if not response.get('success'):
    print("ERROR: Failed to initialize launcher")
    sys.exit(1)

# Step 2: Extract ASAR
print("Step 2: Extracting ASAR (Decompile)...")
status, response = make_request('/api/extract', 'POST')
print(f"  Status: {status}")
print(f"  Response: {json.dumps(response, indent=2)}\n")

if not response.get('success'):
    print(f"ERROR: Extraction failed - {response.get('error')}")
    print(f"  Details: {response.get('details')}")
    sys.exit(1)

# Step 3: Verify extraction
print("Step 3: Verifying extraction...")
time.sleep(1)
docs_dir = os.path.expanduser('~/Documents/RUIE')
dirs = sorted([d for d in os.listdir(docs_dir) if os.path.isdir(os.path.join(docs_dir, d))], reverse=True)
for d in dirs[:2]:
    full_path = os.path.join(docs_dir, d)
    files = [f for f in os.listdir(full_path) if os.path.isfile(os.path.join(full_path, f))]
    subdirs = [f for f in os.listdir(full_path) if os.path.isdir(os.path.join(full_path, f))]
    print(f"  {d}: {len(files)} files, {len(subdirs)} directories")
    if 'app-decompiled' in d and len(subdirs) > 0:
        print(f"    ✓ Contains extracted files!")
        items = list(subdirs)[:5]
        for item in items:
            print(f"      - {item}/")

print("\n✓ Test completed successfully!")
