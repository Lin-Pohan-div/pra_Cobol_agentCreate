*> ============================================================
*> 開始之前：請先閱讀同一個資料夾裡的 README.md
*>   裡面有學習目標、觀念講解、常見錯誤與操作步驟。
*>   卡關時可以執行 .\coblings.cmd hint 看提示。
*> ============================================================
IDENTIFICATION DIVISION.
       PROGRAM-ID. EDIT.

      *> 這一題要體驗「數字編輯欄位」怎麼把數值排版成人看得懂的形式。

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-PRICE      PIC 9(3)V99.
       01  WS-FEE        PIC 9(3)V99.
       01  WS-LINE       PIC 9(5)V99.
       01  WS-BIG        PIC 9(5)V99.
      *>    數字編輯欄位：裡面有 Z、*、+、-、CR、DB，顯示時才會套用格式。
       01  WS-PRICE-ED   PIC *ZZ9.99.
       01  WS-FEE-ED     PIC 9999.99.
       01  WS-LINE-ED    PIC ZZZ9.99.
       01  WS-BIG-ED     PIC ZZZ9.99.
      *>    沒有編輯的欄位：拿來存「數值本身」。
       01  WS-PRICE-VAL  PIC 9(3)V99.
       01  WS-FEE-VAL    PIC 9(3)V99.
       01  WS-LINE-VAL   PIC 9(5)V99.
       01  WS-BIG-VAL    PIC 9(5)V99.

       PROCEDURE DIVISION.
       MAKE-PRICE.
           MOVE 12.5 TO WS-PRICE
           MOVE WS-PRICE TO WS-PRICE-ED
      *>    TODO: 12.50 印出來想要「  12.50」（前導零換成空白），
      *>          但這裡的 PICTURE 用 * 開頭，被抑制的位置會印成星號。
      *>          請把 PICTURE 改成用 Z 來抑制前導零。
           MOVE WS-PRICE-ED TO WS-PRICE-VAL

       MAKE-FEE.
           MOVE 0.5 TO WS-FEE
           MOVE WS-FEE TO WS-FEE-ED
      *>    TODO: 0.50 印出來想要「   0.50」，但這裡的 PICTURE 全部用 9，
      *>          前導零會原樣印出來變成「0000.50」。
      *>          請把該印空白的位數改成 Z。
           MOVE WS-FEE-ED TO WS-FEE-VAL

       MAKE-LINE.
           COMPUTE WS-LINE = WS-PRICE * 100
           MOVE WS-LINE TO WS-LINE-ED
      *>    TODO: 1250.00 的整數部分有四位，編輯欄位要多留一個位數，
      *>          否則高位會被截掉（1250.00 會變成 125.00 或 250.00）。
           MOVE WS-LINE-ED TO WS-LINE-VAL

       MAKE-BIG.
           MOVE 99999.99 TO WS-BIG
           MOVE WS-BIG TO WS-BIG-ED
      *>    TODO: 99999.99 的整數部分有五位，這個編輯欄位也得留五位。
           MOVE WS-BIG-ED TO WS-BIG-VAL

       SHOW-RECEIPT.
           DISPLAY "PRICE=[" WS-PRICE-ED "]"
           DISPLAY "FEE=[" WS-FEE-ED "]"
           DISPLAY "LINE=[" WS-LINE-ED "]"
           DISPLAY "BIG=[" WS-BIG-ED "]"
           EXIT.
