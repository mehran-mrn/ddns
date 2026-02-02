# DDNS Client

A robust Dynamic DNS client for Linux that updates your IP address through a specific network interface to your Laravel DDNS server.

## Features

✅ **Interface-Specific Updates** - Binds to a specific network interface to ensure the correct public IP is detected  
✅ **Automatic Retry** - Configurable retry logic with exponential backoff  
✅ **Systemd Integration** - Run as daemon or scheduled with timer  
✅ **Comprehensive Logging** - Detailed logs with rotation support  
✅ **Graceful Shutdown** - Handles SIGTERM/SIGINT properly  
✅ **Configuration Validation** - Validates config on startup  
✅ **Test Mode** - Test your configuration before deploying  

## Requirements

- Python 3.6 or higher
- Linux with systemd
- Root/sudo access for installation
- Network interface with internet access

## Quick Start

### 1. Download or Clone

```bash
git clone https://github.com/yourusername/ddns-client.git
cd ddns-client
```

### 2. Install

```bash
chmod +x install.sh
sudo ./install.sh
```

The installer will:
- Install required Python packages
- Copy files to `/opt/ddns-client`
- Create config directory `/etc/ddns-client`
- Set up systemd service
- Ask you to choose between daemon or timer mode

### 3. Configure

Edit the configuration file:

```bash
sudo nano /etc/ddns-client/config.yaml
```

**Minimum required configuration:**

```yaml
server:
  url: "https://ddns.yourdomain.com/api/v1/update"
  username: "your_client_username"
  password: "your_client_password"
  interface: "eth1"  # Your network interface
```

**To find your network interfaces:**

```bash
ip addr show
# or
ifconfig
```

### 4. Test Configuration

```bash
sudo /opt/ddns-client/ddns_client.py --test
```

This will:
- Validate your config
- Check if the interface exists
- Test connection to the server
- Show the IP that will be sent

### 5. Start Service

**If using daemon mode:**
```bash
sudo systemctl restart ddns-client.service
sudo systemctl status ddns-client.service
```

**If using timer mode:**
```bash
sudo systemctl restart ddns-client.timer
sudo systemctl status ddns-client.timer
```

## Configuration

### Full Configuration Example

```yaml
server:
  # Your DDNS server endpoint
  url: "https://ddns.example.com/api/v1/update"
  
  # Authentication (from admin panel)
  username: "client123"
  password: "secure_password_here"
  
  # Network interface to use
  # IMPORTANT: This determines which public IP is sent
  interface: "eth1"
  
  # Use only IPv4
  force_ipv4: true
  
  # Connection timeout in seconds
  timeout: 30
  
  # Retry configuration
  retry_count: 3
  retry_delay: 5

client:
  # Update interval in seconds (daemon mode only)
  # 300 = 5 minutes
  update_interval: 300
  
  # Log level: DEBUG, INFO, WARNING, ERROR
  log_level: "INFO"
  
  # Log file location
  log_file: "/var/log/ddns-client/ddns.log"
```

### Interface Selection

The `interface` setting is **critical**. The client will:
1. Get the local IP of the specified interface
2. Bind all HTTP requests to that interface
3. The server will see the public IP of that route

**Example scenarios:**

- **Server with multiple internet connections:**
  - eth0 → Main internet (used by default routing)
  - eth1 → Secondary internet (DDNS should use this)
  - Set `interface: "eth1"`

- **VPN scenario:**
  - eth0 → Regular internet
  - tun0 → VPN tunnel
  - Set `interface: "tun0"` to use VPN IP

## Usage

### Run Modes

**1. Daemon Mode (Recommended)**
```bash
# Run continuously with periodic updates
sudo systemctl start ddns-client.service
```

**2. Timer Mode**
```bash
# Run on schedule (systemd timer)
sudo systemctl start ddns-client.timer
```

**3. One-time Update**
```bash
# Run once and exit
sudo /opt/ddns-client/ddns_client.py --once
```

**4. Test Mode**
```bash
# Test configuration without updating
sudo /opt/ddns-client/ddns_client.py --test
```

### Systemd Commands

```bash
# Start service
sudo systemctl start ddns-client.service

# Stop service
sudo systemctl stop ddns-client.service

# Restart service (reload config)
sudo systemctl restart ddns-client.service

# Check status
sudo systemctl status ddns-client.service

# Enable on boot
sudo systemctl enable ddns-client.service

# Disable on boot
sudo systemctl disable ddns-client.service

# View logs (live)
sudo journalctl -u ddns-client.service -f

# View last 100 lines
sudo journalctl -u ddns-client.service -n 100

# View logs for today
sudo journalctl -u ddns-client.service --since today
```

## Logs

Logs are written to:
- **Systemd Journal**: `journalctl -u ddns-client.service`
- **Log File**: `/var/log/ddns-client/ddns.log`

### Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General informational messages (default)
- **WARNING**: Warning messages
- **ERROR**: Error messages

### Log Examples

```
2024-02-03 10:00:01 - DDNSClient - INFO - Starting DDNS client daemon (update interval: 300s)
2024-02-03 10:00:01 - DDNSClient - INFO - Interface: eth1
2024-02-03 10:00:01 - DDNSClient - INFO - Server: https://ddns.example.com/api/v1/update
2024-02-03 10:00:02 - DDNSClient - INFO - Updating IP through interface: eth1
2024-02-03 10:00:03 - DDNSClient - INFO - ✓ IP updated successfully: 1.2.3.4 → 1.2.3.5
2024-02-03 10:00:03 - DDNSClient - INFO - ✓ DNS updated successfully
```

## Server Responses

The client handles these server responses:

### Success (200 OK)
```json
{
  "status": "success",
  "message": "IP updated successfully",
  "old_ip": "1.2.3.4",
  "new_ip": "1.2.3.5",
  "dns_updated": true
}
```

### No Change (200 OK)
```json
{
  "status": "nochange",
  "message": "IP address unchanged",
  "current_ip": "1.2.3.4"
}
```

### Authentication Failed (401)
```json
{
  "status": "error",
  "message": "Invalid credentials"
}
```

### Client Inactive (403)
```json
{
  "status": "error",
  "message": "Client is inactive"
}
```

## Troubleshooting

### Service won't start

```bash
# Check service status
sudo systemctl status ddns-client.service

# View logs
sudo journalctl -u ddns-client.service -n 50

# Test configuration
sudo /opt/ddns-client/ddns_client.py --test
```

### Interface not found

```bash
# List all interfaces
ip addr show

# Update config with correct interface
sudo nano /etc/ddns-client/config.yaml
```

### Authentication failures

- Verify username/password in config
- Check if client is active in admin panel
- Test credentials manually:

```bash
curl -X POST https://your-server.com/api/v1/update \
  -H "Content-Type: application/json" \
  -d '{"username":"your_user","password":"your_pass"}'
```

### Network issues

```bash
# Test interface connectivity
ping -I eth1 8.8.8.8

# Check routing
ip route get 8.8.8.8 from $(ip addr show eth1 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1)
```

### DNS not updating

- Check if `dns_updated` is `false` in response
- Verify DNS configuration on server
- Check server logs

## Uninstall

```bash
sudo ./uninstall.sh
```

You'll be asked if you want to keep:
- Configuration files
- Log files

To completely remove everything:

```bash
sudo ./uninstall.sh
sudo rm -rf /etc/ddns-client /var/log/ddns-client
```

## Directory Structure

After installation:

```
/opt/ddns-client/              # Application directory
├── ddns_client.py             # Main script
└── requirements.txt           # Python dependencies

/etc/ddns-client/              # Configuration directory
└── config.yaml                # Configuration file

/var/log/ddns-client/          # Log directory
└── ddns.log                   # Log file

/etc/systemd/system/           # Systemd files
├── ddns-client.service        # Service unit
├── ddns-client.timer          # Timer unit (optional)
└── ddns-client-oneshot.service # One-shot service (for timer)
```

## Security Notes

1. **Config file permissions**: Set to 600 (only root can read)
2. **Password storage**: Stored in plain text in config file
3. **HTTPS**: Always use HTTPS for server URL
4. **Firewall**: Ensure outbound HTTPS is allowed

## Advanced Usage

### Custom Config Location

```bash
sudo /opt/ddns-client/ddns_client.py --config /path/to/config.yaml --test
```

### Debug Mode

```bash
# Edit config
sudo nano /etc/ddns-client/config.yaml

# Set log_level to DEBUG
client:
  log_level: "DEBUG"

# Restart service
sudo systemctl restart ddns-client.service
```

### Multiple Instances

You can run multiple instances for different interfaces:

1. Copy and rename service file
2. Create separate config file
3. Modify ExecStart to use different config

## Support

For issues, please:
1. Check logs: `sudo journalctl -u ddns-client.service -n 100`
2. Test config: `sudo /opt/ddns-client/ddns_client.py --test`
3. Open an issue on GitHub with logs

## License

[Your License Here]

## Author

[Your Name/Organization]
