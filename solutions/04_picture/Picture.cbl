*> ============================================================
*> 開始之前：請先閱讀同一個資料夾裡的 README.md
*>   裡面有學習目標、觀念講解、常見錯誤與操作步驟。
*>   卡關時可以執行 .\coblings.cmd hint 看提示。
*> ============================================================
IDENTIFICATION DIVISION.
       PROGRAM-ID. PICTURE.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-SERIAL      PIC 9(5).
       01  WS-NAME        PIC X(8).
       01  WS-PRICE       PIC 9(3)V99.
       01  WS-COUNTER     PIC 9(3).
       01  WS-SERIAL-OUT  PIC 9(5).
       01  WS-NAME-OUT    PIC X(8).
       01  WS-PRICE-OUT   PIC 9(3)V99.
       01  WS-SIZE-FLAG   PIC X(4).

       PROCEDURE DIVISION.
       LOAD-BIG-NUMBER.
           MOVE 12345 TO WS-SERIAL
           MOVE WS-SERIAL TO WS-SERIAL-OUT

       LOAD-LONG-TEXT.
           MOVE "Coblings" TO WS-NAME
           MOVE WS-NAME TO WS-NAME-OUT

       LOAD-PRICE.
           COMPUTE WS-PRICE ROUNDED = 12.567
           MOVE WS-PRICE TO WS-PRICE-OUT

       CHECK-SIZE-ERROR.
           MOVE 999 TO WS-COUNTER
           MOVE "NO" TO WS-SIZE-FLAG
           COMPUTE WS-COUNTER = WS-COUNTER + 1
               ON SIZE ERROR
                   MOVE "YES" TO WS-SIZE-FLAG
           END-COMPUTE
           EXIT.
