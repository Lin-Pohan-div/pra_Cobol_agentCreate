*> ============================================================
*> 開始之前：請先閱讀同一個資料夾裡的 README.md
*>   裡面有學習目標、觀念講解、常見錯誤與操作步驟。
*>   卡關時可以執行 .\coblings.cmd hint 看提示。
*> ============================================================
IDENTIFICATION DIVISION.
       PROGRAM-ID. PICTURE.

      *> 這一題要體驗「欄位位數不夠時會發生什麼事」。

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-SERIAL      PIC 9(3).
       01  WS-NAME        PIC X(5).
       01  WS-PRICE       PIC 9(3)V99.
       01  WS-COUNTER     PIC 9(3).
       01  WS-SERIAL-OUT  PIC 9(5).
       01  WS-NAME-OUT    PIC X(8).
       01  WS-PRICE-OUT   PIC 9(3)V99.
       01  WS-SIZE-FLAG   PIC X(4).

       PROCEDURE DIVISION.
       LOAD-BIG-NUMBER.
           MOVE 12345 TO WS-SERIAL
      *>    TODO: PIC 9(3) 只有三個數字位置，12345 放不下會被截斷（高位丟掉，變成 345）。
      *>          要完整保留序號，請把 WS-SERIAL 的 PICTURE 改大一點，
      *>          搬進去的數字不用動。
           MOVE WS-SERIAL TO WS-SERIAL-OUT

       LOAD-LONG-TEXT.
           MOVE "Coblings" TO WS-NAME
      *>    TODO: PIC X(5) 只有五個字元，"Coblings" 有八個字，右邊會被截掉。
      *>          請把 WS-NAME 的 PICTURE 改大到可以放完 "Coblings"。
           MOVE WS-NAME TO WS-NAME-OUT

       LOAD-PRICE.
           MOVE 12.567 TO WS-PRICE
      *>    TODO: PIC 9(3)V99 有兩位小數，MOVE 進去會「截斷」成 12.56。
      *>          要四捨五入成 12.57，請改用可以加 ROUNDED 的寫法
      *>          （MOVE 後面不能直接加 ROUNDED，COMPUTE 才可以）。
           MOVE WS-PRICE TO WS-PRICE-OUT

       CHECK-SIZE-ERROR.
           MOVE 999 TO WS-COUNTER
           MOVE "NO" TO WS-SIZE-FLAG
      *>    TODO: PIC 9(3) 最大的數是 999，再加 1 就超過欄位容量。
      *>          算術運算放不下時不會讓程式壞掉，而是跳到 ON SIZE ERROR 那一段。
      *>          請在 COMPUTE 後面加上 ON SIZE ERROR，讓 WS-SIZE-FLAG 變成 "YES"。
           COMPUTE WS-COUNTER = WS-COUNTER + 1
           EXIT.
