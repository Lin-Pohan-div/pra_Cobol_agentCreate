# 08 條件判斷 ★

主題：`IF`、`ELSE`、關係運算子、88 條件名稱

## 學習目標

完成這一題後，你會：

- 寫出 `IF … ELSE … END-IF` 的二選一判斷。
- 用 `ELSE IF` 串成多段條件鏈，並安排條件的先後順序。
- 使用六種關係運算子：`=`、`<>`、`>`、`<`、`>=`、`<=`。
- 宣告並使用 88 條件名稱，讓條件讀起來像一句話。

## 這題要做什麼

要修改的檔案：`Branch.cbl`（不要改 `BranchTest.cbl`）

| 段落 | 完成後應該達成 |
| --- | --- |
| `LABEL-OF-SCORE` | 依「≥ 90 → A、≥ 80 → B、≥ 60 → C、其餘 → F」，把 85 分的等級 **B** 放進 `WS-LABEL`；要用 `ELSE IF` 鏈 |
| `ADVICE-OF-TEMP` | 依「≥ 30 → HOT，否則 COLD」，把 35 度的建議 **HOT** 放進 `WS-ADVICE` |
| `USE-88-NAME` | 用 88 條件名稱 `WS-PASSING` 判斷 85 分，把 **PASS** 放進 `WS-ADVICE`；不要自己寫 `>= 60 AND <= 100` |

規則：段落名稱不要改。每個段落目前只剩下 `TODO` 註解和一個單獨的句點，請把你的判斷寫在那個句點**之前**。

## 觀念講解

### 1. 基本的 `IF`

```cobol
IF WS-AGE >= 18
    MOVE "ADULT" TO WS-TYPE
ELSE
    MOVE "CHILD" TO WS-TYPE
END-IF
```

- 條件成立，執行 `IF` 和 `ELSE` 之間的敘述；不成立，執行 `ELSE` 和 `END-IF` 之間的敘述。
- `ELSE` 可以省略。
- `END-IF` 標出整個判斷的結尾，請一律寫上。

### 2. 用 `ELSE IF` 處理三種以上的情況

```cobol
IF WS-AGE >= 65
    MOVE "SENIOR" TO WS-TICKET
ELSE IF WS-AGE >= 18
    MOVE "ADULT" TO WS-TICKET
ELSE IF WS-AGE >= 6
    MOVE "CHILD" TO WS-TICKET
ELSE
    MOVE "FREE" TO WS-TICKET
END-IF
```

條件會**從上往下**檢查，一碰到成立的就執行那一段，其他都跳過。所以範圍判斷要**從最嚴格的寫起**：如果把 `>= 6` 放在最前面，70 歲的人也會拿到兒童票。

### 3. 關係運算子

| 運算子 | 意思 |
| --- | --- |
| `=` | 等於 |
| `<>` | 不等於 |
| `>`、`<` | 大於、小於 |
| `>=`、`<=` | 大於等於、小於等於 |

數字和文字欄位都可以比較。

### 4. 88 條件名稱

88 層級幫一個欄位的「某些值」取名字：

```cobol
01  WS-MONTH      PIC 99.
    88  WS-SUMMER VALUE 6 THRU 8.
    88  WS-WINTER VALUE 12 1 2.
```

之後就可以直接寫：

```cobol
IF WS-SUMMER
    MOVE "SWIM" TO WS-PLAN
END-IF
```

- `VALUE 6 THRU 8` 代表 6 到 8（包含頭尾）；`VALUE 12 1 2` 代表這三個值中的任何一個。
- 88 必須**緊接在**它描述的那個欄位後面，否則不會生效。
- 88 本身不佔記憶體，只是一個「條件的名字」。

## 常見錯誤

- **條件順序寫反**：寬鬆的條件放在前面，會把所有情況都攔下來。
- **在 `IF` 裡面提早寫句點**：句點會一口氣結束所有還沒收尾的 `IF`。在 `ELSE` 之前多打一個句點，後面的 `ELSE` 就接不上，會出現解析錯誤。
- **漏寫 `END-IF`**：巢狀的 `IF` 很容易搞不清楚 `ELSE` 屬於哪一層。
- **自己重寫 88 的範圍**：題目要求用 `IF WS-PASSING`，不要寫成 `IF WS-SCORE >= 60 AND …`。
- **把文字值寫錯**：`"Hot"` 和 `"HOT"` 不一樣。

## 操作步驟

1. 在專案根目錄執行 `.\coblings.cmd run 08_if_else`（Linux／macOS：`./coblings.sh run 08_if_else`），開始監看這一題。
2. 用編輯器打開本資料夾的 `Branch.cbl`，照「這題要做什麼」修改。**不要改 `BranchTest.cbl`**，它是這一題的驗收標準。
3. 存檔後系統會自動檢查：
   - **解析錯誤**：訊息裡有檔名和行號，照著修正語法。
   - **期望／實際不符**：看斷言的標籤，找出是哪個段落的結果不對。
   - **全部通過**：自動跳到下一題。
4. 卡關時執行 `.\coblings.cmd hint 08_if_else` 看提示。
5. 改亂了想重來，執行 `.\coblings.cmd reset 08_if_else` 還原成原題（你改過的版本會備份到 `.coblings/backup/`）。
