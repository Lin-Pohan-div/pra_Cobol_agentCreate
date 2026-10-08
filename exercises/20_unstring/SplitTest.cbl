IDENTIFICATION DIVISION.
       PROGRAM-ID. SPLIT-TEST.

       *> 這份檢查器不需要修改，是這一題的驗收標準。
       *> 它會依序執行學生寫的三個段落，再檢查拆出來的結果。

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  CT-A          PIC X(6).
       01  CT-B          PIC X(6).
       01  CT-C          PIC X(6).
       01  CT-D          PIC X(4).
       01  CT-E          PIC X(2).

       PROCEDURE DIVISION.
       COBLINGS-TEST-MAIN.
           PERFORM SPLIT-DATE
           MOVE WS-YEAR TO CT-D
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "SPLIT-DATE：年"
                     BY CONTENT "2026" BY CONTENT CT-D
           MOVE WS-MONTH TO CT-E
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "SPLIT-DATE：月"
                     BY CONTENT "10" BY CONTENT CT-E
           MOVE WS-DAY TO CT-E
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "SPLIT-DATE：日"
                     BY CONTENT "05" BY CONTENT CT-E

           PERFORM SPLIT-AMOUNT
           MOVE WS-DOLLARS TO CT-D
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "SPLIT-AMOUNT：元"
                     BY CONTENT "1234" BY CONTENT CT-D
           MOVE WS-CENTS TO CT-E
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "SPLIT-AMOUNT：分"
                     BY CONTENT "56" BY CONTENT CT-E

           PERFORM SPLIT-TAGS
           MOVE WS-TAG1 TO CT-A
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "SPLIT-TAGS：第一個標籤"
                     BY CONTENT "red" BY CONTENT CT-A
           MOVE WS-TAG2 TO CT-B
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "SPLIT-TAGS：第二個標籤"
                     BY CONTENT "green" BY CONTENT CT-B
           MOVE WS-TAG3 TO CT-C
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "SPLIT-TAGS：第三個標籤"
                     BY CONTENT "blue" BY CONTENT CT-C

           CALL "COBLINGS-DONE"
           GOBACK.