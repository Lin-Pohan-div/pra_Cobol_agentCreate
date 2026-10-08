# 06 字串串接 ★★

主題：`STRING`、`DELIMITED BY`、`WITH POINTER`、`ON OVERFLOW`

## 學習目標

完成這一題後，你會：

- 分辨 `DELIMITED BY SIZE` 和 `DELIMITED BY " "`，處理 `PIC X` 補位空白造成的多餘空格。
- 用 `WITH POINTER` 分好幾次把文字接在同一個欄位後面。
- 用 `ON OVERFLOW` 偵測目標欄位放不下的情況。

## 這題要做什麼

要修改的檔案：`Concatenate.cbl`（不要改 `ConcatenateTest.cbl`）

| 段落 | 完成後應該達成 |
| --- | --- |
| `BUILD-NAME-LABEL` | `WS-NAME-LABEL` 是 `Amy Chen`，中間只有一個空白 |
| `BUILD-ADDRESS` | 分兩次串接後，`WS-ADDRESS` 是 `City: Taipei Zip: 100` |
| `FILL-SMALL-BUFFER` | `WS-SMALL-BUF` 留下 `ABCDEFGH`，而且放不下的部分讓 `WS-OVERFLOW` 變成 `YES` |

規則：段落名稱不要改。

## 觀念講解

### 1. `STRING` 的完整語法

```cobol
STRING 來源1 DELIMITED BY 分隔
       來源2 DELIMITED BY 分隔
       ...
   INTO 目標
   [WITH POINTER 指標欄位]
   [ON OVERFLOW 敘述...]
END-STRING
```

### 2. `DELIMITED BY` 決定每個來源取多少

假設 `WS-PET` 是 `PIC X(6)`，內容是 `"cat"`（實際上是 `"cat   "`）：

| 寫法 | 取到的內容 |
| --- | --- |
| `WS-PET DELIMITED BY SIZE` | `"cat   "`（整個欄位，含 3 個補位空白） |
| `WS-PET DELIMITED BY " "` | `"cat"`（遇到第一個空白就停） |
| `FUNCTION TRIM(WS-PET) DELIMITED BY SIZE` | `"cat"`（先去掉前後空白，再整個取） |

注意：`DELIMITED BY " "` 遇到「內容本身就有空白」的資料（例如 `"New York"`）會提早停下來，這時用 `TRIM` 比較安全。

### 3. `WITH POINTER`：從第幾個字開始寫

指標欄位記錄「下一個字要寫到目標的第幾個位置」，位置從 **1** 開始算。

```cobol
MOVE SPACES TO WS-MSG
MOVE 1 TO WS-PTR
STRING "Hi, " DELIMITED BY SIZE
   INTO WS-MSG WITH POINTER WS-PTR
END-STRING
*> 這時 WS-MSG = "Hi, "、WS-PTR = 5

STRING "Ken" DELIMITED BY SIZE
   INTO WS-MSG WITH POINTER WS-PTR
END-STRING
*> WS-MSG = "Hi, Ken"、WS-PTR = 8
```

- `STRING` 執行完會**自動更新**指標，讓它指向剛寫完的下一格。
- 指標**不會自己回到 1**。如果你在兩次 `STRING` 之間手動把它改成 1，第二次就會從頭開始，把前面的字蓋掉。

### 4. `ON OVERFLOW`

目標欄位放不下時，多出來的字會被**默默丟掉**。沒寫 `ON OVERFLOW` 的話，你完全不會知道。

```cobol
STRING WS-LONG-TEXT DELIMITED BY SIZE
   INTO WS-SHORT
   ON OVERFLOW
       MOVE "Y" TO WS-CUT
END-STRING
```

放得下的部分仍然會留在目標欄位裡。

## 常見錯誤

- **名字中間一堆空白**：來源是 `PIC X` 欄位又用了 `DELIMITED BY SIZE`。
- **第二次串接蓋掉第一次**：把指標重設成 1，或在兩次之間 `MOVE SPACES` 到目標。
- **指標欄位太小**：`PIC 9` 最多只能記到 9，目標超過 9 個字就不夠用。
- **`ON OVERFLOW` 後面忘了 `END-STRING`**：後面的敘述會被當成溢位處理的一部分。
- **沒先清空目標**：`STRING` 只覆蓋它寫到的位置，其他位置保留舊內容。

## 操作步驟

1. 在專案根目錄執行 `.\coblings.cmd run 06_string_string`（Linux／macOS：`./coblings.sh run 06_string_string`），開始監看這一題。
2. 用編輯器打開本資料夾的 `Concatenate.cbl`，照「這題要做什麼」修改。**不要改 `ConcatenateTest.cbl`**，它是這一題的驗收標準。
3. 存檔後系統會自動檢查：
   - **解析錯誤**：訊息裡有檔名和行號，照著修正語法。
   - **期望／實際不符**：看斷言的標籤，找出是哪個段落的結果不對。
   - **全部通過**：自動跳到下一題。
4. 卡關時執行 `.\coblings.cmd hint 06_string_string` 看提示。
5. 改亂了想重來，執行 `.\coblings.cmd reset 06_string_string` 還原成原題（你改過的版本會備份到 `.coblings/backup/`）。
