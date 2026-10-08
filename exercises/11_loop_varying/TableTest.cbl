IDENTIFICATION DIVISION.
       PROGRAM-ID. TABLE-TEST.

*> 這份檢查器不需要修改，是這一題的驗收標準。
*> 注意：學生的 05 表格項目檢查器讀不到，所以這題的每一段
*> 都把答案放進 01 層級的項目裡。

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  CK-TOTAL      PIC 9(5).
       01  CK-LARGEST    PIC 9(3).
       01  CK-EVEN-COUNT PIC 9(3).

       PROCEDURE DIVISION.
       COBLINGS-TEST-MAIN.
           PERFORM LOAD-TABLE

           PERFORM SUM-TABLE
           MOVE WS-TOTAL TO CK-TOTAL
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "SUM-TABLE：五格成績的總和"
                     BY CONTENT 280
                     BY CONTENT CK-TOTAL

           PERFORM FIND-LARGEST
           MOVE WS-LARGEST TO CK-LARGEST
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "FIND-LARGEST：最大的成績"
                     BY CONTENT 90
                     BY CONTENT CK-LARGEST

           PERFORM COUNT-EVEN
           MOVE WS-EVEN-COUNT TO CK-EVEN-COUNT
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "COUNT-EVEN：偶數的個數"
                     BY CONTENT 3
                     BY CONTENT CK-EVEN-COUNT

           CALL "COBLINGS-DONE"
           GOBACK.
