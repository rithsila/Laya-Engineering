#!/usr/bin/env bash
PID=$(lsof -ti :8080 2>/dev/null)
if [ -n "$PID" ]; then
    echo "Status: RUNNING (PID: $PID)"
    echo "Port  : 8080"
    echo "URL   : http://127.0.0.1:8080/decide"
else
    echo "Status: STOPPED"
fi
