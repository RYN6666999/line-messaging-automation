#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
設定UI  config_ui.py
讓你不寫程式就能調整 auto_click.py 的設定，存到 config.json。

用法：雙擊「設定.command」即可（等同 python3 config_ui.py）。

快捷抓座標：
  把滑鼠移到目標位置，按鍵盤 F2 → 填入第①點、F3 → 填入第②點。
（這樣你不用在那邊開工具看數字再慢慢打字）
"""

import json
import queue
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

import pyautogui
from pynput import keyboard

CONFIG_FILE = Path(__file__).with_name("config.json")

DEFAULTS = {
    "LINE_APP_NAME": "LINE",
    "CLICK_1": [917, 529],
    "CLICK_2": [659, 811],
    "PASTE_TEXT": "各位好朋友 👋✨\n2026 即將來到年底 🎄\n\n想簡單調查一下 📋\n辦什麼活動大家會有興趣參與呢？",
    "REPEAT_TIMES": 2,
    "STEP_INTERVAL": 0.3,
    "COUNTDOWN_SEC": 3,
    "SWITCH_CHAT_HOTKEY": ["down"],
    "DRY_RUN": False,
    "TRACE": True,
}

# 快捷鍵→座標填入：(F2 填 CLICK_1, F3 填 CLICK_2)
_q = queue.Queue()


def on_press(key):
    try:
        if key == keyboard.Key.f2:
            _q.put(("c1", tuple(pyautogui.position())))
        elif key == keyboard.Key.f3:
            _q.put(("c2", tuple(pyautogui.position())))
    except Exception:
        pass


_listener = keyboard.Listener(on_press=on_press)
_listener.daemon = True
_listener.start()


def load_cfg():
    cfg = dict(DEFAULTS)
    if CONFIG_FILE.exists():
        try:
            cfg.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
    return cfg


def build_form(root, cfg):
    # ── 基本 ──
    basic = tk.LabelFrame(root, text="基本", padx=10, pady=8)
    basic.pack(fill="x", padx=10, pady=5)

    tk.Label(basic, text="迴圈次數（發幾個對象）：").grid(row=0, column=0, sticky="w")
    sp_repeat = tk.Spinbox(basic, from_=1, to=99999, width=10,
                           textvariable=tk.StringVar(value=str(cfg.get("REPEAT_TIMES", 2))))
    sp_repeat.grid(row=0, column=1, sticky="w")

    tk.Label(basic, text="每步間隔秒（正值，1=較慢保險）：").grid(row=1, column=0, sticky="w")
    en_interval = tk.Entry(basic, width=10)
    en_interval.insert(0, str(cfg.get("STEP_INTERVAL", 0.3)))
    en_interval.grid(row=1, column=1, sticky="w")

    tk.Label(basic, text="切到下一聊天室的鍵：").grid(row=2, column=0, sticky="w")
    cb_switch = ttk.Combobox(basic, state="readonly", width=12,
                             values=["↓ (down)", "Ctrl+Tab", "↑ (up)"])
    cur = cfg.get("SWITCH_CHAT_HOTKEY", ["down"])
    cb_switch.set({"down": "↓ (down)", "ctrl+tab": "Ctrl+Tab", "up": "↑ (up)"}.get(
        "+".join(cur), "↓ (down)"))
    cb_switch.grid(row=2, column=1, sticky="w")

    var_dry = tk.BooleanVar(value=bool(cfg.get("DRY_RUN", False)))
    tk.Checkbutton(basic, text="測試模式（只移動，不點不送）", variable=var_dry)\
        .grid(row=3, column=0, columnspan=2, sticky="w")

    var_trace = tk.BooleanVar(value=bool(cfg.get("TRACE", True)))
    tk.Checkbutton(basic, text="寫追蹤 log（除錯用）", variable=var_trace)\
        .grid(row=4, column=0, columnspan=2, sticky="w")

    # ── 座標 ──
    coord = tk.LabelFrame(root, text="點擊座標（把滑鼠移到位置按快捷鍵抓取）", padx=10, pady=8)
    coord.pack(fill="x", padx=10, pady=5)

    def make_xy(label, key):
        x, y = cfg.get(key, [0, 0])
        f = tk.Frame(coord)
        f.pack(fill="x", pady=2)
        tk.Label(f, text=label, width=14, anchor="w").pack(side="left")
        ex = tk.Entry(f, width=6)
        ex.insert(0, str(x))
        ex.pack(side="left", padx=2)
        tk.Label(f, text="X").pack(side="left")
        ey = tk.Entry(f, width=6)
        ey.insert(0, str(y))
        ey.pack(side="left", padx=2)
        tk.Label(f, text="Y").pack(side="left")
        return (ex, ey)

    e1x, e1y = make_xy("① 點擊1", "CLICK_1")
    e2x, e2y = make_xy("② 點擊2", "CLICK_2")
    tk.Label(coord, text="提示：滑鼠停在目標上 → 按 F2(填①) / F3(填②)",
             fg="#666").pack(anchor="w", pady=(4, 0))

    # ── 貼上內容 ──
    paste = tk.LabelFrame(root, text="貼上內容（PASTE_TEXT）", padx=10, pady=8)
    paste.pack(fill="both", expand=True, padx=10, pady=5)
    txt = tk.Text(paste, height=9, width=60, font=("PingFang TC", 12))
    txt.insert("1.0", cfg.get("PASTE_TEXT", ""))
    txt.pack(fill="both", expand=True)

    # ── 底部按鈕 ──
    bottom = tk.Frame(root)
    bottom.pack(fill="x", padx=10, pady=6)

    status = tk.StringVar(value="")
    tk.Label(bottom, textvariable=status, fg="#555").pack(side="left")

    def on_save():
        try:
            click1 = [int(e1x.get()), int(e1y.get())]
            click2 = [int(e2x.get()), int(e2y.get())]
            repeat = int(sp_repeat.get())
            interval = float(en_interval.get())
        except ValueError:
            messagebox.showerror("輸入錯誤", "座標/次數/間隔要填數字。")
            return
        switch = {"↓ (down)": ["down"], "Ctrl+Tab": ["ctrl", "tab"], "↑ (up)": ["up"]}[
            cb_switch.get()]
        cfg2 = {
            "LINE_APP_NAME": cfg.get("LINE_APP_NAME", "LINE"),
            "CLICK_1": click1,
            "CLICK_2": click2,
            "PASTE_TEXT": txt.get("1.0", "end").rstrip("\n"),
            "REPEAT_TIMES": repeat,
            "STEP_INTERVAL": interval,
            "COUNTDOWN_SEC": 3,
            "SWITCH_CHAT_HOTKEY": switch,
            "DRY_RUN": bool(var_dry.get()),
            "TRACE": bool(var_trace.get()),
        }
        CONFIG_FILE.write_text(json.dumps(cfg2, ensure_ascii=False, indent=2),
                               encoding="utf-8")
        status.set(f"已儲存 → {CONFIG_FILE.name}（迴圈 {repeat} 次 · "
                   f"間隔 {interval}s · {'測試' if var_dry.get() else '正式'}）")

    tk.Button(bottom, text="💾 儲存設定", command=on_save,
              bg="#00bb33", fg="white", font=("PingFang TC", 13, "bold"),
              padx=16, pady=6).pack(side="right")

    # ── F2/F3 抓座標的即時填入（透過 queue 回收、並非跨執行緒動 widget）──
    def pump():
        try:
            while True:
                which, (x, y) = _q.get_nowait()
                if which == "c1":
                    e1x.delete(0, "end"); e1x.insert(0, str(x))
                    e1y.delete(0, "end"); e1y.insert(0, str(y))
                else:
                    e2x.delete(0, "end"); e2x.insert(0, str(x))
                    e2y.delete(0, "end"); e2y.insert(0, str(y))
        except Exception:
            pass
        root.after(100, pump)
    root.after(100, pump)


def main():
    root = tk.Tk()
    root.title("LINE 自動化 — 設定")
    root.geometry("560x560")
    cfg = load_cfg()
    build_form(root, cfg)
    root.mainloop()


if __name__ == "__main__":
    main()