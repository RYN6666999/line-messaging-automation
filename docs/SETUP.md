# 設定與使用說明（真的能跑）

> 照這份做，就能把這個專案跑起來。目標是讓「沒有資工背景的人」也能自己設定、執行、安全停止。

---

## 1. 需求

- macOS（Apple Silicon 或 Intel 皆可）
- Python 3（macOS 通常已內建；用 `python3 --version` 確認）

## 2. 安裝（終端機一次搞定）

```bash
python3 -m pip install pyautogui pynput
```

驗證裝好了：
```bash
python3 -c "import pyautogui, pynput; print('ok')"   # 印出 ok 即成功
```

> 如果腳本報 `No module named 'pyautogui'`，通常是「多個 Python」造成 — 用 `which -a python3` 看你有幾個，統一用有套件的那個來跑（或改 `.command` 檔裡的 `PY=/usr/local/bin/python3` 那行）。

## 3. 權限（很重要，只有第一次要做）

macOS 會擋滑鼠／鍵盤控制，需要授權給「實際執行的程式」：

1. 開啟「**系統設定 → 隱私權與安全性 → 輔助使用**」
2. 按「＋」把「**終端機**」加進去並打勾（如果你用其他方式跑，就授權給那支程式）
3. **完全退出終端機（Cmd+Q），再重開** — 權限才會生效

> 症狀判別：腳本能動但滑鼠沒反應 ＝ 權限沒生效。

## 4. 對齊（準備階段）

座標是「絕對螢幕座標」，只在你「量座標時的那個 LINE 視窗位置／大小」下才準，所以要先對齊：

```bash
python3 mouse_position.py
```
會在全螢幕標出兩個點（①、②）。把 LINE 視窗拖到「輸入框對到 ①、步驟2 對到 ②」，按 `ESC` 結束。
標記會自動置頂、拖視窗也不消失。

## 5. 設定（只改一個檔）

開啟 `auto_click.py`，改最上方的「★★ 設定區 ★★」：

| 設定 | 說明 |
|---|---|
| `CLICK_1` / `CLICK_2` | 兩個點擊座標（用 mouse_position.py 對齊後照抄） |
| `PASTE_TEXT` | 要貼上的內容（中文／emoji／換行都行） |
| `REPEAT_TIMES` | 要發給幾個對象（跑幾次） |
| `STEP_INTERVAL` | 每個步驟間隔秒數（預設 0.3；量大建議 1.5–2 避免被限流） |
| `SWITCH_CHAT_HOTKEY` | 切到下一位的鍵（`("down",)`＝↓） |
| `DRY_RUN` | `True`＝只移動不點不送（測試）；`False`＝真的執行 |
| `TRACE` | `True`＝每次執行寫 `auto_click_trace.log`（除錯用） |

## 6. 執行與停止

```bash
python3 auto_click.py
```
1. 按 `Enter` 開始（或點螢幕上的「開始」）。
2. 倒數後自動執行。
3. **停止**：按 `ESC`（下一輪前生效）／把滑鼠甩到螢幕**左上角**／`Ctrl+C`。

## 7. 建議的安全流程（先別急著放量）

1. `DRY_RUN = True`：只移動，確認座標都對。
2. `DRY_RUN = False`＋`REPEAT_TIMES = 1`＋在**無關緊要的聊天室**跑一次，確認貼上完整、真的有送出。
3. 確認沒問題後，再把 `REPEAT_TIMES` 調到你想要的量。

## 8. 常見問題快速排除

| 症狀 | 可能原因 | 解法 |
|---|---|---|
| 雙擊 `.py` 沒反應 | macOS 雙擊 .py 只會開編輯器 | 用 `python3 auto_click.py` 跑，或雙擊附的 `.command` |
| `No module named 'pyautogui'` | 多個 Python | 固定用有套件的那個（見 §2） |
| 沒動作 | 缺輔助使用權限 | §3，開完要 Cmd+Q 重開終端機 |
| 貼上是空白／只剩 v/ㄒ | 中文輸入法吃掉 ⌘V | 已內建 pynput 手動 ⌘V；仍偶發就把 `STEP_INTERVAL` 調大 |
| 點擊沒生效 | ① 座標對錯 LINE 位置 ② 視窗動過 | 重跑 mouse_position 對齊；LINE 視窗別移動／縮放 |
| 點一下卻開到別的地方 | 有殘留的標記視窗蓋住 | 已拆到 `mouse_position.py`，`auto_click` 不再畫標記 |

## 9. 重要提醒

- **座標是死的**：LINE 視窗只要移動或縮放，座標就會偏移 — 每次跑前先對齊，不然會點錯人。
- **大批量有風險**：連發通知可能觸發 LINE 限流／帳號警告，量大前先把 `STEP_INTERVAL` 調大並先小量驗證。
- **這是給自己帳號的操作工具**：實際發送對象與內容，請自行確認無誤再執行。