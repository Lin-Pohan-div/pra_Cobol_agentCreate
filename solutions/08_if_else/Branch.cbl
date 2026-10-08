*> ============================================================
*> 開始之前：請先閱讀同一個資料夾裡的 README.md
*>   裡面有學習目標、觀念講解、常見錯誤與操作步驟。
*>   卡關時可以執行 .\coblings.cmd hint 看提示。
*> ============================================================
IDENTIFICATION DIVISION.
       PROGRAM-ID. BRANCH.

*> IF 依照條件成立與否，選擇要走哪一條路：
*>   IF 條件 ... ELSE ... END-IF
*> 關係運算子有 =、<>、>、<、>=、<=；另外還有 88 條件名稱可以用。

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-LABEL   PIC X(8).
       01  WS-SCORE   PIC 9(3).
       88  WS-PASSING VALUE 60 THRU 100.
       01  WS-ADVICE  PIC X(10).
       01  WS-TEMP    PIC S9(3).
       01  WS-CODE    PIC X(1).
       01  WS-COMMENT PIC X(12).

       PROCEDURE DIVISION.

       LABEL-OF-SCORE.
           MOVE 85 TO WS-SCORE
           IF WS-SCORE >= 90
               MOVE "A" TO WS-LABEL
           ELSE IF WS-SCORE >= 80
               MOVE "B" TO WS-LABEL
           ELSE IF WS-SCORE >= 60
               MOVE "C" TO WS-LABEL
           ELSE
               MOVE "F" TO WS-LABEL
           END-IF.

       ADVICE-OF-TEMP.
           MOVE 35 TO WS-TEMP
           IF WS-TEMP >= 30
               MOVE "HOT" TO WS-ADVICE
           ELSE
               MOVE "COLD" TO WS-ADVICE
           END-IF.

       USE-88-NAME.
           MOVE 85 TO WS-SCORE
           IF WS-PASSING
               MOVE "PASS" TO WS-ADVICE
           ELSE
               MOVE "FAIL" TO WS-ADVICE
           END-IF.
           EXIT.
