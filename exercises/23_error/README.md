# 23 執行期錯誤 ★★★

主題：執行期錯誤、`SUBSCRIPT OUT OF RANGE`、`DIVIDE BY ZERO`、`ON SIZE ERROR`

## 學習目標

完成這一題後，你會：

- 認得兩種會讓程式中斷的執行期錯誤：`DIVIDE BY ZERO` 和 `SUBSCRIPT OUT OF RANGE`。
- 用「先檢查、再運算」的防守式寫法避開它們。
- 把下標「夾」在合法範圍內（clamp）。
- 分辨會中斷的錯誤和不會中斷的溢位，並用 `ON SIZE ERROR` 處理後者。

## 這題要做什麼

要修改的檔案：`Guard.cbl`（不要改 `GuardTest.cbl`）

表格 `WS-PRICE` 有 5 格，`LOAD-PRICES` 會放入 1200、1500、1800、2100、2400。

| 段落 | 完成後應該達成 |
| --- | --- |
| `SAFE-AVERAGE` | 執行時**不能出錯**。筆數是 0 時：`WS-STATUS` = `ZERO`、`WS-AVERAGE` = 0；筆數不是 0 時正常計算，`WS-STATUS` = `OK` |
| `SAFE-PICK` | 執行時**不能出錯**。`WS-PICK` 是 9，要先夾到 1～5 之間再取值，結果 `WS-PICKED` = **2400**（最後一格） |
| `SAFE-SCORE` | 執行時**不能出錯**。9000 + 2000 放不進 `PIC 9(4)` 時：`WS-SCORE` = **9999**、`WS-OVERFLOW` = `Y` |
| `CRASH-DIVIDE` | 示範用，**不要改**。它應該發生 `DIVIDE BY ZERO` |
| `CRASH-INDEX` | 示範用，**不要改**。它應該發生 `SUBSCRIPT OUT OF RANGE` |

規則：段落名稱不要改；`CRASH-*` 段落保持原樣，檢查器會確認它們真的會出錯。

## 觀念講解

### 1. 會中斷 vs. 不會中斷

| 狀況 | 結果 | 錯誤訊息 |
| --- | --- | --- |
| 除數是 0 | **程式中斷** | `DIVIDE BY ZERO` |
| 下標小於 1 或大於 `OCCURS` 次數 | **程式中斷** | `SUBSCRIPT OUT OF RANGE` |
| 算術結果的整數位放不下 | 不中斷；接收欄位**維持原值** | 沒有訊息，除非寫了 `ON SIZE ERROR` |

前兩種一旦發生，後面的程式全部不會執行。第三種雖然不會中斷，但結果是錯的，而且你不會收到任何警告。

### 2. 先檢查，再除

```cobol
IF WS-DAYS = 0
    MOVE "NONE" TO WS-RESULT
    MOVE 0 TO WS-DAILY
ELSE
    MOVE "DONE" TO WS-RESULT
    DIVIDE WS-KM BY WS-DAYS GIVING WS-DAILY ROUNDED
END-IF
```

兩條路徑都要把需要的欄位設好，不要只處理「出錯」那一邊。

### 3. 把下標夾在合法範圍內

```cobol
01  WS-SHELF-TABLE.
    05  WS-SHELF  PIC X(5) OCCURS 8 TIMES.
01  WS-SLOT   PIC 99.

IF WS-SLOT < 1
    MOVE 1 TO WS-SLOT
END-IF
IF WS-SLOT > 8
    MOVE 8 TO WS-SLOT
END-IF
MOVE WS-SHELF (WS-SLOT) TO WS-ITEM
```

「夾住」的意思是：太小就拉到最小值、太大就壓到最大值，在範圍內就不動。夾完之後再取用表格，就保證不會超出範圍。

### 4. 溢位要自己接住

```cobol
COMPUTE WS-STOCK = WS-STOCK + WS-IN
    ON SIZE ERROR
        MOVE 999 TO WS-STOCK
        MOVE "Y" TO WS-FULL
END-COMPUTE
```

## 常見錯誤

- **修改了 `CRASH-*` 段落**：它們本來就應該出錯，改掉的話檢查器會判定失敗。
- **只處理除數為 0 的情況**：除數不是 0 時也要把狀態設成 `OK`。
- **只檢查上界、沒檢查下界**（或反過來）：兩邊都要夾。
- **先取值再檢查下標**：取值的那一刻就已經中斷了，檢查一定要在前面。
- **以為溢位會自動變成最大值或被截斷**：不會，接收欄位維持原值，上限要自己 `MOVE` 進去。

## 操作步驟

1. 在專案根目錄執行 `.\coblings.cmd run 23_error`（Linux／macOS：`./coblings.sh run 23_error`），開始監看這一題。
2. 用編輯器打開本資料夾的 `Guard.cbl`，照「這題要做什麼」修改。**不要改 `GuardTest.cbl`**，它是這一題的驗收標準。
3. 存檔後系統會自動檢查：
   - **解析錯誤**：訊息裡有檔名和行號，照著修正語法。
   - **期望／實際不符**：看斷言的標籤，找出是哪個段落的結果不對。
   - **全部通過**：自動跳到下一題。
4. 卡關時執行 `.\coblings.cmd hint 23_error` 看提示。
5. 改亂了想重來，執行 `.\coblings.cmd reset 23_error` 還原成原題（你改過的版本會備份到 `.coblings/backup/`）。
