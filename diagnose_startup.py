
import sys
import traceback
from pathlib import Path

print("="*70)
print("TASTEPARADISE STARTUP DIAGNOSTIC")
print("="*70)

# Test 1: Check license file exists
print("\n1. Checking license file...")
license_file = Path("license.key")
if license_file.exists():
    print(f"   ✓ license.key exists ({license_file.stat().st_size} bytes)")
    try:
        with open(license_file, 'r') as f:
            content = f.read()
            print(f"   Content: {content[:100]}...")
    except Exception as e:
        print(f"   ✗ Error reading license: {e}")
else:
    print("   ✗ license.key NOT FOUND")

# Test 2: Try to import license validator
print("\n2. Testing license validator import...")
try:
    from license_validator import OfflineLicenseValidator
    print("   ✓ License validator imported successfully")
    
    # Test 3: Try to validate
    print("\n3. Testing license validation...")
    validator = OfflineLicenseValidator()
    print(f"   Machine ID: {validator.machine_id}")
    
    result = validator.verify()
    if result["valid"]:
        print(f"   ✓ LICENSE VALID!")
        print(f"   Type: {result.get('type', 'N/A')}")
        print(f"   Expires: {result.get('expiry_date', 'N/A')}")
    else:
        print(f"   ✗ LICENSE INVALID")
        print(f"   Reason: {result.get('reason', 'Unknown')}")
        
except Exception as e:
    print(f"   ✗ Error: {e}")
    traceback.print_exc()

# Test 4: Try to import main app
print("\n4. Testing main app import...")
try:
    import main
    print("   ✓ main.py imported successfully")
    print(f"   App object: {main.app}")
except Exception as e:
    print(f"   ✗ Error importing main: {e}")
    traceback.print_exc()

# Test 5: Check MongoDB connection
print("\n5. Testing MongoDB connection...")
try:
    from pymongo import MongoClient
    client = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=2000)
    info = client.server_info()
    print(f"   ✓ MongoDB connected (version {info['version']})")
except Exception as e:
    print(f"   ✗ MongoDB connection failed: {e}")

print("\n" + "="*70)
print("DIAGNOSTIC COMPLETE")
print("="*70)
