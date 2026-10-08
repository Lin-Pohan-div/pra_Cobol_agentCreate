# 16 GO TO 分派 ★★

主題：`GO TO`、`DEPENDING ON`、`EXIT`

## 學習目標

完成這一題後，你會：

- 用 `GO TO` 跳過不想執行的敘述。
- 用 `GO TO … DEPENDING ON` 依照數值跳到不同的段落，並知道值超出範圍時會發生什麼事。
- 用往回跳的 `GO TO` 寫出簡單的迴圈。
- 理解 `GO TO` 與 `PERFORM … THRU` 搭配時的控制流程。

## 這題要做什麼

要修改的檔案：`Menu.cbl`（不要改 `MenuTest.cbl`）

| 段落 | 完成後應該達成 |
| --- | --- |
| `SKIP-BLOCK` | `WS-TAG` 停在 `BEFORE`，被跳過的 `ADD 1 TO WS-SIDE-COUNT` 不能執行（`WS-SIDE-COUNT` = 0）；要跳到 `SKIP-DONE` |
| `DISPATCH-BY-STEP` | `WS-STEP` = 1 時跳到 `TARGET-HIT`（`WS-HIT-COUNT` = 1、`WS-MISS-COUNT` = 0）；`WS-STEP` = 2 時不跳，繼續往下（`WS-MISS-COUNT` = 1） |
| `REPEAT-BLOCK` | 用往回跳的 `GO TO` 讓 `WS-COUNT` 數到 **3** |

檢查器呼叫方式：`PERFORM SKIP-BLOCK THRU SKIP-DONE`、`PERFORM DISPATCH-BY-STEP THRU TARGET-HIT`、`PERFORM REPEAT-BLOCK`。

規則：段落名稱與順序都不要改。

## 觀念講解

### 1. `GO TO`：無條件跳轉

```cobol
CHECK-INPUT.
    IF WS-INPUT = SPACES
        GO TO CHECK-INPUT-EXIT
    END-IF
    ADD 1 TO WS-VALID
    MOVE WS-INPUT TO WS-LAST.

CHECK-INPUT-EXIT.
    EXIT.
```

- `GO TO 段落名` 會**立刻**跳到那個段落，從跳轉點到段落結尾之間的敘述全部略過。
- 和 `PERFORM` 不同，`GO TO` **不會回來**。

### 2. `GO TO` 與 `PERFORM … THRU` 的搭配

`GO TO` 跳到的段落如果在 `PERFORM` 的範圍**之外**，`PERFORM` 會直接結束，目標段落不會被執行。所以常見的寫法是：

```cobol
PERFORM CHECK-INPUT THRU CHECK-INPUT-EXIT
```

把「出口段落」也包進範圍裡，`GO TO` 跳過去之後還在範圍內，執行完出口段落才回到呼叫端。本題的檢查器就是這樣呼叫你的段落。

### 3. `GO TO … DEPENDING ON`：依數值分派

```cobol
GO TO DEPENDING ON WS-MENU-NO
    OPT-NEW OPT-EDIT OPT-DELETE
DISPLAY "無效的選項"
```

| `WS-MENU-NO` | 結果 |
| --- | --- |
| 1 | 跳到 `OPT-NEW` |
| 2 | 跳到 `OPT-EDIT` |
| 3 | 跳到 `OPT-DELETE` |
| 0、4 或其他 | **哪裡都不跳**，繼續執行下一行（印出「無效的選項」） |

清單裡有幾個段落，就對應 1 到幾。

### 4. 往回跳：用 `GO TO` 寫迴圈

```cobol
RETRY-CONNECT.
    ADD 1 TO WS-TRIES
    IF WS-TRIES < 5 AND WS-CONNECTED = "N"
        GO TO RETRY-CONNECT
    END-IF
    EXIT.
```

跳回段落開頭，就會從頭再執行一次。一定要有**停止條件**，否則會變成無窮迴圈。

> 現代 COBOL 程式通常用 `PERFORM … UNTIL` 取代往回跳的 `GO TO`，因為比較好讀。學 `GO TO` 是為了看得懂舊程式。

## 常見錯誤

- **`GO TO` 寫在要跳過的敘述後面**：該跳過的已經執行了。
- **用普通 `GO TO` 做分派**：不論值是多少都一定會跳，「不跳」的情況永遠不會發生。
- **`DEPENDING ON` 的語法寫錯**：目標清單是段落名稱，用空白隔開。這個系統接受 `GO TO DEPENDING ON 欄位 A B C`，也接受標準 COBOL 的 `GO TO A B C DEPENDING ON 欄位`。
- **往回跳卻沒有停止條件**：無窮迴圈，最後被系統的逾時機制中斷。
- **在 `IF` 裡寫 `EXIT.`**：那個句點會結束整個 `IF`，不會像其他語言的 `return` 一樣跳出段落。

## 操作步驟

1. 在專案根目錄執行 `.\coblings.cmd run 16_go_to`（Linux／macOS：`./coblings.sh run 16_go_to`），開始監看這一題。
2. 用編輯器打開本資料夾的 `Menu.cbl`，照「這題要做什麼」修改。**不要改 `MenuTest.cbl`**，它是這一題的驗收標準。
3. 存檔後系統會自動檢查：
   - **解析錯誤**：訊息裡有檔名和行號，照著修正語法。
   - **期望／實際不符**：看斷言的標籤，找出是哪個段落的結果不對。
   - **全部通過**：自動跳到下一題。
4. 卡關時執行 `.\coblings.cmd hint 16_go_to` 看提示。
5. 改亂了想重來，執行 `.\coblings.cmd reset 16_go_to` 還原成原題（你改過的版本會備份到 `.coblings/backup/`）。
