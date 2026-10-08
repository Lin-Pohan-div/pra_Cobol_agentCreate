*> ============================================================
*> 開始之前：請先閱讀同一個資料夾裡的 README.md
*>   裡面有學習目標、觀念講解、常見錯誤與操作步驟。
*>   卡關時可以執行 .\coblings.cmd hint 看提示。
*> ============================================================
IDENTIFICATION DIVISION.
       PROGRAM-ID. GRID.

*> 巢狀迴圈用 AFTER 寫在同一個 PERFORM VARYING 裡：
*>   PERFORM VARYING 外層 FROM .. BY .. UNTIL ..
*>       AFTER 內層 FROM .. BY .. UNTIL ..
*>       ...迴圈體... END-PERFORM
*> 內層的範圍每換一次外層就從 FROM 重新開始一次。

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-ROW      PIC 9(3).
       01  WS-COL      PIC 9(3).
       01  WS-WEIGHT   PIC 9(3).
       01  WS-CELLS    PIC 9(4).
       01  WS-SUM      PIC 9(5).
       01  WS-MAX      PIC 9(3).
       01  WS-ROW-SUM  PIC 9(5).

       PROCEDURE DIVISION.

       COUNT-CELLS.
           MOVE 0 TO WS-CELLS
           PERFORM VARYING WS-ROW FROM 1 BY 1 UNTIL WS-ROW > 3
               AFTER WS-COL FROM 1 BY 1 UNTIL WS-COL > 4
                   ADD 1 TO WS-CELLS
               END-PERFORM.

       SUM-WITH-WEIGHT.
           MOVE 0 TO WS-SUM
           PERFORM VARYING WS-ROW FROM 1 BY 1 UNTIL WS-ROW > 3
               AFTER WS-COL FROM 1 BY 1 UNTIL WS-COL > 4
                   COMPUTE WS-WEIGHT = 10 * WS-ROW + WS-COL
                   ADD WS-WEIGHT TO WS-SUM
               END-PERFORM.

       ROW-TOTALS.
           MOVE 0 TO WS-SUM
           PERFORM VARYING WS-ROW FROM 1 BY 1 UNTIL WS-ROW > 3
               AFTER WS-COL FROM 1 BY 1 UNTIL WS-COL > 4
                   IF WS-COL > WS-ROW
                       COMPUTE WS-WEIGHT = 10 * WS-ROW + WS-COL
                       ADD WS-WEIGHT TO WS-SUM
                   END-IF
               END-PERFORM.
           EXIT.
