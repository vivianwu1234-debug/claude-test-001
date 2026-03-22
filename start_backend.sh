#!/bin/bash
# 仅启动后端（调试用）
cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
pip install -q -r backend/requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
