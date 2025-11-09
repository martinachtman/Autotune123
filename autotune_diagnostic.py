#!/usr/bin/env python3
"""
Autotune Diagnostic Script
Comprehensive debugging for autotune execution issues
"""

import os
import json
import subprocess
from datetime import datetime

print("🔍 AUTOTUNE DIAGNOSTIC SCRIPT")
print("=" * 60)

# Test environment setup
print("\n1. 🌍 ENVIRONMENT CHECK")
print("-" * 30)
print(f"Current working directory: {os.getcwd()}")
print(f"User: {os.getenv('USER', 'unknown')}")
print(f"Home: {os.path.expanduser('~')}")

# Check oref0 installation
print("\n2. 🛠️  OREF0 INSTALLATION CHECK")
print("-" * 30)
oref0_paths = [
    "/opt/oref0/bin/oref0-autotune.sh",
    "/opt/oref0/bin/ns-get.sh", 
    "/usr/local/bin/ns-get"
]

for path in oref0_paths:
    exists = os.path.exists(path)
    executable = os.access(path, os.X_OK) if exists else False
    print(f"  {path}: {'✅ EXISTS' if exists else '❌ MISSING'} {'& EXECUTABLE' if executable else '& NOT EXECUTABLE' if exists else ''}")

# Check directories
print("\n3. 📁 DIRECTORY STRUCTURE")
print("-" * 30)
directories = [
    "/root/myopenaps",
    "/root/myopenaps/settings",
    "/root/myopenaps/autotune"
]

for directory in directories:
    exists = os.path.exists(directory)
    print(f"  {directory}: {'✅ EXISTS' if exists else '❌ MISSING'}")
    if exists:
        try:
            files = os.listdir(directory)
            print(f"    Contents: {files if files else 'EMPTY'}")
        except PermissionError:
            print("    Contents: PERMISSION DENIED")

# Test profile creation
print("\n4. 📋 PROFILE CREATION TEST")
print("-" * 30)

try:
    # Create test profile
    test_profile = {
        "timezone": "UTC",
        "dia": 4.0,
        "carb_ratio": 10.0,
        "isfProfile": {
            "sensitivities": [{"sensitivity": 45.0, "offset": 0, "start": "00:00:00"}]
        },
        "basalprofile": [
            {"start": "00:00:00", "minutes": 0, "rate": 0.5}
        ]
    }
    
    settings_dir = "/root/myopenaps/settings"
    os.makedirs(settings_dir, exist_ok=True)
    pumpprofile_path = os.path.join(settings_dir, "pumpprofile.json")
    
    with open(pumpprofile_path, 'w') as f:
        json.dump(test_profile, f, indent=2)
    
    print(f"  ✅ Test pumpprofile.json created: {os.path.exists(pumpprofile_path)}")
    
    # Verify file content
    with open(pumpprofile_path, 'r') as f:
        loaded_profile = json.load(f)
    print(f"  ✅ Profile contains {len(loaded_profile)} fields")
    
except Exception as e:
    print(f"  ❌ Profile creation failed: {e}")

# Test oref0-autotune command construction
print("\n5. 🚀 AUTOTUNE COMMAND TEST")
print("-" * 30)

try:
    autotune_cmd = "/opt/oref0/bin/oref0-autotune.sh"
    test_dir = "/root/myopenaps"
    test_host = "https://your-nightscout-site.herokuapp.com"
    test_start = "2025-11-04"
    test_end = "2025-11-08"
    
    # Build command
    command = f"{autotune_cmd} --dir={test_dir} --ns-host={test_host} --start-date={test_start} --end-date={test_end}"
    print(f"  Command: {command}")
    
    # Test command existence
    test_cmd = f"test -x {autotune_cmd}"
    result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True)
    print(f"  ✅ Command executable: {result.returncode == 0}")
    
    # Check for required files before running
    required_files = [
        "/root/myopenaps/settings/pumpprofile.json"
    ]
    
    all_files_exist = True
    for req_file in required_files:
        exists = os.path.exists(req_file)
        print(f"  Required file {req_file}: {'✅ EXISTS' if exists else '❌ MISSING'}")
        if not exists:
            all_files_exist = False
    
    if all_files_exist:
        print("  ✅ All required files exist - ready for autotune execution")
    else:
        print("  ❌ Missing required files - autotune will fail")
        
except Exception as e:
    print(f"  ❌ Command test failed: {e}")

# Environment variables check
print("\n6. 🔐 ENVIRONMENT VARIABLES")
print("-" * 30)
env_vars = ['API_SECRET', 'NIGHTSCOUT_HOST', 'NODE_PATH', 'PATH']
for var in env_vars:
    value = os.getenv(var, 'NOT_SET')
    display_value = value if var != 'API_SECRET' else ('SET' if value != 'NOT_SET' else 'NOT_SET')
    print(f"  {var}: {display_value}")

# Python imports test  
print("\n7. 🐍 PYTHON IMPORTS TEST")
print("-" * 30)
try:
    from autotune import Autotune
    print("  ✅ Autotune class importable")
    
    autotune_instance = Autotune()
    methods = [m for m in dir(autotune_instance) if not m.startswith('_')]
    print(f"  ✅ Available methods: {methods}")
    
except Exception as e:
    print(f"  ❌ Import failed: {e}")

print("\n" + "=" * 60)
print("🏁 DIAGNOSTIC COMPLETE")
print("=" * 60)