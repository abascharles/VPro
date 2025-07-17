@echo off
echo.
echo ================================================================
echo          VideoPlayerPro - Windows Build Script
echo ================================================================
echo.

echo 1. Running pre-build checks...
python check_setup.py
if %errorlevel% neq 0 (
    echo.
    echo ❌ Pre-build checks failed! Please fix the issues above.
    pause
    exit /b 1
)

echo.
echo 2. Installing/Updating PyInstaller...
python -m pip install --upgrade pyinstaller

echo.
echo 3. Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo 4. Building executable...
pyinstaller --clean VideoPlayerPro.spec

if %errorlevel% neq 0 (
    echo ❌ Build failed!
    pause
    exit /b 1
)

echo.
echo 🎉 BUILD COMPLETED SUCCESSFULLY!
echo.
echo Files created:
dir dist
echo.
echo Test your executable: dist\VideoPlayerPro.exe
echo.
pause