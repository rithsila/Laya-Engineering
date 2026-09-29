#!/usr/bin/env bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$DIR/server.pid"
LOG_FILE="$DIR/server.log"

if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "Server already running (PID: $(cat "$PID_FILE"))."
    echo "URL: http://127.0.0.1:8080/decide"
    exit 0
fi

# Clean up stale PID file if process not alive
rm -f "$PID_FILE"

echo "Starting Laya + JEV server in background..."
echo "Loading model into Apple Neural Engine (~15-20s first time)..."

PYTHONUNBUFFERED=1 nohup "$DIR/.venv/bin/python" "$DIR/laya-codex-demo/server.py" < /dev/null >> "$LOG_FILE" 2>&1 &
SERVER_PID=$!
echo "$SERVER_PID" > "$PID_FILE"

# Wait for server port 8080 to become ready
for i in {1..35}; do
    if lsof -ti :8080 >/dev/null 2>&1; then
        echo "Server is ready! (PID: $SERVER_PID)"
        echo "URL: http://127.0.0.1:8080/decide"
        echo ""
        echo "Test command:"
        echo "curl -s -X POST http://127.0.0.1:8080/decide -d '{\"ticket\":\"invoice question\"}'"
        exit 0
    fi
    sleep 1
done

echo "Server started with PID $SERVER_PID. Check server.log if it takes longer."
