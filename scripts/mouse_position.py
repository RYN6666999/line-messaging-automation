#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
找座標＋對齊工具  mouse_position.py

功能：
  1) 在 CLICK_1 / CLICK_2 兩個「點擊座標」上畫紅色十字標記（半透明），
     讓你把 LINE 視窗拖來對齊（輸入框對①、步驟2對②）。
  2) 每 0.3 秒印一次目前滑鼠座標，方便微調。
  3) 按 ESC 結束（標記自動消失）。

用法：雙擊「測座標.command」即可（或 python3 ~/Desktop/mouse_position.py）。
座標要改就改下面的 CLICK_1 / CLICK_2（跟 auto_click.py 的保持一致）。
"""

import time
import tkinter as tk
import pyautogui
from pynput import keyboard

# ── 設定：跟 auto_click.py 的點擊座標保持一致（想改就改這裡）──
CLICK_1 = (917, 529)      # 第1個點擊位置（LINE 的輸入框）
CLICK_2 = (659, 811)      # 第2個點擊位置
# ──────────────────────────────────────────────


# 按 ESC = 結束（標記消失）
STATE = {"stop": False}


def on_press(key):
    if key == keyboard.Key.esc:
        STATE["stop"] = True


listener = keyboard.Listener(on_press=on_press)
listener.daemon = True
listener.start()


def add_marker(root, x, y, tag, wins):
    """在 (x,y) 建一個 110x110 半透明的十字+圓圈標記窗，標『tag』。"""
    w = 110
    wnd = tk.Toplevel(root)
    wnd.overrideredirect(True)
    wnd.attributes("-topmost", True)
    wnd.attributes("-alpha", 0.35)              # 半透明，底下 LINE 看得到
    wnd.geometry(f"{w}x{w}+{x - w // 2}+{y - w // 2}")
    cv = tk.Canvas(wnd, width=w, height=w, bg="black", highlightthickness=0)
    cv.pack()
    cv.create_line(w // 2, 14, w // 2, w - 14, fill="red", width=3)     # 十字
    cv.create_line(14, w // 2, w - 14, w // 2, fill="red", width=3)
    cv.create_oval(w // 2 - 11, w // 2 - 11, w // 2 + 11, w // 2 + 11,
                   outline="yellow", width=3)                            # 黃圓圈
    cv.create_text(w // 2, 14, text=tag, fill="lime",
                   font=("PingFang TC", 13, "bold"))
    wins.append(wnd)


def main():
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    wins = [root]

    add_marker(root, CLICK_1[0], CLICK_1[1], "①點擊1", wins)
    add_marker(root, CLICK_2[0], CLICK_2[1], "②點擊2", wins)

    info = tk.Toplevel(root)
    info.overrideredirect(True)
    info.attributes("-topmost", True)
    info.geometry(f"+{pyautogui.size()[0] // 2 - 220}+30")
    tk.Label(info, text="拖 LINE 對齊標記；下面印滑鼠座標；按 ESC 結束",
             bg="black", fg="lime", font=("PingFang TC", 13, "bold"),
             padx=14, pady=6).pack()
    info.update_idletasks()
    wins.append(info)

    print(f"對齊工具：①標記在 {CLICK_1}，②標記在 {CLICK_2}。")
    print("拖 LINE 視窗把『輸入框』對到 ①、『步驟2』對到 ②；下面會印滑鼠座標。按 ESC 結束。")

    def coords():
        if STATE["stop"]:
            return
        x, y = pyautogui.position()
        print(f"   X={x:>5}   Y={y:>5}", flush=True)
        info.after(300, coords)

    def poll():
        if STATE["stop"]:
            for w in wins:
                try:
                    w.withdraw()
                    w.destroy()
                except Exception:
                    pass
            return
        info.after(50, poll)

    def keep_on_top():
        # 拖 LINE 時標記可能被蓋，每 200ms 重新置頂 → 標記永遠可見
        if STATE["stop"]:
            return
        try:
            for w in wins:
                try:
                    w.lift()
                    w.attributes("-topmost", True)
                except Exception:
                    pass
            info.after(200, keep_on_top)
        except Exception:
            pass

    info.after(300, coords)
    info.after(50, poll)
    info.after(200, keep_on_top)
    root.mainloop()
    print("結束（標記已清除）。")


if __name__ == "__main__":
    main()