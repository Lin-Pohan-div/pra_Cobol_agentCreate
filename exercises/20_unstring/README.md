# 20 字串拆解 ★★

主題：`UNSTRING`、`DELIMITED BY`、文字欄位

## 學習目標

完成這一題後，你會：

- 用 `UNSTRING` 依照分隔字元，把一個字串拆成好幾個欄位。
- 寫對 `UNSTRING` 的語法：來源的 `DELIMITED BY`、`INTO` 清單裡的逗號、每個目標自己的 `DELIMITED BY`。
- 判斷資料用的是哪一種分隔字元。
- 理解拆出來的欄位「靠左、補右邊空白」。

## 這題要做什麼

要修改的檔案：`Split.cbl`（不要改 `SplitTest.cbl`）

| 段落 | 來源 | 完成後應該達成 |
| --- | --- | --- |
| `SPLIT-DATE` | `2026-10-05` | `WS-YEAR` = `2026`、`WS-MONTH` = `10`、`WS-DAY` = `05` |
| `SPLIT-AMOUNT` | `1234.56` | `WS-DOLLARS` = `1234`、`WS-CENTS` = `56` |
| `SPLIT-TAGS` | `red green blue` | `WS-TAG1` = `red`、`WS-TAG2` = `green`、`WS-TAG3` = `blue` |

規則：段落名稱不要改。

## 觀念講解

### 1. `UNSTRING` 是 `STRING` 的反向

`STRING` 把很多段接成一段；`UNSTRING` 把一段切成很多段。

```cobol
MOVE "09:45:30" TO WS-CLOCK
UNSTRING WS-CLOCK DELIMITED BY ":"
    INTO WS-HH DELIMITED BY ":",
         WS-MM DELIMITED BY ":",
         WS-SS DELIMITED BY ":"
*> WS-HH = "09"、WS-MM = "45"、WS-SS = "30"
```

### 2. 語法重點

| 部分 | 說明 |
| --- | --- |
| `UNSTRING 來源 DELIMITED BY "x"` | 看到 `x` 就切一刀 |
| `INTO 目標1 …, 目標2 …, 目標3 …` | 依序放進這些欄位，**目標之間用逗號隔開** |
| 每個目標後面的 `DELIMITED BY "x"` | 這個方言要求每個目標都再寫一次 |

切出來的片段依序放進目標：第 1 段放進目標 1、第 2 段放進目標 2……

### 3. 找出正確的分隔字元

先看資料長什麼樣子，分隔字元就是「夾在每一段中間的那個字元」：

| 資料 | 分隔字元 |
| --- | --- |
| `09:45:30` | `":"` |
| `Taipei/Taichung/Tainan` | `"/"` |
| `apple banana cherry` | `" "`（一個空白） |

寫錯分隔字元時，`UNSTRING` 找不到切點，**整串原文**會被塞進第一個目標（放不下的部分被截掉），其他目標維持原值。

### 4. 拆出來的欄位

目標如果是 `PIC X(n)`，拆出來的內容靠左放，不足的部分補右邊空白。所以 `PIC X(6)` 拿到 `red` 實際上是 `"red   "`。

## 常見錯誤

- **分隔字元寫錯**：第一個目標拿到整串原文（放不下的被截掉），其他目標維持原值。本題事先把目標清成空白，所以你會看到它們是空的。
- **只改了一部分的 `DELIMITED BY`**：來源和每個目標的分隔字元要一致。
- **`INTO` 清單少了逗號**：這個方言用逗號區分目標，漏掉會解析錯誤或切錯。
- **寫成 `DELIMITED BY SIZE`**：意思是「整個欄位都不切」，第一個目標會拿到全部內容。
- **小數點也是分隔字元**：`1234.56` 的元與分之間是 `"."`，不是 `","`。

## 操作步驟

1. 在專案根目錄執行 `.\coblings.cmd run 20_unstring`（Linux／macOS：`./coblings.sh run 20_unstring`），開始監看這一題。
2. 用編輯器打開本資料夾的 `Split.cbl`，照「這題要做什麼」修改。**不要改 `SplitTest.cbl`**，它是這一題的驗收標準。
3. 存檔後系統會自動檢查：
   - **解析錯誤**：訊息裡有檔名和行號，照著修正語法。
   - **期望／實際不符**：看斷言的標籤，找出是哪個段落的結果不對。
   - **全部通過**：自動跳到下一題。
4. 卡關時執行 `.\coblings.cmd hint 20_unstring` 看提示。
5. 改亂了想重來，執行 `.\coblings.cmd reset 20_unstring` 還原成原題（你改過的版本會備份到 `.coblings/backup/`）。
