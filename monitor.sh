#!/bin/bash
# AutoEdit Health Monitor — Restart server if it dies
# Usage: ./monitor.sh &

SERVER_URL="http://127.0.0.1:5002/api/health"
LOG_FILE="/tmp/autoedit_monitor.log"
APP_DIR="$HOME/autoedit-v3"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

while true; do
    if curl -s --connect-timeout 3 "$SERVER_URL" | grep -q '"ok":true'; then
        echo -n "."
    else
        echo ""
        log "Server DOWN, restarting..."
        pkill -f "python3 main.py --server"
        sleep 1
        cd "$APP_DIR" && PYTHONDONTWRITEBYTECODE=1 python3 -u main.py --server --port 5002 >> /tmp/autoedit_server.log 2>&1 &
        sleep 3
        if curl -s --connect-timeout 3 "$SERVER_URL" | grep -q '"ok":true'; then
            log "Server RESTARTED successfully"
            echo "✅ AutoEdit restarted"
        else
            log "Server restart FAILED"
            echo "❌ Restart failed"
        fi
    fi
    sleep 30
done
