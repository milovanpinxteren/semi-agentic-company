# Quick Start Guide

## Next Steps (In Order)

### Step 1: Open in PyCharm (Windows)
1. Download the entire `semi-agentic-company` folder
2. Open PyCharm → Open → Select the folder
3. PyCharm will detect it's a Python project

### Step 2: Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Configure Email & Settings
Edit `config.yaml`:

**REQUIRED CHANGES:**
- Line 11-12: Add your Gmail and app password
  ```yaml
  sender_email: your-email@gmail.com
  sender_password: your-gmail-app-password
  ```
- Line 19: Set your timezone
  ```yaml
  timezone: Europe/Amsterdam  # or your timezone
  ```

**Get Gmail App Password:**
1. Go to: https://myaccount.google.com/apppasswords
2. Generate password for "Mail"
3. Copy to config.yaml

### Step 4: Add Your LinkedIn Bot Code
Edit `bots/linkedin_likebot/bot.py`:
- Add your LinkedIn credentials/setup
- Implement the `perform_likes()` method with your existing logic
- Implement `find_posts()` and `like_post()` methods
- Add dependencies to `requirements.txt` if needed (selenium, etc.)

### Step 5: Test Locally
```bash
python main_scheduler.py
```

Press Ctrl+C to stop after verifying it works.

### Step 6: Push to GitHub
```bash
git init
git add .
git commit -m "Initial setup"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### Step 7: Deploy to NUC (One-Time Setup)
Follow the detailed instructions in `README.md` section "3. Setup on Intel NUC"

**Summary:**
1. SSH to NUC
2. Clone repo with Personal Access Token
3. Create virtual environment
4. Setup systemd service
5. Start service
6. Never touch NUC again!

### Step 8: Daily Workflow
1. Edit code in PyCharm (Windows)
2. `git push`
3. NUC auto-updates in 5 minutes!
4. Get email notifications

---

## What Was Created

✅ **Main Scheduler** (`main_scheduler.py`)
- Orchestrates everything
- Auto git pull every 5 minutes
- Schedules all bots

✅ **Configuration** (`config.yaml`)
- Email settings
- Bot schedules
- Office hours
- Git settings

✅ **Utilities**
- `email_logger.py` - Email notifications
- `humanizer.py` - Random timing, office hours
- `git_updater.py` - Auto git pull & restart
- `schedule_manager.py` - APScheduler wrapper

✅ **LinkedIn Bot** (placeholder)
- Structure ready
- Add your implementation

✅ **Documentation**
- `README.md` - Full documentation
- `QUICKSTART.md` - This file
- Comments throughout code

✅ **DevOps**
- `.gitignore` - Proper exclusions
- `requirements.txt` - Dependencies
- `semi-agentic.service.template` - Systemd service

---

## Current Bot Schedule

The LinkedIn bot is configured to run:
- **When**: Daily
- **Time window**: Random time between 9 AM - 5 PM
- **Random delay**: Additional 5-45 minute delay after scheduled time
- **Max actions**: 20 per run
- **Office hours**: Only Monday-Friday during office hours

**Modify in `config.yaml` under `bots → linkedin_likebot`**

---

## Need Help?

**Common Issues:**
- Email not working? → Check Gmail app password
- Bot not running? → Check logs in `logs/scheduler.log`
- Git not auto-updating? → Verify credentials are cached on NUC

**Check logs:**
- Windows: `logs/scheduler.log`
- Linux NUC: `sudo journalctl -u semi-agentic.service -f`

---

Ready to rock! 🚀
