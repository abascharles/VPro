# check_setup.py - Pre-build verification script for Windows

import os
import sys
import subprocess
from pathlib import Path
import importlib.util

def print_header():
    print("=" * 60)
    print("🔍 VideoPlayerPro - Windows Build Pre-Check")
    print("=" * 60)

def check_python_version():
    """Check Python version"""
    print("📍 Checking Python version...")
    version = sys.version_info
    print(f"   Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("   ❌ Python 3.8+ required!")
        return False
    else:
        print("   ✅ Python version OK")
        return True

def check_pip():
    """Check if pip is available"""
    print("📍 Checking pip...")
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ {result.stdout.strip()}")
            return True
        else:
            print("   ❌ pip not working properly")
            return False
    except Exception as e:
        print(f"   ❌ pip not found: {e}")
        return False

def check_required_files():
    """Check if all required files exist"""
    print("📍 Checking required files...")
    
    required_files = [
        'main.py',
        'requirements.txt',
        'src/__init__.py',
        'src/core/__init__.py',
        'src/gui/__init__.py',
        'assets/vproplayer.ico'
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - MISSING")
            all_exist = False
    
    return all_exist

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("📍 Checking Python dependencies...")
    
    required_packages = [
        'PyQt6',
        'cv2',
        'numpy',
        'PIL',
        'moviepy',
        'imageio',
        'send2trash',
        'numba',
        'psutil'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            # Handle special cases
            if package == 'cv2':
                import cv2
                print(f"   ✅ OpenCV: {cv2.__version__}")
            elif package == 'PIL':
                import PIL
                print(f"   ✅ Pillow: {PIL.__version__}")
            elif package == 'PyQt6':
                import PyQt6
                try:
                    # Try to get version from PyQt6.QtCore
                    from PyQt6.QtCore import PYQT_VERSION_STR
                    print(f"   ✅ PyQt6: {PYQT_VERSION_STR}")
                except ImportError:
                    print(f"   ✅ PyQt6: installed (version unknown)")
            else:
                module = importlib.import_module(package)
                version = getattr(module, '__version__', 'unknown')
                print(f"   ✅ {package}: {version}")
        except ImportError:
            print(f"   ❌ {package} - NOT INSTALLED")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n   📦 Install missing packages with:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_pyinstaller():
    """Check if PyInstaller is installed"""
    print("📍 Checking PyInstaller...")
    
    try:
        import PyInstaller
        print(f"   ✅ PyInstaller: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("   ❌ PyInstaller not installed")
        print("   📦 Install with: pip install pyinstaller")
        return False

def check_icon_file():
    """Check icon file"""
    print("📍 Checking icon file...")
    
    icon_path = Path('assets/vproplayer.ico')
    if not icon_path.exists():
        print("   ❌ Icon file not found: assets/vproplayer.ico")
        return False
    
    # Check file size
    size = icon_path.stat().st_size
    if size == 0:
        print("   ❌ Icon file is empty")
        return False
    elif size > 1024 * 1024:  # 1MB
        print(f"   ⚠️  Icon file is large: {size:,} bytes")
        print("   Consider optimizing for smaller executable size")
    
    # Try to open with PIL to verify it's a valid image
    try:
        from PIL import Image
        with Image.open(icon_path) as img:
            print(f"   ✅ Icon file OK: {img.size[0]}x{img.size[1]}, {img.mode}")
    except Exception as e:
        print(f"   ❌ Icon file corrupted: {e}")
        return False
    
    return True

def check_disk_space():
    """Check available disk space"""
    print("📍 Checking disk space...")
    
    import shutil
    free_bytes = shutil.disk_usage('.').free
    free_mb = free_bytes / (1024 * 1024)
    
    if free_mb < 500:  # Less than 500MB
        print(f"   ⚠️  Low disk space: {free_mb:.1f} MB available")
        print("   Build may fail due to insufficient space")
        return False
    else:
        print(f"   ✅ Disk space OK: {free_mb:.1f} MB available")
        return True

def suggest_fixes():
    """Suggest fixes for common issues"""
    print("\n🔧 Common Setup Issues and Fixes:")
    print("━" * 60)
    
    print("1. Python not found:")
    print("   • Download from https://python.org")
    print("   • Check 'Add Python to PATH' during installation")
    print("   • Restart command prompt after installation")
    
    print("\n2. Dependencies not installed:")
    print("   • Run: pip install -r requirements.txt")
    print("   • If still issues: python -m pip install --upgrade pip")
    
    print("\n3. PyInstaller not found:")
    print("   • Run: pip install pyinstaller")
    print("   • Or: python -m pip install pyinstaller")
    
    print("\n4. Icon file issues:")
    print("   • Ensure assets/vproplayer.ico exists")
    print("   • Use online converter if needed: convertio.co/png-ico")
    print("   • Recommended sizes: 16x16, 32x32, 48x48, 64x64, 128x128, 256x256")

def main():
    print_header()
    
    checks = [
        ("Python Version", check_python_version),
        ("Pip Available", check_pip),
        ("Required Files", check_required_files),
        ("Dependencies", check_dependencies),
        ("PyInstaller", check_pyinstaller),
        ("Icon File", check_icon_file),
        ("Disk Space", check_disk_space),
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        if check_func():
            passed += 1
        print()  # Empty line between checks
    
    print("=" * 60)
    print(f"📊 SUMMARY: {passed}/{total} checks passed")
    print("=" * 60)
    
    if passed == total:
        print("🎉 ALL CHECKS PASSED!")
        print("✅ Your system is ready for building VideoPlayerPro")
        print("\nNext steps:")
        print("1. Run: pyinstaller --name='VideoPlayerPro' --windowed --onefile --icon='assets\\vproplayer.ico' main.py")
        print("2. Edit VideoPlayerPro.spec file with optimized settings")
        print("3. Run: pyinstaller --clean VideoPlayerPro.spec")
        return True
    else:
        failed = total - passed
        print(f"❌ {failed} CHECK(S) FAILED")
        print("Please fix the issues above before building")
        suggest_fixes()
        return False

if __name__ == "__main__":
    success = main()
    
    input("\nPress Enter to exit...")
    
    sys.exit(0 if success else 1)