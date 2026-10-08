# 19 捨入與溢位 ★★

主題：`ROUNDED`、`ON SIZE ERROR`、`DIVIDE BY ZERO`

## 學習目標

完成這一題後，你會：

- 用 `ROUNDED` 讓除法結果四捨五入，而不是預設的截斷。
- 在除法之前先檢查除數，避免 `DIVIDE BY ZERO` 讓程式中斷。
- 用 `COMPUTE … ON SIZE ERROR … END-COMPUTE` 偵測並處理溢位。
- 說得出「截斷」、「SIZE ERROR」和「執行期錯誤」三者的差別。

## 這題要做什麼

要修改的檔案：`Rounding.cbl`（不要改 `RoundingTest.cbl`）

| 段落 | 完成後應該達成 |
| --- | --- |
| `AVERAGE-SPLIT` | 100.00 元分給 7 人，每人 **14.29**（四捨五入），放進 `WS-SHARE` |
| `SAFE-RATE` | 人數是 0 時不能出錯：`WS-STATUS` = `ZERO`、`WS-SHARE` = 0 |
| `CAP-SCORE` | 800 + 500 放不進 `PIC 9(3)` 時：`WS-SCORE` = **999**、`WS-CAPPED` = `Y` |

規則：段落名稱不要改。

## 觀念講解

### 1. 三種「數字出狀況」

| 情況 | 會發生什麼事 | 要怎麼處理 |
| --- | --- | --- |
| 小數位放不下 | **截斷**多的小數位，不報錯 | 加 `ROUNDED` |
| 整數位放不下（算術敘述） | **SIZE ERROR**：接收欄位**維持原值**，不報錯 | 加 `ON SIZE ERROR` |
| 除數是 0 | **執行期錯誤**，程式中斷 | 事先用 `IF` 檢查 |

前兩種都不會讓程式停下來，所以更危險：結果錯了，你卻不知道。

### 2. `ROUNDED`

```cobol
01  WS-PER-CUP  PIC 9(3)V9.

DIVIDE 50 BY 3 GIVING WS-PER-CUP              *> 16.6
DIVIDE 50 BY 3 GIVING WS-PER-CUP ROUNDED      *> 16.7
```

`ROUNDED` 寫在接收欄位的後面。

### 3. 先檢查，再除

```cobol
IF WS-HOURS = 0
    MOVE 0 TO WS-RATE
    MOVE "N/A" TO WS-NOTE
ELSE
    DIVIDE WS-PAY BY WS-HOURS GIVING WS-RATE ROUNDED
END-IF
```

除數是 0 時，「結果是 0」只是你自己決定的處理方式，COBOL 不會幫你這樣做；不檢查的話，程式會直接中斷。

### 4. `ON SIZE ERROR`

```cobol
01  WS-TEMP  PIC 9(2).

COMPUTE WS-TEMP = WS-TEMP + WS-RISE
    ON SIZE ERROR
        MOVE 99 TO WS-TEMP
        MOVE "Y" TO WS-ALARM
END-COMPUTE
```

- 結果的整數部分放不下時，執行 `ON SIZE ERROR` 和 `END-COMPUTE` 之間的敘述。
- 沒有溢位時，這一段完全不會執行。
- 因為發生 SIZE ERROR 時接收欄位會維持原值，要「夾住上限」就得自己在處理程式裡 `MOVE` 上限值進去。

## 常見錯誤

- **`ROUNDED` 放錯位置**：要放在 `GIVING` 後面的接收欄位之後。
- **只在除數為 0 時設狀態**：題目也要求 `WS-SHARE` 為 0，兩個欄位都要設。
- **`ON SIZE ERROR` 沒有 `END-COMPUTE`**：後面的敘述會被當成錯誤處理的一部分。
- **以為溢位時欄位會變成最大值**：不會，它維持原值；最大值要自己放。
- **以為除以 0 的結果是 0**：COBOL 會直接中斷程式。

## 操作步驟

1. 在專案根目錄執行 `.\coblings.cmd run 19_math`（Linux／macOS：`./coblings.sh run 19_math`），開始監看這一題。
2. 用編輯器打開本資料夾的 `Rounding.cbl`，照「這題要做什麼」修改。**不要改 `RoundingTest.cbl`**，它是這一題的驗收標準。
3. 存檔後系統會自動檢查：
   - **解析錯誤**：訊息裡有檔名和行號，照著修正語法。
   - **期望／實際不符**：看斷言的標籤，找出是哪個段落的結果不對。
   - **全部通過**：自動跳到下一題。
4. 卡關時執行 `.\coblings.cmd hint 19_math` 看提示。
5. 改亂了想重來，執行 `.\coblings.cmd reset 19_math` 還原成原題（你改過的版本會備份到 `.coblings/backup/`）。
