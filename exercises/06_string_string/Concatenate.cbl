*> ============================================================
*> 開始之前：請先閱讀同一個資料夾裡的 README.md
*>   裡面有學習目標、觀念講解、常見錯誤與操作步驟。
*>   卡關時可以執行 .\coblings.cmd hint 看提示。
*> ============================================================
IDENTIFICATION DIVISION.
       PROGRAM-ID. CONCATENATE.

      *> 這一題要體驗 STRING 的三個重點：
      *> DELIMITED BY、WITH POINTER、ON OVERFLOW。

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
      *>    TODO: PIC X 的欄位右邊會補空白（"Amy" 放在 PIC X(6) 其實是 "Amy   "）。
      *>          DELIMITED BY SIZE 會把補位的空白也串進去，
      *>          所以現在的結果是 "Amy    Chen"（中間有四個空白）。
      *>          目標是 "Amy Chen"，請想辦法把多餘的空白拿掉。
           STRING WS-FIRST-NAME DELIMITED BY SIZE
                  " " DELIMITED BY SIZE
                  WS-LAST-NAME DELIMITED BY SIZE
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
      *>    TODO: WITH POINTER 執行完會把「下一個要寫的位置」留在 WS-POINTER 裡，
      *>          而且不會自己重設成 1。
      *>          上面寫完 "City: Taipei " 之後，WS-POINTER 已經是 14。
      *>          第二次串接要接在後面，指標就該設成 14；
      *>          現在寫成 1，結果 "Zip: 100" 會從頭蓋掉前面的字，
      *>          變成 "Zip: 100ipei"。目標是 "City: Taipei Zip: 100"。
           MOVE 1 TO WS-POINTER
           STRING "Zip: " DELIMITED BY SIZE
                  "100" DELIMITED BY SIZE
              INTO WS-ADDRESS WITH POINTER WS-POINTER
           END-STRING

       FILL-SMALL-BUFFER.
           MOVE SPACES TO WS-SMALL-BUF
           MOVE "NO" TO WS-OVERFLOW
      *>    TODO: WS-SMALL-BUF 只有 8 個字元，後面的 "IJK" 塞不進去。
      *>          請在這個 STRING 加上 ON OVERFLOW，
      *>          讓放不下的時候把 WS-OVERFLOW 改成 "YES"。
           STRING "ABCDEFGH" DELIMITED BY SIZE
                  "IJK" DELIMITED BY SIZE
              INTO WS-SMALL-BUF
           END-STRING
           EXIT.
