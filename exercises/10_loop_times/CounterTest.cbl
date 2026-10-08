IDENTIFICATION DIVISION.
       PROGRAM-ID. COUNTER-TEST.

*> 這份檢查器不需要修改，是這一題的驗收標準。

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  CK-TOTAL  PIC 9(5).
       01  CK-REMAIN PIC 9(3).
       01  CK-COUNT  PIC 9(3).

       PROCEDURE DIVISION.
       COBLINGS-TEST-MAIN.
           PERFORM SUM-TO-LIMIT
           MOVE WS-TOTAL TO CK-TOTAL
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "SUM-TO-LIMIT：1 加到 10 的總和"
                     BY CONTENT 55
                     BY CONTENT CK-TOTAL

           PERFORM COUNT-DOWN
           MOVE WS-REMAIN TO CK-REMAIN
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "COUNT-DOWN：從 10 數到 0 做了幾次"
                     BY CONTENT 10
                     BY CONTENT CK-REMAIN

           PERFORM COPY-N-TIMES
           MOVE WS-TOTAL TO CK-COUNT
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "COPY-N-TIMES：3 累加 5 次的結果"
                     BY CONTENT 15
                     BY CONTENT CK-COUNT

           CALL "COBLINGS-DONE"
           GOBACK.
