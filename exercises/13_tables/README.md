# 13 價格表格 ★★

主題：表格、`OCCURS`、下標

## 學習目標

完成這一題後，你會：

- 用 `OCCURS … DEPENDING ON` 宣告「實際長度可變」的表格。
- 寫出走過表格每一筆的迴圈，而且不多也不少。
- 用「先拿第 1 筆當冠軍」的方法正確找出最大值與它的位置。
- 認識 `SUBSCRIPT OUT OF RANGE`（下標超出範圍）錯誤。

## 這題要做什麼

要修改的檔案：`Prices.cbl`（不要改 `PricesTest.cbl`）

`LOAD-PRICES` 會放入 5 筆單價（12.50、7.25、30.00、4.99、18.60）與貨號（A01～E05），這段不用改。

| 段落 | 完成後應該達成 |
| --- | --- |
| `SUM-PRICES` | 5 筆單價全部加總 = **73.34**，放進 `WS-TOTAL` |
| `FIND-MAX` | 最高單價 **30.00** 放進 `WS-MAX-PRICE`，它的位置 **3** 放進 `WS-MAX-POS` |
| `SHOW-TABLE` | 已經寫好，不用改；它會逐筆印出「貨號 單價」 |

這題還會比對 `DISPLAY` 的輸出（見 `expected.txt`）：

```text
A01   12.50
B02    7.25
C03   30.00
D04    4.99
E05   18.60
```

規則：段落名稱不要改。

## 觀念講解

### 1. `OCCURS` 與下標

```cobol
01  WS-TEMP-TABLE.
    05  WS-TEMP  PIC S9(2)V9 OCCURS 7 TIMES.
```

- 一次準備 7 個 `WS-TEMP`，用 `WS-TEMP (1)` 到 `WS-TEMP (7)` 存取。
- 下標**從 1 開始**，沒有第 0 筆。

### 2. `OCCURS … DEPENDING ON`：長度可變的表格

```cobol
01  WS-DAYS-USED  PIC 99.
01  WS-TEMP-TABLE.
    05  WS-TEMP  PIC S9(2)V9 OCCURS 31 TIMES DEPENDING ON WS-DAYS-USED.
```

- `OCCURS 31 TIMES` 是**最多**能放幾筆。
- `DEPENDING ON WS-DAYS-USED` 是**目前有效**的筆數。
- 用超過有效筆數的下標存取，會發生 `SUBSCRIPT OUT OF RANGE`，程式直接中斷。所以讀寫之前一定要先把筆數設好。

### 3. 迴圈的上界：跑「剛好 N 次」

```cobol
PERFORM VARYING WS-D FROM 1 BY 1 UNTIL WS-D > WS-DAYS-USED
    ...
END-PERFORM
```

`UNTIL` 是條件成立就停。要處理 1 到 N 筆，條件要寫成「下標**超過** N」：

| 條件 | 實際處理的下標 |
| --- | --- |
| `UNTIL WS-D > 3` | 1、2、3 |
| `UNTIL WS-D >= 3` | 1、2（少一筆） |

### 4. 找最大值的正確起點

```cobol
MOVE WS-TEMP (1) TO WS-HOTTEST
MOVE 1 TO WS-HOTTEST-DAY
PERFORM VARYING WS-D FROM 2 BY 1 UNTIL WS-D > WS-DAYS-USED
    IF WS-TEMP (WS-D) > WS-HOTTEST
        MOVE WS-TEMP (WS-D) TO WS-HOTTEST
        MOVE WS-D TO WS-HOTTEST-DAY
    END-IF
END-PERFORM
```

先把**第 1 筆**當成目前的冠軍（值和位置都要記），再從第 2 筆開始比。如果起點設成 0：

- 資料可能全是負數，0 比誰都大，結果是錯的。
- 冠軍剛好是第 1 筆時，迴圈從第 2 筆開始比，第 1 筆根本沒機會被記錄。

## 常見錯誤

- **`UNTIL i >= 筆數`**：少處理最後一筆。
- **找最大值時只改了值，沒記位置**：題目同時要價格和下標。
- **起點設 0 又從第 2 筆開始比**：第 1 筆被跳過。
- **`DEPENDING ON` 的筆數沒設好**：下標超出範圍，程式中斷。
- **加總前沒歸零**：重複執行時會累加上一次的結果。

## 操作步驟

1. 在專案根目錄執行 `.\coblings.cmd run 13_tables`（Linux／macOS：`./coblings.sh run 13_tables`），開始監看這一題。
2. 用編輯器打開本資料夾的 `Prices.cbl`，照「這題要做什麼」修改。**不要改 `PricesTest.cbl`**，它是這一題的驗收標準。
3. 存檔後系統會自動檢查：
   - **解析錯誤**：訊息裡有檔名和行號，照著修正語法。
   - **期望／實際不符**：看斷言的標籤，找出是哪個段落的結果不對。
   - **全部通過**：自動跳到下一題。
4. 卡關時執行 `.\coblings.cmd hint 13_tables` 看提示。
5. 改亂了想重來，執行 `.\coblings.cmd reset 13_tables` 還原成原題（你改過的版本會備份到 `.coblings/backup/`）。
