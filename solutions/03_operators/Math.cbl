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
           ADD WS-A TO WS-SUM
           ADD WS-B TO WS-SUM
           ADD WS-C TO WS-SUM

       TAKE-AWAY.
           MOVE 30 TO WS-DAYS
           MOVE 12 TO WS-BORROWED
           SUBTRACT WS-BORROWED FROM WS-DAYS

       LINE-TOTAL.
           MOVE 12.5 TO WS-UNIT-PRICE
           MOVE 4 TO WS-QTY
           MOVE 0 TO WS-TOTAL-PRICE
           MULTIPLY WS-UNIT-PRICE BY WS-QTY GIVING WS-TOTAL-PRICE

       AVERAGE-PRICE.
           DIVIDE 100 BY 6 GIVING WS-AVG
           DIVIDE 100 BY 6 GIVING WS-AVG-ROUND ROUNDED.
           EXIT.
