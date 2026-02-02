# DDNS Client - Directory Structure

```
ddns-client/
├── config.yaml              # Configuration file
├── ddns_client.py           # Main application
├── requirements.txt         # Python dependencies
├── install.sh               # Installation script
├── uninstall.sh             # Uninstallation script
├── systemd/                 # systemd service files
│   ├── ddns-client.service
│   └── ddns-client.timer
└── logs/                    # Log files directory
```

## File Descriptions

- **config.yaml** - Configuration file for DDNS client settings
- **ddns_client.py** - Main application script
- **requirements.txt** - Python dependencies list
- **install.sh** - Installation script for setting up the service
- **uninstall.sh** - Uninstallation script for removing the service
- **systemd/** - Directory containing systemd service files
  - **ddns-client.service** - systemd service unit file
  - **ddns-client.timer** - systemd timer unit file
- **logs/** - Directory for storing log files

## Inistall:
```

# کلون کردن یا دانلود فایل‌ها
git clone https://github.com/yourusername/ddns-client.git
cd ddns-client

# اعطای مجوز اجرا
chmod +x install.sh ddns_client.py

# نصب
sudo ./install.sh

```
