# 07 檢查與取代 ★

主題：`INSPECT`、`TALLYING`、`REPLACING`、`CONVERTING`

## 學習目標

完成這一題後，你會：

- 用 `INSPECT … TALLYING` 計算某個字串出現幾次，不必自己寫迴圈。
- 分辨 `REPLACING ALL`、`REPLACING LEADING`、`REPLACING FIRST` 的取代範圍。
- 用 `INSPECT … CONVERTING` 依「字元對照」逐字翻譯。
- 知道哪些 `INSPECT` 會修改原字串、哪些不會。

## 這題要做什麼

要修改的檔案：`Inspect.cbl`（不要改 `InspectTest.cbl`）

| 段落 | 完成後應該達成 |
| --- | --- |
| `COUNT-LETTERS` | 用 `INSPECT … TALLYING` 數出 `MISSISSIPPI` 裡有 **4** 個 `I`，存進 `WS-HITS`；`WS-SOURCE` 本身不能被改動 |
| `NORMALIZE-DATE` | `2024-10-05` 變成 `2024/10/05`，**每一個** `-` 都要換掉 |
| `SWAP-DIGITS` | 用 `INSPECT … CONVERTING` 把 0 和 1 互換：`A10B01C11D00` 變成 `A01B10C00D11` |

規則：段落名稱不要改；三個段落都要用 `INSPECT` 完成，不要自己寫逐字迴圈。

## 觀念講解

### 1. `TALLYING`：數數

```cobol
MOVE 0 TO WS-N
INSPECT WS-WORD TALLYING WS-N FOR ALL "O"
*> WS-WORD = "BOOKSTORE" → WS-N = 3
```

- 計數器會**累加**，不會先歸零，所以要自己先 `MOVE 0`。
- `TALLYING` 只讀不寫，原字串不會改變。
- 也可以數字串：`FOR ALL "OO"` 會數「兩個 O 連在一起」出現幾次。

### 2. `REPLACING`：取代

```cobol
MOVE "**12*3**" TO WS-CODE
INSPECT WS-CODE REPLACING LEADING "*" BY "0"   *> "0012*3**"
INSPECT WS-CODE REPLACING FIRST   "*" BY "-"   *> "0012-3**"
INSPECT WS-CODE REPLACING ALL     "*" BY "_"   *> "0012-3__"
```

| 關鍵字 | 取代範圍 |
| --- | --- |
| `ALL` | 字串裡所有出現的地方 |
| `LEADING` | 只有**開頭連續**出現的那幾個；一遇到別的字元就停 |
| `FIRST` | 只有第一次出現的那一個 |

`REPLACING` 的「找」與「換成」長度必須相同，因為它是原地修改。

### 3. `CONVERTING`：逐字元對照翻譯

`CONVERTING` 一次處理好幾組「A 換成 B」：

```cobol
INSPECT 目標 CONVERTING "要找的字元們" TO "換成的字元們"
```

兩個字串的長度必須相同，**同一個位置的字元兩兩成對**：第 1 個換成第 1 個、第 2 個換成第 2 個……

```cobol
MOVE "bad cab" TO WS-TEXT
INSPECT WS-TEXT CONVERTING "abc" TO "xyz"
*> a→x、b→y、c→z，結果 "yxd zxy"
```

| 位置 | 1 | 2 | 3 |
| --- | --- | --- | --- |
| 要找 | a | b | c |
| 換成 | x | y | z |

重點是：所有對照**同時**生效。「x 換成 y」和「y 換成 x」寫在同一個 `CONVERTING` 裡，不會發生「x 先變成 y、又被變回 x」的情況。

### 4. 哪些會改原字串？

| 子句 | 是否修改原字串 |
| --- | --- |
| `TALLYING` | 否 |
| `REPLACING` | 是 |
| `CONVERTING` | 是 |

## 常見錯誤

- **計數器沒歸零**：重複執行段落時，次數會一直往上加。
- **用 `LEADING` 取代中間的字元**：`LEADING` 只看開頭，中間出現的完全不動。
- **用兩次 `REPLACING` 做互換**：先把 0 換成 1，再把 1 換成 0，結果全變成 0。要互換請用 `CONVERTING` 一次完成。
- **`CONVERTING` 兩邊長度不同**：前後兩個字串要一樣長，才能逐位置對照。
- **把 `TALLYING` 的目標寫成計數器**：`INSPECT` 後面接的是要檢查的字串，`TALLYING` 後面才是計數器。

## 操作步驟

1. 在專案根目錄執行 `.\coblings.cmd run 07_string_inspect`（Linux／macOS：`./coblings.sh run 07_string_inspect`），開始監看這一題。
2. 用編輯器打開本資料夾的 `Inspect.cbl`，照「這題要做什麼」修改。**不要改 `InspectTest.cbl`**，它是這一題的驗收標準。
3. 存檔後系統會自動檢查：
   - **解析錯誤**：訊息裡有檔名和行號，照著修正語法。
   - **期望／實際不符**：看斷言的標籤，找出是哪個段落的結果不對。
   - **全部通過**：自動跳到下一題。
4. 卡關時執行 `.\coblings.cmd hint 07_string_inspect` 看提示。
5. 改亂了想重來，執行 `.\coblings.cmd reset 07_string_inspect` 還原成原題（你改過的版本會備份到 `.coblings/backup/`）。
