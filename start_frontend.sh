#!/bin/bash
# 仅启动前端（调试用）
cd "$(dirname "$0")/frontend"
npm install
npm run dev
