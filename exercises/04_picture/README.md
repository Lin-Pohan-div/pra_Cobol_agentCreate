# 04 PICTURE 與位數 ★★

主題：`PICTURE`、截斷、`SIZE ERROR`、`ROUNDED`

## 學習目標

完成這一題後，你會：

- 預測一個值放進 PICTURE 太小的欄位時，會被截掉哪一邊。
- 依照資料的最大長度，替欄位選擇夠用的 PICTURE。
- 分辨 `MOVE` 的截斷與算術敘述的 **SIZE ERROR**。
- 用 `COMPUTE … ROUNDED` 做四捨五入，用 `ON SIZE ERROR` 偵測溢位。

## 這題要做什麼

要修改的檔案：`Picture.cbl`（不要改 `PictureTest.cbl`）

| 段落 | 完成後應該達成 |
| --- | --- |
| `LOAD-BIG-NUMBER` | 序號 12345 完整保留，不會變成 345（題目要求改 PICTURE，不改搬進去的數字） |
| `LOAD-LONG-TEXT` | 名字 `Coblings` 完整保留，不會變成 `Cobli` |
| `LOAD-PRICE` | 12.567 四捨五入成 **12.57**，而不是截斷的 12.56 |
| `CHECK-SIZE-ERROR` | 999 + 1 放不進 `PIC 9(3)` 時，`WS-SIZE-FLAG` 變成 `YES` |

規則：段落名稱不要改。

## 觀念講解

### 1. 放不下時，截掉哪一邊？

| 欄位種類 | 對齊方式 | 放不下時丟掉 | 例子 |
| --- | --- | --- | --- |
| 數字 `PIC 9(n)` | 靠小數點（整數靠右） | **左邊的高位** | `98765` → `PIC 9(2)` 得到 `65` |
| 文字 `PIC X(n)` | 靠左 | **右邊的字** | `"Kaohsiung"` → `PIC X(4)` 得到 `"Kaoh"` |

`MOVE` 截斷時**不會報錯**，程式照樣執行，只是資料已經壞了。這是 COBOL 最常見的隱形 bug。

### 2. 欄位要開多大？

先數「最壞情況」要幾位：

```cobol
01  WS-YEAR     PIC 9(4).        *> 西元年最多 4 位
01  WS-CITY     PIC X(12).       *> 最長的城市名稱 + 一點餘裕
01  WS-AMOUNT   PIC 9(6)V99.     *> 最多 999999.99
```

### 3. 截斷 vs. 四捨五入

```cobol
01  WS-KG   PIC 9(2)V9.

MOVE 3.46 TO WS-KG                       *> 3.4（MOVE 只會截斷）
COMPUTE WS-KG ROUNDED = 3.46             *> 3.5
```

`ROUNDED` 只能接在**算術敘述**（`COMPUTE`、`ADD`、`SUBTRACT`、`MULTIPLY`、`DIVIDE`）的接收欄位後面，`MOVE` 沒有這個選項。

### 4. `ON SIZE ERROR`

算術結果的整數部分放不下接收欄位時，就是 SIZE ERROR：

```cobol
01  WS-LEVEL   PIC 9.

COMPUTE WS-LEVEL = WS-LEVEL + 5
    ON SIZE ERROR
        DISPLAY "等級已達上限"
END-COMPUTE
```

- 發生 SIZE ERROR 時，接收欄位**維持原值**，然後執行 `ON SIZE ERROR` 後面的敘述。
- 有寫 `ON SIZE ERROR` 時，記得用 `END-COMPUTE` 收尾，否則後面的敘述也會被當成錯誤處理的一部分。

## 常見錯誤

- **改了資料，沒改 PICTURE**：題目要你讓「欄位裝得下資料」，不是把資料改小。
- **只改了一半**：資料一路經過好幾個欄位時，每一個中途的欄位都要夠大，最窄的那個決定結果。
- **想在 `MOVE` 後面加 `ROUNDED`**：語法不允許，要改用 `COMPUTE`。
- **`ON SIZE ERROR` 沒有 `END-COMPUTE`**：後面的敘述會被吃進錯誤處理裡，只有溢位時才執行。

## 操作步驟

1. 在專案根目錄執行 `.\coblings.cmd run 04_picture`（Linux／macOS：`./coblings.sh run 04_picture`），開始監看這一題。
2. 用編輯器打開本資料夾的 `Picture.cbl`，照「這題要做什麼」修改。**不要改 `PictureTest.cbl`**，它是這一題的驗收標準。
3. 存檔後系統會自動檢查：
   - **解析錯誤**：訊息裡有檔名和行號，照著修正語法。
   - **期望／實際不符**：看斷言的標籤，找出是哪個段落的結果不對。
   - **全部通過**：自動跳到下一題。
4. 卡關時執行 `.\coblings.cmd hint 04_picture` 看提示。
5. 改亂了想重來，執行 `.\coblings.cmd reset 04_picture` 還原成原題（你改過的版本會備份到 `.coblings/backup/`）。
