*> ============================================================
*> 開始之前：請先閱讀同一個資料夾裡的 README.md
*>   裡面有學習目標、觀念講解、常見錯誤與操作步驟。
*>   卡關時可以執行 .\coblings.cmd hint 看提示。
*> ============================================================
IDENTIFICATION DIVISION.
       PROGRAM-ID. HELLO.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-NAME    PIC X(8).
       01  WS-RESULT  PIC X(24).

       PROCEDURE DIVISION.
       GET-GREET.
           MOVE "Coblings" TO WS-NAME
           MOVE SPACES TO WS-RESULT
           STRING "Hello," DELIMITED BY SIZE
                  " " DELIMITED BY SIZE
                  WS-NAME DELIMITED BY SIZE
                  "!" DELIMITED BY SIZE
              INTO WS-RESULT
           END-STRING

       SHOW-GREET.
           DISPLAY WS-RESULT
           EXIT.