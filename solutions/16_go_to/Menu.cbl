*> ============================================================
*> 開始之前：請先閱讀同一個資料夾裡的 README.md
*>   裡面有學習目標、觀念講解、常見錯誤與操作步驟。
*>   卡關時可以執行 .\coblings.cmd hint 看提示。
*> ============================================================
IDENTIFICATION DIVISION.
PROGRAM-ID. MENU.

*> 這一題練習 GO TO：跳轉、GO TO … DEPENDING ON、以及往回跳做迴圈。
*> 你要修的是下面三個段落，段落名稱與順序都不要改。

DATA DIVISION.
WORKING-STORAGE SECTION.

*> 檢查器會用這個欄位決定要跳到哪一段
01  WS-STEP        PIC 99 VALUE 0.

*> 檢查器讀得到的結果（01 層級）
01  WS-TAG         PIC X(12).
01  WS-COUNT       PIC 99 VALUE 0.

*> 「副作用計數器」：如果被跳過的敘述不該跑，它就會一直是 0。
01  WS-SIDE-COUNT  PIC 99 VALUE 0.
01  WS-HIT-COUNT   PIC 99 VALUE 0.
01  WS-MISS-COUNT  PIC 99 VALUE 0.

PROCEDURE DIVISION.

*> ------------------------------------------------------------------
*> 段落一：GO TO 可以「跳過」不想執行的敘述。
*> 在執行 ADD 1 TO WS-SIDE-COUNT 之前，先跳到 SKIP-DONE。
*> ------------------------------------------------------------------
SKIP-BLOCK.
    MOVE SPACES TO WS-TAG
    MOVE 0 TO WS-SIDE-COUNT
    MOVE "BEFORE" TO WS-TAG
    GO TO SKIP-DONE
    ADD 1 TO WS-SIDE-COUNT
    MOVE "AFTER" TO WS-TAG
    EXIT.

SKIP-DONE.
    EXIT.

*> ------------------------------------------------------------------
*> 段落二：GO TO … DEPENDING ON 依「值」決定跳到第幾個目標。
*>   WS-STEP = 1 → 跳到 TARGET-HIT
*>   WS-STEP = 2 → 沒有第 2 個目標，哪裡都不跳，繼續往下執行
*> ------------------------------------------------------------------
DISPATCH-BY-STEP.
    MOVE 0 TO WS-HIT-COUNT
    MOVE 0 TO WS-MISS-COUNT
    GO TO DEPENDING ON WS-STEP TARGET-HIT
    ADD 1 TO WS-MISS-COUNT
    EXIT.

TARGET-HIT.
    ADD 1 TO WS-HIT-COUNT
    EXIT.

*> ------------------------------------------------------------------
*> 段落三：GO TO 也可以往「上」跳，用來做簡單的迴圈。
*> 還沒數到 3 就跳回本段開頭。
*> ------------------------------------------------------------------
REPEAT-BLOCK.
    ADD 1 TO WS-COUNT
    IF WS-COUNT < 3
        GO TO REPEAT-BLOCK
    END-IF
    EXIT.

*> 最後一段用 EXIT. 收尾。
LAST-STOP.
    EXIT.
