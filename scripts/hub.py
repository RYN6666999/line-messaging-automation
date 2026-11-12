#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
總控台  hub.py
把「設定 / 對齊 / 開始執行」三個功能收進一個視窗，只要記住一個入口。

原理：只做「膠水」——用 subprocess 把三支子程式各自開成【獨立進程】。
所以執行邏輯( auto_click.py )不會跟這個視窗共存，避免「加在一起就互相干擾」。

用法：雙擊「開始.command」即可（等同 python3 hub.py）。
"""

import json
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

BASE = Path(__file__).parent
PY = __import__("sys").executable  # 執行本身的那個 Python


def launch(name):
    """開一支子程式為獨立進程，然後關掉本視窗（避免殘留干擾）。"""
    try:
        subprocess.Popen([PY, str(BASE / name)])
    except Exception as e:
        messagebox.showerror("啟動失敗", f"無法啟動 {name}\n{e}")
    root.after(300, root.destroy)   # 啟動後 0.3 秒才關，讓子進程先起來


def show_config():
    """顯示目前 config.json 的設定摘要。"""
    cfg_file = BASE / "config.json"
    try:
        cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
    except Exception as e:
        messagebox.showwarning("讀取失敗", f"讀 config.json 失敗：{e}")
        return
    lines = [f"迴圈次數：{cfg.get('REPEAT_TIMES')}",
             f"座標：①{tuple(cfg.get('CLICK_1', []))}  ②{tuple(cfg.get('CLICK_2', []))}",
             f"間隔：{cfg.get('STEP_INTERVAL')}s · 切換鍵：{'+'.join(cfg.get('SWITCH_CHAT_HOTKEY', []))}",
             f"模式：{'測試(只移動)' if cfg.get('DRY_RUN') else '正式(會送出)'} · 追蹤log：{'開' if cfg.get('TRACE') else '關'}"]
    messagebox.showinfo("目前設定", "\n".join(lines))


root = tk.Tk()
root.title("LINE 自動化 — 總控台")
root.geometry("400x300")
tk.Label(root, text="LINE 大量訊息自動化",
         font=("PingFang TC", 16, "bold"), pady=6).pack()

tk.Button(root, text="① 設定（次數/座標/內容）",
          command=lambda: launch("config_ui.py"), height=2,
          font=("PingFang TC", 13)).pack(fill="x", padx=20, pady=5)
tk.Button(root, text="② 對齊（標記＋座標）",
          command=lambda: launch("mouse_position.py"), height=2,
          font=("PingFang TC", 13)).pack(fill="x", padx=20, pady=5)
tk.Button(root, text="③ 開始執行",
          command=lambda: launch("auto_click.py"), height=2,
          font=("PingFang TC", 13, "bold"), bg="#00bb33", fg="white",
          activebackground="#00dd44").pack(fill="x", padx=20, pady=5)
tk.Button(root, text="看看目前設定",
          command=show_config, font=("PingFang TC", 12)).pack(fill="x", padx=20, pady=4)

tk.Label(root, text="執行後若已送出訊息，請留意 LINE 收件對象。ESC/左上角可停止。",
         fg="#888", font=("PingFang TC", 10)).pack(pady=6)

root.mainloop()