@echo off
setlocal enabledelayedexpansion

cd /d "D:\TasteParadise-Standalone (2)\TasteParadise-Standalone"

echo ============================================
echo TASTEPARADISE - AUTO MONGODB INSTALLER
echo ============================================
echo.

mkdir mongodb\bin 2>nul

REM Download MongoDB portable binary automatically
echo Downloading MongoDB (this takes 1-2 minutes)...
echo Please wait...
echo.

REM Create temporary directory
mkdir temp_mongo 2>nul

REM Download using PowerShell
powershell -Command ^
  "$ProgressPreference = 'SilentlyContinue'; ^
   $url = 'https://fastdl.mongodb.org/windows/mongodb-windows-x86_64-7.0.0.zip'; ^
   $output = 'temp_mongo\mongodb.zip'; ^
   [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; ^
   Invoke-WebRequest -Uri $url -OutFile $output -ErrorAction SilentlyContinue; ^
   if (Test-Path $output) { ^
     Write-Host 'Extract in progress...'; ^
     Add-Type -AssemblyName System.IO.Compression.FileSystem; ^
     [System.IO.Compression.ZipFile]::ExtractToDirectory($output, 'temp_mongo'); ^
     Write-Host 'Copying MongoDB binaries...'; ^
     Get-ChildItem 'temp_mongo\mongodb-win32-*\bin\mongod.exe' -Recurse | Copy-Item -Destination 'mongodb\bin\mongod.exe'; ^
     Get-ChildItem 'temp_mongo\mongodb-win32-*\bin\mongos.exe' -Recurse | Copy-Item -Destination 'mongodb\bin\mongos.exe' -ErrorAction SilentlyContinue; ^
     Remove-Item 'temp_mongo' -Recurse -Force; ^
     Write-Host 'SUCCESS: MongoDB installed!'; ^
   } else { ^
     Write-Host 'FAILED: Could not download MongoDB'; ^
   }"

echo.
echo Checking installation...
if exist "mongodb\bin\mongod.exe" (
    echo ✅ MongoDB successfully installed!
    echo.
    echo Starting TasteParadise...
    timeout /t 2
    python main.py
) else (
    echo ❌ Installation failed.
    echo.
    echo ALTERNATIVE: Install MongoDB manually:
    echo https://www.mongodb.com/try/download/community
    echo.
    echo Then run:
    echo python main.py
    pause
)
