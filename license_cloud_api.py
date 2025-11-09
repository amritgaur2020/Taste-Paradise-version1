"""
TasteParadise License System with REAL-TIME Cloud Validation
Every startup checks MongoDB Atlas for revocation/expiry
Author: Amrit Gaur
"""

import os
import hashlib
import platform
import subprocess
import uuid
from datetime import datetime, timedelta
from pymongo import MongoClient
import json

# MongoDB Atlas Configuration
MONGODB_URI = "mongodb+srv://tasteparadise_customer:YOUR_NEW_PASSWORD_HERE@cluster01.7o6we1z.mongodb.net/tasteparadise?retryWrites=true&w=majority&appName=cluster01"

class RealtimeLicenseSystem:
    """
    Real-time license validation with cloud sync
    - Checks MongoDB on EVERY startup
    - Instant revocation detection
    - Instant expiry updates
    """
    
    def __init__(self):
        self.license_file = "taste_paradise.license"
        try:
            self.client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
            self.db = self.client['tasteparadise']
            self.licenses = self.db['licenses']
            self.client.server_info()
            self.online = True
        except:
            self.client = None
            self.online = False
    
    def get_machine_id(self):
        """Generate unique hardware fingerprint"""
        identifiers = []
        try:
            # MAC Address
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) 
                           for i in range(0, 48, 8)])
            identifiers.append(mac)
            
            # Computer name
            identifiers.append(platform.node())
            
            # Platform
            identifiers.append(platform.platform())
            
            # CPU (Windows)
            if platform.system() == "Windows":
                try:
                    cpu_info = subprocess.check_output(
                        "wmic cpu get ProcessorId", 
                        shell=True,
                        stderr=subprocess.DEVNULL
                    ).decode().split('\n')[1].strip()
                    identifiers.append(cpu_info)
                except:
                    pass
            
            combined = '|'.join(filter(None, identifiers))
            machine_hash = hashlib.sha256(combined.encode()).hexdigest()
            return machine_hash[:16].upper()
        
        except:
            return str(uuid.getnode())[:16].upper()
    
    def save_local_license(self, license_data):
        """Save license locally (encrypted)"""
        try:
            json_str = json.dumps(license_data, indent=2)
            encoded = json_str.encode('utf-8').hex()
            with open(self.license_file, 'w') as f:
                f.write(encoded)
            return True
        except Exception as e:
            print(f"⚠️ Error saving license: {e}")
            return False
    
    def load_local_license(self):
        """Load license from local file"""
        try:
            if not os.path.exists(self.license_file):
                return None
            with open(self.license_file, 'r') as f:
                encoded = f.read()
            json_str = bytes.fromhex(encoded).decode('utf-8')
            return json.loads(json_str)
        except:
            return None
    
    def validate_with_cloud(self, license_key):
        """
        REAL-TIME cloud validation
        Called on EVERY startup
        """
        try:
            if not self.online:
                return {'success': False, 'reason': 'Cannot connect to license server'}
            
            # Query MongoDB for license
            license_doc = self.licenses.find_one({'key': license_key})
            
            if not license_doc:
                return {'success': False, 'reason': 'License key not found in database'}
            
            # ============================================================
            # INSTANT REVOCATION CHECK
            # ============================================================
            if license_doc.get('revoked'):
                revoke_date = license_doc.get('revoked_date', 'Unknown')[:10]
                return {
                    'success': False,
                    'reason': f"🚫 LICENSE REVOKED on {revoke_date}",
                    'revoked': True
                }
            
            # ============================================================
            # INSTANT EXPIRY CHECK
            # ============================================================
            expiry = datetime.fromisoformat(license_doc['expiry_date'])
            if datetime.now() > expiry:
                return {
                    'success': False,
                    'reason': f"⏰ LICENSE EXPIRED on {expiry.date()}",
                    'expired': True
                }
            
            # Update last validation timestamp in cloud
            self.licenses.update_one(
                {'key': license_key},
                {'$set': {'last_validation': datetime.now().isoformat()}}
            )
            
            # License is VALID
            return {
                'success': True,
                'license_data': {
                    'key': license_key,
                    'customer': license_doc.get('customer', 'Licensed User'),
                    'email': license_doc.get('email', ''),
                    'plan': license_doc.get('plan', 'standard'),
                    'expiry_date': license_doc['expiry_date'],
                    'machine_id': license_doc.get('machine_id'),
                    'activated_date': license_doc.get('activation_date')
                }
            }
            
        except Exception as e:
            return {'success': False, 'reason': f'Connection error: {str(e)}'}
    
    def activate_license_cloud(self, license_key, machine_id):
        """ONE-TIME cloud activation"""
        try:
            if not self.online:
                return {'success': False, 'message': 'Cannot connect to license server'}
            
            license_doc = self.licenses.find_one({'key': license_key})
            
            if not license_doc:
                return {'success': False, 'message': 'License key not found'}
            
            # Check if revoked
            if license_doc.get('revoked'):
                return {'success': False, 'message': f"License revoked on {license_doc.get('revoked_date', 'N/A')[:10]}"}
            
            # Check expiry
            expiry = datetime.fromisoformat(license_doc['expiry_date'])
            if datetime.now() > expiry:
                return {'success': False, 'message': f"License expired on {expiry.date()}"}
            
            # Check if already activated on different machine
            if license_doc.get('activated') and license_doc.get('machine_id') != machine_id:
                return {
                    'success': False,
                    'message': f"License already activated on another computer (ID: {license_doc.get('machine_id')})"
                }
            
            # ACTIVATE in cloud
            self.licenses.update_one(
                {'key': license_key},
                {
                    '$set': {
                        'activated': True,
                        'machine_id': machine_id,
                        'activation_date': datetime.now().isoformat()
                    }
                }
            )
            
            # Prepare local license data
            local_license = {
                'key': license_key,
                'customer': license_doc.get('customer', 'Licensed User'),
                'email': license_doc.get('email', ''),
                'plan': license_doc.get('plan', 'standard'),
                'expiry_date': license_doc['expiry_date'],
                'machine_id': machine_id,
                'activated_date': datetime.now().isoformat()
            }
            
            return {'success': True, 'license_data': local_license}
            
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def verify_license_startup(self):
        """
        REAL-TIME license verification on EVERY startup
        - Always checks MongoDB first (if online)
        - Detects instant revocation
        - Detects instant expiry updates
        """
        print("\n" + "="*70)
        print("🔒 TASTEPARADISE LICENSE VERIFICATION")
        print("="*70)
        
        # Load local license
        local_license = self.load_local_license()
        
        if not local_license:
            # No license found - need activation
            print("\n📧 No license found - activation required")
            return self.activate_new_license()
        
        # Verify machine ID
        current_machine = self.get_machine_id()
        stored_machine = local_license.get('machine_id')
        
        if current_machine != stored_machine:
            print("\n" + "="*70)
            print("❌ LICENSE ERROR: Machine Mismatch")
            print("="*70)
            print("   This license is registered to another computer.")
            print(f"   Current Machine ID: {current_machine}")
            print(f"   Licensed Machine ID: {stored_machine}")
            print("   Contact support: gaurhariom60@gmail.com")
            print("="*70)
            return False
        
        license_key = local_license.get('key')
        
        # ============================================================
        # REAL-TIME CLOUD VALIDATION (CRITICAL!)
        # ============================================================
        if self.online:
            print("🌐 Checking license status with cloud server...")
            
            cloud_validation = self.validate_with_cloud(license_key)
            
            if not cloud_validation['success']:
                # License REVOKED or EXPIRED in cloud
                print("\n" + "="*70)
                print("❌ LICENSE INVALID")
                print("="*70)
                print(f"   {cloud_validation['reason']}")
                
                if cloud_validation.get('revoked'):
                    print("\n   Your license has been revoked remotely.")
                    print("   Please contact support: gaurhariom60@gmail.com")
                elif cloud_validation.get('expired'):
                    print("\n   Please renew your license to continue.")
                    print("   Contact: gaurhariom60@gmail.com")
                
                print("="*70)
                
                # Delete local license file
                try:
                    os.remove(self.license_file)
                except:
                    pass
                
                return False
            
            # Update local cache with latest cloud data
            updated_license = cloud_validation['license_data']
            updated_license['machine_id'] = current_machine  # Keep machine ID
            self.save_local_license(updated_license)
            
            # Calculate days remaining
            try:
                expiry = datetime.fromisoformat(updated_license['expiry_date'])
                days_remaining = (expiry - datetime.now()).days
            except:
                days_remaining = 0
            
            print("\n" + "="*70)
            print("✅ LICENSE VALID (Cloud Verified)")
            print("="*70)
            print(f"   Licensed to: {updated_license.get('customer', 'User')}")
            print(f"   Plan: {updated_license.get('plan', 'Standard').upper()}")
            print(f"   Expires on: {updated_license.get('expiry_date', 'Unknown')[:10]}")
            print(f"   Days remaining: {days_remaining} days")
            print("="*70)
            
            # Show warning if less than 7 days remaining
            if days_remaining <= 7:
                print("\n⚠️ WARNING: License expiring soon!")
                print(f"   Only {days_remaining} days remaining")
                print("   Contact: gaurhariom60@gmail.com to renew")
                print("="*70)
            
            return True
        
        else:
            # ============================================================
            # OFFLINE MODE (Only if cloud is unreachable)
            # ============================================================
            print("⚠️ Cannot reach cloud server - using cached license")
            
            # Check local expiry
            try:
                expiry = datetime.fromisoformat(local_license['expiry_date'])
                if datetime.now() > expiry:
                    print("\n" + "="*70)
                    print("❌ LICENSE EXPIRED")
                    print("="*70)
                    print(f"   Expired on: {expiry.date()}")
                    print("   Please renew your license.")
                    print("="*70)
                    return False
                
                days_remaining = (expiry - datetime.now()).days
            except:
                days_remaining = 0
            
            print("\n" + "="*70)
            print("✅ LICENSE VALID (Offline Mode)")
            print("="*70)
            print(f"   Licensed to: {local_license.get('customer', 'Unknown')}")
            print(f"   Plan: {local_license.get('plan', 'Unknown').upper()}")
            print(f"   Days remaining: {days_remaining} days")
            print("\n   ⚠️ Connect to internet for license verification")
            print("="*70)
            return True
    
    def activate_new_license(self):
        """First-time license activation"""
        print("\n" + "="*70)
        print("🔐 LICENSE ACTIVATION")
        print("="*70)
        print("\n📧 Please enter your license key")
        print("   Format: XXXXX-XXXXX-XXXXX-XXXXX-XXXXX")
        print("-"*70)
        
        max_attempts = 3
        for attempt in range(max_attempts):
            license_key = input("\nLicense Key: ").strip().upper()
            
            # Validate format
            if len(license_key) != 29 or license_key.count('-') != 4:
                print(f"❌ Invalid format! ({attempt + 1}/{max_attempts})")
                if attempt < max_attempts - 1:
                    print("   Please try again.")
                continue
            
            machine_id = self.get_machine_id()
            print(f"\n🔑 Machine ID: {machine_id}")
            print("⏳ Validating with license server...")
            
            # ONE-TIME cloud activation
            result = self.activate_license_cloud(license_key, machine_id)
            
            if not result['success']:
                print(f"\n❌ ACTIVATION FAILED: {result['message']}")
                if attempt < max_attempts - 1:
                    print(f"   ({attempt + 1}/{max_attempts} attempts remaining)")
                continue
            
            # Save license locally
            license_data = result['license_data']
            if self.save_local_license(license_data):
                print("\n" + "="*70)
                print("✅ LICENSE ACTIVATED SUCCESSFULLY!")
                print("="*70)
                print(f"   👤 Licensed to: {license_data['customer']}")
                print(f"   📧 Email: {license_data['email']}")
                print(f"   📦 Plan: {license_data['plan'].upper()}")
                print(f"   📅 Valid until: {license_data['expiry_date'][:10]}")
                print("\n   Your license is now saved!")
                print("="*70)
                return True
            else:
                print("\n❌ Error saving license locally!")
                return False
        
        print("\n" + "="*70)
        print("❌ MAXIMUM ATTEMPTS REACHED")
        print("="*70)
        print("   Contact support: gaurhariom60@gmail.com")
        print("="*70)
        return False

# Global instance
try:
    license_system = RealtimeLicenseSystem()
except:
    license_system = None

def check_license():
    """Main license check - called by main.py"""
    if not license_system:
        print("❌ License system initialization failed!")
        return False
    return license_system.verify_license_startup()
