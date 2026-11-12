#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
設定UI  config_ui.py
讓你不寫程式就能調整 auto_click.py 的設定，存到 config.json。

用法：雙擊「設定.command」即可（等同 python3 config_ui.py）。

抓座標：按「抓①座標 / 抓②座標」→ 把滑鼠移到目標 → 按任意鍵鎖定。
把 pynput 鍵盤監聽的使用降到最少（macOS 26 已知問題：常駐監聽時按 CapsLock
切輸入法會讓整支程式崩潰），所以採「按鈕→短暫監聽→立刻關」。
⚠️ 抓座標的幾秒內，也請別用 CapsLock 切中英輸入法。
"""

import json
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

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


def load_cfg():
    cfg = dict(DEFAULTS)
    if CONFIG_FILE.exists():
        try:
            cfg.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
    return cfg


class App:
    def __init__(self, root, cfg):
        self.root = root
        self.cfg = cfg
        self._listener = None
        self._build()

    # ── 短暫監聽（只在抓座標期間存在，鎖定後立刻關）──
    def _stop_listener(self):
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None

    def grab_coord(self, ex, ey, label):
        self._stop_listener()   # 先關上一次的殘留
        top = tk.Toplevel(self.root)
        top.geometry("+40+120")
        top.attributes("-topmost", True)
        tk.Label(top,
                 text=f"把滑鼠移到【{label}】的目標位置，\n然後按鍵盤【任意鍵】鎖定（Esc 取消）",
                 font=("PingFang TC", 13)).pack(padx=24, pady=14)
        tk.Label(top, text="⚠️ 此刻勿用 CapsLock 切中英輸入法",
                 fg="#c00", font=("PingFang TC", 11)).pack(pady=(0, 10))

        state = {"done": False}

        def close():
            if state["done"]:
                return
            state["done"] = True
            self._stop_listener()
            try:
                top.destroy()
            except Exception:
                pass

        def on_capture():
            if state["done"]:
                return
            state["done"] = True
            pos = tuple(pyautogui.position())
            self._stop_listener()
            top.destroy()
            ex.delete(0, "end"); ex.insert(0, str(pos[0]))
            ey.delete(0, "end"); ey.insert(0, str(pos[1]))

        def on_press(key):
            try:
                if key == keyboard.Key.esc:
                    self.root.after(0, close)
                else:
                    self.root.after(0, on_capture)
            except Exception:
                self.root.after(0, on_capture)

        self._listener = keyboard.Listener(on_press=on_press)
        self._listener.daemon = True
        self._listener.start()
        top.protocol("WM_DELETE_WINDOW", close)

    # ── UI ──
    def _build(self):
        cfg = self.cfg

        basic = tk.LabelFrame(self.root, text="基本", padx=10, pady=8)
        basic.pack(fill="x", padx=10, pady=5)
        tk.Label(basic, text="迴圈次數（發幾個對象）：").grid(row=0, column=0, sticky="w")
        self.sp_repeat = tk.Spinbox(basic, from_=1, to=99999, width=10,
                                    textvariable=tk.StringVar(value=str(cfg.get("REPEAT_TIMES", 2))))
        self.sp_repeat.grid(row=0, column=1, sticky="w")
        tk.Label(basic, text="每步間隔秒：").grid(row=1, column=0, sticky="w")
        self.en_interval = tk.Entry(basic, width=10)
        self.en_interval.insert(0, str(cfg.get("STEP_INTERVAL", 0.3)))
        self.en_interval.grid(row=1, column=1, sticky="w")
        tk.Label(basic, text="切到下一聊天室的鍵：").grid(row=2, column=0, sticky="w")
        self.cb_switch = ttk.Combobox(basic, state="readonly", width=12,
                                      values=["↓ (down)", "Ctrl+Tab", "↑ (up)"])
        cur = cfg.get("SWITCH_CHAT_HOTKEY", ["down"])
        self.cb_switch.set({"down": "↓ (down)", "ctrl+tab": "Ctrl+Tab", "up": "↑ (up)"}.get(
            "+".join(cur), "↓ (down)"))
        self.cb_switch.grid(row=2, column=1, sticky="w")
        self.var_dry = tk.BooleanVar(value=bool(cfg.get("DRY_RUN", False)))
        tk.Checkbutton(basic, text="測試模式（只移動，不點不送）", variable=self.var_dry)\
            .grid(row=3, column=0, columnspan=2, sticky="w")
        self.var_trace = tk.BooleanVar(value=bool(cfg.get("TRACE", True)))
        tk.Checkbutton(basic, text="寫追蹤 log（除錯用）", variable=self.var_trace)\
            .grid(row=4, column=0, columnspan=2, sticky="w")

        coord = tk.LabelFrame(self.root, text="點擊座標（按『抓座標』後移滑鼠過去，按任意鍵）", padx=10, pady=8)
        coord.pack(fill="x", padx=10, pady=5)

        def make_xy(label):
            x, y = cfg.get(("CLICK_1" if label == "①" else "CLICK_2"), [0, 0])
            f = tk.Frame(coord)
            f.pack(fill="x", pady=2)
            ex = tk.Entry(f, width=6)
            ex.insert(0, str(x))
            ex.pack(side="left", padx=2)
            ey = tk.Entry(f, width=6)
            ey.insert(0, str(y))
            ey.pack(side="left", padx=2)
            tk.Button(f, text=f"抓{label}座標",
                      command=lambda e=ex, y=ey, l=label: self.grab_coord(e, y, f"{l}點")).pack(side="left", padx=4)
            return ex, ey

        self.e1x, self.e1y = make_xy("①")
        self.e2x, self.e2y = make_xy("②")

        paste = tk.LabelFrame(self.root, text="貼上內容（PASTE_TEXT）", padx=10, pady=8)
        paste.pack(fill="both", expand=True, padx=10, pady=5)
        self.txt = tk.Text(paste, height=9, width=60, font=("PingFang TC", 12))
        self.txt.insert("1.0", cfg.get("PASTE_TEXT", ""))
        self.txt.pack(fill="both", expand=True)

        bottom = tk.Frame(self.root)
        bottom.pack(fill="x", padx=10, pady=6)
        self.status = tk.StringVar(value="")
        tk.Label(bottom, textvariable=self.status, fg="#555", wraplength=360).pack(side="left")
        tk.Button(bottom, text="💾 儲存設定", command=self.on_save,
                  bg="#00bb33", fg="white", font=("PingFang TC", 13, "bold"),
                  padx=16, pady=6).pack(side="right")

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        self._stop_listener()
        self.root.destroy()

    def on_save(self):
        try:
            click1 = [int(self.e1x.get()), int(self.e1y.get())]
            click2 = [int(self.e2x.get()), int(self.e2y.get())]
            repeat = int(self.sp_repeat.get())
            interval = float(self.en_interval.get())
        except ValueError:
            messagebox.showerror("輸入錯誤", "座標/次數/間隔要填數字。")
            return
        switch = {"↓ (down)": ["down"], "Ctrl+Tab": ["ctrl", "tab"], "↑ (up)": ["up"]}[
            self.cb_switch.get()]
        cfg2 = {
            "LINE_APP_NAME": self.cfg.get("LINE_APP_NAME", "LINE"),
            "CLICK_1": click1,
            "CLICK_2": click2,
            "PASTE_TEXT": self.txt.get("1.0", "end").rstrip("\n"),
            "REPEAT_TIMES": repeat,
            "STEP_INTERVAL": interval,
            "COUNTDOWN_SEC": 3,
            "SWITCH_CHAT_HOTKEY": switch,
            "DRY_RUN": bool(self.var_dry.get()),
            "TRACE": bool(self.var_trace.get()),
        }
        CONFIG_FILE.write_text(json.dumps(cfg2, ensure_ascii=False, indent=2), encoding="utf-8")
        self.status.set(f"已儲存 → {CONFIG_FILE.name}（迴圈 {repeat} 次 · 間隔 {interval}s · "
                        f"{'測試' if self.var_dry.get() else '正式'}）")


def main():
    root = tk.Tk()
    root.title("LINE 自動化 — 設定")
    root.geometry("580x560")
    App(root, load_cfg())
    root.mainloop()


if __name__ == "__main__":
    main()