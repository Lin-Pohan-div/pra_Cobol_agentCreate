# 09 多分支選擇 ★

主題：`EVALUATE`、`WHEN`、`WHEN OTHER`

## 學習目標

完成這一題後，你會：

- 用 `EVALUATE … WHEN … END-EVALUATE` 取代一長串的 `ELSE IF`。
- 在 `WHEN` 裡寫範圍條件，並理解「第一個符合就結束」的規則。
- 知道為什麼一定要補上 `WHEN OTHER`。
- 比較同一個需求用 `EVALUATE` 和 `ELSE IF` 寫的差別。

## 這題要做什麼

要修改的檔案：`Grade.cbl`（不要改 `GradeTest.cbl`）

| 段落 | 完成後應該達成 |
| --- | --- |
| `GRADE-OF` | 依「≥ 90 A、≥ 80 B、≥ 70 C、≥ 60 D、其餘 F」，85 分得到 **B**，放進 `WS-GRADE`；用 `EVALUATE`，最後要有 `WHEN OTHER` |
| `SIZE-OF` | 依「≥ 1000 BIG、≥ 100 MID、其餘 SML」，2500 得到 **BIG**，放進 `WS-SIZE`；這段指定用 `ELSE IF` 寫 |
| `COMMENT-OF-DAYS` | 依「> 90 SEVERE、> 30 OVERDUE、其餘 OK」，45 天得到 **OVERDUE**，放進 `WS-COMMENT`；用 `EVALUATE` |

規則：段落名稱不要改。每個段落目前只剩 `TODO` 註解和一個單獨的句點，請把程式寫在句點之前。

## 觀念講解

### 1. 比對「值」的 `EVALUATE`

```cobol
EVALUATE WS-WEEKDAY
    WHEN 6
    WHEN 7
        MOVE "WEEKEND" TO WS-DAY-TYPE
    WHEN 0
        MOVE "INVALID" TO WS-DAY-TYPE
    WHEN OTHER
        MOVE "WORKDAY" TO WS-DAY-TYPE
END-EVALUATE
```

- `EVALUATE` 後面是要比對的對象（主題）。
- 連續兩個 `WHEN` 中間沒有敘述，代表「6 或 7 都執行同一段」。
- 這種寫法只能比對「等於某個值」。要比較大小或範圍，請用下一節「在 `WHEN` 裡寫條件」的寫法。

### 2. 在 `WHEN` 裡寫「條件」

要寫 `>=`、`>` 這種比較時，每個 `WHEN` 後面放一個完整的條件。本題的 `TODO` 要求的是這種寫法：

```cobol
EVALUATE WS-SPEED
    WHEN WS-SPEED > 120
        MOVE "DANGER" TO WS-ALERT
    WHEN WS-SPEED > 100
        MOVE "FAST" TO WS-ALERT
    WHEN OTHER
        MOVE "NORMAL" TO WS-ALERT
END-EVALUATE
```

在這個系統裡，`WHEN` 後面是條件時，就直接判斷這個條件成不成立。

> 補充：標準 COBOL（例如 GnuCOBOL）在這種情況通常寫成 `EVALUATE TRUE`，意思是「找出第一個條件為真的 `WHEN`」。這個系統兩種寫法都能執行，結果相同。以後換到真正的編譯器時，請記得改用 `EVALUATE TRUE`。

### 3. 只會執行第一個符合的分支

`EVALUATE` 從上往下找，找到第一個符合的 `WHEN` 就執行、然後**直接跳到 `END-EVALUATE`**。和 C／Java 的 `switch` 不同，不需要 `break`，也不會「掉」到下一個分支。

因此範圍要**由嚴到鬆**排列。上面的例子如果把 `> 100` 寫在 `> 120` 前面，時速 150 也只會得到 `FAST`。

### 4. `WHEN OTHER`

`WHEN OTHER` 負責「以上都不符合」。沒寫的話，沒有分支符合時什麼都不做，結果欄位會保留**舊值**，這種 bug 很難發現。

### 5. `EVALUATE` 與 `ELSE IF` 的對照

| | `EVALUATE` | `ELSE IF` 鏈 |
| --- | --- | --- |
| 結尾 | 一個 `END-EVALUATE` | 一個 `END-IF` |
| 預設分支 | `WHEN OTHER` | 最後的 `ELSE` |
| 可讀性 | 分支多的時候比較整齊 | 分支少的時候比較直接 |

兩者都是「從上往下、第一個符合就停」。

## 常見錯誤

- **範圍順序寫反**：寬鬆的條件放前面，嚴格的永遠輪不到。
- **漏掉 `WHEN OTHER`**：沒有分支符合時，欄位保留上一次的值。
- **`>` 和 `>=` 用錯**：題目說「> 30」就是 31 天以上，30 天本身不算。
- **寫 `WHEN 80 THRU 89`**：這個系統的 `EVALUATE` 不支援 `THRU` 範圍，請改用 `WHEN 主題 >= 80` 這種條件寫法。
- **在 `WHEN` 之間加句點**：句點會提前結束整個 `EVALUATE`，後面的 `WHEN` 就變成解析錯誤。
- **`SIZE-OF` 也寫成 `EVALUATE`**：這段題目指定練習 `ELSE IF`，請照題目要求寫。

## 操作步驟

1. 在專案根目錄執行 `.\coblings.cmd run 09_evaluate`（Linux／macOS：`./coblings.sh run 09_evaluate`），開始監看這一題。
2. 用編輯器打開本資料夾的 `Grade.cbl`，照「這題要做什麼」修改。**不要改 `GradeTest.cbl`**，它是這一題的驗收標準。
3. 存檔後系統會自動檢查：
   - **解析錯誤**：訊息裡有檔名和行號，照著修正語法。
   - **期望／實際不符**：看斷言的標籤，找出是哪個段落的結果不對。
   - **全部通過**：自動跳到下一題。
4. 卡關時執行 `.\coblings.cmd hint 09_evaluate` 看提示。
5. 改亂了想重來，執行 `.\coblings.cmd reset 09_evaluate` 還原成原題（你改過的版本會備份到 `.coblings/backup/`）。
