#!/bin/bash
# DDNS Client Installer
# Usage: sudo ./install.sh

set -e

# رنگ‌ها برای خروجی
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}DDNS Client Installer${NC}"
echo "========================="

# بررسی root بودن
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (sudo)${NC}"
    exit 1
fi

# مسیر نصب
INSTALL_DIR="/opt/ddns-client"
CONFIG_DIR="/etc/ddns-client"
LOG_DIR="/var/log/ddns-client"
SYSTEMD_DIR="/etc/systemd/system"

echo "Installation directory: $INSTALL_DIR"
echo "Configuration directory: $CONFIG_DIR"
echo "Log directory: $LOG_DIR"

# ایجاد دایرکتوری‌ها
echo -e "\n${YELLOW}Creating directories...${NC}"
mkdir -p $INSTALL_DIR
mkdir -p $CONFIG_DIR
mkdir -p $LOG_DIR
mkdir -p $INSTALL_DIR/systemd

# کپی فایل‌ها
echo -e "\n${YELLOW}Copying files...${NC}"
cp ddns_client.py $INSTALL_DIR/
cp requirements.txt $INSTALL_DIR/
cp systemd/ddns-client.service $INSTALL_DIR/systemd/
cp systemd/ddns-client.timer $INSTALL_DIR/systemd/

# ایجاد فایل config نمونه اگر وجود ندارد
if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
    echo -e "\n${YELLOW}Creating sample configuration...${NC}"
    cat > $CONFIG_DIR/config.yaml << EOF
# DDNS Client Configuration

server:
  url: "https://ddns.oiii.ir/api/v1/update"
  username: "CHANGE_ME"
  password: "CHANGE_ME"
  interface: "eth0"
  force_ipv4: true
  timeout: 30
  retry_count: 3
  retry_delay: 5

client:
  update_interval: 300
  log_level: "INFO"
  log_file: "/var/log/ddns-client/ddns.log"
  pid_file: "/var/run/ddns-client.pid"
  check_dns: false
  dns_server: "8.8.8.8"
  dns_timeout: 5
EOF
    echo -e "${GREEN}Sample config created at $CONFIG_DIR/config.yaml${NC}"
    echo -e "${YELLOW}Please edit the config file with your settings!${NC}"
fi

# ایجاد symlink برای config
ln -sf $CONFIG_DIR/config.yaml $INSTALL_DIR/config.yaml

# تنظیم مجوزها
echo -e "\n${YELLOW}Setting permissions...${NC}"
chown -R root:root $INSTALL_DIR
chmod 755 $INSTALL_DIR/ddns_client.py
chmod 644 $CONFIG_DIR/config.yaml
chmod 755 $LOG_DIR

# نصب Python و وابستگی‌ها
echo -e "\n${YELLOW}Installing Python dependencies...${NC}"
if command -v pip3 &> /dev/null; then
    pip3 install -r $INSTALL_DIR/requirements.txt
elif command -v pip &> /dev/null; then
    pip install -r $INSTALL_DIR/requirements.txt
else
    echo -e "${RED}pip not found. Installing pip...${NC}"
    apt-get update && apt-get install -y python3-pip
    pip3 install -r $INSTALL_DIR/requirements.txt
fi

# نصب systemd service
echo -e "\n${YELLOW}Setting up systemd service...${NC}"
cp $INSTALL_DIR/systemd/ddns-client.service $SYSTEMD_DIR/
cp $INSTALL_DIR/systemd/ddns-client.timer $SYSTEMD_DIR/

# اصلاح مسیرها در service file
sed -i "s|/opt/ddns-client|$INSTALL_DIR|g" $SYSTEMD_DIR/ddns-client.service
sed -i "s|/etc/ddns-client|$CONFIG_DIR|g" $SYSTEMD_DIR/ddns-client.service

# راه‌اندازی سرویس
echo -e "\n${YELLOW}Enabling and starting service...${NC}"
systemctl daemon-reload
systemctl enable ddns-client.timer
systemctl start ddns-client.timer
systemctl start ddns-client.service

# بررسی وضعیت
echo -e "\n${YELLOW}Checking service status...${NC}"
systemctl status ddns-client.service --no-pager

echo -e "\n${GREEN}Installation completed successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Edit the configuration file: sudo nano $CONFIG_DIR/config.yaml"
echo "2. Set your username and password"
echo "3. Set the correct network interface"
echo "4. Restart the service: sudo systemctl restart ddns-client.service"
echo ""
echo "Useful commands:"
echo "  Check logs: sudo journalctl -u ddns-client.service -f"
echo "  Run once: sudo $INSTALL_DIR/ddns_client.py --once"
echo "  Test config: sudo $INSTALL_DIR/ddns_client.py --test"
