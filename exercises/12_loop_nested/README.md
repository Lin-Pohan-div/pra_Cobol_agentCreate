# 12 巢狀迴圈 ★★★

主題：`PERFORM VARYING`、`AFTER`、巢狀迴圈

## 學習目標

完成這一題後，你會：

- 用 `PERFORM VARYING … AFTER …` 在**一個** `PERFORM` 裡寫出兩層迴圈。
- 預測巢狀迴圈的執行次數與每一輪的 (外層, 內層) 組合。
- 在迴圈體裡用兩個計數器做運算。
- 用迴圈體裡的 `IF` 只挑出部分組合，而不是去改迴圈範圍。

## 這題要做什麼

要修改的檔案：`Grid.cbl`（不要改 `GridTest.cbl`）

把它想成一個 3 列 × 4 欄的格子：`WS-ROW` 是 1～3，`WS-COL` 是 1～4。

| 段落 | 完成後應該達成 |
| --- | --- |
| `COUNT-CELLS` | 數出總共有 **12** 格，放進 `WS-CELLS` |
| `SUM-WITH-WEIGHT` | 每格權重 = 10 × 列 + 欄，12 格權重加總 = **270**，放進 `WS-SUM` |
| `ROW-TOTALS` | 只加總「欄 > 列」的格子（共 6 格），結果 **120**，放進 `WS-SUM` |

規則：段落名稱不要改；兩層迴圈都要照規格走完整的範圍（列 1～3、欄 1～4）。每段只剩 `TODO` 和一個句點，請寫在句點之前。

## 觀念講解

### 1. `AFTER`：一個 `PERFORM`，兩層迴圈

```cobol
PERFORM VARYING WS-H FROM 1 BY 1 UNTIL WS-H > 2
        AFTER   WS-M FROM 0 BY 30 UNTIL WS-M > 30
    DISPLAY WS-H ":" WS-M
END-PERFORM
```

輸出：

```text
1:0
1:30
2:0
2:30
```

- `VARYING` 是**外層**，`AFTER` 是**內層**。
- 內層跑完一整圈，外層才前進一步；外層每前進一步，內層就**從 `FROM` 重新開始**。
- 整個結構只有一個 `END-PERFORM`，迴圈體寫在 `AFTER` 子句之後。

### 2. 次數怎麼算

外層跑 a 次、內層跑 b 次，迴圈體總共執行 a × b 次。寫之前先算好預期次數，跑完對答案，是最快抓錯的方法。

### 3. 在迴圈體裡用兩個計數器

```cobol
COMPUTE WS-SEAT-NO = (WS-H - 1) * 10 + WS-M
```

`COMPUTE` 可以直接用兩個計數器算出這一格的值。

### 4. 只挑部分組合：條件寫在迴圈體裡

想要「只處理某些格子」時，讓迴圈照常走完全部，再用 `IF` 決定這一格要不要處理：

```cobol
PERFORM VARYING WS-H FROM 1 BY 1 UNTIL WS-H > 5
        AFTER   WS-M FROM 1 BY 1 UNTIL WS-M > 5
    IF WS-H = WS-M
        ADD 1 TO WS-DIAG-COUNT
    END-IF
END-PERFORM
```

這樣迴圈的範圍和規格一致，篩選條件也一目了然。

## 常見錯誤

- **寫成兩個獨立的 `PERFORM`**：前一個跑完，後一個才開始，就不是巢狀了。
- **兩層的 `UNTIL` 用錯上界**：列和欄的數量不同，3 列 4 欄別都寫成 `> 3`。
- **終止條件寫成 `>=`**：會少跑最後一列或最後一欄。
- **累加欄位沒歸零**：`SUM-WITH-WEIGHT` 和 `ROW-TOTALS` 共用 `WS-SUM`。
- **「欄 > 列」寫成 `>=`**：對角線那幾格也會被算進去。

## 操作步驟

1. 在專案根目錄執行 `.\coblings.cmd run 12_loop_nested`（Linux／macOS：`./coblings.sh run 12_loop_nested`），開始監看這一題。
2. 用編輯器打開本資料夾的 `Grid.cbl`，照「這題要做什麼」修改。**不要改 `GridTest.cbl`**，它是這一題的驗收標準。
3. 存檔後系統會自動檢查：
   - **解析錯誤**：訊息裡有檔名和行號，照著修正語法。
   - **期望／實際不符**：看斷言的標籤，找出是哪個段落的結果不對。
   - **全部通過**：自動跳到下一題。
4. 卡關時執行 `.\coblings.cmd hint 12_loop_nested` 看提示。
5. 改亂了想重來，執行 `.\coblings.cmd reset 12_loop_nested` 還原成原題（你改過的版本會備份到 `.coblings/backup/`）。
