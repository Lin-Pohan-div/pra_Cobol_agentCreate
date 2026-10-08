IDENTIFICATION DIVISION.
       PROGRAM-ID. GRID-TEST.

*> 這份檢查器不需要修改，是這一題的驗收標準。

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  CK-CELLS PIC 9(4).
       01  CK-SUM   PIC 9(5).

       PROCEDURE DIVISION.
       COBLINGS-TEST-MAIN.
           PERFORM COUNT-CELLS
           MOVE WS-CELLS TO CK-CELLS
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "COUNT-CELLS：3 乘 4 的格數"
                     BY CONTENT 12
                     BY CONTENT CK-CELLS

           PERFORM SUM-WITH-WEIGHT
           MOVE WS-SUM TO CK-SUM
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "SUM-WITH-WEIGHT：十二格權重的總和"
                     BY CONTENT 270
                     BY CONTENT CK-SUM

           PERFORM ROW-TOTALS
           MOVE WS-SUM TO CK-SUM
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "ROW-TOTALS：上三角六格權重的總和"
                     BY CONTENT 120
                     BY CONTENT CK-SUM

           CALL "COBLINGS-DONE"
           GOBACK.
