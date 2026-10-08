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
      *> TODO: 規格：每次把 WS-COUNT 加 1，並把 WS-COUNT 加進 WS-TOTAL，
      *>       重複到 WS-COUNT 剛好等於 10 為止。答案應該是 55。
      *>       請用 PERFORM UNTIL WS-COUNT >= 10 ... END-PERFORM。
      *>       迴圈體（END-PERFORM 之前）放每次要做的事。
           .

       COUNT-DOWN.
           MOVE 10 TO WS-COUNT
           MOVE 0 TO WS-REMAIN
      *> TODO: 規格：每次把 WS-COUNT 減 1，並讓 WS-REMAIN 加 1，
      *>       直到 WS-COUNT 變成 0。答案應該是 10。
      *>       請用 PERFORM UNTIL WS-COUNT = 0 ... END-PERFORM。
           .

       COPY-N-TIMES.
           MOVE 0 TO WS-TOTAL
           MOVE 3 TO WS-START
      *> TODO: 規格：把 3 累加 5 次，結果 15 存進 WS-TOTAL（WS-COUNT 當計數器）。
      *>       請用 PERFORM UNTIL WS-COUNT >= 5 ... END-PERFORM，
      *>       記得先把 WS-COUNT 和 WS-TOTAL 都清成 0，
      *>       否則一開始就滿足了終止條件，迴圈一次都不會跑。
           .
           EXIT.
