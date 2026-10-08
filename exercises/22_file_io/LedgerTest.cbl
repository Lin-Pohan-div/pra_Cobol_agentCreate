IDENTIFICATION DIVISION.
       PROGRAM-ID. LEDGER-TEST.

       *> 這份檢查器不需要修改，是這一題的驗收標準。
       *> 它會先讓學生寫檔，再讀回來檢查，最後把 ledger.dat 清空。

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT CLEAN-FILE ASSIGN TO "ledger.dat".

       DATA DIVISION.
       FILE SECTION.
       FD  CLEAN-FILE.
       01  CLEAN-FILE   PIC X(12).

       WORKING-STORAGE SECTION.
       01  CT-COUNT    PIC 9(3).
       01  CT-LINE     PIC X(12).

       PROCEDURE DIVISION.
       COBLINGS-TEST-MAIN.
           PERFORM WRITE-LEDGER
           PERFORM READ-LEDGER

           MOVE WS-COUNT TO CT-COUNT
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "READ-LEDGER：ledger.dat 裡的紀錄筆數"
                     BY CONTENT 3 BY CONTENT CT-COUNT
           MOVE WS-LINE TO CT-LINE
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "READ-LEDGER：最後讀到的那一筆"
                     BY CONTENT "C03 99.99   " BY CONTENT CT-LINE

           PERFORM CLEAN-UP

           CALL "COBLINGS-DONE"
           GOBACK.

       *> 把題目資料夾裡的 ledger.dat 清空，避免污染版本控制。
       CLEAN-UP.
           OPEN OUTPUT CLEAN-FILE.
           CLOSE CLEAN-FILE.
           EXIT.