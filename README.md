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

## Config:

sudo nano /etc/ddns-client/config.yaml

```
server:
  url: "https://ddns.oiii.ir/api/v1/update"
  username: "your_client_username"  # از پنل ادمین
  password: "your_client_password"  # از پنل ادمین
  interface: "eth0"  # کارت شبکه A
```

## Test:
```
# تست دریافت IP
sudo /opt/ddns-client/ddns_client.py --test

# اجرای یکباره
sudo /opt/ddns-client/ddns_client.py --once

# مشاهده لاگ‌ها
sudo journalctl -u ddns-client.service -f
```

## Commands:
```
# راه‌اندازی/توقف
sudo systemctl start ddns-client.service
sudo systemctl stop ddns-client.service

# وضعیت
sudo systemctl status ddns-client.service

# مشاهده لاگ
sudo journalctl -u ddns-client.service -f

# ریلود config
sudo systemctl restart ddns-client.service
```


