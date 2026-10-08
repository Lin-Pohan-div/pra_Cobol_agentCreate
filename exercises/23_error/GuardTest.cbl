IDENTIFICATION DIVISION.
       PROGRAM-ID. GUARD-TEST.

       *> 這份檢查器不需要修改，是這一題的驗收標準。
       *> 它會驗證兩件事：
       *>   1. SAFE-* 段落跑完之後「不應該」出錯，而且結果要正確。
       *>   2. CRASH-* 段落跑起來「應該」出錯，而且訊息要對。

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  CT-STATUS     PIC X(4).
       01  CT-AVERAGE    PIC S9(5)V99.
       01  CT-PICKED     PIC 9(4).
       01  CT-SCORE      PIC 9(4).
       01  CT-OVERFLOW   PIC X.

       PROCEDURE DIVISION.
       COBLINGS-TEST-MAIN.
           CALL "COBLINGS-EXPECT-NO-ERROR"
               USING BY CONTENT "SAFE-AVERAGE 不應該出錯"
                     BY CONTENT "SAFE-AVERAGE"
           MOVE WS-STATUS TO CT-STATUS
           MOVE WS-AVERAGE TO CT-AVERAGE
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "SAFE-AVERAGE：筆數為零時的狀態"
                     BY CONTENT "ZERO" BY CONTENT CT-STATUS
           CALL "COBLINGS-EXPECT-CLOSE"
               USING BY CONTENT "SAFE-AVERAGE：筆數為零時的平均"
                     BY CONTENT 0 BY CONTENT CT-AVERAGE BY CONTENT 0

           CALL "COBLINGS-EXPECT-NO-ERROR"
               USING BY CONTENT "SAFE-PICK 不應該出錯"
                     BY CONTENT "SAFE-PICK"
           MOVE WS-PICKED TO CT-PICKED
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "SAFE-PICK：下標被夾到最後一格"
                     BY CONTENT 2400 BY CONTENT CT-PICKED

           CALL "COBLINGS-EXPECT-NO-ERROR"
               USING BY CONTENT "SAFE-SCORE 不應該出錯"
                     BY CONTENT "SAFE-SCORE"
           MOVE WS-SCORE TO CT-SCORE
           MOVE WS-OVERFLOW TO CT-OVERFLOW
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "SAFE-SCORE：溢位後設成 9999"
                     BY CONTENT 9999 BY CONTENT CT-SCORE
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "SAFE-SCORE：溢位旗標"
                     BY CONTENT "Y" BY CONTENT CT-OVERFLOW

           CALL "COBLINGS-EXPECT-ERROR"
               USING BY CONTENT "CRASH-DIVIDE 要除以零"
                     BY CONTENT "CRASH-DIVIDE"
                     BY CONTENT "DIVIDE BY ZERO"
           CALL "COBLINGS-EXPECT-ERROR"
               USING BY CONTENT "CRASH-INDEX 要下標超出範圍"
                     BY CONTENT "CRASH-INDEX"
                     BY CONTENT "SUBSCRIPT OUT OF RANGE"

           CALL "COBLINGS-DONE"
           GOBACK.