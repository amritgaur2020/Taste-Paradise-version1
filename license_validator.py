"""
TasteParadise Offline License Validator
Validates license activation WITHOUT INTERNET
Author: Amrit Gaur
"""

import os
import json
import hashlib
from datetime import datetime
from hardware_fingerprint import get_machine_id

# ============================================================
# IMPORTANT: Use the SAME secret key as in generator
# ============================================================
SECRET_KEY = "TasteParadise_Secret_2025_Amrit_Gaur_XYZ123"

class OfflineLicenseValidator:
    """Validate offline licenses"""
    
    def __init__(self):
        self.secret_key = SECRET_KEY
        self.license_file = "tasteparadise.lic"
        self.machine_id = get_machine_id()
    
    def validate_activation_code(self, activation_code):
        """
        Validate activation code format and signature
        Returns: (is_valid, license_data, error_message)
        """
        try:
            # Parse activation code (format: LICENSE_KEY|MACHINE_ID|EXPIRY|SIGNATURE)
            parts = activation_code.split('|')
            
            if len(parts) != 4:
                return False, None, f"Invalid activation code format (expected 4 parts, got {len(parts)})"
            
            license_key, machine_id, expiry_date, signature = parts
            
            # Verify signature
            data = f"{license_key}|{machine_id}|{expiry_date}"
            expected_signature = hashlib.sha256(f"{data}|{self.secret_key}".encode()).hexdigest()
            
            if signature != expected_signature:
                return False, None, "Invalid activation code (signature mismatch - tampered or wrong secret key)"
            
            # Verify machine ID matches
            current_machine = self.machine_id
            if machine_id != current_machine:
                return False, None, f"Machine mismatch!\n   Your Machine ID: {current_machine}\n   Activation Machine ID: {machine_id}\n   This activation is for a different computer."
            
            # Check expiry
            try:
                expiry_dt = datetime.fromisoformat(expiry_date)
                if expiry_dt < datetime.now():
                    days_expired = (datetime.now() - expiry_dt).days
                    return False, None, f"License expired {days_expired} days ago"
            except:
                return False, None, "Invalid expiry date format"
            
            # All checks passed
            license_data = {
                'license_key': license_key,
                'machine_id': machine_id,
                'expiry_date': expiry_date,
                'activated_at': datetime.now().isoformat(),
                'status': 'active'
            }
            
            return True, license_data, None
            
        except Exception as e:
            return False, None, f"Validation error: {str(e)}"
    
    def save_license(self, license_data):
        """Save activated license to file"""
        try:
            with open(self.license_file, 'w') as f:
                json.dump(license_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Warning: Could not save license: {e}")
            return False
    
    def load_license(self):
        """Load license from file"""
        if not os.path.exists(self.license_file):
            return None
        
        try:
            with open(self.license_file, 'r') as f:
                return json.load(f)
        except:
            return None
    
    def validate_existing_license(self):
        """
        Validate license on every startup
        Returns: (is_valid, license_data, message)
        """
        license_data = self.load_license()
        
        if not license_data:
            return False, None, "No license found - activation required"
        
        # Verify machine ID
        if license_data.get('machine_id') != self.machine_id:
            return False, None, "License machine mismatch - invalid license"
        
        # Check expiry
        expiry_date = license_data.get('expiry_date')
        if expiry_date:
            try:
                expiry_dt = datetime.fromisoformat(expiry_date)
                if expiry_dt < datetime.now():
                    days_expired = (datetime.now() - expiry_dt).days
                    return False, None, f"License expired {days_expired} days ago"
                
                days_remaining = (expiry_dt - datetime.now()).days
                return True, license_data, f"License valid ({days_remaining} days remaining)"
            except:
                return False, None, "Invalid license data"
        
        return True, license_data, "License valid (lifetime)"
    
    def activate_interactive(self):
        """Interactive activation process"""
        print("\n" + "="*70)
        print("🔒 TASTEPARADISE LICENSE ACTIVATION")
        print("="*70)
        
        # Check existing license
        is_valid, license_data, message = self.validate_existing_license()
        
        if is_valid:
            print(f"\n✅ {message}")
            print(f"   License Key: {license_data.get('license_key')}")
            print(f"   Expires: {license_data.get('expiry_date', 'Never')[:10]}")
            return True
        
        # No valid license - need activation
        print(f"\n⚠️  {message}")
        print("\n" + "-"*70)
        print("📋 LICENSE ACTIVATION REQUIRED")
        print("-"*70)
        
        # Show machine ID
        print(f"\n🔑 Your Machine ID: {self.machine_id}")
        print("\nℹ️ ACTIVATION STEPS:")
        print("  1. Contact support with your Machine ID")
        print("  2. Receive activation code from support")
        print("  3. Enter activation code below")
        print("-"*70)
        
        activation_code = input("\n🔓 Enter Activation Code: ").strip()
        
        if not activation_code:
            print("❌ Activation code is required!")
            return False
        
        # Validate activation code
        print("\n⏳ Validating activation code...")
        is_valid, license_data, error = self.validate_activation_code(activation_code)
        
        if not is_valid:
            print(f"\n❌ ACTIVATION FAILED!")
            print(f"   Reason: {error}")
            print("\n📞 Contact support: gaurhariom60@gmail.com")
            return False
        
        # Save license
        if self.save_license(license_data):
            print("\n" + "="*70)
            print("✅ LICENSE ACTIVATED SUCCESSFULLY!")
            print("="*70)
            print(f"   License Key: {license_data['license_key']}")
            print(f"   Expires: {license_data['expiry_date'][:10]}")
            print(f"   Machine ID: {license_data['machine_id']}")
            print("="*70)
            return True
        else:
            print("\n⚠️ License validated but could not save to file")
            return True


# ============================================================
# MAIN - Integrate this into your TasteParadise main.py
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("              TASTE PARADISE")
    print("         Restaurant Management System")
    print("="*70)
    
    validator = OfflineLicenseValidator()
    
    if validator.activate_interactive():
        print("\n✅ Starting TasteParadise...")
        # Your application code here
        input("\nPress Enter to exit...")
    else:
        print("\n❌ Cannot start - valid license required")
        input("\nPress Enter to exit...")
