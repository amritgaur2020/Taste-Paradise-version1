@echo off
echo Cleaning up TasteParadise project...

echo Deleting node_modules...
if exist node_modules rmdir /s /q node_modules

echo Deleting Python cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

echo Deleting build folders...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist build_old_13399 rmdir /s /q build_old_13399
if exist TasteParadise-Deploy rmdir /s /q TasteParadise-Deploy

echo Deleting venv...
if exist venv rmdir /s /q venv

echo Deleting logs and temp files...
if exist error.txt del error.txt
if exist licenses.db.json.backup del licenses.db.json.backup
del /s /q *.log 2>nul

echo.
echo ✅ Cleanup complete!
echo.
echo Your project should now be under 100 MB.
echo.
echo To reinstall dependencies:
echo 1. Backend: python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt
echo 2. Frontend: npm install
pause
