#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
設定UI  config_ui.py
讓你不寫程式就能調整 auto_click.py 的設定（次數/座標/發送清單…），存到 config.json。

★ 發送清單：每個人會「依序」收到這些（可文字、可圖片、可檔案）
  ＋「每人也重複」可讓同一串連發 N 次。
★ 抓座標：按「抓①/②座標」→ 把滑鼠移到目標 → 按任意鍵鎖定。
★ 刻意不用 pynput：macOS 26 已知問題（常駐 pynput 監聽 + CapsLock 切輸入法
  會讓整支程式崩潰），所以全用 tkinter 自己的鍵盤事件。

用法：雙擊「設定.command」即可（等同 python3 config_ui.py）。
"""

import json
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import pyautogui
from tkinter import scrolledtext

CONFIG_FILE = Path(__file__).with_name("config.json")

# 常見圖片副檔名（用「加入圖片/檔案」時判斷是圖片還是檔案）
_IMG_EXT = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp", ".heic"}

DEFAULTS = {
    "LINE_APP_NAME": "LINE",
    "CLICK_1": [917, 529],
    "CLICK_2": [659, 811],
    "PASTE_TEXT": "各位好朋友 👋✨",
    "REPEAT_TIMES": 2,
    "PER_PERSON_REPEAT": 1,
    "SEND_ITEMS": [{"type": "text", "text": "各位好朋友 👋✨"}],
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


def _fmt_item(i, it):
    """把一筆項目格式化成一行可讀文字（顯示在清單）。"""
    t = it.get("type", "text")
    if t in ("image", "file"):
        p = it.get("path", "")
        name = p.split("/")[-1] if "/" in p else p
        return f"{i}. [{'🖼 圖片' if t == 'image' else '📎 檔案'}] {name}"
    txt = (it.get("text") or "").replace("\n", " ")
    return f"{i}. [💬 文字] {txt[:42]}{'…' if len(txt) > 42 else ''}"


class App:
    def __init__(self, root, cfg):
        self.root = root
        self.cfg = cfg
        self.items = list(cfg.get("SEND_ITEMS") or
                          [{"type": "text", "text": cfg.get("PASTE_TEXT", "")}])
        self._build()

    # ── 抓座標（用 tkinter 鍵盤事件，不用 pynput，避免 macOS 26 崩潰）──
    def grab_coord(self, ex, ey, label):
        top = tk.Toplevel(self.root)
        top.geometry("+40+120")
        top.attributes("-topmost", True)
        tk.Label(top,
                 text=f"把滑鼠移到【{label}】的目標位置，\n然後按鍵盤【任意鍵】鎖定（Esc 取消）",
                 font=("PingFang TC", 13)).pack(padx=24, pady=14)
        top.lift()
        top.focus_force()

        state = {"done": False}

        def finish(pos):
            if state["done"]:
                return
            state["done"] = True
            try:
                top.destroy()
            except Exception:
                pass
            if pos:
                ex.delete(0, "end"); ex.insert(0, str(pos[0]))
                ey.delete(0, "end"); ey.insert(0, str(pos[1]))

        def on_key(ev):
            finish(None if ev.keysym == "Escape" else tuple(pyautogui.position()))

        top.bind("<Key>", on_key)
        top.bind("<Escape>", lambda e: finish(None))
        top.protocol("WM_DELETE_WINDOW", lambda: finish(None))

    # ── 發送清單操作 ──
    def _refresh_list(self):
        self.lb.delete(0, "end")
        for i, it in enumerate(self.items, 1):
            self.lb.insert("end", _fmt_item(i, it))

    def add_text(self, index=None):
        """新增文字/超連結；index 給定時 = 編輯該筆（預先填入）。"""
        is_edit = index is not None
        top = tk.Toplevel(self.root)
        top.title("編輯文字/超連結" if is_edit else "加入文字/超連結")
        top.geometry("520x360")
        tk.Label(top, text="要發送的內容（超連結直接貼網址即可）",
                 font=("PingFang TC", 12)).pack(anchor="w", padx=12, pady=(10, 4))
        st = scrolledtext.ScrolledText(top, height=12, width=60,
                                       font=("PingFang TC", 12))
        st.pack(fill="both", expand=True, padx=12, pady=4)
        if is_edit:
            st.insert("1.0", self.items[index].get("text", ""))

        def confirm():
            txt = st.get("1.0", "end").rstrip("\n")
            if not txt.strip():
                messagebox.showwarning("空白", "內容是空的。")
                return
            if is_edit:
                self.items[index] = {"type": "text", "text": txt}
            else:
                self.items.append({"type": "text", "text": txt})
            self._refresh_list()
            top.destroy()

        tk.Button(top, text="✔ 確定", command=confirm,
                  bg="#00bb33", fg="white", font=("PingFang TC", 12, "bold"),
                  padx=14, pady=5).pack(side="right", padx=12, pady=8)

    def add_file(self, index=None):
        """新增圖片/檔案；index 給定時 = 編輯該筆（重新選檔）。"""
        kinds = [("所有檔案", "*.*"), ("圖片", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff *.webp *.heic"),
                 ("影片", "*.mp4 *.mov *.mkv *.avi"), ("文件", "*.pdf *.docx *.xlsx *.pptx *.txt")]
        path = filedialog.askopenfilename(parent=self.root, title="選擇要傳的檔案", filetypes=kinds)
        if not path:
            return
        new_item = {"type": "image", "path": path} if path.lower().endswith(
            tuple(_IMG_EXT)) else {"type": "file", "path": path}
        if index is not None:
            self.items[index] = new_item
        else:
            self.items.append(new_item)
        self._refresh_list()

    def edit_selected(self):
        """編輯目前選中的那一筆（雙擊或按『✏ 編輯』）。"""
        sel = self.lb.curselection()
        if not sel:
            messagebox.showinfo("提示", "先在清單選一條要編輯的。")
            return
        i = sel[0]
        if self.items[i].get("type") == "text":
            self.add_text(index=i)
        else:
            self.add_file(index=i)

    def _move(self, d):
        sel = self.lb.curselection()
        if not sel:
            return
        i = sel[0]
        j = i + d
        if not (0 <= j < len(self.items)):
            return
        self.items[i], self.items[j] = self.items[j], self.items[i]
        self._refresh_list()
        self.lb.selection_set(j)

    def _delete(self):
        sel = self.lb.curselection()
        if not sel:
            return
        self.items.pop(sel[0])
        self._refresh_list()

    # ── UI ──
    def _build(self):
        cfg = self.cfg

        basic = tk.LabelFrame(self.root, text="基本", padx=10, pady=8)
        basic.pack(fill="x", padx=10, pady=5)
        tk.Label(basic, text="迴圈次數（發幾個對象）：").grid(row=0, column=0, sticky="w")
        self.sp_repeat = tk.Spinbox(basic, from_=1, to=99999, width=10,
                                    textvariable=tk.StringVar(value=str(cfg.get("REPEAT_TIMES", 2))))
        self.sp_repeat.grid(row=0, column=1, sticky="w", padx=(2, 18))
        tk.Label(basic, text="每步間隔秒：").grid(row=0, column=2, sticky="w")
        self.en_interval = tk.Entry(basic, width=7)
        self.en_interval.insert(0, str(cfg.get("STEP_INTERVAL", 0.3)))
        self.en_interval.grid(row=0, column=3, sticky="w", padx=(2, 18))
        tk.Label(basic, text="切到下一聊天室：").grid(row=1, column=0, sticky="w")
        self.cb_switch = ttk.Combobox(basic, state="readonly", width=10,
                                      values=["↓ (down)", "Ctrl+Tab", "↑ (up)"])
        cur = cfg.get("SWITCH_CHAT_HOTKEY", ["down"])
        self.cb_switch.set({"down": "↓ (down)", "ctrl+tab": "Ctrl+Tab", "up": "↑ (up)"}.get(
            "+".join(cur), "↓ (down)"))
        self.cb_switch.grid(row=1, column=1, sticky="w", padx=(2, 18))
        tk.Label(basic, text="每人也重複(輪)：").grid(row=1, column=2, sticky="w")
        self.sp_ppr = tk.Spinbox(basic, from_=1, to=99, width=7,
                                 textvariable=tk.StringVar(value=str(cfg.get("PER_PERSON_REPEAT", 1))))
        self.sp_ppr.grid(row=1, column=3, sticky="w", padx=(2, 10))
        self.var_dry = tk.BooleanVar(value=bool(cfg.get("DRY_RUN", False)))
        tk.Checkbutton(basic, text="測試模式（只移動不點不送）", variable=self.var_dry)\
            .grid(row=2, column=0, columnspan=2, sticky="w")
        self.var_trace = tk.BooleanVar(value=bool(cfg.get("TRACE", True)))
        tk.Checkbutton(basic, text="寫追蹤 log", variable=self.var_trace)\
            .grid(row=2, column=2, columnspan=2, sticky="w")

        coord = tk.LabelFrame(self.root, text="點擊座標（按『抓座標』後移滑鼠過去，按任意鍵）", padx=10, pady=8)
        coord.pack(fill="x", padx=10, pady=5)

        def make_xy(label):
            x, y = cfg.get(("CLICK_1" if label == "①" else "CLICK_2"), [0, 0])
            f = tk.Frame(coord)
            f.pack(fill="x", pady=2)
            ex = tk.Entry(f, width=6); ex.insert(0, str(x)); ex.pack(side="left", padx=2)
            ey = tk.Entry(f, width=6); ey.insert(0, str(y)); ey.pack(side="left", padx=2)
            tk.Button(f, text=f"抓{label}座標",
                      command=lambda e=ex, y=ey, l=label: self.grab_coord(e, y, f"{l}點")).pack(side="left", padx=4)
            return ex, ey

        self.e1x, self.e1y = make_xy("①")
        self.e2x, self.e2y = make_xy("②")

        send = tk.LabelFrame(self.root, text="發送清單（每人都會依序收到這些）＋ 也可重複多輪", padx=10, pady=8)
        send.pack(fill="both", expand=True, padx=10, pady=5)
        self.lb = tk.Listbox(send, height=7, font=("PingFang TC", 12),
                             selectmode=tk.SINGLE)
        self.lb.pack(fill="both", expand=True)
        self.lb.bind("<Double-Button-1>", lambda e: self.edit_selected())
        row = tk.Frame(send)
        row.pack(fill="x", pady=(6, 0))
        tk.Button(row, text="＋ 加入文字/超連結", command=self.add_text,
                  font=("PingFang TC", 11)).pack(side="left", padx=2)
        tk.Button(row, text="＋ 加入圖片/檔案", command=self.add_file,
                  font=("PingFang TC", 11)).pack(side="left", padx=2)
        tk.Button(row, text="✏ 編輯(選取後點/雙擊)", command=self.edit_selected,
                  font=("PingFang TC", 11)).pack(side="left", padx=2)
        tk.Button(row, text="↑ 上移", command=lambda: self._move(-1),
                  font=("PingFang TC", 11)).pack(side="left", padx=2)
        tk.Button(row, text="↓ 下移", command=lambda: self._move(1),
                  font=("PingFang TC", 11)).pack(side="left", padx=2)
        tk.Button(row, text="🗑 刪除", command=self._delete,
                  font=("PingFang TC", 11)).pack(side="left", padx=2)
        self._refresh_list()

        bottom = tk.Frame(self.root)
        bottom.pack(fill="x", padx=10, pady=6)
        self.status = tk.StringVar(value="")
        tk.Label(bottom, textvariable=self.status, fg="#555", wraplength=340).pack(side="left")
        tk.Button(bottom, text="💾 儲存設定", command=self.on_save,
                  bg="#00bb33", fg="white", font=("PingFang TC", 13, "bold"),
                  padx=14, pady=6).pack(side="right")
        tk.Button(bottom, text="① 對齊", command=lambda: self.next_step("mouse_position.py"),
                  font=("PingFang TC", 12)).pack(side="right", padx=4)
        tk.Button(bottom, text="▶ 開始執行", command=lambda: self.next_step("auto_click.py"),
                  font=("PingFang TC", 12, "bold")).pack(side="right", padx=4)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        self.root.destroy()

    def _save_cfg(self):
        try:
            click1 = [int(self.e1x.get()), int(self.e1y.get())]
            click2 = [int(self.e2x.get()), int(self.e2y.get())]
            repeat = int(self.sp_repeat.get())
            interval = float(self.en_interval.get())
            ppr = int(self.sp_ppr.get())
        except ValueError:
            messagebox.showerror("輸入錯誤", "座標/次數/間隔/重複要填數字。")
            return False
        switch = {"↓ (down)": ["down"], "Ctrl+Tab": ["ctrl", "tab"], "↑ (up)": ["up"]}[
            self.cb_switch.get()]
        # 從清單讀出發送項目；第一個 text 拿來當 PASTE_TEXT 向後相容
        txt0 = next((it.get("text", "") for it in self.items if it.get("type") == "text"), "")
        cfg2 = {
            "LINE_APP_NAME": self.cfg.get("LINE_APP_NAME", "LINE"),
            "CLICK_1": click1,
            "CLICK_2": click2,
            "PASTE_TEXT": txt0,
            "REPEAT_TIMES": repeat,
            "PER_PERSON_REPEAT": ppr,
            "SEND_ITEMS": self.items,
            "STEP_INTERVAL": interval,
            "COUNTDOWN_SEC": 3,
            "SWITCH_CHAT_HOTKEY": switch,
            "DRY_RUN": bool(self.var_dry.get()),
            "TRACE": bool(self.var_trace.get()),
        }
        CONFIG_FILE.write_text(json.dumps(cfg2, ensure_ascii=False, indent=2), encoding="utf-8")
        self.status.set(f"已儲存 → {CONFIG_FILE.name}（發 {repeat} 人 · 每人 {len(self.items)} 條×{ppr} 輪）")
        return True

    def on_save(self):
        self._save_cfg()

    def next_step(self, target):
        if not self._save_cfg():
            return
        try:
            subprocess.Popen([sys.executable, str(Path(__file__).parent / target)])
        except Exception as e:
            messagebox.showerror("啟動失敗", f"無法啟動 {target}\n{e}")
            return
        self.root.after(300, self._on_close)


def main():
    root = tk.Tk()
    root.title("LINE 自動化 — 設定")
    root.geometry("620x660")
    App(root, load_cfg())
    root.mainloop()


if __name__ == "__main__":
    main()