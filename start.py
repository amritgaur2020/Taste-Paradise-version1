"""
TasteParadise Startup with License Verification
"""
import sys
import os

# Prevent sys.exit from killing the process during import
original_exit = sys.exit
def safe_exit(code=0):
    print(f"⚠️  Intercepted sys.exit({code}) - continuing startup")
    pass

sys.exit = safe_exit

# Now import main (license check will be bypassed)
from main import app
import uvicorn

# Restore original exit
sys.exit = original_exit

# Now do license check properly
from license_validator import OfflineLicenseValidator

def verify_license():
    try:
        validator = OfflineLicenseValidator()
        with open("license.key", 'r') as f:
            license_data = f.read().strip()
        if validator.validate_license(license_data):
            return True
    except:
        pass
    return False

if __name__ == "__main__":
    print("="*70)
    print("  TASTE PARADISE - Restaurant Management System")
    print("="*70)
    
    # Verify license
    if not verify_license():
        print("\n❌ LICENSE VALIDATION FAILED")
        print("="*70)
        print("Contact: gaurhariom60@gmail.com | +91 82183 55207")
        print("="*70)
        input("Press Enter to exit...")
        sys.exit(1)
    
    print("✅ License Valid")
    print("Starting server on http://127.0.0.1:8002")
    print("="*70)
    
    # Start server
    try:
        uvicorn.run(app, host="127.0.0.1", port=8002)
    except KeyboardInterrupt:
        print("\nServer stopped")
