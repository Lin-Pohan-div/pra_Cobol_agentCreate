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
*> 預期：先記錄 BEFORE，接著 GO TO 跳走，WS-SIDE-COUNT 保持 0。
*> TODO: 少了 GO TO 那一行（或目標寫錯），所以程式一路執行到底，
*>       WS-SIDE-COUNT 被 加成 1、WS-TAG 被寫成 "AFTER"。
*>       請在執行 ADD 1 TO WS-SIDE-COUNT 之前，就跳到 SKIP-DONE。
*> ------------------------------------------------------------------
SKIP-BLOCK.
    MOVE SPACES TO WS-TAG
    MOVE 0 TO WS-SIDE-COUNT
    MOVE "BEFORE" TO WS-TAG
    ADD 1 TO WS-SIDE-COUNT
    MOVE "AFTER" TO WS-TAG
    EXIT.

SKIP-DONE.
    EXIT.

*> ------------------------------------------------------------------
*> 段落二：GO TO … DEPENDING ON 依「值」決定跳到第幾個目標。
*>   WS-STEP = 1 → 跳到 TARGET-HIT，WS-HIT-COUNT 變 1、WS-MISS-COUNT 保持 0
*>   WS-STEP = 2 → 沒有第 2 個目標，所以哪裡都不跳，
*>                 接著執行下一行，WS-MISS-COUNT 變 1
*> TODO: 現在寫成普通的 GO TO TARGET-HIT，不論 WS-STEP 是多少都一定跳過去，
*>       所以 WS-MISS-COUNT 永遠是 0。
*>       請改用 GO TO … DEPENDING ON WS-STEP TARGET-HIT。
*> ------------------------------------------------------------------
DISPATCH-BY-STEP.
    MOVE 0 TO WS-HIT-COUNT
    MOVE 0 TO WS-MISS-COUNT
    GO TO TARGET-HIT
    ADD 1 TO WS-MISS-COUNT
    EXIT.

TARGET-HIT.
    ADD 1 TO WS-HIT-COUNT
    EXIT.

*> ------------------------------------------------------------------
*> 段落三：GO TO 也可以往「上」跳，用來做簡單的迴圈。
*> 預期：WS-COUNT 會停在 3。
*> TODO: 數完一次就直接 EXIT. 結束，迴圈只跑一次，WS-COUNT 只會是 1。
*>       請在 WS-COUNT 還沒到 3 的時候，用 GO TO 跳回本段開頭。
*> ------------------------------------------------------------------
REPEAT-BLOCK.
    ADD 1 TO WS-COUNT
    IF WS-COUNT < 3
        EXIT.
    END-IF
    EXIT.

*> 最後一段用 EXIT. 收尾。
LAST-STOP.
    EXIT.
