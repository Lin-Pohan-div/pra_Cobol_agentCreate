# 10 定次與條件迴圈 ★★

主題：`PERFORM`、`UNTIL`、迴圈、計數器

## 學習目標

完成這一題後，你會：

- 寫出內嵌式的 `PERFORM UNTIL 條件 … END-PERFORM` 迴圈。
- 牢記 `UNTIL` 是「條件**成立**就停」。
- 自己維護計數器：歸零、遞增或遞減、寫出正確的終止條件。
- 知道 `UNTIL` 迴圈是「先檢查、再執行」，所以可能一次都不跑。

## 這題要做什麼

要修改的檔案：`Counter.cbl`（不要改 `CounterTest.cbl`）

| 段落 | 完成後應該達成 |
| --- | --- |
| `SUM-TO-LIMIT` | 1 + 2 + … + 10 = **55**，放進 `WS-TOTAL`；用 `PERFORM UNTIL` |
| `COUNT-DOWN` | `WS-COUNT` 從 10 遞減到 0，每次讓 `WS-REMAIN` 加 1，最後 `WS-REMAIN` = **10** |
| `COPY-N-TIMES` | 把 `WS-START`（3）累加 5 次，`WS-TOTAL` = **15**；用 `WS-COUNT` 當計數器 |

規則：段落名稱不要改。三個段落都用 `PERFORM UNTIL … END-PERFORM` 寫，每段只剩 `TODO` 和一個句點，請寫在句點之前。

## 觀念講解

### 1. 內嵌式 `PERFORM UNTIL`

```cobol
MOVE 1 TO WS-PAGE
PERFORM UNTIL WS-PAGE > 3
    DISPLAY "印第 " WS-PAGE " 頁"
    ADD 1 TO WS-PAGE
END-PERFORM
```

輸出：

```text
印第 1 頁
印第 2 頁
印第 3 頁
```

- `PERFORM` 和 `END-PERFORM` 之間的敘述就是**迴圈體**。
- 每一輪**開始前**先檢查條件，條件成立就結束迴圈。

### 2. `UNTIL` 是「直到」，不是「當」

很多語言的 `while (條件)` 是「條件成立就**繼續**」；COBOL 的 `UNTIL 條件` 剛好相反，是「條件成立就**停**」。

| 想表達的意思 | 其他語言 | COBOL |
| --- | --- | --- |
| 還沒到 3 就繼續 | `while (page <= 3)` | `UNTIL WS-PAGE > 3` |

把 `<=` 原封不動地搬到 `UNTIL` 後面，是最常見的錯誤。

### 3. 計數器三件事

用 `UNTIL` 做「做 N 次」的迴圈時，計數器得自己管：

1. **歸零**（或設成起始值）：在迴圈**之前**。
2. **更新**：在迴圈體**裡面**加 1 或減 1。
3. **終止條件**：用「已經做滿了」來描述。

```cobol
MOVE 0 TO WS-TIMES
PERFORM UNTIL WS-TIMES >= 4
    ADD 2 TO WS-SCORE
    ADD 1 TO WS-TIMES
END-PERFORM
*> WS-SCORE 增加了 2 × 4 = 8
```

### 4. 可能一次都不跑

因為是先檢查再執行，條件一開始就成立的話，迴圈體一次都不會執行。計數器沒歸零、還留著上一段的值，就會發生這種情況。

## 常見錯誤

- **條件寫反**：`UNTIL WS-COUNT < 10` 一開始就成立（0 < 10），迴圈一次都不跑。
- **忘了更新計數器**：條件永遠不成立，變成無窮迴圈，最後被系統的逾時機制中斷。
- **計數器沒歸零**：上一個段落留下的值讓迴圈直接結束。注意 `SUM-TO-LIMIT` 和 `COPY-N-TIMES` 共用 `WS-COUNT` 和 `WS-TOTAL`。
- **先加總再遞增，順序搞錯**：想加 1 到 10，計數器要先加 1 再累加，否則會加成 0 到 9。
- **迴圈體裡出現句點**：句點會提前結束整個 `PERFORM`，`END-PERFORM` 就對不上了。

## 操作步驟

1. 在專案根目錄執行 `.\coblings.cmd run 10_loop_times`（Linux／macOS：`./coblings.sh run 10_loop_times`），開始監看這一題。
2. 用編輯器打開本資料夾的 `Counter.cbl`，照「這題要做什麼」修改。**不要改 `CounterTest.cbl`**，它是這一題的驗收標準。
3. 存檔後系統會自動檢查：
   - **解析錯誤**：訊息裡有檔名和行號，照著修正語法。
   - **期望／實際不符**：看斷言的標籤，找出是哪個段落的結果不對。
   - **全部通過**：自動跳到下一題。
4. 卡關時執行 `.\coblings.cmd hint 10_loop_times` 看提示。
5. 改亂了想重來，執行 `.\coblings.cmd reset 10_loop_times` 還原成原題（你改過的版本會備份到 `.coblings/backup/`）。
