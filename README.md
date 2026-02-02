# نصب
sudo ./install.sh

# تنظیمات
sudo nano /etc/ddns-client/config.yaml

# تست
sudo /opt/ddns-client/ddns_client.py --test

# راه‌اندازی
sudo systemctl restart ddns-client.service
