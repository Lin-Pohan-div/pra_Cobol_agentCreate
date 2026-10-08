# 14 二維矩陣 ★★★

主題：表格、二維表格、下標

## 學習目標

完成這一題後，你會：

- 用兩層 `OCCURS` 宣告二維表格，並用 `(列, 欄)` 兩個下標存取。
- 用巢狀的 `PERFORM VARYING` 走過整個矩陣，而且兩層的上界不搞混。
- 只處理矩陣的「一部分」：單一列，或對角線。
- 找出整個矩陣的最大值與它的位置。

## 這題要做什麼

要修改的檔案：`Matrix.cbl`（不要改 `MatrixTest.cbl`）

`LOAD-MATRIX` 會把 1 到 12 依序填入 3 列 × 4 欄的矩陣：

```text
        欄1  欄2  欄3  欄4
列1      1    2    3    4
列2      5    6    7    8
列3      9   10   11   12
```

| 段落 | 完成後應該達成 |
| --- | --- |
| `SUM-MATRIX` | 12 格全部加總 = **78**，放進 `WS-TOTAL` |
| `SUM-ROW-TWO` | 只加第 2 列：5 + 6 + 7 + 8 = **26**，放進 `WS-ROW-SUM` |
| `SUM-DIAGONAL` | 對角線 (1,1)、(2,2)、(3,3)：1 + 6 + 11 = **18**，放進 `WS-DIAGONAL` |
| `FIND-MAX` | 最大值 **12** 放進 `WS-MAX`，位置 (**3**, **4**) 放進 `WS-MAX-R`、`WS-MAX-C`（這段本身是正確的，前面幾段修好後就會通過） |

規則：段落名稱不要改。

## 觀念講解

### 1. 宣告二維表格

表格裡面再放表格：

```cobol
01  WS-SEATS.
    05  WS-SEAT-ROW  OCCURS 5 TIMES.
        10  WS-SEAT  PIC X OCCURS 8 TIMES.
```

- 外層 `WS-SEAT-ROW` 有 5 列。
- 每一列裡面有 8 個 `WS-SEAT`。
- 取用時寫 `WS-SEAT (列, 欄)`，例如 `WS-SEAT (2, 7)` 是第 2 列第 7 個座位。

### 2. 巢狀迴圈走過整個矩陣

```cobol
PERFORM VARYING WS-R FROM 1 BY 1 UNTIL WS-R > 5          *> 5 列
    PERFORM VARYING WS-C FROM 1 BY 1 UNTIL WS-C > 8      *> 8 欄
        IF WS-SEAT (WS-R, WS-C) = "X"
            ADD 1 TO WS-SOLD
        END-IF
    END-PERFORM
END-PERFORM
```

外層變數配外層上界、內層變數配內層上界。列數和欄數不一樣時，搞混就會漏掉一些格子，或超出範圍。

### 3. 只走一部分

**只看某一列**：列下標固定，只跑欄。

```cobol
MOVE 0 TO WS-ROW-SOLD
PERFORM VARYING WS-C FROM 1 BY 1 UNTIL WS-C > 8
    IF WS-SEAT (4, WS-C) = "X"
        ADD 1 TO WS-ROW-SOLD
    END-IF
END-PERFORM
```

**只看對角線**：對角線上的格子「列下標 = 欄下標」，所以只需要**一個**迴圈變數，同時拿來當列和欄的下標，不需要讓兩層都完整跑一遍。

### 4. 迴圈也可以只跑一次

`PERFORM VARYING X FROM a BY 1 UNTIL X > a` 只會跑一次（X = a）。有時候為了保留巢狀結構，會這樣把內層「釘」在某個值上。

## 常見錯誤

- **內層上界用了列數**：3 列 4 欄的矩陣，內層寫 `> WS-ROW-COUNT` 會漏掉第 4 欄。
- **想算一列卻跑了全部列**：外層沒有限制，結果等於整個矩陣的總和。
- **對角線寫成「從 WS-R 開始到最後一欄」**：那是上三角，不是對角線。
- **下標順序寫反**：`WS-CELL (欄, 列)` 和 `WS-CELL (列, 欄)` 是不同的格子，還可能超出範圍。
- **累加欄位沒歸零**。

## 操作步驟

1. 在專案根目錄執行 `.\coblings.cmd run 14_table_2d`（Linux／macOS：`./coblings.sh run 14_table_2d`），開始監看這一題。
2. 用編輯器打開本資料夾的 `Matrix.cbl`，照「這題要做什麼」修改。**不要改 `MatrixTest.cbl`**，它是這一題的驗收標準。
3. 存檔後系統會自動檢查：
   - **解析錯誤**：訊息裡有檔名和行號，照著修正語法。
   - **期望／實際不符**：看斷言的標籤，找出是哪個段落的結果不對。
   - **全部通過**：自動跳到下一題。
4. 卡關時執行 `.\coblings.cmd hint 14_table_2d` 看提示。
5. 改亂了想重來，執行 `.\coblings.cmd reset 14_table_2d` 還原成原題（你改過的版本會備份到 `.coblings/backup/`）。
