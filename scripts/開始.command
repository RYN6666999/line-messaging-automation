#!/bin/bash
# 雙擊這個檔 → 開啟「總控台」：設定 / 對齊 / 開始執行 三個入口一個視窗
cd "$(dirname "$0")"

PY=/usr/local/bin/python3

if ! "$PY" -c "import pyautogui, pynput, tkinter" 2>/dev/null; then
  echo "首次執行：安裝 pyautogui 與 pynput（需連網，約10秒）…"
  "$PY" -m pip install --user pyautogui pynput
fi

"$PY" hub.py
exec $SHELL