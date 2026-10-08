IDENTIFICATION DIVISION.
       PROGRAM-ID. GRADE-TEST.

*> 這份檢查器不需要修改，是這一題的驗收標準。

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  CK-GRADE   PIC X(2).
       01  CK-SIZE    PIC X(4).
       01  CK-COMMENT PIC X(14).

       PROCEDURE DIVISION.
       COBLINGS-TEST-MAIN.
           PERFORM GRADE-OF
           MOVE WS-GRADE TO CK-GRADE
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "GRADE-OF：85 分的等第"
                     BY CONTENT "B"
                     BY CONTENT CK-GRADE

           PERFORM SIZE-OF
           MOVE WS-SIZE TO CK-SIZE
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "SIZE-OF：2500 的規模"
                     BY CONTENT "BIG"
                     BY CONTENT CK-SIZE

           PERFORM COMMENT-OF-DAYS
           MOVE WS-COMMENT TO CK-COMMENT
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "COMMENT-OF-DAYS：45 天的說明"
                     BY CONTENT "OVERDUE"
                     BY CONTENT CK-COMMENT

           CALL "COBLINGS-DONE"
           GOBACK.
