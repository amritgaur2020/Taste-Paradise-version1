"""
Hardware Fingerprint Generator - STABLE & CONSISTENT
Generates SAME Machine ID for the same computer always
Author: Amrit Gaur
"""

import hashlib
import platform
import subprocess
import uuid
import os

class HardwareFingerprint:
    """Generate permanent hardware fingerprint"""
    
    def __init__(self):
        self.cache_file = ".machine_id"
    
    def get_windows_machine_guid(self):
        """Get Windows Machine GUID - NEVER CHANGES"""
        try:
            if platform.system() == "Windows":
                result = subprocess.check_output(
                    'reg query "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Cryptography" /v MachineGuid',
                    shell=True,
                    stderr=subprocess.DEVNULL
                ).decode()
                
                for line in result.split('\n'):
                    if 'MachineGuid' in line:
                        guid = line.split()[-1].strip()
                        return guid
        except:
            pass
        return None
    
    def get_motherboard_serial(self):
        """Get motherboard serial number"""
        try:
            if platform.system() == "Windows":
                result = subprocess.check_output(
                    'wmic baseboard get SerialNumber',
                    shell=True,
                    stderr=subprocess.DEVNULL
                ).decode()
                
                serial = result.split('\n')[1].strip()
                if serial and serial != 'SerialNumber' and len(serial) > 3:
                    return serial
        except:
            pass
        return None
    
    def get_cpu_id(self):
        """Get CPU ID"""
        try:
            if platform.system() == "Windows":
                result = subprocess.check_output(
                    'wmic cpu get ProcessorId',
                    shell=True,
                    stderr=subprocess.DEVNULL
                ).decode()
                
                cpu_id = result.split('\n')[1].strip()
                if cpu_id and cpu_id != 'ProcessorId':
                    return cpu_id
        except:
            pass
        return None
    
    def generate_machine_id(self):
        """
        Generate STABLE 16-character machine ID
        Same ID every time on same computer
        """
        identifiers = []
        
        # Priority 1: Windows GUID (Best - never changes)
        win_guid = self.get_windows_machine_guid()
        if win_guid:
            identifiers.append(f"GUID:{win_guid}")
        
        # Priority 2: Motherboard Serial
        mb_serial = self.get_motherboard_serial()
        if mb_serial:
            identifiers.append(f"MB:{mb_serial}")
        
        # Priority 3: CPU ID
        cpu_id = self.get_cpu_id()
        if cpu_id:
            identifiers.append(f"CPU:{cpu_id}")
        
        # Priority 4: MAC Address
        mac = hex(uuid.getnode())[2:].upper()
        identifiers.append(f"MAC:{mac}")
        
        # Priority 5: Hostname
        hostname = platform.node()
        identifiers.append(f"HOST:{hostname}")
        
        # Generate SHA256 hash
        combined = '|'.join(identifiers)
        machine_hash = hashlib.sha256(combined.encode()).hexdigest()
        
        return machine_hash[:16].upper()
    
    def get_machine_id(self):
        """Get cached machine ID or generate new one"""
        # Check cache first
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    cached_id = f.read().strip()
                    if len(cached_id) == 16:
                        return cached_id
            except:
                pass
        
        # Generate new ID
        machine_id = self.generate_machine_id()
        
        # Save to cache
        try:
            with open(self.cache_file, 'w') as f:
                f.write(machine_id)
        except:
            pass
        
        return machine_id


# Global instance
fingerprint = HardwareFingerprint()

def get_machine_id():
    """Get stable machine ID"""
    return fingerprint.get_machine_id()


if __name__ == "__main__":
    # Test
    print("\n" + "="*70)
    print("TESTING MACHINE ID STABILITY")
    print("="*70)
    
    print("\nGenerating Machine ID 5 times to verify stability:\n")
    
    ids = []
    for i in range(5):
        machine_id = get_machine_id()
        ids.append(machine_id)
        print(f"  Attempt {i+1}: {machine_id}")
    
    if len(set(ids)) == 1:
        print("\n✅ SUCCESS! Machine ID is STABLE")
        print(f"   Your Machine ID: {ids[0]}")
    else:
        print("\n❌ WARNING! Machine ID is INCONSISTENT")
    
    print("="*70)
