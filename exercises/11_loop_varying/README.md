# 11 計數迴圈 ★★

主題：`PERFORM VARYING`、`OCCURS`、表格、迴圈

## 學習目標

完成這一題後，你會：

- 用 `PERFORM VARYING … FROM … BY … UNTIL …` 讓 COBOL 幫你管理計數器。
- 用迴圈計數器當下標，走過 `OCCURS` 表格的每一格。
- 寫出三種常見的表格處理：加總、找最大值、計數。
- 用 `DIVIDE … REMAINDER` 判斷奇偶。

## 這題要做什麼

要修改的檔案：`Table.cbl`（不要改 `TableTest.cbl`）

表格 `WS-SCORE-ITEM` 有 5 格，`LOAD-TABLE` 已經放好 40、75、20、90、55，這段是正確的範例，不用改。

| 段落 | 完成後應該達成 |
| --- | --- |
| `SUM-TABLE` | 5 格加總 = **280**，放進 `WS-TOTAL` |
| `FIND-LARGEST` | 最大值 **90**，放進 `WS-LARGEST` |
| `COUNT-EVEN` | 偶數的個數 = **3**，放進 `WS-EVEN-COUNT` |

規則：段落名稱不要改。三段都用 `PERFORM VARYING` 走過全部 5 格，每段只剩 `TODO` 和一個句點，請寫在句點之前。

## 觀念講解

### 1. `PERFORM VARYING`

```cobol
PERFORM VARYING WS-K FROM 1 BY 1 UNTIL WS-K > 4
    DISPLAY "第 " WS-K " 次"
END-PERFORM
```

| 部分 | 意思 |
| --- | --- |
| `VARYING WS-K` | 由 COBOL 管理的計數器 |
| `FROM 1` | 起始值 |
| `BY 1` | 每輪結束後加多少（可以是負數） |
| `UNTIL WS-K > 4` | 條件**成立**就停 |

執行順序：設定 `WS-K = 1` → 檢查條件 → 執行迴圈體 → `WS-K` 加 1 → 再檢查……所以 `UNTIL WS-K > 4` 剛好跑 1、2、3、4 共 4 次。

### 2. 表格與下標

```cobol
01  WS-RAIN-TABLE.
    05  WS-RAIN  PIC 9(3) OCCURS 7 TIMES.
```

- `OCCURS 7 TIMES` 表示一次準備 7 格。
- 用 `WS-RAIN (3)` 取第 3 格。下標**從 1 開始**。
- 下標可以是變數，所以迴圈計數器可以直接拿來用：`WS-RAIN (WS-K)`。

### 3. 三種常見的表格處理

**累加**：先歸零，每格加進去。

```cobol
MOVE 0 TO WS-WEEK-TOTAL
PERFORM VARYING WS-K FROM 1 BY 1 UNTIL WS-K > 7
    ADD WS-RAIN (WS-K) TO WS-WEEK-TOTAL
END-PERFORM
```

**找最小值**（找最大值的道理一樣，只是比較方向相反）：先拿第 1 格當目前的紀錄保持者，再一格一格比。

```cobol
MOVE WS-RAIN (1) TO WS-DRIEST
PERFORM VARYING WS-K FROM 2 BY 1 UNTIL WS-K > 7
    IF WS-RAIN (WS-K) < WS-DRIEST
        MOVE WS-RAIN (WS-K) TO WS-DRIEST
    END-IF
END-PERFORM
```

**計數**：符合條件就加 1。

### 4. 用餘數判斷奇偶

```cobol
DIVIDE 17 BY 2 GIVING WS-Q REMAINDER WS-R
*> WS-Q = 8、WS-R = 1
```

餘數是 0 就是偶數，1 就是奇數。

## 常見錯誤

- **`UNTIL WS-I >= 5`**：第 5 格還沒處理就停了，少算一格。
- **下標從 0 開始**：COBOL 表格沒有第 0 格。
- **累加或計數前沒歸零**：會把殘值算進去。
- **找最大值時把起始值設得太大**：起始值比所有資料都大，就永遠更新不到。
- **忘了括號**：要寫 `WS-SCORE-ITEM (WS-I)`，不能寫 `WS-SCORE-ITEM WS-I`。

## 操作步驟

1. 在專案根目錄執行 `.\coblings.cmd run 11_loop_varying`（Linux／macOS：`./coblings.sh run 11_loop_varying`），開始監看這一題。
2. 用編輯器打開本資料夾的 `Table.cbl`，照「這題要做什麼」修改。**不要改 `TableTest.cbl`**，它是這一題的驗收標準。
3. 存檔後系統會自動檢查：
   - **解析錯誤**：訊息裡有檔名和行號，照著修正語法。
   - **期望／實際不符**：看斷言的標籤，找出是哪個段落的結果不對。
   - **全部通過**：自動跳到下一題。
4. 卡關時執行 `.\coblings.cmd hint 11_loop_varying` 看提示。
5. 改亂了想重來，執行 `.\coblings.cmd reset 11_loop_varying` 還原成原題（你改過的版本會備份到 `.coblings/backup/`）。
