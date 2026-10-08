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
      *> TODO: 規格：一個 3 列 4 欄的表格共有 12 格，存進 WS-CELLS。
      *>       請寫成 PERFORM VARYING WS-ROW FROM 1 BY 1 UNTIL WS-ROW > 3
      *>           AFTER WS-COL FROM 1 BY 1 UNTIL WS-COL > 4
      *>           ADD 1 TO WS-CELLS END-PERFORM
           .

       SUM-WITH-WEIGHT.
           MOVE 0 TO WS-SUM
      *> TODO: 規格：每一格 (列, 欄) 的權重是 10 * WS-ROW + WS-COL，
      *>       把 12 格的權重全部加總，結果 270 存進 WS-SUM。
      *>       請用 COMPUTE WS-WEIGHT = 10 * WS-ROW + WS-COL 算出該格權重。
           .

       ROW-TOTALS.
           MOVE 0 TO WS-SUM
      *> TODO: 規格：只計算「欄號大於列號」的格子（嚴格上三角），
      *>       3 列時共有 6 格：(1,2) (1,3) (1,4) (2,3) (2,4) (3,4)，
      *>       權重依序是 12 13 14 23 24 34，總和 120 存進 WS-SUM。
      *>       條件寫在迴圈體裡，用 IF WS-COL > WS-ROW 才累加
      *>       （這樣內層仍然要照規格走 1 到 4，只是有的格子不計）。
           .
           EXIT.
