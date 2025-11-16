# 🚀 NUC Deployment Guide

## Overview
This guide will help you deploy your semi-agentic automation system to your Linux NUC. After the one-time setup, you'll code on Windows and your NUC will automatically update!

---

## Part 1: 💻 LAPTOP SETUP (Windows - One Time)

### 1. Create GitHub Personal Access Token

**Why needed?** For automatic git pulls on NUC without passwords.

1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. Give it a name like: `NUC-AutoUpdate`
4. Set expiration: **No expiration** (or 1 year)
5. Check the **"repo"** scope (Full control of private repositories)
6. Click **"Generate token"**
7. **📋 COPY THE TOKEN** - you'll need it on the NUC!

### 2. Add Deployment Script to Repository

1. **Copy the deployment script** to your project root:
   - Save `deploy_to_nuc.sh` in your `semi-agentic-company` folder
   - Make sure it's in the same folder as `main_scheduler.py`

2. **Commit and push**:
   ```bash
   git add deploy_to_nuc.sh
   git commit -m "Add NUC deployment script"
   git push
   ```

---

## Part 2: 🖥️ NUC SETUP (Linux - One Time Only!)

### 1. SSH into Your NUC
```bash
ssh your_username@your_nuc_ip_address
# Example: ssh pi@192.168.1.100
```

### 2. Run the Deployment Script
```bash
# Download and run deployment
wget https://raw.githubusercontent.com/milovanpinxteren/semi-agentic-company/main/deploy_to_nuc.sh
chmod +x deploy_to_nuc.sh
./deploy_to_nuc.sh
```

### 3. Follow the Script Prompts
The script will ask for:
- **GitHub username**: Your GitHub username
- **Personal Access Token**: The token you created in Part 1

### 4. Verify Everything Works
After deployment completes, run:
```bash
# Check if running
sac-status

# View logs
sac-logs
```

### 5. Exit SSH
```bash
exit
```
**🎉 You're done with the NUC! Never need to SSH again!**

---

## Part 3: 🔄 DAILY WORKFLOW (Windows)

### Your New Development Workflow:

1. **Code on Windows** in PyCharm
   - Edit your LinkedIn bot
   - Modify schedules in `config.yaml`
   - Add new features

2. **Push changes**:
   ```bash
   git add .
   git commit -m "Updated LinkedIn bot logic"
   git push
   ```

3. **Automatic NUC Update**:
   - NUC checks GitHub every X minutes (your config)
   - Automatically pulls your changes
   - Restarts the scheduler
   - Sends you email confirmation

**That's it!** Your NUC runs 24/7 and stays updated automatically.

---

## 🛠️ MONITORING & TROUBLESHOOTING

### From Any Computer (SSH to NUC):

```bash
# Quick status check
sac-status

# View recent logs
sac-logs

# Restart if needed
sac-restart

# Stop the system
sac-stop

# Start the system
sac-start
```

### Common Issues:

**❌ "Semi-Agentic Scheduler is not running"**
- Solution: `sac-start`

**❌ Git authentication failed**
- Solution: SSH to NUC and run:
  ```bash
  cd ~/semi-agentic-company
  git config credential.helper store
  git pull  # Enter credentials again
  ```

**❌ No email notifications**
- Check your `config.yaml` email settings
- View logs with `sac-logs`

**❌ Bots not running**
- Check schedules in `config.yaml`
- View logs for errors: `sac-logs`

---

## 📁 What Gets Created on NUC:

```
/home/your_username/
└── semi-agentic-company/           # Your project
    ├── main_scheduler.py           # Main automation
    ├── config.yaml                 # Your settings
    ├── bots/                       # Your LinkedIn bot
    ├── logs/                       # Log files
    ├── scheduler.pid               # Process ID
    ├── scripts/                    # Management scripts
    │   ├── status.sh
    │   ├── logs.sh
    │   ├── stop.sh
    │   ├── restart.sh
    │   └── start.sh
    └── venv/                       # Python environment
```

---

## ⚙️ Configuration Notes:

**Auto-update frequency**: Edit `config.yaml` on your laptop:
```yaml
git_updater:
  enabled: true
  check_interval_minutes: 5  # Check GitHub every 5 minutes
```

**Office hours**: Already configured in your `config.yaml`

**Email notifications**: Already working with your Hostinger SMTP

---

## 🎯 Summary:

**✅ After setup:**
- Code on Windows laptop in PyCharm
- Push to GitHub
- NUC automatically updates within minutes
- Monitor via SSH if needed
- Never manually deploy again!

**🔧 Management:**
- All done via simple commands (`sac-status`, `sac-logs`, etc.)
- Email notifications keep you informed
- Automatic restarts on code updates

**📱 Remote monitoring:**
- SSH from anywhere to check status
- Email alerts for errors or important events
- Logs available via `sac-logs` command