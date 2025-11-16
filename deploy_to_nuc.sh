#!/bin/bash

echo "🚀 Semi-Agentic Company - NUC Deployment Script"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="semi-agentic-company"
REPO_URL="https://github.com/milovanpinxteren/semi-agentic-company.git"
INSTALL_DIR="$HOME/$PROJECT_NAME"

echo -e "${BLUE}Step 1: Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

echo -e "${BLUE}Step 2: Installing required packages...${NC}"
sudo apt install -y python3 python3-pip python3-venv git curl wget

echo -e "${BLUE}Step 3: Setting up GitHub authentication...${NC}"
echo "For automatic git pulls to work, we need your GitHub Personal Access Token."
echo ""
echo -e "${YELLOW}If you don't have one yet:${NC}"
echo "1. Go to: https://github.com/settings/tokens"
echo "2. Click 'Generate new token (classic)'"
echo "3. Give it a name like 'NUC-AutoUpdate'"
echo "4. Check the 'repo' scope (full repository access)"
echo "5. Click 'Generate token' and copy it"
echo ""

read -p "Enter your GitHub username: " GITHUB_USERNAME
read -s -p "Enter your GitHub Personal Access Token: " GITHUB_TOKEN
echo ""

# Create repository URL with authentication
AUTH_REPO_URL="https://$GITHUB_USERNAME:$GITHUB_TOKEN@github.com/milovanpinxteren/semi-agentic-company.git"

echo -e "${BLUE}Step 4: Cloning repository...${NC}"
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}Directory already exists. Removing...${NC}"
    rm -rf "$INSTALL_DIR"
fi

git clone "$AUTH_REPO_URL" "$INSTALL_DIR"
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to clone repository. Check your credentials.${NC}"
    exit 1
fi

cd "$INSTALL_DIR"

echo -e "${BLUE}Step 5: Setting up Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

echo -e "${BLUE}Step 6: Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to install requirements. Check requirements.txt${NC}"
    exit 1
fi

echo -e "${BLUE}Step 7: Configuring git for automatic updates...${NC}"
git config credential.helper store
git config user.name "$GITHUB_USERNAME"
git config user.email "$GITHUB_USERNAME@users.noreply.github.com"

# Test git authentication
echo -e "${BLUE}Step 8: Testing git authentication...${NC}"
git pull origin main
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Git authentication test failed.${NC}"
    exit 1
fi

echo -e "${BLUE}Step 9: Creating management scripts...${NC}"
mkdir -p scripts

# Create status script
cat > scripts/status.sh << 'EOF'
#!/bin/bash
PID_FILE="$HOME/semi-agentic-company/scheduler.pid"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null; then
        echo "✅ Semi-Agentic Scheduler is running (PID: $PID)"
        echo "📊 Process details:"
        ps -p $PID -o pid,ppid,cmd,etime
        echo ""
        echo "📁 Log files:"
        ls -la ~/semi-agentic-company/logs/ 2>/dev/null || echo "No log directory found"
    else
        echo "❌ Semi-Agentic Scheduler is not running (stale PID file)"
        rm -f "$PID_FILE"
    fi
else
    echo "❌ Semi-Agentic Scheduler is not running (no PID file)"
fi
EOF

# Create logs script
cat > scripts/logs.sh << 'EOF'
#!/bin/bash
echo "📋 Recent logs from Semi-Agentic Scheduler:"
echo "============================================"
if [ -f "$HOME/semi-agentic-company/logs/output.log" ]; then
    tail -50 "$HOME/semi-agentic-company/logs/output.log"
else
    echo "No output.log found. Checking nohup.out..."
    if [ -f "$HOME/semi-agentic-company/nohup.out" ]; then
        tail -50 "$HOME/semi-agentic-company/nohup.out"
    else
        echo "No log files found."
    fi
fi
echo ""
echo "💡 For live logs, run: tail -f ~/semi-agentic-company/logs/output.log"
EOF

# Create stop script
cat > scripts/stop.sh << 'EOF'
#!/bin/bash
PID_FILE="$HOME/semi-agentic-company/scheduler.pid"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null; then
        echo "🛑 Stopping Semi-Agentic Scheduler (PID: $PID)..."
        kill $PID
        sleep 3
        if ps -p $PID > /dev/null; then
            echo "⚠️ Process still running, force killing..."
            kill -9 $PID
        fi
        rm -f "$PID_FILE"
        echo "✅ Semi-Agentic Scheduler stopped"
    else
        echo "❌ Process not running (stale PID file)"
        rm -f "$PID_FILE"
    fi
else
    echo "❌ Semi-Agentic Scheduler is not running"
fi
EOF

# Create restart script
cat > scripts/restart.sh << 'EOF'
#!/bin/bash
echo "🔄 Restarting Semi-Agentic Scheduler..."
cd "$HOME/semi-agentic-company"
./scripts/stop.sh
sleep 2
./scripts/start.sh
EOF

# Create start script
cat > scripts/start.sh << 'EOF'
#!/bin/bash
cd "$HOME/semi-agentic-company"
PID_FILE="scheduler.pid"

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null; then
        echo "⚠️ Semi-Agentic Scheduler is already running (PID: $PID)"
        exit 1
    else
        echo "🗑️ Removing stale PID file..."
        rm -f "$PID_FILE"
    fi
fi

# Create logs directory
mkdir -p logs

# Activate virtual environment and start
source venv/bin/activate
echo "🚀 Starting Semi-Agentic Scheduler..."
nohup python main_scheduler.py > logs/output.log 2>&1 & echo $! > "$PID_FILE"
sleep 2

# Check if it started successfully
if ps -p $(cat "$PID_FILE") > /dev/null; then
    echo "✅ Semi-Agentic Scheduler started successfully (PID: $(cat $PID_FILE))"
    echo "📋 View logs with: ./scripts/logs.sh"
    echo "📊 Check status with: ./scripts/status.sh"
else
    echo "❌ Failed to start Semi-Agentic Scheduler"
    echo "Check logs: cat logs/output.log"
    rm -f "$PID_FILE"
fi
EOF

# Make all scripts executable
chmod +x scripts/*.sh

echo -e "${BLUE}Step 10: Creating convenience aliases...${NC}"
# Add aliases to bashrc
cat >> ~/.bashrc << EOF

# Semi-Agentic Company aliases
alias sac-status='$INSTALL_DIR/scripts/status.sh'
alias sac-logs='$INSTALL_DIR/scripts/logs.sh'
alias sac-stop='$INSTALL_DIR/scripts/stop.sh'
alias sac-restart='$INSTALL_DIR/scripts/restart.sh'
alias sac-start='$INSTALL_DIR/scripts/start.sh'
alias sac-cd='cd $INSTALL_DIR'
EOF

echo -e "${BLUE}Step 11: Starting Semi-Agentic Scheduler...${NC}"
./scripts/start.sh

echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo "========================"
echo ""
echo -e "${GREEN}✅ Your Semi-Agentic Company automation is now running!${NC}"
echo ""
echo -e "${YELLOW}Quick Commands (available after running 'source ~/.bashrc'):${NC}"
echo "  sac-status   - Check if running"
echo "  sac-logs     - View recent logs"
echo "  sac-stop     - Stop the scheduler"
echo "  sac-restart  - Restart the scheduler"
echo "  sac-cd       - Go to project directory"
echo ""
echo -e "${YELLOW}Manual Commands:${NC}"
echo "  Status:  $INSTALL_DIR/scripts/status.sh"
echo "  Logs:    $INSTALL_DIR/scripts/logs.sh"
echo "  Stop:    $INSTALL_DIR/scripts/stop.sh"
echo "  Restart: $INSTALL_DIR/scripts/restart.sh"
echo ""
echo -e "${BLUE}💡 Your system will now:${NC}"
echo "  • Run your LinkedIn bots according to config.yaml schedules"
echo "  • Automatically check for GitHub updates"
echo "  • Pull and restart when you push new code"
echo "  • Send email notifications for runs and errors"
echo ""
echo -e "${YELLOW}Next steps on your laptop:${NC}"
echo "1. Make code changes in PyCharm"
echo "2. git add . && git commit -m 'your changes' && git push"
echo "3. NUC will auto-update within your configured interval!"
echo ""
echo -e "${GREEN}🚀 Happy automating!${NC}"