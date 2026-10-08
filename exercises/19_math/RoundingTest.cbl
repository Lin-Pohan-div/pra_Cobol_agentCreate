IDENTIFICATION DIVISION.
       PROGRAM-ID. ROUNDING-TEST.

       *> 這份檢查器不需要修改，是這一題的驗收標準。
       *> 它會依序執行學生寫的三個段落，再檢查結果。

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  CT-SHARE    PIC S9(5)V99.
       01  CT-STATUS   PIC X(4).
       01  CT-SCORE    PIC 9(3).
       01  CT-CAPPED   PIC X.

       PROCEDURE DIVISION.
       COBLINGS-TEST-MAIN.
           PERFORM AVERAGE-SPLIT
           MOVE WS-SHARE TO CT-SHARE
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "AVERAGE-SPLIT：100.00 分給 7 人（要四捨五入）"
                     BY CONTENT 14.29
                     BY CONTENT CT-SHARE

           PERFORM SAFE-RATE
           MOVE WS-STATUS TO CT-STATUS
           MOVE WS-SHARE TO CT-SHARE
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "SAFE-RATE：除數為零時的狀態碼"
                     BY CONTENT "ZERO"
                     BY CONTENT CT-STATUS
           CALL "COBLINGS-EXPECT-CLOSE"
               USING BY CONTENT "SAFE-RATE：除數為零時的結果"
                     BY CONTENT 0
                     BY CONTENT CT-SHARE
                     BY CONTENT 0

           PERFORM CAP-SCORE
           MOVE WS-SCORE TO CT-SCORE
           MOVE WS-CAPPED TO CT-CAPPED
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "CAP-SCORE：溢位後截成 999"
                     BY CONTENT 999
                     BY CONTENT CT-SCORE
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "CAP-SCORE：溢位旗標"
                     BY CONTENT "Y"
                     BY CONTENT CT-CAPPED

           CALL "COBLINGS-DONE"
           GOBACK.