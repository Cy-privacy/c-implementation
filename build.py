import PyInstaller.__main__
import sys
import os
import shutil

def create_exe():
    # Clean up previous builds
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('LunarVision.spec'):
        os.remove('LunarVision.spec')
        
    # Create necessary directories
    os.makedirs('dist', exist_ok=True)
    
    # Copy required files
    if not os.path.exists('lib/config'):
        os.makedirs('lib/config')
    
    # PyInstaller configuration
    PyInstaller.__main__.run([
        'lunar.py',
        '--onefile',
        '--noconsole',
        '--add-data', 'lib/best.pt;lib',
        '--add-data', 'lib/config;lib/config',
        '--icon=lib/icon.ico',
        '--name=LunarVision',
        '--clean',
        '--windowed',
        '--hidden-import=torch',
        '--hidden-import=torchvision',
        '--hidden-import=cv2',
        '--hidden-import=numpy',
        '--hidden-import=mss',
        '--hidden-import=win32api',
        '--hidden-import=PyQt6',
        '--hidden-import=ultralytics',
        '--uac-admin',  # Request admin privileges
        '--noupx'  # Disable UPX compression for better compatibility
    ])

    print("Build complete! Executable is in the dist folder.")
    print("Note: First run might take longer as it initializes the neural network.")

if __name__ == "__main__":
    create_exe()