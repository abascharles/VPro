# VideoPlayerPro.spec - Windows PyInstaller Configuration
# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

block_cipher = None

# Get the current directory
current_dir = Path(SPECPATH)

# Define data files to include
datas = [
    (str(current_dir / "assets"), "assets"),
    (str(current_dir / "src"), "src"),
]

# Hidden imports for PyQt6 and video processing
hiddenimports = [
    # PyQt6 core modules
    'PyQt6.QtCore',
    'PyQt6.QtWidgets',
    'PyQt6.QtGui',
    'PyQt6.QtMultimedia',
    
    # Video processing
    'cv2',
    'numpy',
    'PIL',
    'PIL.Image',
    'PIL.ImageSequence',
    'PIL.ImageFile',
    
    # MoviePy and dependencies
    'moviepy',
    'moviepy.editor',
    'moviepy.video.io.VideoFileClip',
    'moviepy.video.fx',
    'moviepy.audio.fx',
    
    # Image processing
    'imageio',
    'imageio_ffmpeg',
    'imageio.plugins',
    'imageio.plugins.ffmpeg',
    
    # File operations
    'send2trash',
    
    # Performance
    'numba',
    'psutil',
    
    # Additional PyQt6 modules that might be needed
    'PyQt6.QtNetwork',
    'PyQt6.QtPrintSupport',
    'PyQt6.QtSvg',
    'PyQt6.QtOpenGL',
    
    # Codec support
    'numpy.core._methods',
    'numpy.lib.format',
    
    # Other potential dependencies
    'pkg_resources',
    'pkg_resources.py2_warn',
    'packaging',
    'packaging.version',
    'packaging.specifiers',
    'packaging.requirements',
]

# Analysis configuration
a = Analysis(
    ['main.py'],
    pathex=[str(current_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'tkinter',
        'matplotlib',
        'scipy',
        'pandas',
        'jupyter',
        'IPython',
        'test',
        'unittest',
        'pdb',
        'doctest',
        'sqlite3',
        'xml',
        'xmlrpc',
        'http',
        'urllib',
        'email',
        'ftplib',
        'imaplib',
        'poplib',
        'smtplib',
        'telnetlib',
        'calendar',
        'pickle',
        'shelve',
        'dbm',
        'gzip',
        'tarfile',
        'zipfile',
        'bz2',
        'lzma',
        'zlib',
        'ctypes.test',
        'distutils',
        'ensurepip',
        'lib2to3',
        'pydoc_data',
        'turtledemo',
        'multiprocessing',
        'concurrent.futures',
        'asyncio',
        'tornado',
        'django',
        'flask',
        'requests',
        'urllib3',
        'certifi',
        'charset_normalizer',
        'idna',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Create PYZ archive
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Create executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VideoPlayerPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Use UPX compression if available
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(current_dir / 'assets' / 'vproplayer.ico'),
    version_file=None,
)