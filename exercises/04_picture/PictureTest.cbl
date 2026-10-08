IDENTIFICATION DIVISION.
       PROGRAM-ID. PICTURE-TEST.

      *> 這份檢查器不需要修改，是這一題的驗收標準。
      *> 檢查的是「輸出欄位」：學生改了來源欄位的 PICTURE 之後，
      *> 這裡就應該讀得到完整的值。

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  CT-SERIAL    PIC 9(5).
       01  CT-NAME      PIC X(8).
       01  CT-PRICE     PIC 9(3)V99.
       01  CT-SIZE-FLAG PIC X(4).

       PROCEDURE DIVISION.
       COBLINGS-TEST-MAIN.
           PERFORM LOAD-BIG-NUMBER
           MOVE WS-SERIAL-OUT TO CT-SERIAL
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "序號 12345 不該被截斷成 345"
                     BY CONTENT 12345
                     BY CONTENT CT-SERIAL

           PERFORM LOAD-LONG-TEXT
           MOVE WS-NAME-OUT TO CT-NAME
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "名字 Coblings 不該被截斷成 Cobli"
                     BY CONTENT "Coblings"
                     BY CONTENT CT-NAME

           PERFORM LOAD-PRICE
           MOVE WS-PRICE-OUT TO CT-PRICE
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "12.567 四捨五入到兩位小數應是 12.57"
                     BY CONTENT 12.57
                     BY CONTENT CT-PRICE

           PERFORM CHECK-SIZE-ERROR
           MOVE WS-SIZE-FLAG TO CT-SIZE-FLAG
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "999 + 1 超出 PIC 9(3)，ON SIZE ERROR 應該被觸發"
                     BY CONTENT "YES"
                     BY CONTENT CT-SIZE-FLAG

           CALL "COBLINGS-DONE"
           GOBACK.
