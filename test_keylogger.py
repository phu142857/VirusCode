#!/usr/bin/env python3
"""
Test script to diagnose keylogger issues
"""
import os
import sys
import time

print("=" * 70)
print("KEYLOGGER DIAGNOSTICS")
print("=" * 70)

# Check environment
print("\n1. Environment:")
print(f"   XDG_SESSION_TYPE: {os.environ.get('XDG_SESSION_TYPE', 'not set')}")
print(f"   WAYLAND_DISPLAY: {os.environ.get('WAYLAND_DISPLAY', 'not set')}")
print(f"   DISPLAY: {os.environ.get('DISPLAY', 'not set')}")

# Check Python path
print(f"\n2. Python:")
print(f"   Executable: {sys.executable}")
print(f"   Version: {sys.version}")

# Check libraries
print("\n3. Libraries:")
try:
    import evdev
    print("   ✅ evdev: Available")
    try:
        devices = list(evdev.list_devices())
        print(f"   ✅ evdev.list_devices(): Found {len(devices)} devices")
        if devices:
            for i, dev_path in enumerate(devices[:3], 1):
                try:
                    dev = evdev.InputDevice(dev_path)
                    print(f"      [{i}] {dev.name} ({dev_path})")
                except PermissionError:
                    print(f"      [{i}] {dev_path} - ❌ Permission denied")
                except Exception as e:
                    print(f"      [{i}] {dev_path} - ❌ Error: {e}")
    except Exception as e:
        print(f"   ❌ evdev.list_devices() failed: {e}")
except ImportError:
    print("   ❌ evdev: Not available (pip install evdev)")

try:
    from pynput import keyboard
    print("   ✅ pynput: Available")
    try:
        # Try to create a listener
        listener = keyboard.Listener(on_press=lambda k: None)
        listener.start()
        time.sleep(0.1)
        if listener.is_alive():
            print("   ✅ pynput listener: Can start")
            listener.stop()
        else:
            print("   ❌ pynput listener: Failed to start")
    except Exception as e:
        print(f"   ❌ pynput listener failed: {e}")
except ImportError:
    print("   ❌ pynput: Not available (pip install pynput)")

# Check permissions
print("\n4. Permissions:")
import subprocess
try:
    result = subprocess.run(['ls', '-l', '/dev/input/event*'], 
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                          text=True, timeout=2)
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')[:3]
        print("   Input device permissions:")
        for line in lines:
            print(f"      {line}")
    else:
        print(f"   ❌ Cannot check permissions: {result.stderr}")
except Exception as e:
    print(f"   ❌ Error checking permissions: {e}")

# Check groups
try:
    import grp
    user_groups = [g.gr_name for g in grp.getgrall() if os.getlogin() in g.gr_mem]
    user_groups.append(grp.getgrgid(os.getgid()).gr_name)
    print(f"\n5. User groups: {', '.join(user_groups)}")
    if 'input' in user_groups:
        print("   ✅ User is in 'input' group")
    else:
        print("   ❌ User is NOT in 'input' group")
        print("   Fix: sudo usermod -a -G input $USER (then logout/login)")
except Exception as e:
    print(f"\n5. Cannot check groups: {e}")

print("\n" + "=" * 70)
print("DIAGNOSTICS COMPLETE")
print("=" * 70)

