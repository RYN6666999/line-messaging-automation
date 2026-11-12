#!/bin/bash
# 雙擊這個檔 → 打開「設定 UI」，調整迴圈次數/座標/貼上內容後存成 config.json
cd "$(dirname "$0")"

PY=/usr/local/bin/python3

if ! "$PY" -c "import pyautogui, pynput, tkinter" 2>/dev/null; then
  echo "首次執行：安裝 pyautogui 與 pynput（需連網，約10秒）…"
  "$PY" -m pip install --user pyautogui pynput
fi

"$PY" config_ui.py
exec $SHELL