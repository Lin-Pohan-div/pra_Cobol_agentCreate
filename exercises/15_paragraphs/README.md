# 15 段落結構 ★★

主題：段落、`PERFORM`、`THROUGH`

## 學習目標

完成這一題後，你會：

- 把段落當成副程式（subroutine），用 `PERFORM 段落名` 呼叫。
- 用 `PERFORM A THRU B` 依序執行一整段範圍內的段落。
- 判斷 `THRU` 的結束段落該設在哪裡：範圍太小會漏跑，太大會多跑。
- 了解段落最後用 `EXIT.` 收尾的用意。

## 這題要做什麼

要修改的檔案：`Report.cbl`（不要改 `ReportTest.cbl`）

`LOAD-NUMS` 會放入 10、20、30、40；`MAKE-SUM` 是正確的範例，結果是 100，兩段都不用改。

| 段落 | 完成後應該達成 |
| --- | --- |
| `MAKE-DOUBLED` | 依序執行 `DOUBLING`（10 × 2）→ `FINISH-ADD`（+ 7）→ `FINISH-DOUBLING`（收尾），`WS-DOUBLED` = **27** |
| `MAKE-LABEL` | 只執行 `SETUP-LABEL`，`WS-LABEL` = `REPORT-OK`；連續執行兩次，結果都一樣 |

規則：段落名稱與順序都不要改。

## 觀念講解

### 1. 段落就是副程式

```cobol
MAIN-FLOW.
    PERFORM PRINT-HEADER
    PERFORM PRINT-BODY
    EXIT.

PRINT-HEADER.
    DISPLAY "=== 月報 ===".

PRINT-BODY.
    DISPLAY "內容……".
```

`PERFORM PRINT-HEADER` 會跳到那個段落、執行完就**回到呼叫它的下一行**，和其他語言呼叫函式很像。

### 2. `PERFORM A THRU B`：執行一整段範圍

```cobol
    PERFORM STEP-OPEN THRU STEP-CLOSE
    ...

STEP-OPEN.
    DISPLAY "1. 開檔".
STEP-READ.
    DISPLAY "2. 讀資料".
STEP-CLOSE.
    DISPLAY "3. 關檔".
```

輸出：

```text
1. 開檔
2. 讀資料
3. 關檔
```

- 從 `A` 開始，**依照段落在檔案裡的排列順序**一路執行到 `B` 結束，然後才回來。
- `THRU` 和 `THROUGH` 意思一樣。

### 3. 範圍要剛好

| 寫法 | 實際執行 |
| --- | --- |
| `PERFORM STEP-OPEN THRU STEP-OPEN` | 只有 `STEP-OPEN`（範圍太小，後兩步沒跑） |
| `PERFORM STEP-OPEN THRU STEP-CLOSE` | 三段全部 |
| `PERFORM STEP-READ THRU STEP-READ` | 只有 `STEP-READ` |

結束段落如果設得**超過**你想要的範圍，後面那些「不該跑」的段落也會被執行，可能把剛算好的結果蓋掉。

`PERFORM X THRU X` 等於 `PERFORM X`，只執行一段。

### 4. 用 `EXIT.` 當段落的收尾

```cobol
STEP-DONE.
    EXIT.
```

`EXIT` 本身什麼都不做，只是讓段落有一個明確的終點。常見的寫法是 `PERFORM 某段 THRU 某段-EXIT`，把「這一組段落到哪裡結束」標清楚。

## 常見錯誤

- **`THRU` 的結束段落寫成開頭那一段**：只會執行一段，後面的步驟全部沒跑到。
- **`THRU` 範圍包到不相干的段落**：多執行的段落會改掉你的結果。
- **只看段落名稱、不看檔案順序**：`THRU` 依照段落在檔案裡的**物理順序**執行，不是依照名字或呼叫順序。
- **改變段落的順序**：題目規定不能動，因為 `THRU` 的行為和順序綁在一起。

## 操作步驟

1. 在專案根目錄執行 `.\coblings.cmd run 15_paragraphs`（Linux／macOS：`./coblings.sh run 15_paragraphs`），開始監看這一題。
2. 用編輯器打開本資料夾的 `Report.cbl`，照「這題要做什麼」修改。**不要改 `ReportTest.cbl`**，它是這一題的驗收標準。
3. 存檔後系統會自動檢查：
   - **解析錯誤**：訊息裡有檔名和行號，照著修正語法。
   - **期望／實際不符**：看斷言的標籤，找出是哪個段落的結果不對。
   - **全部通過**：自動跳到下一題。
4. 卡關時執行 `.\coblings.cmd hint 15_paragraphs` 看提示。
5. 改亂了想重來，執行 `.\coblings.cmd reset 15_paragraphs` 還原成原題（你改過的版本會備份到 `.coblings/backup/`）。
