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

# ════════════════════ ★★ 設定（從 config.json 讀取） ════════════════════
# 用「設定.command」的 UI 調整即可，不用手改這支程式。
# 下面是「預設值」：只有當 config.json 不存在或讀取失敗時才會用到。
import json
from pathlib import Path
CONFIG_FILE = Path(__file__).with_name("config.json")
_DEFAULT_CONFIG = {
    "LINE_APP_NAME": "LINE",
    "CLICK_1": [917, 529],
    "CLICK_2": [659, 811],
    "PASTE_TEXT": ("各位好朋友 👋✨\n"
                   "2026 即將來到年底 🎄\n\n"
                   "想簡單調查一下 📋\n"
                   "辦什麼活動大家會有興趣參與呢？\n\n"
                   "📚 +1 讀書會\n類型不拘，會提前公布 📖\n\n"
                   "🎲 +2 桌遊\n知識性與娛樂性兼具 🧠🎉\n\n"
                   "🚴‍♂️ +3 運動\n可能是夜騎 🌙 或爬山淨山 ⛰️♻️\n\n"
                   "🤖 +4 AI 相關\n工作坊或資訊分享 💡💻\n\n"
                   "🤝 +5 聯誼活動\n手作 ✂️🎨 或對談 ☕💬\n\n"
                   "👉 回我「+數字」就可以"),
    "REPEAT_TIMES": 2,
    "PER_PERSON_REPEAT": 1,
    "SEND_ITEMS": [
        {"type": "text",
         "text": ("各位好朋友 👋✨\n"
                  "2026 即將來到年底 🎄\n\n"
                  "想簡單調查一下 📋\n"
                  "辦什麼活動大家會有興趣參與呢？\n\n"
                  "📚 +1 讀書會\n類型不拘，會提前公布 📖\n\n"
                  "🎲 +2 桌遊\n知識性與娛樂性兼具 🧠🎉\n\n"
                  "🚴‍♂️ +3 運動\n可能是夜騎 🌙 或爬山淨山 ⛰️♻️\n\n"
                  "🤖 +4 AI 相關\n工作坊或資訊分享 💡💻\n\n"
                  "🤝 +5 聯誼活動\n手作 ✂️🎨 或對談 ☕💬\n\n"
                  "👉 回我「+數字」就可以")}
    ],
    "STEP_INTERVAL": 0.3,
    "COUNTDOWN_SEC": 3,
    "SWITCH_CHAT_HOTKEY": ["down"],
    "DRY_RUN": False,
    "TRACE": True,
}


def load_config():
    cfg = dict(_DEFAULT_CONFIG)
    if CONFIG_FILE.exists():
        try:
            for k, v in json.loads(CONFIG_FILE.read_text(encoding="utf-8")).items():
                cfg[k] = v
        except Exception as e:
            print(f"⚠️ config.json 讀取失敗({e})，使用預設值。")
    return cfg


_cfg = load_config()
LINE_APP_NAME        = _cfg["LINE_APP_NAME"]
CLICK_1              = tuple(_cfg["CLICK_1"])
CLICK_2              = tuple(_cfg["CLICK_2"])
PASTE_TEXT           = _cfg["PASTE_TEXT"]
REPEAT_TIMES         = int(_cfg["REPEAT_TIMES"])
STEP_INTERVAL        = float(_cfg["STEP_INTERVAL"])
COUNTDOWN_SEC        = int(_cfg["COUNTDOWN_SEC"])
SWITCH_CHAT_HOTKEY   = tuple(_cfg["SWITCH_CHAT_HOTKEY"])
DRY_RUN              = bool(_cfg["DRY_RUN"])
TRACE                = bool(_cfg.get("TRACE", True))
TRACE_FILE           = "auto_click_trace.log"
# 發送清單 + 每人重複次數（向後相容：沒填 SEND_ITEMS 就用 PASTE_TEXT 當純文字）
PER_PERSON_REPEAT    = max(1, int(_cfg.get("PER_PERSON_REPEAT", 1)))
SEND_ITEMS           = _cfg.get("SEND_ITEMS") or [{"type": "text", "text": _cfg.get("PASTE_TEXT", "")}]
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


def put_text(txt):
    """文字/超連結 → 剪貼簿。"""
    subprocess.run(["pbcopy"], input=(txt or "").encode("utf-8"))
    time.sleep(0.3)
    return True


def put_image(path):
    """圖片 → 剪貼簿（用 NSPasteboard 放 PNG 資料）。"""
    try:
        from AppKit import (NSPasteboard, NSPasteboardTypePNG,
                            NSImage, NSBitmapImageRep)
        pb = NSPasteboard.generalPasteboard()
        pb.clearContents()
        img = NSImage.alloc().initWithContentsOfFile_(str(path))
        if img is None:
            print(f"  ⚠️ 讀不到圖片：{path}")
            return False
        rep = NSBitmapImageRep.imageRepWithData_(img.TIFFRepresentation())
        png = rep.representationUsingType_properties_(NSBitmapImageRep.NSPNGFileType, None)
        pb.setData_forType_(png, NSPasteboardTypePNG)
        time.sleep(0.2)
        return True
    except Exception as e:
        print(f"  ⚠️ 圖片進剪貼簿失敗：{e}")
        return False


def put_file(path):
    """影片/文件 → 剪貼簿（NSPasteboard 放 file URL，等同 Finder 複製檔案）。"""
    try:
        from AppKit import NSPasteboard, NSURL
        pb = NSPasteboard.generalPasteboard()
        pb.clearContents()
        ok = pb.writeObjects_([NSURL.fileURLWithPath_(str(Path(path).resolve()))])
        time.sleep(0.2)
        return bool(ok)
    except Exception as e:
        print(f"  ⚠️ 檔案進剪貼簿失敗：{e}")
        return False


def put_clipboard_for(item):
    """依項目類型把內容放進剪貼簿。type: text / link / image / file。"""
    t = item.get("type", "text")
    if t == "image":
        return put_image(item.get("path", ""))
    if t == "file":
        return put_file(item.get("path", ""))
    return put_text(item.get("text", ""))


def send_item(item, n, idx):
    """發送一個項目給目前這個人：放剪貼簿 → ⌘V → Enter 送出。"""
    ensure_line_foreground()
    ok = put_clipboard_for(item)
    if ok:
        paste_via_system()
    pause()
    ensure_line_foreground()
    pyautogui.press("enter")
    pause()
    log(f"[第{n}人] 發送#{idx} type={item.get('type','text')} prep={ok} "
        f"frontmost={frontmost_app_name()}")


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
            log(f"[第{n}人] ①點擊前 frontmost={frontmost_app_name()} ensure={e}")
            click_at(*CLICK_1); pause()

            # ② 點擊
            e = ensure_line_foreground()
            log(f"[第{n}人] ②點擊前 frontmost={frontmost_app_name()} ensure={e}")
            click_at(*CLICK_2); pause()

            # ③ 把「發送清單」每一條依序送給這個人（可重複幾輪 = PER_PERSON_REPEAT）
            done = 0
            for _ in range(PER_PERSON_REPEAT):
                for idx, item in enumerate(SEND_ITEMS, 1):
                    if STATE["stop"]:
                        raise KeyboardInterrupt()
                    send_item(item, n, idx)
                    done += 1

            # ④ 換下一個人
            e = ensure_line_foreground()
            log(f"[第{n}人] 換人前 frontmost={frontmost_app_name()}")
            pyautogui.hotkey(*SWITCH_CHAT_HOTKEY); pause()
            print(f"✅ 第 {n} 人完成（共 {REPEAT_TIMES} 人 · 每人 {done} 條）")
        except pyautogui.FailSafeException:
            print("🛑 滑鼠在左上角，緊急停止！"); break
        except KeyboardInterrupt:
            print("🛑 已停止（ESC/Ctrl+C）。"); break
    print("🏁 全部完成。")


if __name__ == "__main__":
    main()