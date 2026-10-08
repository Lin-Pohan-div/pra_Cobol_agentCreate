*> ============================================================
*> 開始之前：請先閱讀同一個資料夾裡的 README.md
*>   裡面有學習目標、觀念講解、常見錯誤與操作步驟。
*>   卡關時可以執行 .\coblings.cmd hint 看提示。
*> ============================================================
IDENTIFICATION DIVISION.
       PROGRAM-ID. EDIT.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-PRICE      PIC 9(3)V99.
       01  WS-FEE        PIC 9(3)V99.
       01  WS-LINE       PIC 9(5)V99.
       01  WS-BIG        PIC 9(5)V99.
       01  WS-PRICE-ED   PIC ZZZ9.99.
       01  WS-FEE-ED     PIC ZZZ9.99.
       01  WS-LINE-ED    PIC ZZZZ9.99.
       01  WS-BIG-ED     PIC ZZZZ9.99.
       01  WS-PRICE-VAL  PIC 9(3)V99.
       01  WS-FEE-VAL    PIC 9(3)V99.
       01  WS-LINE-VAL   PIC 9(5)V99.
       01  WS-BIG-VAL    PIC 9(5)V99.

       PROCEDURE DIVISION.
       MAKE-PRICE.
           MOVE 12.5 TO WS-PRICE
           MOVE WS-PRICE TO WS-PRICE-ED
           MOVE WS-PRICE-ED TO WS-PRICE-VAL

       MAKE-FEE.
           MOVE 0.5 TO WS-FEE
           MOVE WS-FEE TO WS-FEE-ED
           MOVE WS-FEE-ED TO WS-FEE-VAL

       MAKE-LINE.
           COMPUTE WS-LINE = WS-PRICE * 100
           MOVE WS-LINE TO WS-LINE-ED
           MOVE WS-LINE-ED TO WS-LINE-VAL

       MAKE-BIG.
           MOVE 99999.99 TO WS-BIG
           MOVE WS-BIG TO WS-BIG-ED
           MOVE WS-BIG-ED TO WS-BIG-VAL

       SHOW-RECEIPT.
           DISPLAY "PRICE=[" WS-PRICE-ED "]"
           DISPLAY "FEE=[" WS-FEE-ED "]"
           DISPLAY "LINE=[" WS-LINE-ED "]"
           DISPLAY "BIG=[" WS-BIG-ED "]"
           EXIT.
