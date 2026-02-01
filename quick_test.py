#!/usr/bin/env python3
"""
Quick test - Initialize and Decompile
"""
import urllib.request
import json
import time
import os

def post_api(endpoint, data=None):
    url = f'http://localhost:5000{endpoint}'
    if data:
        data = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read())
        except:
            return {'error': e.reason}

print("Initializing...")
init_resp = post_api('/api/init', {'asarPath': 'C:\\Program Files\\Roberts Space Industries\\RSI Launcher\\resources\\app.asar'})
print(f"✓ Init: {init_resp.get('success')}")

print("\nDecompiling (Decompile button)...")
extract_resp = post_api('/api/extract')
print(f"✓ Extract: {extract_resp.get('success')}")
print(f"  Path: {extract_resp.get('extractedPath')}")

time.sleep(1)
# Check the extraction
latest_dir = os.path.join(os.path.expanduser('~/Documents/RUIE'), extract_resp.get('extractedPath').split('\\')[-1])
if os.path.exists(latest_dir):
    file_count = len([f for f in os.listdir(latest_dir) if os.path.isfile(os.path.join(latest_dir, f))])
    print(f"✓ Extracted {file_count} files + directories to: {latest_dir}")
