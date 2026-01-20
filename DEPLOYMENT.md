# VPS Deployment Guide

This guide explains how to deploy the Binance SPOT trading bot on a Linux VPS (Virtual Private Server).

## Why Use a VPS?

- **24/7 Uptime**: Keep bot running continuously
- **Stable Connection**: Better internet reliability than home networks
- **Low Latency**: Faster connection to Binance servers
- **Remote Access**: Monitor from anywhere

## Recommended VPS Providers

### Budget Options ($5-10/month)
- **DigitalOcean**: Easy to use, good performance
- **Vultr**: Competitive pricing, global locations
- **Linode**: Reliable, good documentation
- **Hetzner**: Excellent value in Europe

### Requirements
- **OS**: Ubuntu 22.04 LTS or Debian 11+
- **RAM**: Minimum 1GB (2GB recommended)
- **Storage**: 10GB SSD
- **Location**: Close to Binance servers (Singapore, Tokyo, or US East)

## Step 1: Initial VPS Setup

### 1.1 Create VPS Instance

Choose your provider and create a new instance:
- **OS**: Ubuntu 22.04 LTS (recommended)
- **Plan**: Basic (1-2GB RAM)
- **Region**: Singapore or Tokyo (lowest latency to Binance)

### 1.2 Connect via SSH

```bash
ssh root@your_vps_ip
```

Replace `your_vps_ip` with your VPS IP address.

### 1.3 Create Non-Root User

**Security best practice - never run as root!**

```bash
# Create new user
adduser trader

# Add to sudo group
usermod -aG sudo trader

# Switch to new user
su - trader
```

### 1.4 Update System

```bash
sudo apt update
sudo apt upgrade -y
```

## Step 2: Install Dependencies

### 2.1 Install Python 3.10+

```bash
# Check Python version
python3 --version

# If Python 3.10+ not available, install from deadsnakes PPA
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip -y
```

### 2.2 Install Git

```bash
sudo apt install git -y
```

### 2.3 Install Screen (for persistent sessions)

```bash
sudo apt install screen -y
```

## Step 3: Deploy Bot

### 3.1 Clone Repository

```bash
cd ~
git clone https://github.com/ucal54/ucal54bot.git
cd ucal54bot
```

### 3.2 Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3.3 Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.4 Configure Environment Variables

```bash
# Copy example file
cp .env.example .env

# Edit with nano or vim
nano .env
```

Add your Binance API credentials:
```
BINANCE_API_KEY=your_actual_api_key_here
BINANCE_API_SECRET=your_actual_api_secret_here
```

Save and exit (Ctrl+X, then Y, then Enter in nano).

### 3.5 Configure Bot Settings

```bash
# Copy example config
cp config/config.example.yml config/config.yml

# Edit configuration
nano config/config.yml
```

Key settings to configure:
- `symbol`: Your trading pair
- `dry_run`: Set to `true` for testing, `false` for live
- Strategy and risk parameters

## Step 4: Test the Bot

### 4.1 Test in Dry-Run Mode

```bash
# Ensure dry_run: true in config.yml
python main.py
```

Press `Ctrl+C` to stop after verifying it works.

### 4.2 Check Logs

```bash
# View today's log
tail -f logs/bot_$(date +%Y%m%d).log

# View trade history
cat trades.csv
```

## Step 5: Run Bot Persistently

### Method 1: Using Screen (Simple)

**Start bot in screen session:**
```bash
# Create new screen session
screen -S tradingbot

# Activate virtual environment
cd ~/ucal54bot
source venv/bin/activate

# Run bot
python main.py
```

**Detach from screen:**
- Press `Ctrl+A`, then `D`

**Reattach to screen:**
```bash
screen -r tradingbot
```

**List all screen sessions:**
```bash
screen -ls
```

**Kill screen session:**
```bash
screen -X -S tradingbot quit
```

### Method 2: Using Systemd (Production)

**More robust - auto-restarts on failure, starts on boot**

#### 5.1 Create Systemd Service File

```bash
sudo nano /etc/systemd/system/tradingbot.service
```

Add the following content (adjust paths if needed):

```ini
[Unit]
Description=Binance SPOT Trading Bot
After=network.target

[Service]
Type=simple
User=trader
WorkingDirectory=/home/trader/ucal54bot
Environment="PATH=/home/trader/ucal54bot/venv/bin"
ExecStart=/home/trader/ucal54bot/venv/bin/python /home/trader/ucal54bot/main.py
Restart=always
RestartSec=10
StandardOutput=append:/home/trader/ucal54bot/logs/systemd.log
StandardError=append:/home/trader/ucal54bot/logs/systemd-error.log

[Install]
WantedBy=multi-user.target
```

#### 5.2 Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable tradingbot

# Start service
sudo systemctl start tradingbot

# Check status
sudo systemctl status tradingbot
```

#### 5.3 Service Management Commands

```bash
# Start bot
sudo systemctl start tradingbot

# Stop bot
sudo systemctl stop tradingbot

# Restart bot
sudo systemctl restart tradingbot

# View logs
sudo journalctl -u tradingbot -f

# View last 100 lines
sudo journalctl -u tradingbot -n 100

# Disable auto-start
sudo systemctl disable tradingbot
```

## Step 6: Monitoring

### 6.1 Check Bot Logs

```bash
# Real-time log viewing
tail -f ~/ucal54bot/logs/bot_$(date +%Y%m%d).log

# View trade history
tail -f ~/ucal54bot/trades.csv

# Check for errors
grep ERROR ~/ucal54bot/logs/bot_*.log
```

### 6.2 Monitor System Resources

```bash
# Check CPU and memory usage
htop

# Check disk space
df -h

# Check network connectivity
ping api.binance.com
```

### 6.3 Set Up Log Rotation

Prevent logs from filling disk:

```bash
sudo nano /etc/logrotate.d/tradingbot
```

Add:
```
/home/trader/ucal54bot/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
}
```

## Step 7: Security Hardening

### 7.1 Configure Firewall

```bash
# Enable UFW firewall
sudo ufw allow OpenSSH
sudo ufw enable

# Check status
sudo ufw status
```

### 7.2 Disable Root Login

```bash
sudo nano /etc/ssh/sshd_config
```

Set:
```
PermitRootLogin no
PasswordAuthentication no  # Use SSH keys only
```

Restart SSH:
```bash
sudo systemctl restart sshd
```

### 7.3 Set Up SSH Keys

On your local machine:
```bash
ssh-keygen -t ed25519
ssh-copy-id trader@your_vps_ip
```

### 7.4 Install Fail2Ban

Protect against brute-force attacks:
```bash
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 7.5 Secure API Keys

```bash
# Ensure .env has correct permissions
chmod 600 ~/ucal54bot/.env

# Verify
ls -la ~/ucal54bot/.env
# Should show: -rw------- (owner read/write only)
```

## Step 8: Updates and Maintenance

### 8.1 Update Bot Code

```bash
cd ~/ucal54bot

# Stop bot
sudo systemctl stop tradingbot  # If using systemd
# OR
screen -X -S tradingbot quit    # If using screen

# Backup current version
cp -r ~/ucal54bot ~/ucal54bot-backup-$(date +%Y%m%d)

# Pull latest changes
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Restart bot
sudo systemctl start tradingbot  # If using systemd
# OR follow screen steps again
```

### 8.2 Backup Trade Data

```bash
# Manual backup
cp ~/ucal54bot/trades.csv ~/backups/trades_$(date +%Y%m%d).csv

# Automated daily backup (cron)
crontab -e
```

Add:
```bash
0 0 * * * cp ~/ucal54bot/trades.csv ~/backups/trades_$(date +%Y%m%d).csv
```

### 8.3 System Updates

```bash
# Weekly system updates
sudo apt update
sudo apt upgrade -y
sudo reboot  # If kernel updated
```

## Step 9: Troubleshooting

### Bot Not Starting

**Check logs:**
```bash
sudo journalctl -u tradingbot -n 50
tail -n 50 ~/ucal54bot/logs/bot_*.log
```

**Common issues:**
- Missing API keys in .env
- Wrong Python version
- Virtual environment not activated
- Configuration file errors

### Connection Issues

**Test Binance connectivity:**
```bash
ping api.binance.com
curl https://api.binance.com/api/v3/ping
```

**Check DNS:**
```bash
nslookup api.binance.com
```

### High Memory Usage

```bash
# Check memory
free -h

# If needed, add swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Bot Keeps Stopping

**If using systemd:**
```bash
# Check why it's failing
sudo systemctl status tradingbot
sudo journalctl -u tradingbot -n 100

# Increase restart delay if needed
sudo nano /etc/systemd/system/tradingbot.service
# Change RestartSec=10 to RestartSec=30
```

## Step 10: Best Practices

### Daily Checklist

- [ ] Check bot is running: `systemctl status tradingbot`
- [ ] Review trades: `tail trades.csv`
- [ ] Check logs for errors: `grep ERROR logs/bot_*.log`
- [ ] Monitor account balance on Binance
- [ ] Verify no suspicious activity

### Weekly Checklist

- [ ] Review performance metrics
- [ ] Check VPS disk space: `df -h`
- [ ] Update system packages: `sudo apt update && sudo apt upgrade`
- [ ] Backup trade data
- [ ] Review and adjust strategy if needed

### Monthly Checklist

- [ ] Full performance analysis
- [ ] Rotate logs
- [ ] Security audit (check auth logs)
- [ ] Optimize configuration
- [ ] Update bot to latest version

## Emergency Procedures

### If You Need to Stop Immediately

```bash
# Using systemd
sudo systemctl stop tradingbot

# Using screen
screen -r tradingbot
# Then press Ctrl+C
```

The bot will attempt to close any open positions on shutdown.

### If VPS Becomes Unreachable

1. Use VPS provider's console/dashboard
2. Access via VNC or serial console
3. Check system logs
4. Reboot if necessary

### If You Lose Access to API Keys

1. Immediately stop the bot
2. Deactivate compromised API keys on Binance
3. Generate new API keys
4. Update .env file
5. Restart bot

## Cost Optimization

### Reduce VPS Costs

- Start with smallest plan, upgrade if needed
- Use spot instances if provider offers them
- Consider annual billing (usually discounted)

### Monitor Data Transfer

```bash
# Check bandwidth usage
vnstat -d
```

Most VPS plans include sufficient bandwidth for trading bots.

## Support and Resources

- **VPS Provider Support**: Use your provider's help desk
- **Bot Issues**: Check logs, GitHub issues
- **Binance API**: https://binance-docs.github.io/apidocs/spot/en/

---

**Remember:** Always test thoroughly in dry-run mode before going live. Start with small capital to verify everything works correctly in production.
