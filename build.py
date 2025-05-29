import PyInstaller.__main__
import sys
import os

def create_exe():
    # Ensure the dist directory exists
    if not os.path.exists('dist'):
        os.makedirs('dist')
        
    PyInstaller.__main__.run([
        'lunar.py',
        '--onefile',
        '--noconsole',
        '--add-data', 'lib/best.pt;lib',
        '--add-data', 'lib/config;lib/config',
        '--icon=lib/icon.ico',
        '--name=LunarVision',
        '--clean',
        '--windowed'
    ])

if __name__ == "__main__":
    create_exe()