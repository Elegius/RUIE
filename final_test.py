#!/usr/bin/env python3
"""
Final verification test
"""
import urllib.request
import json
import time
import os
import sys

def post_api(endpoint, data=None):
    url = f'http://localhost:5000{endpoint}'
    if data:
        data = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req) as response:
            return 200, json.loads(response.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except:
            return e.code, {'error': e.reason}

print("=" * 60)
print("RUIE DECOMPILE BUTTON FUNCTIONALITY TEST")
print("=" * 60)

# Step 1: Init
print("\n[1/3] Initializing launcher...")
status, resp = post_api('/api/init', {'asarPath': 'C:\\Program Files\\Roberts Space Industries\\RSI Launcher\\resources\\app.asar'})
if status == 200 and resp.get('success'):
    print("      ✓ PASS - Launcher initialized")
else:
    print(f"      ✗ FAIL - {resp}")
    sys.exit(1)

# Step 2: Extract
print("\n[2/3] Calling /api/extract (Decompile button)...")
status, resp = post_api('/api/extract')
if status == 200 and resp.get('success'):
    extracted_path = resp.get('extractedPath')
    print(f"      ✓ PASS - Extraction successful")
    print(f"      Path: {extracted_path}")
else:
    print(f"      ✗ FAIL - {resp}")
    sys.exit(1)

# Step 3: Verify files
print("\n[3/3] Verifying extracted files...")
time.sleep(1)
if os.path.exists(extracted_path):
    all_items = []
    for root, dirs, files in os.walk(extracted_path):
        all_items.extend(files)
        all_items.extend(dirs)
    
    print(f"      ✓ PASS - Directory exists with {len(all_items)} items")
    
    # Show sample files
    items = os.listdir(extracted_path)[:5]
    print(f"      Sample contents:")
    for item in items:
        print(f"        - {item}/")
else:
    print(f"      ✗ FAIL - Directory not found: {extracted_path}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ ALL TESTS PASSED - DECOMPILE BUTTON IS WORKING!")
print("=" * 60)
