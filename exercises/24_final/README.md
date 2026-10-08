# 24 綜合演練 ★★★★

主題：`UNSTRING`、`SEARCH`、`ROUNDED`、`ON SIZE ERROR`、順序檔

## 學習目標

完成這一題後，你會：

- 把前面學過的技巧串成一個完整的小程式：寫檔、讀檔、拆字串、查表、計算。
- 先看懂資料流，再一個段落一個段落地修。
- 寫出能正確處理檔案結尾、不會多算一輪的讀檔迴圈。
- 在一個流程裡同時處理溢位與四捨五入。

## 這題要做什麼

要修改的檔案：`Checkout.cbl`（不要改 `CheckoutTest.cbl`）

這是一個小小的結帳程式。商品表（`LOAD-CATALOG`，單價以「分」為單位）：

| 代號 | 名稱 | 單價 |
| --- | --- | --- |
| A001 | MOCHA | 1235 |
| B002 | LATTE | 1500 |
| P003 | MATCHA | 2250 |

訂單檔 `order.dat` 每一行固定 12 碼，格式是「代號,數量」，例如 `B002,7`。

| 段落 | 完成後應該達成 |
| --- | --- |
| `WRITE-ORDER` | 3 行訂單真的寫進 `order.dat` |
| `READ-FIRST-LINE` | 讀回第一行並拆開：`WS-SKU-TEXT` = `B002`、`WS-QTY-TEXT` 是數量 |
| `FIND-UNIT-PRICE` | 用 `SEARCH` 查到 B002：`WS-HIT` = `Y`、`WS-UNIT` = **1500** |
| `SUM-ORDER` | 逐行計算小計並加總：共 **3** 件；小計放不進 4 碼時夾成 9999，並設 `WS-CLAMPED` = `Y`；總額 `WS-TOTAL` = **19439** |
| `AVERAGE-ORDER` | 平均 = 總額 ÷ 件數，四捨五入到分：`WS-AVERAGE` = **6479.67** |

檢查器會依序執行這 5 段，最後把 `order.dat` 清空。

規則：段落名稱不要改。每個 `TODO` 都標出一個要修的地方，共 7 個：`READ-FIRST-LINE` 和 `SUM-ORDER` 各有兩個，其他段落各一個。

## 觀念講解

這一題沒有新語法，重點是**把舊技巧放在一起用**。下面是每個環節的複習與對應題號。

### 1. 先畫出資料流

```text
order.dat ──READ──▶ WS-LINE ──UNSTRING──▶ 代號、數量
                                           │
                     商品表 ◀──SEARCH──────┘
                       │
                    單價 × 數量 ──▶ 小計 ──ADD──▶ 總額 ──DIVIDE──▶ 平均
```

每個段落負責其中一段。某個斷言失敗時，先找出是哪個環節的輸出不對，再回頭看那一段。

### 2. 檔案（第 22 題）

- 寫完一定要 `CLOSE`，資料才會落地。
- `READ … AT END … END-READ`，讀到結尾時設旗標。

### 3. 讀檔迴圈不要多算一輪（第 22 題）

```cobol
PERFORM UNTIL WS-EOF = "Y"
    READ IN-FILE INTO WS-REC
        AT END MOVE "Y" TO WS-EOF
    END-READ
    IF WS-EOF = "N"
        *> 只有真的讀到資料，才處理這一筆
        ...
    END-IF
END-PERFORM
```

碰到結尾的那一輪，`WS-REC` 還留著上一筆的內容。如果不加 `IF`，最後一筆會被重複計算。

### 4. 拆字串（第 20 題）

`UNSTRING` 的分隔字元要和資料一致；`DELIMITED BY SIZE` 表示整個欄位都不切。

### 5. 查表（第 21 題）

`SEARCH 表格 VARYING 索引 FROM 1 BY 1 UNTIL 索引 > 上限`，`WHEN` 裡的欄位要帶下標。

### 6. 溢位與捨入（第 19 題）

- 乘法結果可能超過接收欄位：`COMPUTE … ON SIZE ERROR … END-COMPUTE`，在錯誤處理裡放上限值並設旗標。
- 除法要四捨五入：在 `GIVING` 的接收欄位後面加 `ROUNDED`。

## 常見錯誤

- **一次改全部、再一次跑**：一次改一段、存檔看結果，比較容易找出錯在哪裡。
- **`WRITE-ORDER` 沒有 `CLOSE`**：後面每一段都讀不到資料，錯誤訊息看起來會像是別的段落有問題。
- **讀檔迴圈多算一輪**：件數變成 4，總額也跟著錯。
- **溢位時忘了設旗標或上限值**：題目同時檢查 `WS-CLAMPED` 和總額。
- **平均沒有 `ROUNDED`**：結果會是截斷的 6479.66。

## 操作步驟

1. 在專案根目錄執行 `.\coblings.cmd run 24_final`（Linux／macOS：`./coblings.sh run 24_final`），開始監看這一題。
2. 用編輯器打開本資料夾的 `Checkout.cbl`，照「這題要做什麼」修改。**不要改 `CheckoutTest.cbl`**，它是這一題的驗收標準。
3. 存檔後系統會自動檢查：
   - **解析錯誤**：訊息裡有檔名和行號，照著修正語法。
   - **期望／實際不符**：看斷言的標籤，找出是哪個段落的結果不對。
   - **全部通過**：恭喜，24 題全部完成！
4. 卡關時執行 `.\coblings.cmd hint 24_final` 看提示。
5. 改亂了想重來，執行 `.\coblings.cmd reset 24_final` 還原成原題（你改過的版本會備份到 `.coblings/backup/`）。

`order.dat` 是執行時產生的資料檔，檢查器跑完會清空它，不需要手動處理。
