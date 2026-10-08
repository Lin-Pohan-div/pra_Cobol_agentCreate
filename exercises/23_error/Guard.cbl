*> ============================================================
*> 開始之前：請先閱讀同一個資料夾裡的 README.md
*>   裡面有學習目標、觀念講解、常見錯誤與操作步驟。
*>   卡關時可以執行 .\coblings.cmd hint 看提示。
*> ============================================================
IDENTIFICATION DIVISION.
       PROGRAM-ID. GUARD.

       *> ============================================================
       *> 這一題練習「執行期錯誤」與「防守式寫法」。
       *>
       *> COBOL 遇到下列情況會直接讓程式「中斷」，並且印出錯誤訊息：
       *>   SUBSCRIPT OUT OF RANGE：下標超出 OCCURS 宣告的範圍
       *>   DIVIDE BY ZERO         ：除數是零
       *> 至於算術結果「放不下欄位」（SIZE ERROR），程式不會中斷，
       *> 接收欄位會維持原本的值，也不會有任何訊息；要自己用
       *> ON SIZE ERROR ... END-COMPUTE 才知道發生了溢位。
       *>
       *> 所以正確的寫法是「先檢查、再運算」，不要等它出錯。
       *>
       *> 這個檔案裡有兩種類型的段落：
       *>   SAFE-*  ：一開始會中斷或算錯，請補上檢查與處理。
       *>   CRASH-* ：示範用的段落，本來就會出錯，請不要動它。
       *> ============================================================

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-PRICE-TABLE.
           05  WS-PRICE OCCURS 5 TIMES PIC 9(4).

       01  WS-TOTAL      PIC S9(5)V99.
       01  WS-COUNT      PIC 9(3).
       01  WS-AVERAGE    PIC S9(5)V99.
       01  WS-STATUS     PIC X(4).
       01  WS-PICK       PIC 9(2).
       01  WS-PICKED     PIC 9(4).
       01  WS-BASE       PIC 9(4).
       01  WS-BONUS      PIC 9(4).
       01  WS-SCORE      PIC 9(4).
       01  WS-OVERFLOW   PIC X VALUE "N".

       PROCEDURE DIVISION.

       LOAD-PRICES.
           MOVE 1200 TO WS-PRICE (1)
           MOVE 1500 TO WS-PRICE (2)
           MOVE 1800 TO WS-PRICE (3)
           MOVE 2100 TO WS-PRICE (4)
           MOVE 2400 TO WS-PRICE (5)
           EXIT.

       SAFE-AVERAGE.
           PERFORM LOAD-PRICES
           MOVE 1200 TO WS-TOTAL
           MOVE 0 TO WS-COUNT
           MOVE "NONE" TO WS-STATUS
           *> TODO: WS-COUNT 有可能是 0，除以零會讓程式中斷
           *>       （DIVIDE BY ZERO）。請先用 IF 判斷：
           *>       筆數為零時把 WS-STATUS 設成 "ZERO"、WS-AVERAGE 設成 0；
           *>       否則正常計算，並把 WS-STATUS 設成 "OK"。
           DIVIDE WS-TOTAL BY WS-COUNT GIVING WS-AVERAGE ROUNDED
           EXIT.

       SAFE-PICK.
           PERFORM LOAD-PRICES
           MOVE 9 TO WS-PICK
           *> TODO: WS-PICK 有可能是 9，但表格只有 5 格，
           *>       取用時會中斷（SUBSCRIPT OUT OF RANGE）。
           *>       請先把 WS-PICK 夾在 1 到 5 之間再取值，
           *>       夾完之後存進 WS-PICKED。
           MOVE WS-PRICE (WS-PICK) TO WS-PICKED
           EXIT.

       SAFE-SCORE.
           MOVE 9000 TO WS-BASE
           MOVE 2000 TO WS-BONUS
           MOVE "N" TO WS-OVERFLOW
           *> TODO: 9000 + 2000 放不進四碼的 WS-SCORE，
           *>       程式不會報錯，WS-SCORE 只會默默維持原值。
           *>       請改用 COMPUTE ... ON SIZE ERROR ... END-COMPUTE，
           *>       溢位時把 WS-SCORE 設成 9999、WS-OVERFLOW 設成 "Y"。
           COMPUTE WS-SCORE = WS-BASE + WS-BONUS
           EXIT.

       CRASH-DIVIDE.
           DIVIDE 100 BY 0 GIVING WS-AVERAGE
           EXIT.

       CRASH-INDEX.
           MOVE WS-PRICE (7) TO WS-PICKED
           EXIT.