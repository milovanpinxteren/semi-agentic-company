# Semi-Agentic Company Scheduler

Automated bot scheduler with self-updating capabilities, human-like behavior patterns, and email notifications.

## Features

- 🤖 **Multi-bot scheduling** - Run different bots on different schedules (daily, weekly, monthly, interval)
- 🔄 **Auto-updates** - Automatically pulls code from GitHub and restarts
- 👤 **Human-like behavior** - Randomized timing, office hours, breaks between actions
- 📧 **Email notifications** - Get notified of bot runs, errors, and updates
- 🐍 **Pure Python** - Built with APScheduler, no complex dependencies

## Project Structure

```
semi-agentic-company/
├── main_scheduler.py          # Main entry point
├── config.yaml                # Configuration file (edit this!)
├── requirements.txt           # Python dependencies
│
├── bots/
│   └── linkedin_likebot/      # Your LinkedIn bot
│       └── bot.py             # Bot implementation (add your code here)
│
├── utils/
│   ├── schedule_manager.py    # Scheduling logic
│   ├── git_updater.py         # Auto git pull
│   ├── humanizer.py           # Random timing utilities
│   └── email_logger.py        # Email notifications
│
└── logs/
    └── scheduler.log          # Application logs
```

## Setup

### 1. Initial Setup on Windows (Development)

1. **Clone or create the project in PyCharm**
   ```bash
   # If starting fresh, create a new project with this folder
   # If using git, clone your repository
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the system**
   - Edit `config.yaml`:
     - Set your email credentials (use Gmail app password)
     - Configure bot schedules
     - Adjust office hours and timezone
     - Add your LinkedIn credentials (if needed)

5. **Test locally**
   ```bash
   python main_scheduler.py
   ```

### 2. Setup GitHub Repository

1. **Create a GitHub repository**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/yourrepo.git
   git push -u origin main
   ```

2. **Use HTTPS with Personal Access Token** (recommended for auto-pull)
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Generate new token with `repo` permissions
   - Use this token instead of password when cloning on NUC

### 3. Setup on Intel NUC (Linux - One Time Only!)

SSH into your NUC for this initial setup:

```bash
ssh username@your-nuc-ip
```

#### Install Python and dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv git -y
```

#### Clone repository

```bash
# Navigate to where you want the project
cd /home/yourusername/

# Clone with HTTPS (you'll need your GitHub Personal Access Token)
git clone https://github.com/yourusername/yourrepo.git semi-agentic-company
cd semi-agentic-company

# Configure git to cache credentials (so auto-pull works)
git config credential.helper store
git pull  # Enter username and token - it will be saved
```

#### Setup virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Create systemd service (auto-start on boot)

```bash
sudo nano /etc/systemd/system/semi-agentic.service
```

Paste this content (adjust paths to match your setup):

```ini
[Unit]
Description=Semi-Agentic Company Scheduler
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/home/yourusername/semi-agentic-company
ExecStart=/home/yourusername/semi-agentic-company/venv/bin/python main_scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Enable and start the service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable semi-agentic.service

# Start service now
sudo systemctl start semi-agentic.service

# Check status
sudo systemctl status semi-agentic.service
```

#### View logs (remotely)

```bash
# View real-time logs
sudo journalctl -u semi-agentic.service -f

# Or check the log file
tail -f /home/yourusername/semi-agentic-company/logs/scheduler.log
```

### 4. Daily Workflow (Windows Development)

After initial setup, you never need to touch the NUC again!

1. **Edit code on Windows in PyCharm**
   - Make changes to bot implementations
   - Update configuration
   - Test locally if needed

2. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Updated LinkedIn bot logic"
   git push
   ```

3. **NUC automatically updates!**
   - Within 5-10 minutes (or whatever you configured)
   - NUC pulls changes and restarts
   - You get an email notification

## Configuration Guide

### Email Setup (Gmail)

1. **Enable 2-Factor Authentication** on your Google account
2. **Create App Password**:
   - Go to: https://myaccount.google.com/apppasswords
   - Generate password for "Mail"
   - Use this password in `config.yaml`

```yaml
email:
  enabled: true
  smtp_server: smtp.gmail.com
  smtp_port: 587
  sender_email: your-email@gmail.com
  sender_password: your-app-password-here
  recipient_email: your-email@gmail.com
```

### Bot Schedules

#### Daily Bot (runs once per day)
```yaml
bots:
  my_daily_bot:
    enabled: true
    schedule_type: daily
    time_window:
      start: "09:00"
      end: "17:00"
    random_delay_minutes:
      min: 5
      max: 45
```

#### Weekly Bot (specific day of week)
```yaml
bots:
  my_weekly_bot:
    enabled: true
    schedule_type: weekly
    day_of_week: monday  # monday, tuesday, wednesday, etc.
    time: "10:00"
    random_delay_minutes:
      min: 0
      max: 30
```

#### Monthly Bot (specific day of month)
```yaml
bots:
  my_monthly_bot:
    enabled: true
    schedule_type: monthly
    day_of_month: 1  # First day of month
    time: "09:00"
    random_delay_minutes:
      min: 0
      max: 60
```

#### Interval Bot (every X minutes)
```yaml
bots:
  my_interval_bot:
    enabled: true
    schedule_type: interval
    interval_minutes: 60  # Every hour
```

## Adding Your LinkedIn Bot Code

Edit `bots/linkedin_likebot/bot.py` and add your implementation:

1. **Add setup logic** (browser initialization, login)
2. **Implement `perform_likes()`** - your main bot logic
3. **Implement `find_posts()`** - find posts to interact with
4. **Implement `like_post()`** - like a specific post
5. **Add cleanup** - close browser, etc.

The framework handles:
- Scheduling
- Random delays
- Office hours checking
- Email notifications
- Error handling

## Useful Commands

### On Windows (Development)

```bash
# Test the scheduler
python main_scheduler.py

# Update dependencies
pip install -r requirements.txt

# Push changes
git add .
git commit -m "Your message"
git push
```

### On Linux NUC (via SSH)

```bash
# Check service status
sudo systemctl status semi-agentic.service

# View real-time logs
sudo journalctl -u semi-agentic.service -f

# Restart service manually
sudo systemctl restart semi-agentic.service

# Stop service
sudo systemctl stop semi-agentic.service

# Check git status
cd /home/yourusername/semi-agentic-company
git status
git log --oneline -5
```

## Troubleshooting

### Service won't start
```bash
# Check logs for errors
sudo journalctl -u semi-agentic.service -n 50

# Verify Python can run the script
cd /home/yourusername/semi-agentic-company
source venv/bin/activate
python main_scheduler.py
```

### Git auto-pull not working
```bash
# Verify git credentials
cd /home/yourusername/semi-agentic-company
git pull  # Should work without password prompt

# If not, reconfigure credential helper
git config credential.helper store
git pull  # Enter credentials once
```

### Not receiving emails
- Verify Gmail app password is correct
- Check spam folder
- Review logs for email errors
- Test SMTP connection manually

## Security Notes

⚠️ **Important**: 
- Never commit passwords or tokens to git
- Use `.gitignore` to exclude sensitive files
- Use environment variables or separate config files for secrets
- LinkedIn may ban accounts using automation - use at your own risk

## License

This project is for personal use. Be aware of terms of service for platforms you interact with.
