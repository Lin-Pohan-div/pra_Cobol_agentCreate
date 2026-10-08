*> ============================================================
*> 開始之前：請先閱讀同一個資料夾裡的 README.md
*>   裡面有學習目標、觀念講解、常見錯誤與操作步驟。
*>   卡關時可以執行 .\coblings.cmd hint 看提示。
*> ============================================================
IDENTIFICATION DIVISION.
       PROGRAM-ID. COUNTER.

*> 迴圈有兩種基本寫法：
*>   PERFORM UNTIL 條件 ... END-PERFORM   ── 條件「成立」就停
*>   PERFORM VARYING 計數器 FROM 起始 BY 步長 UNTIL 條件 ... END-PERFORM
*> 這題先練習 UNTIL：自己維護一個計數器當「已經做了幾次」。

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-TOTAL   PIC 9(5).
       01  WS-COUNT   PIC 9(3).
       01  WS-LIMIT   PIC 9(3).
       01  WS-REMAIN  PIC 9(3).
       01  WS-START   PIC 9(3).

       PROCEDURE DIVISION.

       SUM-TO-LIMIT.
           MOVE 0 TO WS-TOTAL
           MOVE 0 TO WS-COUNT
           MOVE 10 TO WS-LIMIT
           PERFORM UNTIL WS-COUNT >= 10
               ADD 1 TO WS-COUNT
               ADD WS-COUNT TO WS-TOTAL
           END-PERFORM.

       COUNT-DOWN.
           MOVE 10 TO WS-COUNT
           MOVE 0 TO WS-REMAIN
           PERFORM UNTIL WS-COUNT = 0
               SUBTRACT 1 FROM WS-COUNT
               ADD 1 TO WS-REMAIN
           END-PERFORM.

       COPY-N-TIMES.
           MOVE 0 TO WS-COUNT
           MOVE 0 TO WS-TOTAL
           MOVE 3 TO WS-START
           PERFORM UNTIL WS-COUNT >= 5
               ADD 1 TO WS-COUNT
               ADD WS-START TO WS-TOTAL
           END-PERFORM.
           EXIT.
