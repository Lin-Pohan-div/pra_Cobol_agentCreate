IDENTIFICATION DIVISION.
       PROGRAM-ID. HELLO-TEST.

       *> 這份檢查器不需要修改，是這一題的驗收標準。
       *> 它會先執行學生寫的 GET-GREET 段落，再檢查結果。

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-ACTUAL  PIC X(24).

       PROCEDURE DIVISION.
       COBLINGS-TEST-MAIN.
           PERFORM GET-GREET
           MOVE WS-RESULT TO WS-ACTUAL

           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "GET-GREET 產生的字串"
                     BY CONTENT "Hello, Coblings!"
                     BY CONTENT WS-ACTUAL

           PERFORM SHOW-GREET

           CALL "COBLINGS-DONE"
           GOBACK.