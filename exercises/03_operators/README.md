# 03 四則運算 ★

主題：`ADD`、`SUBTRACT`、`MULTIPLY`、`DIVIDE`

## 學習目標

完成這一題後，你會：

- 用 COBOL 的四個算術動詞做加減乘除，並說得出「結果寫到哪個欄位」。
- 用 `GIVING` 把結果放進另一個欄位，保住原本的運算元。
- 分辨 `DIVIDE … BY …` 與 `DIVIDE … INTO …` 的方向。
- 知道結果預設是**截斷**，要四捨五入得加 `ROUNDED`。

## 這題要做什麼

要修改的檔案：`Math.cbl`（不要改 `MathTest.cbl`）

| 段落 | 完成後應該達成 |
| --- | --- |
| `SUM-THREE` | `WS-SUM` = 12 + 30 + 45 = **87**，過程中不能動到 `WS-B` |
| `TAKE-AWAY` | `WS-DAYS` 從 30 減掉 12 剩 **18**；`WS-BORROWED` 維持 12 |
| `LINE-TOTAL` | `WS-TOTAL-PRICE` = 12.50 × 4 = **50.00**，單價不能被蓋掉 |
| `AVERAGE-PRICE` | `WS-AVG` = 100 ÷ 6 截斷 = **16.66**；`WS-AVG-ROUND` = 四捨五入 = **16.67** |

規則：段落名稱不要改。

## 觀念講解

COBOL 的算術動詞讀起來像英文句子，**最後被改掉的是哪個欄位**是重點。

### 1. `ADD`

```cobol
ADD 5 TO WS-STOCK                   *> WS-STOCK = WS-STOCK + 5
ADD WS-X WS-Y GIVING WS-Z           *> WS-Z = WS-X + WS-Y，WS-X、WS-Y 不變
```

`TO` 右邊的欄位會被改掉。

### 2. `SUBTRACT`

```cobol
SUBTRACT 3 FROM WS-STOCK            *> WS-STOCK = WS-STOCK - 3
```

讀成「從 WS-STOCK **減掉** 3」：`FROM` 右邊的是被減數，結果也寫回它。

### 3. `MULTIPLY` 與 `DIVIDE`

```cobol
MULTIPLY 2 BY WS-SIZE               *> WS-SIZE = 2 * WS-SIZE（寫回 BY 右邊）
MULTIPLY WS-W BY WS-H GIVING WS-AREA *> WS-AREA = WS-W * WS-H，兩個運算元都不變

DIVIDE WS-DIST BY WS-TIME GIVING WS-SPEED   *> WS-SPEED = WS-DIST / WS-TIME
DIVIDE 4 INTO WS-CAKE                        *> WS-CAKE  = WS-CAKE / 4
```

| 寫法 | 被除數 | 除數 |
| --- | --- | --- |
| `DIVIDE a BY b` | a | b |
| `DIVIDE a INTO b` | b | a |

沒寫 `GIVING` 時，結果會寫回其中一個運算元，原本的值就不見了。

### 4. 截斷與 `ROUNDED`

結果的小數位比接收欄位多時，預設是**直接砍掉**多的位數：

```cobol
01  WS-RATE  PIC 9V99.
DIVIDE 2 BY 3 GIVING WS-RATE            *> 0.66（截斷）
DIVIDE 2 BY 3 GIVING WS-RATE ROUNDED    *> 0.67（四捨五入）
```

`ROUNDED` 要寫在接收欄位的**後面**。

## 常見錯誤

- **改到不該改的欄位**：`ADD x TO y` 會改 y。想累加到總和，`TO` 後面就要放總和欄位。
- **`SUBTRACT` 順序寫反**：`SUBTRACT a FROM b` 是 b − a，寫反了連被減的那個也會被改掉。
- **乘完單價不見了**：沒有 `GIVING` 的 `MULTIPLY` 會把結果寫回 `BY` 右邊的欄位。
- **`BY` 和 `INTO` 搞混**：100 ÷ 6 和 6 ÷ 100 差很多；不確定時一律用 `BY` 搭配 `GIVING`，最好讀。
- **以為會自動四捨五入**：COBOL 預設截斷，只有算術敘述可以加 `ROUNDED`。

## 操作步驟

1. 在專案根目錄執行 `.\coblings.cmd run 03_operators`（Linux／macOS：`./coblings.sh run 03_operators`），開始監看這一題。
2. 用編輯器打開本資料夾的 `Math.cbl`，照「這題要做什麼」修改。**不要改 `MathTest.cbl`**，它是這一題的驗收標準。
3. 存檔後系統會自動檢查：
   - **解析錯誤**：訊息裡有檔名和行號，照著修正語法。
   - **期望／實際不符**：看斷言的標籤，找出是哪個段落的結果不對。
   - **全部通過**：自動跳到下一題。
4. 卡關時執行 `.\coblings.cmd hint 03_operators` 看提示。
5. 改亂了想重來，執行 `.\coblings.cmd reset 03_operators` 還原成原題（你改過的版本會備份到 `.coblings/backup/`）。
