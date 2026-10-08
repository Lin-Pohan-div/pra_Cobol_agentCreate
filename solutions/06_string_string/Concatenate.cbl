*> ============================================================
*> 開始之前：請先閱讀同一個資料夾裡的 README.md
*>   裡面有學習目標、觀念講解、常見錯誤與操作步驟。
*>   卡關時可以執行 .\coblings.cmd hint 看提示。
*> ============================================================
IDENTIFICATION DIVISION.
       PROGRAM-ID. CONCATENATE.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-FIRST-NAME  PIC X(6).
       01  WS-LAST-NAME   PIC X(8).
       01  WS-CITY        PIC X(8).
       01  WS-NAME-LABEL  PIC X(20).
       01  WS-ADDRESS     PIC X(24).
       01  WS-POINTER     PIC 9(3).
       01  WS-SMALL-BUF   PIC X(8).
       01  WS-OVERFLOW    PIC X(3).

       PROCEDURE DIVISION.
       BUILD-NAME-LABEL.
           MOVE "Amy" TO WS-FIRST-NAME
           MOVE "Chen" TO WS-LAST-NAME
           MOVE SPACES TO WS-NAME-LABEL
           STRING FUNCTION TRIM(WS-FIRST-NAME) DELIMITED BY SIZE
                  " " DELIMITED BY SIZE
                  FUNCTION TRIM(WS-LAST-NAME) DELIMITED BY SIZE
              INTO WS-NAME-LABEL
           END-STRING

       BUILD-ADDRESS.
           MOVE "Taipei" TO WS-CITY
           MOVE SPACES TO WS-ADDRESS
           MOVE 1 TO WS-POINTER
           STRING "City: " DELIMITED BY SIZE
                  FUNCTION TRIM(WS-CITY) DELIMITED BY SIZE
                  " " DELIMITED BY SIZE
              INTO WS-ADDRESS WITH POINTER WS-POINTER
           END-STRING
           MOVE 14 TO WS-POINTER
           STRING "Zip: " DELIMITED BY SIZE
                  "100" DELIMITED BY SIZE
              INTO WS-ADDRESS WITH POINTER WS-POINTER
           END-STRING

       FILL-SMALL-BUFFER.
           MOVE SPACES TO WS-SMALL-BUF
           MOVE "NO" TO WS-OVERFLOW
           STRING "ABCDEFGH" DELIMITED BY SIZE
                  "IJK" DELIMITED BY SIZE
              INTO WS-SMALL-BUF
              ON OVERFLOW
                  MOVE "YES" TO WS-OVERFLOW
           END-STRING
           EXIT.
