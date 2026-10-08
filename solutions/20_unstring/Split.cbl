*> ============================================================
*> 開始之前：請先閱讀同一個資料夾裡的 README.md
*>   裡面有學習目標、觀念講解、常見錯誤與操作步驟。
*>   卡關時可以執行 .\coblings.cmd hint 看提示。
*> ============================================================
IDENTIFICATION DIVISION.
       PROGRAM-ID. SPLIT.

       *> ============================================================
       *> UNSTRING 可以把一個字串依指定的分隔字元拆成好幾欄。
       *> 語法：
       *>     UNSTRING 來源欄位 DELIMITED BY "分隔字元"
       *>         INTO 目標1 DELIMITED BY "分隔字元",
       *>              目標2 DELIMITED BY "分隔字元",
       *>              目標3 DELIMITED BY "分隔字元"
       *> 注意：INTO 後面的每一個目標之間要用逗號隔開，
       *>       而且每個目標後面都要再寫一次自己的 DELIMITED BY。
       *> ============================================================

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-SOURCE    PIC X(20).
       01  WS-YEAR      PIC X(4).
       01  WS-MONTH     PIC X(2).
       01  WS-DAY       PIC X(2).
       01  WS-DOLLARS   PIC X(4).
       01  WS-CENTS     PIC X(2).
       01  WS-TAG1      PIC X(6).
       01  WS-TAG2      PIC X(6).
       01  WS-TAG3      PIC X(6).

       PROCEDURE DIVISION.

       SPLIT-DATE.
           MOVE "2026-10-05" TO WS-SOURCE
           MOVE SPACES TO WS-YEAR, WS-MONTH, WS-DAY
           UNSTRING WS-SOURCE DELIMITED BY "-"
               INTO WS-YEAR DELIMITED BY "-",
                    WS-MONTH DELIMITED BY "-",
                    WS-DAY DELIMITED BY "-"
           EXIT.

       SPLIT-AMOUNT.
           MOVE "1234.56" TO WS-SOURCE
           MOVE SPACES TO WS-DOLLARS, WS-CENTS
           UNSTRING WS-SOURCE DELIMITED BY "."
               INTO WS-DOLLARS DELIMITED BY ".",
                    WS-CENTS DELIMITED BY "."
           EXIT.

       SPLIT-TAGS.
           MOVE "red green blue" TO WS-SOURCE
           MOVE SPACES TO WS-TAG1, WS-TAG2, WS-TAG3
           UNSTRING WS-SOURCE DELIMITED BY " "
               INTO WS-TAG1 DELIMITED BY " ",
                    WS-TAG2 DELIMITED BY " ",
                    WS-TAG3 DELIMITED BY " "
           EXIT.