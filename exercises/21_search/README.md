# 21 查表 ★★

主題：`OCCURS`、`SEARCH`、88 條件名稱

## 學習目標

完成這一題後，你會：

- 宣告「每一筆有好幾個欄位」的表格，並用下標取出某一筆的某個欄位。
- 用 `SEARCH … VARYING … WHEN …` 在表格裡找出符合條件的那一筆。
- 把表格裡的值搬到一般欄位，再用 88 條件名稱判斷。
- 處理「表格容量」和「實際資料筆數」不同的情況。

## 這題要做什麼

要修改的檔案：`Lookup.cbl`（不要改 `LookupTest.cbl`）

`LOAD-CATALOG` 會放入 3 筆商品（表格容量是 5 格）：

| 筆 | `WS-SKU` | `WS-NAME` | `WS-PRICE` | `WS-KIND` |
| --- | --- | --- | --- | --- |
| 1 | A001 | MOCHA | 1800 | B |
| 2 | B002 | LATTE | 1500 | B |
| 3 | P003 | MATCHA | 2200 | P |

| 段落 | 完成後應該達成 |
| --- | --- |
| `FIND-ITEM` | 用 `SEARCH` 找到 `P003`：`WS-HIT` = `Y`、`WS-HIT-NAME` = `MATCHA`、`WS-HIT-PRICE` = **2200** |
| `COUNT-PREMIUM` | 用 88 條件名稱 `IS-PREMIUM` 數出進階商品（種類 `P`）有 **1** 筆，放進 `WS-PREMIUM-CNT` |
| `HIGHEST-PRICE` | 3 筆中的最高價 **2200**，放進 `WS-BEST` |

規則：段落名稱不要改。

## 觀念講解

### 1. 每一筆有好幾個欄位的表格

```cobol
01  WS-STAFF.
    05  WS-PERSON  OCCURS 10 TIMES.
        10  WS-ID     PIC X(3).
        10  WS-DEPT   PIC X(4).
        10  WS-AGE    PIC 99.
```

- `WS-PERSON (4)` 是第 4 個人的整筆資料。
- `WS-DEPT (4)` 是第 4 個人的部門。
- 每個子欄位都要帶下標，因為它們都「重複了 10 次」。

### 2. `SEARCH`：在表格裡找東西

這個系統的 `SEARCH` 寫法如下：

```cobol
MOVE "N" TO WS-FOUND
SEARCH WS-PERSON VARYING WS-K FROM 1 BY 1 UNTIL WS-K > 10
    WHEN WS-ID (WS-K) = "E07"
        MOVE "Y" TO WS-FOUND
        MOVE WS-DEPT (WS-K) TO WS-FOUND-DEPT
END-SEARCH
```

- `SEARCH` 後面接的是有 `OCCURS` 的那一層（`WS-PERSON`），不是子欄位。
- `VARYING … FROM … BY … UNTIL …` 讓索引從頭一路前進。少了這一段，索引不會移動。
- 找到第一個符合 `WHEN` 的那一筆就停，執行 `WHEN` 底下的敘述。
- `WHEN` 裡取用欄位時要帶下標，才知道是「找到的那一筆」。

> 補充：標準 COBOL 的 `SEARCH` 通常搭配 `INDEXED BY` 和 `SET 索引 TO 1`，寫法和這裡不同。本系統使用上面的 `VARYING` 寫法。

### 3. 88 條件名稱與表格

88 掛在一般欄位下面：

```cobol
01  WS-ONE-DEPT   PIC X(4).
    88  IS-SALES  VALUE "SALE".
```

要判斷表格裡某一筆的值，先把它搬到這個欄位，再判斷：

```cobol
MOVE WS-DEPT (WS-K) TO WS-ONE-DEPT
IF IS-SALES
    ADD 1 TO WS-SALES-CNT
END-IF
```

### 4. 容量 vs. 實際筆數

`OCCURS 10 TIMES` 只代表最多 10 筆。實際只放了幾筆，迴圈就該跑幾筆：跑太少會漏資料，跑到沒放資料的格子則可能拿到空白或 0。

## 常見錯誤

- **`SEARCH` 少了 `VARYING`**：索引不前進，用它取資料會出錯。
- **`WHEN` 裡的欄位沒帶下標**：不知道要比哪一筆。
- **迴圈上界少算**：只跑到第 2 筆，第 3 筆的資料就漏掉了。
- **找最大值從 0 起算又從第 2 筆開始比**：第 1 筆沒機會被比到。先把第 1 筆當成起點。
- **直接對表格欄位用 88**：本題的 88 掛在 `WS-LEVEL` 下面，要先 `MOVE` 過去再判斷。

## 操作步驟

1. 在專案根目錄執行 `.\coblings.cmd run 21_search`（Linux／macOS：`./coblings.sh run 21_search`），開始監看這一題。
2. 用編輯器打開本資料夾的 `Lookup.cbl`，照「這題要做什麼」修改。**不要改 `LookupTest.cbl`**，它是這一題的驗收標準。
3. 存檔後系統會自動檢查：
   - **解析錯誤**：訊息裡有檔名和行號，照著修正語法。
   - **期望／實際不符**：看斷言的標籤，找出是哪個段落的結果不對。
   - **全部通過**：自動跳到下一題。
4. 卡關時執行 `.\coblings.cmd hint 21_search` 看提示。
5. 改亂了想重來，執行 `.\coblings.cmd reset 21_search` 還原成原題（你改過的版本會備份到 `.coblings/backup/`）。
