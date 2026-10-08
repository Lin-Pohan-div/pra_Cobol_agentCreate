*> ============================================================
*> 開始之前：請先閱讀同一個資料夾裡的 README.md
*>   裡面有學習目標、觀念講解、常見錯誤與操作步驟。
*>   卡關時可以執行 .\coblings.cmd hint 看提示。
*> ============================================================
IDENTIFICATION DIVISION.
       PROGRAM-ID. ROUNDING.

       *> ============================================================
       *> 這一題練習三件事：
       *>   1. ROUNDED：數字欄位放不下小數位時，預設是「砍掉」，
       *>      要四捨五入必須在接收欄位後面加 ROUNDED。
       *>   2. 除數為零：COBOL 會直接讓程式出錯（DIVIDE BY ZERO），
       *>      必須自己先判斷。
       *>   3. ON SIZE ERROR：運算結果塞不進欄位時（溢位），
       *>      用 ON SIZE ERROR ... END-COMPUTE 處理。
       *> ============================================================

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-TOTAL     PIC S9(5)V99.
       01  WS-PEOPLE    PIC 9(3).
       01  WS-SHARE     PIC S9(5)V99.
       01  WS-STATUS    PIC X(4).
       01  WS-BASE      PIC 9(3).
       01  WS-BONUS     PIC 9(3).
       01  WS-SCORE     PIC 9(3).
       01  WS-CAPPED    PIC X.

       PROCEDURE DIVISION.

       AVERAGE-SPLIT.
           MOVE 100.00 TO WS-TOTAL
           MOVE 7 TO WS-PEOPLE
           DIVIDE WS-TOTAL BY WS-PEOPLE GIVING WS-SHARE ROUNDED
           EXIT.

       SAFE-RATE.
           MOVE 0 TO WS-PEOPLE
           IF WS-PEOPLE = 0
               MOVE "ZERO" TO WS-STATUS
               MOVE 0 TO WS-SHARE
           ELSE
               MOVE "NONE" TO WS-STATUS
               DIVIDE 250.00 BY WS-PEOPLE GIVING WS-SHARE ROUNDED
           END-IF
           EXIT.

       CAP-SCORE.
           MOVE 800 TO WS-BASE
           MOVE 500 TO WS-BONUS
           MOVE "N" TO WS-CAPPED
           COMPUTE WS-SCORE = WS-BASE + WS-BONUS
               ON SIZE ERROR
                   MOVE 999 TO WS-SCORE
                   MOVE "Y" TO WS-CAPPED
           END-COMPUTE.
           EXIT.