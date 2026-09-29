#!/usr/bin/env bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$DIR/server.pid"

if [ -f "$PID_FILE" ]; then
    PID="$(cat "$PID_FILE")"
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        echo "Stopped server (PID: $PID)."
    else
        echo "Server process (PID: $PID) was not active."
    fi
    rm -f "$PID_FILE"
else
    # Fallback to kill by port 8080 or process name
    PID=$(lsof -ti :8080 2>/dev/null)
    if [ -n "$PID" ]; then
        kill "$PID"
        echo "Stopped server on port 8080 (PID: $PID)."
    else
        echo "Server is not running."
    fi
fi
