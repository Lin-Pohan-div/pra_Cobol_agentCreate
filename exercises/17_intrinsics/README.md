# 17 內建函式 ★★

主題：內建函式、`FUNCTION`、字串

## 學習目標

完成這一題後，你會：

- 用 `FUNCTION 名稱 (引數)` 呼叫內建函式，並把結果 `MOVE` 或 `COMPUTE` 到欄位裡。
- 用 `NUMVAL` 把「文字形式的數字」轉成真正的數值。
- 分辨「欄位長度」和「實際內容長度」，知道什麼時候要先 `TRIM`。
- 把函式**巢狀**起來用，並安排正確的先後順序。
- 使用 `MOD`、`MAX`、`MIN` 處理數字。

## 這題要做什麼

要修改的檔案：`Helper.cbl`（不要改 `HelperTest.cbl`）

| 段落 | 完成後應該達成 |
| --- | --- |
| `PARSE-NUMBER` | 文字 `"  0012.50  "` 轉成數值 **12.50**，放進 `WS-NUM`；`TODO` 要求先用 `TRIM` 清掉前後空白再轉換 |
| `CLEAN-TEXT` | `"  coblings  "` 的實際長度 **8** 放進 `WS-LEN`；去掉前後空白再轉大寫的 `COBLINGS` 放進 `WS-CLEAN` |
| `MATH-HELPERS` | `WS-REM` = 17 除以 5 的餘數 **2**；`WS-BIG` = **42**；`WS-SMALL` = **7** |

規則：段落名稱不要改。

## 觀念講解

### 1. 呼叫內建函式

```cobol
MOVE FUNCTION UPPER-CASE (WS-CITY) TO WS-CITY-UP
COMPUTE WS-HALF = FUNCTION INTEGER (WS-QTY / 2)
```

- 寫法是 `FUNCTION 函式名 (引數, 引數…)`。
- 函式的結果可以放在 `MOVE` 的來源，或 `COMPUTE` 的算式裡。
- 函式**不會**修改引數本身，`WS-CITY` 還是原本的樣子。

### 2. 常用的字串函式

| 函式 | 作用 | 例子 |
| --- | --- | --- |
| `TRIM (x)` | 去掉前後空白 | `"  ab  "` → `"ab"` |
| `UPPER-CASE (x)` | 轉大寫 | `"Tea"` → `"TEA"` |
| `LOWER-CASE (x)` | 轉小寫 | `"Tea"` → `"tea"` |
| `LENGTH (x)` | 長度 | 見下一節 |
| `NUMVAL (x)` | 文字轉數值 | `"-3.5"` → -3.5 |

### 3. `LENGTH`：欄位長度 vs. 內容長度

```cobol
01  WS-PET  PIC X(10) VALUE "cat".

FUNCTION LENGTH (WS-PET)                  *> 10（整個欄位）
FUNCTION LENGTH (FUNCTION TRIM (WS-PET))  *> 3（實際內容）
```

`PIC X(10)` 的欄位永遠是 10 個字元，後面補的空白也算在內。要量「真正的文字」，得先把空白去掉。

### 4. 函式可以巢狀

函式的結果可以直接當成另一個函式的引數，**由內往外**依序計算：

```cobol
MOVE FUNCTION LOWER-CASE (FUNCTION TRIM (WS-CODE)) TO WS-KEY
*> 先 TRIM，再把 TRIM 的結果轉小寫
```

### 5. 數字函式

| 函式 | 作用 | 例子 |
| --- | --- | --- |
| `MOD (a, b)` | a 除以 b 的餘數 | `MOD (20, 6)` = 2 |
| `MAX (a, b, …)` | 最大值 | `MAX (3, 9, 4)` = 9 |
| `MIN (a, b, …)` | 最小值 | `MIN (3, 9, 4)` = 3 |

`MOD` 的引數**有順序**：`MOD (6, 20)` 是 6 除以 20，餘數是 6。

## 常見錯誤

- **把資料直接丟給 `NUMVAL` 而不先清理**：`NUMVAL` 可以接受前後的空白，但資料來源一多（例如中間夾了別的符號），先 `TRIM` 再轉是比較保險的習慣，也是本題 `TODO` 要求的寫法。
- **用 `LENGTH` 量 `PIC X` 欄位**：拿到的是欄位寬度，不是文字長度。
- **巢狀順序反了**：注意是哪個函式的結果要交給哪個函式。
- **`MOD` 引數對調**：被除數在前、除數在後。
- **忘了寫 `FUNCTION`**：直接寫 `TRIM (WS-X)` 會被當成欄位名稱，出現解析錯誤。

## 操作步驟

1. 在專案根目錄執行 `.\coblings.cmd run 17_intrinsics`（Linux／macOS：`./coblings.sh run 17_intrinsics`），開始監看這一題。
2. 用編輯器打開本資料夾的 `Helper.cbl`，照「這題要做什麼」修改。**不要改 `HelperTest.cbl`**，它是這一題的驗收標準。
3. 存檔後系統會自動檢查：
   - **解析錯誤**：訊息裡有檔名和行號，照著修正語法。
   - **期望／實際不符**：看斷言的標籤，找出是哪個段落的結果不對。
   - **全部通過**：自動跳到下一題。
4. 卡關時執行 `.\coblings.cmd hint 17_intrinsics` 看提示。
5. 改亂了想重來，執行 `.\coblings.cmd reset 17_intrinsics` 還原成原題（你改過的版本會備份到 `.coblings/backup/`）。
