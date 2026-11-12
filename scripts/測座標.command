#!/bin/bash
# 雙擊這個檔 → 自動開終端機並執行「滑鼠座標工具」
cd ~/Desktop

# 固定用「有裝套件的 Python」（多版本混亂時最穩）
PY=/usr/local/bin/python3

# 沒裝套件就自動先裝（只需一次）
if ! "$PY" -c "import pyautogui, pynput, tkinter" 2>/dev/null; then
  echo "首次執行：安裝 pyautogui 與 pynput（需連網，約10秒）…"
  "$PY" -m pip install --user pyautogui pynput
fi

"$PY" mouse_position.py
echo ""
echo "── 已結束（Ctrl+C 或關窗）。"
exec $SHELL