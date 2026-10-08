*> ============================================================
*> 開始之前：請先閱讀同一個資料夾裡的 README.md
*>   裡面有學習目標、觀念講解、常見錯誤與操作步驟。
*>   卡關時可以執行 .\coblings.cmd hint 看提示。
*> ============================================================
IDENTIFICATION DIVISION.
       PROGRAM-ID. VARIABLES.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-NAME      PIC X(10).
       01  WS-COUNT     PIC 9(3).
       01  WS-PRICE     PIC 9(3)V99.
       01  WS-NAME-OUT  PIC X(10).
       01  WS-COUNT-OUT PIC 9(3).
       01  WS-PRICE-OUT PIC 9(3)V99.

       PROCEDURE DIVISION.
       FILL-FIELDS.
           MOVE "Amy" TO WS-NAME
           MOVE 45 TO WS-COUNT
      *>    TODO: WS-PRICE 的 PICTURE 是 9(3)V99，也就是「最多三位整數、兩位小數」。
      *>          單價 12.50 元要寫成 12.5，寫成 1250 會被當成 1250.00 元（差了 100 倍）。
           MOVE 1250 TO WS-PRICE

       COPY-FIELDS.
      *>    TODO: MOVE 的順序是「來源 TO 接收端」，這兩行方向寫反了，
      *>          結果 WS-COUNT 被清成 0，WS-COUNT-OUT 也等於 0。
           MOVE WS-COUNT-OUT TO WS-COUNT
           MOVE WS-COUNT TO WS-COUNT-OUT
           MOVE WS-NAME TO WS-NAME-OUT
           MOVE WS-PRICE TO WS-PRICE-OUT

       SHOW-FIELDS.
           DISPLAY "NAME: " WS-NAME-OUT
           DISPLAY "COUNT: " WS-COUNT-OUT
           DISPLAY "PRICE: " WS-PRICE-OUT
           EXIT.
