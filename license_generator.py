"""
TasteParadise License Key Generator - OFFLINE
Generate license keys and activation codes
Author: Amrit Gaur
"""

import secrets
import string
import hashlib
import json
from datetime import datetime, timedelta

# ============================================================
# IMPORTANT: Use the SAME secret key in both generator and validator
# ============================================================
SECRET_KEY = "TasteParadise_Secret_2025_Amrit_Gaur_XYZ123"

class OfflineLicenseGenerator:
    """Generate license keys and activation codes"""
    
    def __init__(self):
        self.secret_key = SECRET_KEY
        self.chars = string.ascii_uppercase + string.digits
    
    def generate_license_key(self):
        """Generate random license key: XXXXX-XXXXX-XXXXX-XXXXX-XXXXX"""
        segments = []
        for _ in range(5):
            segment = ''.join(secrets.choice(self.chars) for _ in range(5))
            segments.append(segment)
        return '-'.join(segments)
    
    def generate_activation_code(self, license_key, machine_id, expiry_days=365):
        """
        Generate activation code that binds license key to machine ID
        """
        expiry_date = (datetime.now() + timedelta(days=expiry_days)).isoformat()
        
        # Combine data
        data = f"{license_key}|{machine_id}|{expiry_date}"
        
        # Create signature using secret key
        signature = hashlib.sha256(f"{data}|{self.secret_key}".encode()).hexdigest()
        
        # Create activation code
        activation_code = f"{license_key}|{machine_id}|{expiry_date}|{signature}"
        
        return activation_code
    
    def create_license(self, customer_name, plan_type, validity_days, machine_id=None):
        """Create complete license package"""
        license_key = self.generate_license_key()
        
        license_info = {
            'license_key': license_key,
            'customer_name': customer_name,
            'plan': plan_type,
            'generated_date': datetime.now().isoformat(),
            'expiry_days': validity_days,
            'machine_id': machine_id,
            'status': 'generated' if not machine_id else 'activated'
        }
        
        # If machine ID provided, generate activation code
        if machine_id:
            activation_code = self.generate_activation_code(license_key, machine_id, validity_days)
            license_info['activation_code'] = activation_code
            license_info['expiry_date'] = (datetime.now() + timedelta(days=validity_days)).isoformat()
        
        return license_info


# ============================================================
# ADMIN PANEL
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("  🔐 TASTEPARADISE OFFLINE LICENSE GENERATOR")
    print("="*70)
    
    generator = OfflineLicenseGenerator()
    
    while True:
        print("\n" + "="*70)
        print("MENU:")
        print("  1. Generate New License Key (send to customer)")
        print("  2. Generate Activation Code (after customer sends Machine ID)")
        print("  3. Exit")
        print("="*70)
        
        choice = input("\nSelect (1-3): ").strip()
        
        if choice == '1':
            print("\n" + "-"*70)
            print("GENERATE LICENSE KEY")
            print("-"*70)
            
            customer = input("Customer Name: ").strip()
            
            print("\nPlan Types:")
            print("  1. TRIAL (7 days)")
            print("  2. BASIC (1 year)")
            print("  3. PRO (1 year)")
            print("  4. ENTERPRISE (10 years)")
            
            plan_choice = input("\nSelect Plan (1-4): ").strip()
            
            plan_map = {
                '1': ('trial', 7),
                '2': ('basic', 365),
                '3': ('pro', 365),
                '4': ('enterprise', 3650)
            }
            
            if plan_choice in plan_map:
                plan_type, days = plan_map[plan_choice]
                
                license = generator.create_license(customer, plan_type, days)
                
                print("\n" + "="*70)
                print("✅ LICENSE KEY GENERATED!")
                print("="*70)
                print(f"\n🔑 LICENSE KEY: {license['license_key']}")
                print(f"👤 Customer: {customer}")
                print(f"📦 Plan: {plan_type.upper()}")
                print(f"⏱️ Validity: {days} days")
                print("\n📧 SEND THIS TO CUSTOMER:")
                print("-"*70)
                print(f"License Key: {license['license_key']}")
                print("\nNext Steps:")
                print("1. Customer enters this license key in TasteParadise")
                print("2. Software will show their Machine ID")
                print("3. Customer sends you their Machine ID")
                print("4. You generate Activation Code (Menu Option 2)")
                print("="*70)
                
                # Save to file
                filename = f"license_{license['license_key'][:15]}.json"
                with open(filename, 'w') as f:
                    json.dump(license, f, indent=2)
                print(f"\n💾 Saved to: {filename}")
            else:
                print("❌ Invalid choice!")
        
        elif choice == '2':
            print("\n" + "-"*70)
            print("GENERATE ACTIVATION CODE")
            print("-"*70)
            
            license_key = input("License Key: ").strip()
            machine_id = input("Machine ID (from customer): ").strip()
            
            if len(license_key) != 29:
                print("❌ Invalid license key format! Should be XXXXX-XXXXX-XXXXX-XXXXX-XXXXX")
                continue
            
            if len(machine_id) != 16:
                print("❌ Invalid machine ID format! Should be 16 characters.")
                continue
            
            days_input = input("Validity (days, default 365): ").strip()
            days = int(days_input) if days_input else 365
            
            activation_code = generator.generate_activation_code(license_key, machine_id, days)
            
            print("\n" + "="*70)
            print("✅ ACTIVATION CODE GENERATED!")
            print("="*70)
            print(f"\n🔓 ACTIVATION CODE:")
            print(f"{activation_code}")
            print("\n📧 SEND THIS TO CUSTOMER:")
            print("-"*70)
            print("Your TasteParadise activation code:")
            print(f"{activation_code}")
            print("\nInstructions:")
            print("1. Open TasteParadise")
            print("2. Enter this activation code when prompted")
            print("3. Your software will be activated!")
            print("="*70)
            
            # Copy to clipboard instructions
            print("\n💡 TIP: Copy the activation code above and send via email/WhatsApp")
        
        elif choice == '3':
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice!")
