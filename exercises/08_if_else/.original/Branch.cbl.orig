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
      *> TODO: 規格：分數 >= 90 標 "A"，>= 80 標 "B"，>= 60 標 "C"，其餘標 "F"。
      *>       85 分要標 "B"。要用 ELSE IF 寫出這一串條件：
      *>       IF ... ELSE IF ... ELSE IF ... ELSE ... END-IF
           .

       ADVICE-OF-TEMP.
           MOVE 35 TO WS-TEMP
      *> TODO: 規格：35 度要給 "HOT"。請用關係運算子寫：
      *>       溫度 >= 30 給 "HOT"，否則給 "COLD"。
           .

       USE-88-NAME.
           MOVE 85 TO WS-SCORE
      *> TODO: 規格：85 分在 60 到 100 之間，要給 "PASS"。
      *>       請用 88 條件名稱 WS-PASSING 判斷，不要自己寫 >= 60 AND <= 100。
           .
           EXIT.
