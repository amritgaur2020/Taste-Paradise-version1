@echo off
setlocal enabledelayedexpansion

cd /d "D:\TasteParadise-Standalone (2)\TasteParadise-Standalone"

echo ╔════════════════════════════════════════════════╗
echo ║  TASTEPARADISE - MONGODB BINARY RESTORATION   ║
echo ╚════════════════════════════════════════════════╝
echo.

REM Use the backup MongoDB files we have
echo 📁 Restoring MongoDB binaries from backup...

REM Create bin folder
mkdir mongodb\bin 2>nul

REM Copy from the distributions backup (if it exists)
REM Or check old mongodb files
if exist "mongodb_backup" (
    copy "mongodb_backup\bin\mongod.exe" "mongodb\bin\" >nul 2>&1
    copy "mongodb_backup\bin\mongos.exe" "mongodb\bin\" >nul 2>&1
    echo ✅ Restored from backup!
) else (
    REM Use local installation if available
    echo ⚠️  Looking for MongoDB in system...
    
    REM Check common installation paths
    if exist "C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe" (
        copy "C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe" "mongodb\bin\" >nul
        copy "C:\Program Files\MongoDB\Server\7.0\bin\mongos.exe" "mongodb\bin\" >nul 2>&1
        echo ✅ Copied from: C:\Program Files\MongoDB\Server\7.0
    ) else if exist "C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe" (
        copy "C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe" "mongodb\bin\" >nul
        copy "C:\Program Files\MongoDB\Server\6.0\bin\mongos.exe" "mongodb\bin\" >nul 2>&1
        echo ✅ Copied from: C:\Program Files\MongoDB\Server\6.0
    ) else (
        echo ❌ MongoDB not found!
        echo Please download MongoDB Community Edition from:
        echo https://www.mongodb.com/try/download/community
        pause
        exit /b 1
    )
)

echo.
echo ✅ MongoDB restoration complete!
echo.
echo Starting TasteParadise...
python main.py

pause
