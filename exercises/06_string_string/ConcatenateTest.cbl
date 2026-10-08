IDENTIFICATION DIVISION.
       PROGRAM-ID. CONCATENATE-TEST.

      *> 這份檢查器不需要修改，是這一題的驗收標準。
      *> 文字斷言會先把兩個值補空白到一樣長再比，
      *> 所以右邊多出來的空白不用擔心。

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  CT-NAME-LABEL PIC X(20).
       01  CT-ADDRESS    PIC X(24).
       01  CT-SMALL-BUF  PIC X(8).
       01  CT-OVERFLOW   PIC X(3).

       PROCEDURE DIVISION.
       COBLINGS-TEST-MAIN.
           PERFORM BUILD-NAME-LABEL
           MOVE WS-NAME-LABEL TO CT-NAME-LABEL
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "姓名標籤中間應該只有一個空白（Amy Chen）"
                     BY CONTENT "Amy Chen"
                     BY CONTENT CT-NAME-LABEL

           PERFORM BUILD-ADDRESS
           MOVE WS-ADDRESS TO CT-ADDRESS
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "第二次串接前指標要重設（City: Taipei Zip: 100）"
                     BY CONTENT "City: Taipei Zip: 100"
                     BY CONTENT CT-ADDRESS

           PERFORM FILL-SMALL-BUFFER
           MOVE WS-SMALL-BUF TO CT-SMALL-BUF
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "塞得下的前八個字元要留在緩衝區裡"
                     BY CONTENT "ABCDEFGH"
                     BY CONTENT CT-SMALL-BUF

           MOVE WS-OVERFLOW TO CT-OVERFLOW
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "塞不下的 IJK 應該觸發 ON OVERFLOW"
                     BY CONTENT "YES"
                     BY CONTENT CT-OVERFLOW

           CALL "COBLINGS-DONE"
           GOBACK.
