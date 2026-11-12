#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_click.py — 在 LINE 上反覆：點擊→點擊→貼上→Enter→往下
開始時彈出懸浮窗按 Enter；每輪前把 LINE 叫到前景；ESC 停止
DRY_RUN=True 時只移動滑鼠到座標、不執行動作，方便先測試位置。
"""

import time
import subprocess
import tkinter as tk
import pyautogui
from pynput import keyboard

# ════════════════════ ★★ 設定區（只改這裡） ════════════════════
LINE_APP_NAME = "LINE"          # LINE 的 App 名稱
CLICK_1 = (917, 529)            # 步驟1：輸入框位置
CLICK_2 = (659, 811)            # 步驟2：點擊位置
PASTE_TEXT = """各位好朋友 👋✨
2026 即將來到年底 🎄

想簡單調查一下 📋
辦什麼活動大家會有興趣參與呢？

📚 +1 讀書會
類型不拘，會提前公布 📖

🎲 +2 桌遊
知識性與娛樂性兼具 🧠🎉

🚴‍♂️ +3 運動
可能是夜騎 🌙 或爬山淨山 ⛰️♻️

🤖 +4 AI 相關
工作坊或資訊分享 💡💻

🤝 +5 聯誼活動
手作 ✂️🎨 或對談 ☕💬

👉 回我「+數字」就可以"""   # 每次貼這一段
REPEAT_TIMES = 2                # 先測真動作：2次（確認對再放大）
STEP_INTERVAL = 0.3             # 每個步驟之間固定等 0.3 秒
COUNTDOWN_SEC = 3               # 按 Enter 後倒數(秒)

# 切到下一個聊天室的鍵（你實測過是 ↓，所以用方向鍵下）
# 若之後想換別的鍵，改成例如 ("ctrl","tab") 或 ("down",)
SWITCH_CHAT_HOTKEY = ("down",)

# ★ 測試開關：True=只移動滑鼠檢查座標(不點不貼不送出)；False=真的跑
DRY_RUN = False

# ★ 追蹤開關：True=把每一動的「前景App/滑鼠位置/剪貼簿」寫進 auto_click_trace.log
#             用來驗證點擊到底有沒有作用在 LINE 上（排錯用）
TRACE = True
TRACE_FILE = "auto_click_trace.log"
# ════════════════════ 設定區結束 ════════════════════

STATE = {"start": False, "stop": False}


def on_press(key):
    """背景監聽：Enter=開始；ESC=取消/停止。開始也可以滑鼠點『▶開始』。"""
    if key == keyboard.Key.enter:
        STATE["start"] = True
    elif key == keyboard.Key.esc:
        STATE["stop"] = True


listener = keyboard.Listener(on_press=on_press)
listener.daemon = True
listener.start()


def osa(script):
    """跑一段 AppleScript，回傳輸出文字（失敗回 None）。"""
    try:
        r = subprocess.run(["osascript", "-e", script],
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def activate_line():
    """把 LINE 叫到螢幕最前面（必須在前景，座標才點得對）。"""
    ok = osa(f'tell application "{LINE_APP_NAME}" to activate')
    time.sleep(0.5)
    return ok is not None


def frontmost_app_name():
    """讀『當下最前面的App』名稱（例如 LINE / Python / Safari）。失敗回 '?'。"""
    try:
        from AppKit import NSWorkspace
        nm = NSWorkspace.sharedWorkspace().frontmostApplication().localizedName()
        return nm or "?"
    except Exception:
        return "?"


def foreground_is_line():
    """極快(約0.0001秒)讀出『當下最前面的App』是不是LINE。回 True/False/None。"""
    return (frontmost_app_name() == LINE_APP_NAME)


def log(msg):
    """追蹤：把一行訊息寫進 auto_click_trace.log（TRACE=False 時不寫）。"""
    if not TRACE:
        return
    try:
        with open(TRACE_FILE, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")
    except Exception:
        pass


def ensure_line_foreground():
    """嚴格確保 LINE 在前景（每一個動作前呼叫）：
    讀『當下前景App』，是LINE就直接做(零成本)；不是則拉回並重驗(最多3次)；
    仍失敗就印警告。回 True=確認在前景 / False=不確定。"""
    for _ in range(3):
        try:
            if foreground_is_line() is True:
                return True            # 確認是 LINE，直接做
        except Exception:
            pass
        activate_line()                # 不是 LINE → 叫回
        time.sleep(0.4)                # 等切換生效
    print("   ⚠️ 無法確認 LINE 在前景（可能要點到別的地方）")
    return False


def click_at(x, y, dwell=0.25):
    """穩健點擊：macOS 上 pyautogui.click() 有時只『移到』沒『點到』(已知問題#467)。
    做法：慢慢移過去並停留(讓 macOS 處理 hover)，再用 pynput Controller 發真正左鍵；
    pynput 失敗就回退 pyautogui mouseDown/Up。"""
    pyautogui.moveTo(x, y, duration=0.15)   # 慢慢移，別瞬移
    time.sleep(dwell)                        # 停留：避免太快被系統吞掉
    try:
        from pynput.mouse import Controller, Button
        mc = Controller()
        mc.position = (x, y)
        mc.press(Button.left)
        time.sleep(0.05)
        mc.release(Button.left)
    except Exception:
        pyautogui.mouseDown()
        time.sleep(0.05)
        pyautogui.mouseUp()
    time.sleep(0.05)


def paste_via_system():
    """貼上 ⌘V（用 pyautogui 手動按鍵：全程按住 command，避免中文輸入法漏成 v/ㄒ）。
    註：不要用 System Events — 那需要 osascript 的輔助使用權限，多數環境沒有(錯1002)。"""
    try:
        pyautogui.keyDown("command"); time.sleep(0.08)
        pyautogui.keyDown("v");      time.sleep(0.08)
        pyautogui.keyUp("v");        time.sleep(0.08)
        pyautogui.keyUp("command")
    except Exception as e:
        print(f"   ⚠️ 貼上例外：{e}")
    time.sleep(0.2)


def show_align_overlay():
    """開始前的指示小窗（放在畫面角落，絕不畫在點擊座標上 — 
    標記視窗蓋在點擊點會吃掉滑鼠事件，導致點擊打不到 LINE）。
    對好位置後按 Enter 開始，按 ESC 取消。"""
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    wins = [root]

    # 指示窗(置頂、不擋操作，位置在畫面上方，不會擋 LINE 的點擊)
    info = tk.Toplevel(root)
    info.overrideredirect(True)
    info.attributes("-topmost", True)
    info.geometry(f"+{pyautogui.size()[0] // 2 - 240}+30")
    box = tk.Frame(info, bg="black")
    box.pack()
    tk.Label(box, text="準備好後按 Enter 或滑鼠點『開始』（ESC 取消）：",
             bg="black", fg="white",
             font=("PingFang TC", 14, "bold")).pack(padx=16, pady=6)
    # 按鈕不抓鍵盤焦點(takefocus=0)：Enter 的開啟統一由 pynput 處理；滑鼠點擊仍有效
    tk.Button(box, text="▶ 開始（一律用滑鼠點）",
              command=lambda: STATE.update(start=True),
              takefocus=0,
              font=("PingFang TC", 15, "bold"), bg="#00bb33", fg="white",
              activebackground="#00dd44", padx=20, pady=8).pack(padx=16, pady=10)
    info.update_idletasks()
    wins.append(info)

    def keep_on_top():
        # 拖 LINE 時標記可能被蓋，每 200ms 重新置頂；視窗關閉後就自動停
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

    def poll():
        if STATE["start"] or STATE["stop"]:      # 點『開始』或按 ESC
            for w in wins:
                try:
                    w.withdraw()
                    w.destroy()
                except Exception:
                    pass
            try:
                root.update()                    # 讓視窗真正從螢幕移除，不擋點擊
            except Exception:
                pass
            return
        info.after(50, poll)                     # 用 info 當主迴圈
    info.after(200, keep_on_top)
    info.after(50, poll)
    root.mainloop()


def pause():
    """每個步驟之間固定等 STEP_INTERVAL 秒。"""
    time.sleep(STEP_INTERVAL)


def main():
    pyautogui.FAILSAFE = True        # 滑鼠到左上角(0,0)立刻中斷
    pyautogui.PAUSE = 0.1
    pyautogui.DARWIN_CATCH_UP_TIME = 0.05   # macOS：事件後多補時差，減少被吞

    print("🪟 準備好後按 Enter 開始（ESC 取消）。"
          + ("此時是測試模式(只移動不點擊)" if DRY_RUN
             else "⚠️ 正式模式，會真的送出訊息") + "。")
    show_align_overlay()          # 畫標記 + 等你拖 LINE 對齊、按 Enter

    if STATE["stop"]:             # 在疊加層按了 ESC → 取消
        print("🛑 已取消，未開始。"); return

    if activate_line():
        print("→ 已把 LINE 叫到最前面")
    else:
        print("⚠️  找不到 LINE，請先開 LINE")

    if DRY_RUN:
        # ── 測試模式：只把滑鼠移到每個動作座標，讓你看滑鼠停在哪 ──
        print(f"…測試模式，{COUNTDOWN_SEC} 秒後把滑鼠依序停到每個位置（不執行）：")
        for i in range(COUNTDOWN_SEC, 0, -1):
            print(f"   {i} 秒…"); time.sleep(1)
        for _ in range(REPEAT_TIMES):
            if STATE["stop"]:
                print("🛑 ESC，已結束。"); break
            for x, y, name in [(CLICK_1[0], CLICK_1[1], "輸入框"),
                               (CLICK_2[0], CLICK_2[1], "步驟2")]:
                pyautogui.moveTo(x, y)          # 只移動，不點擊
                print(f"   → 滑鼠停在 {name} ({x},{y})…ESC可停")
                time.sleep(1.0)                 # 停一秒讓你看
        pyautogui.moveTo(0, 0)
        print("\n🏁 測試結束。滑鼠停的位置都對的話，"
              "把 DRY_RUN 改成 False 再正式跑。")
        return

    # ── 正式模式 ──
    print(f"✅ 開始！ {COUNTDOWN_SEC} 秒後執行（停止=ESC / 滑鼠甩左上角 / Ctrl+C）")
    for i in range(COUNTDOWN_SEC, 0, -1):
        print(f"   {i} 秒…"); time.sleep(1)

    for n in range(1, REPEAT_TIMES + 1):
        if STATE["stop"]:
            print("🛑 ESC，已結束迴圈。"); break
        try:
            # ① 點輸入框
            e = ensure_line_foreground()
            log(f"[第{n}次] ①點擊前 frontmost={frontmost_app_name()} ensure={e} mouse={pyautogui.position()}")
            click_at(*CLICK_1); pause()
            log(f"[第{n}次] ①點擊後 mouse={pyautogui.position()} frontmost={frontmost_app_name()}")

            # ② 點擊
            e = ensure_line_foreground()
            log(f"[第{n}次] ②點擊前 frontmost={frontmost_app_name()} ensure={e} mouse={pyautogui.position()}")
            click_at(*CLICK_2); pause()
            log(f"[第{n}次] ②點擊後 mouse={pyautogui.position()} frontmost={frontmost_app_name()}")

            # ③ 貼上
            e = ensure_line_foreground()
            cb0 = len(subprocess.run(["pbpaste"], capture_output=True, text=True).stdout)
            subprocess.run(["pbcopy"], input=PASTE_TEXT.encode("utf-8"))
            time.sleep(0.3)
            paste_via_system()
            cb1 = len(subprocess.run(["pbpaste"], capture_output=True, text=True).stdout)
            log(f"[第{n}次] ③貼上 ensure={e} 剪貼簿:{cb0}->{cb1}字 frontmost={frontmost_app_name()} mouse={pyautogui.position()}")
            pause()

            # ④ Enter=送出
            e = ensure_line_foreground()
            log(f"[第{n}次] ④Enter前 frontmost={frontmost_app_name()} ensure={e}")
            pyautogui.press("enter"); pause()
            log(f"[第{n}次] ④Enter後 frontmost={frontmost_app_name()}")

            # ⑤ 切到下一個聊天室
            e = ensure_line_foreground()
            log(f"[第{n}次] ⑤↓前 frontmost={frontmost_app_name()} ensure={e}")
            pyautogui.hotkey(*SWITCH_CHAT_HOTKEY); pause()
            log(f"[第{n}次] ⑤↓後 frontmost={frontmost_app_name()}")
            print(f"✅ 第 {n} 次完成（共 {REPEAT_TIMES} 次）")
        except pyautogui.FailSafeException:
            print("🛑 滑鼠在左上角，緊急停止！"); break
        except KeyboardInterrupt:
            print("🛑 Ctrl+C 中止。"); break
    print("🏁 全部完成。")


if __name__ == "__main__":
    main()