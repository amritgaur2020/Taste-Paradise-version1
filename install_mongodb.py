import urllib.request
import zipfile
import os
import shutil
import subprocess

print("=" * 50)
print("TASTEPARADISE - MONGODB AUTO INSTALLER")
print("=" * 50)

# Create bin folder
os.makedirs("mongodb/bin", exist_ok=True)

print("\nDownloading MongoDB (200 MB - 2 minutes)...")
url = "https://fastdl.mongodb.org/windows/mongodb-windows-x86_64-7.0.0.zip"
zip_file = "mongodb_temp.zip"

try:
    urllib.request.urlretrieve(url, zip_file)
    print("✅ Downloaded successfully!")
    
    print("\nExtracting...")
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(".")
    
    print("✅ Extracted!")
    
    print("\nCopying MongoDB binaries...")
    # Find and copy mongod.exe
    for root, dirs, files in os.walk("."):
        if "mongod.exe" in files:
            src = os.path.join(root, "mongod.exe")
            dst = "mongodb/bin/mongod.exe"
            shutil.copy(src, dst)
            print(f"✅ Copied mongod.exe")
        if "mongos.exe" in files:
            src = os.path.join(root, "mongos.exe")
            dst = "mongodb/bin/mongos.exe"
            shutil.copy(src, dst)
            print(f"✅ Copied mongos.exe")
    
    # Cleanup
    print("\nCleaning up...")
    os.remove(zip_file)
    for item in os.listdir("."):
        if item.startswith("mongodb-win32-"):
            shutil.rmtree(item, ignore_errors=True)
    
    print("\n" + "=" * 50)
    print("✅ MONGODB INSTALLED SUCCESSFULLY!")
    print("=" * 50)
    
    if os.path.exists("mongodb/bin/mongod.exe"):
        print("\n🚀 Starting TasteParadise...")
        os.system("python main.py")
    else:
        print("❌ Installation failed!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nPlease install MongoDB manually from:")
    print("https://www.mongodb.com/try/download/community")
