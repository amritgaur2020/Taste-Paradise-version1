"""
TasteParadise License Generator
USE THIS TO GENERATE LICENSE KEYS FOR CUSTOMERS
Keep this file SECRET - don't give to customers!

Author: Your Name
Created: October 2025
"""

import hashlib
import json
import secrets
from datetime import datetime, timedelta
from pathlib import Path

SECRET_KEY = "TasteParadise_Secret_2025_UTU_Project"  # Must match license_system.py!

class LicenseGenerator:
    """Generate license keys for customers"""
    
    def __init__(self):
        self.secret_key = SECRET_KEY
        self.db_file = Path("licenses_db.json")
        self._init_database()
    
    def _init_database(self):
        """Create database file if it doesn't exist"""
        if not self.db_file.exists():
            with open(self.db_file, 'w') as f:
                json.dump([], f)
    
    def generate_license(self, customer_name, email, phone="", plan="basic", duration_days=365):
        """
        Generate a new license key
        
        Args:
            customer_name: Restaurant name (e.g., "Maharaja Restaurant")
            email: Customer email
            phone: Customer phone (optional)
            plan: "basic", "pro", or "enterprise"
            duration_days: Validity period (365 = 1 year, 730 = 2 years)
        
        Returns:
            license_key: The generated key (format: XXXXX-XXXXX-XXXXX-XXXXX-XXXXX)
            license_data: Full license information dictionary
        """
        # Create license data
        license_data = {
            'customer': customer_name,
            'email': email,
            'phone': phone,
            'plan': plan,
            'issued_date': datetime.now().isoformat(),
            'expiry_date': (datetime.now() + timedelta(days=duration_days)).isoformat(),
            'max_activations': 1,  # Can only use on 1 computer
            'duration_days': duration_days
        }
        
        # Generate unique license ID (16 characters)
        license_id = secrets.token_hex(8).upper()
        
        # Create signature (12 characters)
        signature = self._create_signature(license_data)
        
        # Combine: ID (16) + Signature (9) = 25 characters total
        combined = (license_id + signature)[:25]
        
        # Format as XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
        license_key = '-'.join([combined[i:i+5] for i in range(0, 25, 5)])
        
        # Save to database
        self._save_to_database(license_key, license_data)
        
        return license_key, license_data
    
    def _create_signature(self, data):
        """Create cryptographic signature that can't be forged"""
        data_string = json.dumps({
            'customer': data['customer'],
            'plan': data['plan'],
        }, sort_keys=True)
        
        message = f"{data_string}:{self.secret_key}"
        return hashlib.sha256(message.encode()).hexdigest()[:12].upper()
    
    def _save_to_database(self, key, data):
        """Save license to database"""
        # Load existing licenses
        try:
            with open(self.db_file, 'r') as f:
                licenses = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            licenses = []
        
        # Add new license
        record = {
            'key': key,
            **data,
            'activated': False,
            'machine_id': None,
            'activation_date': None,
            'generated_date': datetime.now().isoformat()
        }
        licenses.append(record)
        
        # Save back
        with open(self.db_file, 'w') as f:
            json.dump(licenses, f, indent=2)
    
    def list_licenses(self, filter_plan=None, filter_activated=None):
        """
        List all generated licenses with optional filters
        
        Args:
            filter_plan: Filter by plan ("basic", "pro", "enterprise")
            filter_activated: Filter by activation status (True/False)
        """
        try:
            with open(self.db_file, 'r') as f:
                licenses = json.load(f)
            
            # Apply filters
            if filter_plan:
                licenses = [l for l in licenses if l.get('plan') == filter_plan]
            
            if filter_activated is not None:
                licenses = [l for l in licenses if l.get('activated') == filter_activated]
            
            return licenses
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def get_license_details(self, license_key):
        """Get details of a specific license"""
        licenses = self.list_licenses()
        for lic in licenses:
            if lic['key'] == license_key:
                return lic
        return None
    
    def revoke_license(self, license_key):
        """Revoke/disable a license"""
        try:
            with open(self.db_file, 'r') as f:
                licenses = json.load(f)
            
            found = False
            for lic in licenses:
                if lic['key'] == license_key:
                    lic['revoked'] = True
                    lic['revoked_date'] = datetime.now().isoformat()
                    found = True
                    break
            
            if found:
                with open(self.db_file, 'w') as f:
                    json.dump(licenses, f, indent=2)
                return True
            return False
        except Exception as e:
            print(f"Error revoking license: {e}")
            return False


def print_header():
    """Print application header"""
    print("\n" + "="*70)
    print(" "*15 + "TASTEPARADISE LICENSE GENERATOR")
    print(" "*20 + "For Internal Use Only")
    print("="*70)


def main():
    """Interactive license generation"""
    generator = LicenseGenerator()
    
    while True:
        print_header()
        print("\n📋 MENU:")
        print("  1. Generate New License")
        print("  2. View All Licenses")
        print("  3. View License Details")
        print("  4. Revoke License")
        print("  5. View Statistics")
        print("  6. Exit")
        
        choice = input("\n👉 Select option (1-6): ").strip()
        
        if choice == "1":
            # Generate New License
            print("\n" + "-"*70)
            print("GENERATE NEW LICENSE")
            print("-"*70)
            
            customer = input("Restaurant Name: ").strip()
            if not customer:
                print("❌ Customer name is required!")
                continue
            
            email = input("Customer Email: ").strip()
            phone = input("Customer Phone (optional): ").strip()
            
            print("\n📦 PLANS:")
            print("  1. Basic   - ₹10,000 (1 year)")
            print("  2. Pro     - ₹45,000 (1 year)")
            print("  3. Enterprise - ₹99,000 (lifetime/10 years)")
            
            plan_choice = input("\nSelect plan (1/2/3): ").strip()
            plan_map = {"1": "basic", "2": "pro", "3": "enterprise"}
            plan = plan_map.get(plan_choice, "basic")
            
            # Set duration
            if plan == "enterprise":
                duration = 3650  # 10 years
            else:
                duration_input = input("Duration in days (default 365 for 1 year): ").strip()
                duration = int(duration_input) if duration_input.isdigit() else 365
            
            # Generate
            print("\n⏳ Generating license...")
            key, data = generator.generate_license(customer, email, phone, plan, duration)
            
            print("\n" + "="*70)
            print("✅ LICENSE GENERATED SUCCESSFULLY!")
            print("="*70)
            print(f"🏪 Customer: {data['customer']}")
            print(f"📧 Email: {data['email']}")
            if data['phone']:
                print(f"📱 Phone: {data['phone']}")
            print(f"📦 Plan: {data['plan'].upper()}")
            print(f"📅 Valid Until: {data['expiry_date'][:10]}")
            print(f"\n🔑 LICENSE KEY:")
            print(f"   {key}")
            print("\n📧 Send this key to customer via email/WhatsApp")
            print("="*70)
            input("\nPress Enter to continue...")
        
        elif choice == "2":
            # View All Licenses
            licenses = generator.list_licenses()
            
            print("\n" + "="*70)
            print(f"ALL LICENSES (Total: {len(licenses)})")
            print("="*70)
            
            if not licenses:
                print("\n⚠️  No licenses generated yet.")
            else:
                for i, lic in enumerate(licenses, 1):
                    status = "✅ Activated" if lic.get('activated') else "⏳ Not Activated"
                    revoked = " (🚫 REVOKED)" if lic.get('revoked') else ""
                    
                    print(f"\n{i}. {lic['customer']}")
                    print(f"   Key: {lic['key']}")
                    print(f"   Plan: {lic['plan'].upper()} | Status: {status}{revoked}")
                    print(f"   Expires: {lic['expiry_date'][:10]}")
            
            input("\nPress Enter to continue...")
        
        elif choice == "3":
            # View License Details
            license_key = input("\nEnter License Key: ").strip().upper()
            details = generator.get_license_details(license_key)
            
            if details:
                print("\n" + "="*70)
                print("LICENSE DETAILS")
                print("="*70)
                print(f"🔑 Key: {details['key']}")
                print(f"🏪 Customer: {details['customer']}")
                print(f"📧 Email: {details['email']}")
                if details.get('phone'):
                    print(f"📱 Phone: {details['phone']}")
                print(f"📦 Plan: {details['plan'].upper()}")
                print(f"📅 Issued: {details['issued_date'][:10]}")
                print(f"📅 Expires: {details['expiry_date'][:10]}")
                print(f"✅ Activated: {'Yes' if details.get('activated') else 'No'}")
                if details.get('activated'):
                    print(f"🖥️  Machine ID: {details.get('machine_id', 'N/A')}")
                    print(f"📅 Activation Date: {details.get('activation_date', 'N/A')[:10]}")
                if details.get('revoked'):
                    print(f"🚫 REVOKED on {details.get('revoked_date', 'N/A')[:10]}")
                print("="*70)
            else:
                print("\n❌ License not found!")
            
            input("\nPress Enter to continue...")
        
        elif choice == "4":
            # Revoke License
            license_key = input("\nEnter License Key to Revoke: ").strip().upper()
            confirm = input(f"⚠️  Are you sure you want to revoke {license_key}? (yes/no): ").strip().lower()
            
            if confirm == "yes":
                if generator.revoke_license(license_key):
                    print("\n✅ License revoked successfully!")
                else:
                    print("\n❌ License not found!")
            else:
                print("\n❌ Revocation cancelled.")
            
            input("\nPress Enter to continue...")
        
        elif choice == "5":
            # Statistics
            licenses = generator.list_licenses()
            total = len(licenses)
            activated = len([l for l in licenses if l.get('activated')])
            not_activated = total - activated
            revoked = len([l for l in licenses if l.get('revoked')])
            
            basic = len([l for l in licenses if l.get('plan') == 'basic'])
            pro = len([l for l in licenses if l.get('plan') == 'pro'])
            enterprise = len([l for l in licenses if l.get('plan') == 'enterprise'])
            
            print("\n" + "="*70)
            print("LICENSE STATISTICS")
            print("="*70)
            print(f"\n📊 Total Licenses: {total}")
            print(f"✅ Activated: {activated}")
            print(f"⏳ Not Activated: {not_activated}")
            print(f"🚫 Revoked: {revoked}")
            print(f"\n📦 Plans:")
            print(f"   Basic: {basic}")
            print(f"   Pro: {pro}")
            print(f"   Enterprise: {enterprise}")
            print("="*70)
            
            input("\nPress Enter to continue...")
        
        elif choice == "6":
            print("\n👋 Goodbye!")
            break
        
        else:
            print("\n❌ Invalid choice! Please select 1-6.")
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
