#!/bin/bash
# 雙擊這個檔 → 自動開終端機並執行「auto_click 主程式」
cd ~/Desktop

PY=/usr/local/bin/python3

if ! "$PY" -c "import pyautogui, pynput, tkinter" 2>/dev/null; then
  echo "首次執行：安裝 pyautogui 與 pynput（需連網，約10秒）…"
  "$PY" -m pip install --user pyautogui pynput
fi

"$PY" auto_click.py
echo ""
echo "── 程式已結束。關掉此視窗即可。"
exec $SHELL