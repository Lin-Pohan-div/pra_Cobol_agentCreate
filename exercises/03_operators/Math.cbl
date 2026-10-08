*> ============================================================
*> 開始之前：請先閱讀同一個資料夾裡的 README.md
*>   裡面有學習目標、觀念講解、常見錯誤與操作步驟。
*>   卡關時可以執行 .\coblings.cmd hint 看提示。
*> ============================================================
IDENTIFICATION DIVISION.
       PROGRAM-ID. MATH.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-A           PIC 9(4).
       01  WS-B           PIC 9(4).
       01  WS-C           PIC 9(4).
       01  WS-SUM         PIC 9(4).
       01  WS-DAYS        PIC 9(3).
       01  WS-BORROWED    PIC 9(3).
       01  WS-UNIT-PRICE  PIC 9(3)V99.
       01  WS-QTY         PIC 9(3).
       01  WS-TOTAL-PRICE PIC 9(5)V99.
       01  WS-AVG         PIC 9(3)V99.
       01  WS-AVG-ROUND   PIC 9(3)V99.

       PROCEDURE DIVISION.
       SUM-THREE.
           MOVE 12 TO WS-A
           MOVE 30 TO WS-B
           MOVE 45 TO WS-C
           MOVE 0 TO WS-SUM
      *>    TODO: ADD x TO y 的意思是「把 x 加到 y」，y 是被改的那一個。
      *>          這裡應該把三個分數都累加到 WS-SUM，不該動到 WS-B。
           ADD WS-A TO WS-B
           ADD WS-A TO WS-SUM
           ADD WS-B TO WS-SUM
           ADD WS-C TO WS-SUM

       TAKE-AWAY.
           MOVE 30 TO WS-DAYS
           MOVE 12 TO WS-BORROWED
      *>    TODO: SUBTRACT 後面放「被減的那個」，FROM 後面放「要減掉的那個」。
      *>          借出 12 天之後剩下 18 天，應該寫成
      *>          SUBTRACT WS-BORROWED FROM WS-DAYS（結果寫回 WS-DAYS）。
           SUBTRACT WS-DAYS FROM WS-BORROWED

       LINE-TOTAL.
           MOVE 12.5 TO WS-UNIT-PRICE
           MOVE 4 TO WS-QTY
      *>    TODO: 沒有寫 GIVING 時，結果會直接寫回 BY 右邊的 WS-UNIT-PRICE，
      *>          單價就被蓋掉了，WS-TOTAL-PRICE 還是 0。
           MOVE 0 TO WS-TOTAL-PRICE
           MULTIPLY WS-QTY BY WS-UNIT-PRICE

       AVERAGE-PRICE.
      *>    TODO: DIVIDE a BY b 是 a 除以 b；INTO 的方向相反。
      *>          100 除以 6 應該寫成 DIVIDE 100 BY 6，結果 16.66（截斷）。
           DIVIDE 6 INTO 100 GIVING WS-AVG
           DIVIDE 100 BY 6 GIVING WS-AVG-ROUND ROUNDED.
           EXIT.
