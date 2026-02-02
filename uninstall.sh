#!/bin/bash
# DDNS Client Uninstaller
# Usage: sudo ./uninstall.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${RED}DDNS Client Uninstaller${NC}"
echo "=========================="

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (sudo)${NC}"
    exit 1
fi

# توقف و غیرفعال کردن سرویس
echo -e "\n${YELLOW}Stopping services...${NC}"
systemctl stop ddns-client.service ddns-client.timer 2>/dev/null || true
systemctl disable ddns-client.service ddns-client.timer 2>/dev/null || true

# حذف فایل‌های systemd
echo -e "\n${YELLOW}Removing systemd files...${NC}"
rm -f /etc/systemd/system/ddns-client.service
rm -f /etc/systemd/system/ddns-client.timer
systemctl daemon-reload

# حذف دایرکتوری‌ها
echo -e "\n${YELLOW}Removing directories...${NC}"
INSTALL_DIR="/opt/ddns-client"
CONFIG_DIR="/etc/ddns-client"
LOG_DIR="/var/log/ddns-client"

if [ -d "$INSTALL_DIR" ]; then
    rm -rf $INSTALL_DIR
    echo "Removed: $INSTALL_DIR"
fi

# فقط فایل config را حذف می‌کنیم، دایرکتوری config را نگه می‌داریم
if [ -f "$CONFIG_DIR/config.yaml" ]; then
    rm -f $CONFIG_DIR/config.yaml
    echo "Removed: $CONFIG_DIR/config.yaml"
fi

# فقط فایل‌های لاگ را حذف می‌کنیم
if [ -d "$LOG_DIR" ]; then
    rm -f $LOG_DIR/*.log
    echo "Cleared logs in: $LOG_DIR"
fi

echo -e "\n${GREEN}Uninstallation completed!${NC}"
echo "Note: User data in $CONFIG_DIR and $LOG_DIR preserved (except config.yaml)"
