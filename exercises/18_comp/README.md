# 18 數字儲存 ★★★

主題：`COMP`、`COMP-3`、`INDEX`、`SET`

## 學習目標

完成這一題後，你會：

- 認識 `USAGE` 子句：`DISPLAY`、`COMP`（二進位）、`COMP-3`（壓縮十進位）的差別。
- 知道 `USAGE` 只改變**儲存方式**，不改變數值的意義。
- 用 `USAGE INDEX` 欄位當表格下標，並用 `SET` 設定它。
- 用 INDEX 當 `PERFORM VARYING` 的計數器走過表格。

## 這題要做什麼

要修改的檔案：`Storage.cbl`（不要改 `StorageTest.cbl`）

| 段落 | 完成後應該達成 |
| --- | --- |
| `LOAD-ITEMS` | 表格 `WS-ITEM` 的 5 格依序是 100、200、300、400、500 |
| `SUM-ITEMS` | 用 `USAGE INDEX` 的 `WS-IDX` 當下標，從第 1 格加到第 `WS-CNT` 格，`WS-TOTAL` = **1500** |
| `FIND-LARGEST` | 用 `SET` 把 `WS-IDX` 移到最後一格，`WS-LARGEST` = **500**、`WS-LARGEST-IDX` = **5** |
| `COPY-TO-BOTH` | 已經寫好，不用改；示範 `COMP` 和 `COMP-3` 都能存 -1234.56 |

規則：段落名稱不要改。

## 觀念講解

### 1. `USAGE`：數字怎麼存

| 宣告 | 儲存方式 | 常見用途 |
| --- | --- | --- |
| `PIC 9(5)`（預設 `DISPLAY`） | 每個數字一個字元 | 要印出來、要和文字交換的資料 |
| `PIC S9(5) COMP` | 二進位整數 | 計數器、下標，計算快 |
| `PIC S9(5)V99 COMP-3` | 壓縮十進位（每 byte 放兩個數字） | 金額、會計資料，省空間又精確 |

```cobol
01  WS-QTY-D   PIC S9(4).
01  WS-QTY-B   PIC S9(4) COMP.
01  WS-QTY-P   PIC S9(4) COMP-3.

MOVE -321 TO WS-QTY-D WS-QTY-B WS-QTY-P
*> 三個欄位在記憶體裡的樣子不同，但值都是 -321
```

`PIC` 仍然決定位數、小數位和正負號；`USAGE` 只決定位元組怎麼排。對你寫的程式來說，運算和比較的結果都一樣。

### 2. `USAGE INDEX` 與 `SET`

```cobol
01  WS-POS   USAGE INDEX.
```

INDEX 欄位是專門用來當表格下標的，**不寫 `PIC`**。設定它的值要用 `SET`：

```cobol
SET WS-POS TO 1               *> 設成常數
SET WS-POS TO WS-LAST-ROW     *> 設成另一個欄位的值
```

取用表格時就像一般下標：`WS-ROOM (WS-POS)`。

### 3. 用 INDEX 跑迴圈

`PERFORM VARYING` 的計數器也可以是 INDEX 欄位，COBOL 會自動幫你遞增：

```cobol
PERFORM VARYING WS-POS FROM 1 BY 1 UNTIL WS-POS > WS-ROOMS
    ADD WS-ROOM (WS-POS) TO WS-GUESTS
END-PERFORM
```

### 4. 表格下標從 1 開始

和一般欄位一樣，INDEX 指向的是「第幾格」，第一格是 1。從 0 開始取用會超出範圍，或讓結果錯位。

## 常見錯誤

- **表格只填了一部分**：沒填的 `COMP-3` 格子是 0，加總會少。
- **下標從 0 開始**：表格沒有第 0 格。
- **用 `MOVE` 設定 INDEX**：標準 COBOL 規定 INDEX 欄位要用 `SET` 設定值。這個系統雖然也接受 `MOVE`，但請養成用 `SET` 的習慣，本題也要求用 `SET`。
- **`SET` 設錯位置**：想取「最後一筆」，就要設成筆數，而不是 1。
- **以為 `COMP` 會改變數值**：-1234.56 用哪一種 `USAGE` 存，取出來都還是 -1234.56。

## 操作步驟

1. 在專案根目錄執行 `.\coblings.cmd run 18_comp`（Linux／macOS：`./coblings.sh run 18_comp`），開始監看這一題。
2. 用編輯器打開本資料夾的 `Storage.cbl`，照「這題要做什麼」修改。**不要改 `StorageTest.cbl`**，它是這一題的驗收標準。
3. 存檔後系統會自動檢查：
   - **解析錯誤**：訊息裡有檔名和行號，照著修正語法。
   - **期望／實際不符**：看斷言的標籤，找出是哪個段落的結果不對。
   - **全部通過**：自動跳到下一題。
4. 卡關時執行 `.\coblings.cmd hint 18_comp` 看提示。
5. 改亂了想重來，執行 `.\coblings.cmd reset 18_comp` 還原成原題（你改過的版本會備份到 `.coblings/backup/`）。
