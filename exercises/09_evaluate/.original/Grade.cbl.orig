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
      *> TODO: 規格：>= 90 給 "A"，>= 80 給 "B"，>= 70 給 "C"，>= 60 給 "D"，
      *>       其餘給 "F"。85 分要給 "B"。
      *>       請用 EVALUATE WS-SCORE 搭配 WHEN 關係運算子，
      *>       最後一定要補一個 WHEN OTHER。
           .

       SIZE-OF.
           MOVE 2500 TO WS-SCORE
      *> TODO: 規格：2500 要標 "BIG"。請用 ELSE IF 寫：
      *>       >= 1000 標 "BIG"，>= 100 標 "MID"，其餘標 "SML"。
           .

       COMMENT-OF-DAYS.
           MOVE 45 TO WS-DAYS
      *> TODO: 規格：45 天要說 "OVERDUE"。請用 EVALUATE WS-DAYS：
      *>       > 90 說 "SEVERE"，> 30 說 "OVERDUE"，其餘說 "OK"。
      *>       條件要由嚴到鬆排列，因為 EVALUATE 只會執行「第一個」符合的分支。
           .
           EXIT.
