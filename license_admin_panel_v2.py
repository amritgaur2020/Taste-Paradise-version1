"""
License Admin Panel V2 - FIXED MongoDB Atlas Connection
Works with mobile hotspot, WiFi, and all networks
Author: Amrit Gaur
"""

import sys
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import time

# MongoDB Atlas Configuration
ATLAS_MONGO_URI = "mongodb+srv://gaurhariom60_db_user:S4J2vvbZLbrRAlP7@cluster01.7o6we1z.mongodb.net/tasteparadise?retryWrites=true&w=majority&appName=cluster01"

class LicenseAdmin:
    """MongoDB Atlas License Management - Network Optimized"""
    
    def __init__(self):
        """Connect to MongoDB Atlas with retry logic"""
        print("\n" + "="*70)
        print("    🔐 TASTEPARADISE LICENSE ADMIN PANEL V2")
        print("="*70)
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"\n⏳ Connecting to MongoDB Atlas... (Attempt {attempt + 1}/{max_retries})")
                print("   Please wait 10-15 seconds...")
                
                self.client = MongoClient(
                    ATLAS_MONGO_URI,
                    serverSelectionTimeoutMS=20000,  # 20 second timeout
                    connectTimeoutMS=20000,
                    socketTimeoutMS=20000,
                    retryWrites=True,
                    w='majority'
                )
                
                # Test connection
                self.client.admin.command('ping')
                
                self.db = self.client['tasteparadise']
                self.licenses = self.db['licenses']
                
                print("✅ Connected to license server successfully!\n")
                return
                
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                if attempt < max_retries - 1:
                    print(f"⚠️  Connection failed. Retrying in 3 seconds...")
                    time.sleep(3)
                    continue
                else:
                    print("\n" + "="*70)
                    print("❌ CONNECTION FAILED AFTER 3 ATTEMPTS")
                    print("="*70)
                    print("\n🔍 Troubleshooting:")
                    print("  1. Check internet connection")
                    print("  2. Try using mobile hotspot")
                    print("  3. Disable VPN if using one")
                    print("  4. Check if MongoDB Atlas is accessible")
                    print("\n📌 Alternative: Use MongoDB Atlas Web Interface")
                    print("   URL: https://cloud.mongodb.com/")
                    print("="*70)
                    
                    # Ask if user wants to continue in VIEW-ONLY mode
                    print("\n❓ Continue in VIEW-ONLY mode? (view local backup)")
                    choice = input("   Enter 'yes' to continue: ").strip().lower()
                    
                    if choice == 'yes':
                        self.client = None
                        self.offline_mode = True
                        print("\n✅ Running in offline mode (view-only)")
                        return
                    else:
                        sys.exit(1)
            
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                sys.exit(1)
    
    def generate_license(self, customer_name, plan_type, duration_days, max_devices=1):
        """Generate new license"""
        if self.offline_mode:
            print("❌ Cannot generate license in offline mode!")
            return None
        
        try:
            from license_generator import LicenseGenerator
            
            generator = LicenseGenerator()
            license_data = generator.generate_license(
                customer_name=customer_name,
                plan_type=plan_type,
                duration_days=duration_days,
                max_devices=max_devices
            )
            
            # Add to cloud database
            license_doc = {
                'key': license_data['key'],
                'customer_name': customer_name,
                'plan': plan_type,
                'generated_date': datetime.now().isoformat(),
                'expiry_date': license_data['expiry_date'],
                'max_devices': max_devices,
                'revoked': False,
                'hardware_id': None
            }
            
            self.licenses.insert_one(license_doc)
            
            return license_data
            
        except Exception as e:
            print(f"❌ Error generating license: {e}")
            return None
    
    def list_all_licenses(self):
        """List all licenses from cloud"""
        if self.offline_mode:
            # Load from backup file
            try:
                import json
                with open('licenses_db.json.backup', 'r') as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
            except:
                return []
        
        try:
            return list(self.licenses.find().sort('generated_date', -1))
        except Exception as e:
            print(f"❌ Error fetching licenses: {e}")
            return []
    
    def get_license(self, license_key):
        """Get specific license"""
        if self.offline_mode:
            licenses = self.list_all_licenses()
            for lic in licenses:
                if lic.get('key') == license_key:
                    return lic
            return None
        
        try:
            return self.licenses.find_one({'key': license_key})
        except Exception as e:
            print(f"❌ Error fetching license: {e}")
            return None
    
    def revoke_license(self, license_key):
        """Revoke a license"""
        if self.offline_mode:
            print("❌ Cannot revoke license in offline mode!")
            return False
        
        try:
            result = self.licenses.update_one(
                {'key': license_key},
                {'$set': {'revoked': True, 'revoked_date': datetime.now().isoformat()}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"❌ Error revoking license: {e}")
            return False
    
    def extend_license(self, license_key, additional_days):
        """Extend license expiry"""
        if self.offline_mode:
            print("❌ Cannot extend license in offline mode!")
            return False
        
        try:
            license_doc = self.licenses.find_one({'key': license_key})
            if not license_doc:
                return False
            
            # Parse current expiry
            current_expiry = datetime.fromisoformat(license_doc['expiry_date'])
            new_expiry = current_expiry + timedelta(days=additional_days)
            
            result = self.licenses.update_one(
                {'key': license_key},
                {'$set': {'expiry_date': new_expiry.isoformat()}}
            )
            
            return result.modified_count > 0
        except Exception as e:
            print(f"❌ Error extending license: {e}")
            return False
    
    offline_mode = False

def display_license(license_doc):
    """Display license details"""
    print("\n" + "-"*70)
    print(f"📋 License Key: {license_doc['key']}")
    print(f"👤 Customer: {license_doc.get('customer_name', license_doc.get('customer', 'N/A'))}")
    print(f"📦 Plan: {license_doc.get('plan', 'N/A')}")
    print(f"📅 Generated: {license_doc.get('generated_date', license_doc.get('issued_date', 'N/A'))[:10]}")
    print(f"⏰ Expires: {license_doc.get('expiry_date', 'N/A')[:10]}")
    print(f"💻 Max Devices: {license_doc.get('max_devices', license_doc.get('max_activations', 1))}")
    
    is_revoked = license_doc.get('revoked', False)
    is_activated = license_doc.get('activated', False)
    
    status_parts = []
    if is_revoked:
        status_parts.append('❌ REVOKED')
    elif is_activated:
        status_parts.append('✅ Active & Activated')
    else:
        status_parts.append('🟡 Generated (Not Activated)')
    
    print(f"🔒 Status: {' | '.join(status_parts)}")
    
    if license_doc.get('machine_id') and license_doc.get('machine_id') != 'null':
        print(f"🖥️  Machine ID: {license_doc['machine_id']}")
    
    print("-"*70)

def main():
    """Main admin panel"""
    
    admin = LicenseAdmin()
    
    while True:
        print("\n" + "="*70)
        print("📋 MENU:")
        print("  1. Generate New License" + (" (OFFLINE - Disabled)" if admin.offline_mode else ""))
        print("  2. View All Licenses")
        print("  3. Revoke License" + (" (OFFLINE - Disabled)" if admin.offline_mode else ""))
        print("  4. Extend License" + (" (OFFLINE - Disabled)" if admin.offline_mode else ""))
        print("  5. View License Details")
        print("  6. Export License List")
        print("  7. Exit")
        print("="*70)
        
        choice = input("\n👉 Select (1-7): ").strip()
        
        if choice == '1':
            if admin.offline_mode:
                print("\n❌ Cannot generate license in offline mode!")
                print("   Please connect to internet and restart.")
                continue
            
            # Generate new license
            print("\n" + "-"*70)
            print("GENERATE NEW LICENSE")
            print("-"*70)
            
            customer_name = input("Customer Name: ").strip()
            
            if not customer_name:
                print("❌ Customer name is required!")
                continue
            
            print("\nPlan Types:")
            print("  1. FREE (7 days)")
            print("  2. MONTHLY (30 days)")
            print("  3. YEARLY (365 days)")
            print("  4. LIFETIME (10000 days)")
            
            plan_choice = input("\nSelect Plan (1-4): ").strip()
            
            plan_map = {
                '1': ('FREE', 7),
                '2': ('MONTHLY', 30),
                '3': ('YEARLY', 365),
                '4': ('LIFETIME', 10000)
            }
            
            if plan_choice not in plan_map:
                print("❌ Invalid plan selection!")
                continue
            
            plan_type, duration = plan_map[plan_choice]
            
            max_devices = input("Max Devices (default: 1): ").strip() or "1"
            
            try:
                max_devices = int(max_devices)
            except:
                max_devices = 1
            
            print("\n⏳ Generating license...")
            
            license_data = admin.generate_license(
                customer_name=customer_name,
                plan_type=plan_type,
                duration_days=duration,
                max_devices=max_devices
            )
            
            if license_data:
                print("\n" + "="*70)
                print("✅ LICENSE GENERATED SUCCESSFULLY!")
                print("="*70)
                print(f"\n🔑 LICENSE KEY: {license_data['key']}")
                print(f"👤 Customer: {customer_name}")
                print(f"📦 Plan: {plan_type}")
                print(f"📅 Valid Until: {license_data['expiry_date'][:10]}")
                print(f"💻 Max Devices: {max_devices}")
                print("\n📧 Send this license key to the customer!")
                print("="*70)
        
        elif choice == '2':
            # View all licenses
            print("\n" + "-"*70)
            print("ALL LICENSES" + (" (OFFLINE MODE - Viewing Backup)" if admin.offline_mode else ""))
            print("-"*70)
            
            licenses = admin.list_all_licenses()
            
            if not licenses:
                print("\n⚠️  No licenses found.")
            else:
                print(f"\n📊 Found {len(licenses)} licenses:\n")
                for license_doc in licenses:
                    display_license(license_doc)
        
        elif choice == '3':
            if admin.offline_mode:
                print("\n❌ Cannot revoke license in offline mode!")
                continue
            
            # Revoke license
            print("\n" + "-"*70)
            print("REVOKE LICENSE")
            print("-"*70)
            
            license_key = input("\nEnter License Key: ").strip()
            
            if not license_key:
                print("❌ License key is required!")
                continue
            
            confirm = input(f"\n⚠️  Revoke license {license_key[:20]}...? (yes/no): ").strip().lower()
            
            if confirm == 'yes':
                if admin.revoke_license(license_key):
                    print("\n✅ License revoked successfully!")
                    print("   Customer's app will stop working on next cloud check.")
                else:
                    print("\n❌ Failed to revoke license. Check if key exists.")
            else:
                print("\n❌ Revocation cancelled.")
        
        elif choice == '4':
            if admin.offline_mode:
                print("\n❌ Cannot extend license in offline mode!")
                continue
            
            # Extend license
            print("\n" + "-"*70)
            print("EXTEND LICENSE")
            print("-"*70)
            
            license_key = input("\nEnter License Key: ").strip()
            
            if not license_key:
                print("❌ License key is required!")
                continue
            
            # Show current license
            license_doc = admin.get_license(license_key)
            if not license_doc:
                print("\n❌ License not found!")
                continue
            
            display_license(license_doc)
            
            days = input("\nExtend by how many days? ").strip()
            
            try:
                days = int(days)
            except:
                print("❌ Invalid number of days!")
                continue
            
            if admin.extend_license(license_key, days):
                print(f"\n✅ License extended by {days} days!")
                print("   Customer will receive updated expiry on next cloud check.")
            else:
                print("\n❌ Failed to extend license.")
        
        elif choice == '5':
            # View license details
            print("\n" + "-"*70)
            print("LICENSE DETAILS")
            print("-"*70)
            
            license_key = input("\nEnter License Key: ").strip()
            
            if not license_key:
                print("❌ License key is required!")
                continue
            
            license_doc = admin.get_license(license_key)
            
            if license_doc:
                display_license(license_doc)
            else:
                print("\n❌ License not found!")
        
        elif choice == '6':
            # Export license list
            print("\n" + "-"*70)
            print("EXPORT LICENSE LIST")
            print("-"*70)
            
            filename = f"licenses_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            try:
                licenses = admin.list_all_licenses()
                
                with open(filename, 'w') as f:
                    f.write("="*70 + "\n")
                    f.write("TASTEPARADISE LICENSE LIST\n")
                    f.write(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    if admin.offline_mode:
                        f.write("MODE: Offline (Backup Data)\n")
                    f.write("="*70 + "\n\n")
                    
                    for lic in licenses:
                        f.write(f"License Key: {lic['key']}\n")
                        f.write(f"Customer: {lic.get('customer_name', lic.get('customer', 'N/A'))}\n")
                        f.write(f"Plan: {lic.get('plan', 'N/A')}\n")
                        f.write(f"Expires: {lic.get('expiry_date', 'N/A')[:10]}\n")
                        f.write(f"Status: {'REVOKED' if lic.get('revoked') else 'Active'}\n")
                        f.write("-"*70 + "\n\n")
                
                print(f"\n✅ Exported to: {filename}")
                print(f"   Total licenses: {len(licenses)}")
                
            except Exception as e:
                print(f"\n❌ Export failed: {e}")
        
        elif choice == '7':
            # Exit
            print("\n👋 Goodbye!")
            break
        
        else:
            print("\n❌ Invalid choice! Please select 1-7.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
