*> ============================================================
*> 開始之前：請先閱讀同一個資料夾裡的 README.md
*>   裡面有學習目標、觀念講解、常見錯誤與操作步驟。
*>   卡關時可以執行 .\coblings.cmd hint 看提示。
*> ============================================================
IDENTIFICATION DIVISION.
       PROGRAM-ID. GRADE.

*> EVALUATE 可以一次比對多種情況，比一長串 ELSE IF 好讀：
*>   EVALUATE 主題 WHEN 值 ... WHEN 值 ... WHEN OTHER ... END-EVALUATE
*> 它會從上往下找「第一個符合的 WHEN」，找到就執行那一段然後結束。

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-SCORE   PIC 9(5).
       01  WS-GRADE   PIC X(2).
       01  WS-SIZE    PIC X(4).
       01  WS-COMMENT PIC X(14).
       01  WS-DAYS    PIC 9(3).

       PROCEDURE DIVISION.

       GRADE-OF.
           MOVE 85 TO WS-SCORE
           EVALUATE WS-SCORE
               WHEN WS-SCORE >= 90
                   MOVE "A" TO WS-GRADE
               WHEN WS-SCORE >= 80
                   MOVE "B" TO WS-GRADE
               WHEN WS-SCORE >= 70
                   MOVE "C" TO WS-GRADE
               WHEN WS-SCORE >= 60
                   MOVE "D" TO WS-GRADE
               WHEN OTHER
                   MOVE "F" TO WS-GRADE
           END-EVALUATE.

       SIZE-OF.
           MOVE 2500 TO WS-SCORE
           IF WS-SCORE >= 1000
               MOVE "BIG" TO WS-SIZE
           ELSE IF WS-SCORE >= 100
               MOVE "MID" TO WS-SIZE
           ELSE
               MOVE "SML" TO WS-SIZE
           END-IF.

       COMMENT-OF-DAYS.
           MOVE 45 TO WS-DAYS
           EVALUATE WS-DAYS
               WHEN WS-DAYS > 90
                   MOVE "SEVERE" TO WS-COMMENT
               WHEN WS-DAYS > 30
                   MOVE "OVERDUE" TO WS-COMMENT
               WHEN OTHER
                   MOVE "OK" TO WS-COMMENT
           END-EVALUATE.
           EXIT.
