#!/usr/bin/env python3
"""
DDNS Client for DDNS Server
Author: DDNS System
Version: 1.0.0
"""

import os
import sys
import time
import json
import logging
import socket
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import yaml
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class DDNSClient:
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize DDNS Client
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = self.load_config()
        self.current_ip = None
        self.last_update = None
        self.setup_logging()
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config_path = Path(self.config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # اعتبارسنجی تنظیمات الزامی
        required_fields = [
            ('server.url', str),
            ('server.username', str),
            ('server.password', str),
            ('server.interface', str),
        ]
        
        for field, field_type in required_fields:
            if not self._get_nested(config, field):
                raise ValueError(f"Required field missing: {field}")
        
        return config
    
    def _get_nested(self, data: Dict, path: str, default=None):
        """Get nested value from dictionary using dot notation"""
        keys = path.split('.')
        for key in keys:
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                return default
        return data
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_level = self._get_nested(self.config, 'client.log_level', 'INFO')
        log_file = self._get_nested(self.config, 'client.log_file')
        
        # ایجاد دایرکتوری لاگ اگر وجود ندارد
        if log_file:
            log_dir = os.path.dirname(log_file)
            os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file) if log_file else logging.StreamHandler(),
                logging.StreamHandler()  # همیشه به کنسول هم خروجی بده
            ]
        )
        
        self.logger = logging.getLogger('ddns-client')
        self.logger.info(f"DDNS Client initialized with config: {self.config_path}")
    
    def get_interface_ip(self, interface: str = None) -> Optional[str]:
        """
        Get IP address of specific network interface
        
        Args:
            interface: Network interface name (e.g., eth0, ens3)
        
        Returns:
            IP address as string or None if not found
        """
        if interface is None:
            interface = self._get_nested(self.config, 'server.interface', 'eth0')
        
        try:
            # روش ۱: استفاده از socket (پشتیبانی از IPv4 و IPv6)
            if self._get_nested(self.config, 'server.force_ipv4', True):
                # فقط IPv4
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(2)
                
                # Connect to a dummy address to get interface IP
                sock.connect(('8.8.8.8', 80))
                ip_address = sock.getsockname()[0]
                sock.close()
                
                # بررسی اینکه IP متعلق به interface درخواستی است
                if self._validate_interface_ip(ip_address, interface):
                    return ip_address
            else:
                # استفاده از ifconfig/ip command
                cmd = f"ip -4 addr show {interface} | grep -oP '(?<=inet\\s)\\d+(\\.\\d+){3}'"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip().split('\n')[0]
            
            # روش جایگزین: استفاده از netifaces (اگر نصب باشد)
            try:
                import netifaces
                addresses = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addresses:
                    return addresses[netifaces.AF_INET][0]['addr']
            except ImportError:
                self.logger.debug("netifaces not installed, using alternative methods")
            
            self.logger.error(f"Could not get IP address for interface: {interface}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting IP for interface {interface}: {str(e)}")
            return None
    
    def _validate_interface_ip(self, ip_address: str, interface: str) -> bool:
        """Validate that IP belongs to the specified interface"""
        try:
            # بررسی همه interfaceها
            cmd = "ip -4 addr show"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            current_interface = None
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line and not line.startswith(' '):
                    # خط جدید interface
                    parts = line.split(':')
                    if len(parts) >= 2:
                        current_interface = parts[1].strip()
                elif ip_address in line and current_interface == interface:
                    return True
            
            return False
        except Exception:
            # اگر بررسی شکست خورد، حداقل IP برگردانده شده را قبول کن
            return True
    
    def get_public_ip(self) -> Optional[str]:
        """
        Get public IP address using external services
        
        Returns:
            Public IP address or None
        """
        services = [
            "https://api.ipify.org",
            "https://checkip.amazonaws.com",
            "https://ifconfig.me/ip",
            "https://icanhazip.com",
        ]
        
        for service in services:
            try:
                response = requests.get(service, timeout=10)
                if response.status_code == 200:
                    ip = response.text.strip()
                    if self._is_valid_ip(ip):
                        self.logger.info(f"Public IP from {service}: {ip}")
                        return ip
            except Exception as e:
                self.logger.debug(f"Failed to get IP from {service}: {str(e)}")
                continue
        
        self.logger.error("Could not get public IP from any service")
        return None
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address format"""
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False
    
    def update_ddns(self, ip_address: str) -> bool:
        """
        Send update request to DDNS server
        
        Args:
            ip_address: IP address to update
        
        Returns:
            True if successful, False otherwise
        """
        url = self._get_nested(self.config, 'server.url')
        username = self._get_nested(self.config, 'server.username')
        password = self._get_nested(self.config, 'server.password')
        timeout = self._get_nested(self.config, 'server.timeout', 30)
        retry_count = self._get_nested(self.config, 'server.retry_count', 3)
        retry_delay = self._get_nested(self.config, 'server.retry_delay', 5)
        
        payload = {
            "username": username,
            "password": password
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"DDNS-Client/1.0 ({socket.gethostname()})"
        }
        
        # تنظیم retry strategy
        retry_strategy = Retry(
            total=retry_count,
            backoff_factor=retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        http = requests.Session()
        http.mount("https://", adapter)
        http.mount("http://", adapter)
        
        try:
            self.logger.info(f"Sending update request for IP: {ip_address}")
            
            response = http.post(
                url,
                json=payload,
                headers=headers,
                timeout=timeout
            )
            
            self.logger.info(f"Server response: {response.status_code} - {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') in ['success', 'nochange']:
                    self.current_ip = ip_address
                    self.last_update = datetime.now()
                    
                    # ارسال نوتیفیکیشن
                    if self._get_nested(self.config, 'notifications.enabled', False):
                        self.send_notification(ip_address, result)
                    
                    # ارسال Webhook
                    if self._get_nested(self.config, 'webhook.enabled', False):
                        self.send_webhook(ip_address, result)
                    
                    return True
                else:
                    self.logger.error(f"Update failed: {result.get('message', 'Unknown error')}")
            else:
                self.logger.error(f"HTTP error: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON response: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
        
        return False
    
    def send_notification(self, ip_address: str, result: Dict):
        """Send email notification"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            config = self._get_nested(self.config, 'notifications', {})
            
            msg = MIMEMultipart()
            msg['From'] = config.get('from_email')
            msg['To'] = config.get('to_email')
            msg['Subject'] = f"DDNS Update - {socket.gethostname()}"
            
            body = f"""
            DDNS Update Report
            ------------------
            Hostname: {socket.gethostname()}
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            IP Address: {ip_address}
            Status: {result.get('status', 'unknown')}
            Message: {result.get('message', '')}
            Old IP: {result.get('old_ip', 'N/A')}
            New IP: {result.get('new_ip', 'N/A')}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(config.get('smtp_server'), config.get('smtp_port', 587)) as server:
                server.starttls()
                server.login(config.get('smtp_username'), config.get('smtp_password'))
                server.send_message(msg)
                
            self.logger.info("Notification email sent")
            
        except Exception as e:
            self.logger.error(f"Failed to send notification: {str(e)}")
    
    def send_webhook(self, ip_address: str, result: Dict):
        """Send webhook notification"""
        try:
            url = self._get_nested(self.config, 'webhook.url')
            secret = self._get_nested(self.config, 'webhook.secret', '')
            
            payload = {
                "hostname": socket.gethostname(),
                "timestamp": datetime.now().isoformat(),
                "ip_address": ip_address,
                "status": result.get('status'),
                "message": result.get('message'),
                "old_ip": result.get('old_ip'),
                "new_ip": result.get('new_ip'),
                "secret": secret
            }
            
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                self.logger.info("Webhook sent successfully")
            else:
                self.logger.warning(f"Webhook failed: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Failed to send webhook: {str(e)}")
    
    def check_dns_resolution(self, domain: str = None) -> bool:
        """Check if DNS is resolving correctly"""
        if not self._get_nested(self.config, 'client.check_dns', False):
            return True
        
        if domain is None:
            domain = socket.gethostname()
        
        try:
            dns_server = self._get_nested(self.config, 'client.dns_server', '8.8.8.8')
            timeout = self._get_nested(self.config, 'client.dns_timeout', 5)
            
            # استفاده از nslookup
            cmd = f"nslookup {domain} {dns_server}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
            
            if result.returncode == 0:
                self.logger.debug(f"DNS resolution successful for {domain}")
                return True
            else:
                self.logger.warning(f"DNS resolution failed for {domain}")
                return False
                
        except Exception as e:
            self.logger.error(f"DNS check error: {str(e)}")
            return False
    
    def run_once(self) -> bool:
        """
        Run a single update cycle
        
        Returns:
            True if update was attempted (regardless of success), False if error
        """
        self.logger.info("Starting DDNS update cycle")
        
        # ۱. دریافت IP از interface مشخص شده
        interface = self._get_nested(self.config, 'server.interface', 'eth0')
        ip_address = self.get_interface_ip(interface)
        
        if not ip_address:
            self.logger.error(f"Could not get IP address from interface: {interface}")
            return False
        
        self.logger.info(f"Current IP from {interface}: {ip_address}")
        
        # ۲. بررسی تغییر IP (اختیاری)
        if self.current_ip == ip_address:
            self.logger.info("IP address unchanged, skipping update")
            return True
        
        # ۳. ارسال درخواست به سرور
        success = self.update_ddns(ip_address)
        
        if success:
            self.logger.info("DDNS update completed successfully")
        else:
            self.logger.error("DDNS update failed")
        
        # ۴. بررسی DNS (اختیاری)
        if success and self._get_nested(self.config, 'client.check_dns', False):
            self.check_dns_resolution()
        
        return True
    
    def run_continuous(self):
        """Run in continuous mode with interval"""
        update_interval = self._get_nested(self.config, 'client.update_interval', 300)
        
        self.logger.info(f"Starting continuous mode with {update_interval}s interval")
        
        try:
            while True:
                start_time = time.time()
                
                self.run_once()
                
                # محاسبه زمان خواب تا اجرای بعدی
                elapsed = time.time() - start_time
                sleep_time = max(1, update_interval - elapsed)
                
                self.logger.debug(f"Cycle completed in {elapsed:.2f}s, sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            self.logger.info("Shutting down gracefully...")
        except Exception as e:
            self.logger.error(f"Fatal error: {str(e)}")
            sys.exit(1)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='DDNS Client for Laravel DDNS Server')
    parser.add_argument('-c', '--config', default='config.yaml', help='Path to configuration file')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--interface', help='Override network interface from config')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--test', action='store_true', help='Test mode (no actual update)')
    
    args = parser.parse_args()
    
    try:
        client = DDNSClient(args.config)
        
        if args.debug:
            client.logger.setLevel(logging.DEBUG)
        
        if args.interface:
            client.config['server']['interface'] = args.interface
        
        if args.test:
            client.logger.info("Test mode enabled")
            ip = client.get_interface_ip()
            client.logger.info(f"Test IP: {ip}")
            return
        
        if args.once:
            client.run_once()
        else:
            client.run_continuous()
            
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
