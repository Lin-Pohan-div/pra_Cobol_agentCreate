# 22 順序檔案 ★★★

主題：`SELECT`、`FD`、`OPEN`、`WRITE`、`READ`、`CLOSE`

## 學習目標

完成這一題後，你會：

- 用 `SELECT … ASSIGN TO` 與 `FD` 宣告一個順序檔（sequential file）和它的記錄格式。
- 依照「開檔 → 寫入 → 關檔」的流程寫出資料檔。
- 依照「開檔 → 逐筆讀取 → 關檔」的流程讀回資料。
- 用 `AT END` 偵測檔案結尾，寫出不會出錯的讀檔迴圈。

## 這題要做什麼

要修改的檔案：`Ledger.cbl`（不要改 `LedgerTest.cbl`）

| 段落 | 完成後應該達成 |
| --- | --- |
| `WRITE-LEDGER` | 把 3 筆記錄寫到 `ledger.dat`，而且真的寫進磁碟 |
| `READ-LEDGER` | 讀回全部記錄：`WS-COUNT` = **3**，`WS-LINE` 是最後一筆 `C03 99.99   ` |

檢查器會先執行 `WRITE-LEDGER`、再執行 `READ-LEDGER`，最後把 `ledger.dat` 清空。

規則：段落名稱不要改。

## 觀念講解

### 1. 宣告檔案

```cobol
ENVIRONMENT DIVISION.
INPUT-OUTPUT SECTION.
FILE-CONTROL.
    SELECT NOTE-FILE ASSIGN TO "notes.dat".

DATA DIVISION.
FILE SECTION.
FD  NOTE-FILE.
01  NOTE-REC   PIC X(20).
```

| 部分 | 作用 |
| --- | --- |
| `SELECT 檔名 ASSIGN TO "實體檔"` | 程式裡的檔名對應到磁碟上的哪個檔案 |
| `FD 檔名` | 這個檔案的描述 |
| `FD` 底下的 `01` | 每一筆記錄的格式（記錄緩衝區） |

### 2. 寫檔：`OPEN OUTPUT` → `WRITE` → `CLOSE`

```cobol
OPEN OUTPUT NOTE-FILE
MOVE "buy milk" TO NOTE-REC
WRITE NOTE-REC
MOVE "call mom" TO NOTE-REC
WRITE NOTE-REC
CLOSE NOTE-FILE
```

- `OPEN OUTPUT` 會**先清空**檔案。
- 每次 `WRITE` 把記錄緩衝區的內容加到檔案最後。
- 一定要 `CLOSE`：在這個系統裡，資料到 `CLOSE` 時才真正寫進磁碟。

### 3. 讀檔：`OPEN INPUT` → `READ` → `CLOSE`

```cobol
OPEN INPUT NOTE-FILE
MOVE "N" TO WS-DONE
PERFORM UNTIL WS-DONE = "Y"
    READ NOTE-FILE INTO WS-NOTE
        AT END
            MOVE "Y" TO WS-DONE
        NOT AT END
            ADD 1 TO WS-NOTES
    END-READ
END-PERFORM
CLOSE NOTE-FILE
```

- `READ 檔名 INTO 欄位` 讀一筆，順便複製到 `WS-NOTE`。
- `AT END`：已經沒有資料可以讀時執行，通常用來設結束旗標。
- 已經讀到結尾、卻沒有 `AT END` 可以處理時，這個系統會讓程式**中斷**。
- 也可以不用 `NOT AT END`，改在 `END-READ` 之後用 `IF WS-DONE = "N"` 判斷是否真的讀到資料。

### 4. 讀檔迴圈的節奏

每一輪：`READ` 一次 → 判斷有沒有讀到 → 有就處理、沒有就結束。最後一次 `READ` 會碰到結尾，這一輪**不應該**被算成一筆資料。

## 常見錯誤

- **寫完沒有 `CLOSE`**：磁碟上的檔案是空的，之後讀不到任何資料。
- **讀檔沒有 `AT END`**：讀完最後一筆再讀一次就中斷。
- **把碰到結尾的那一輪也算進去**：筆數多 1。
- **`READ` 後面忘了 `END-READ`**：後面的敘述會被當成 `AT END` 的一部分，只在讀到結尾時執行。
- **讀之前沒有 `OPEN INPUT`，或寫之前沒有 `OPEN OUTPUT`**：開檔模式要和動作一致。

## 操作步驟

1. 在專案根目錄執行 `.\coblings.cmd run 22_file_io`（Linux／macOS：`./coblings.sh run 22_file_io`），開始監看這一題。
2. 用編輯器打開本資料夾的 `Ledger.cbl`，照「這題要做什麼」修改。**不要改 `LedgerTest.cbl`**，它是這一題的驗收標準。
3. 存檔後系統會自動檢查：
   - **解析錯誤**：訊息裡有檔名和行號，照著修正語法。
   - **期望／實際不符**：看斷言的標籤，找出是哪個段落的結果不對。
   - **全部通過**：自動跳到下一題。
4. 卡關時執行 `.\coblings.cmd hint 22_file_io` 看提示。
5. 改亂了想重來，執行 `.\coblings.cmd reset 22_file_io` 還原成原題（你改過的版本會備份到 `.coblings/backup/`）。

`ledger.dat` 是執行時產生的資料檔，檢查器跑完會清空它，不需要手動處理。
