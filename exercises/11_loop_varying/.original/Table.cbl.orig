*> ============================================================
*> 開始之前：請先閱讀同一個資料夾裡的 README.md
*>   裡面有學習目標、觀念講解、常見錯誤與操作步驟。
*>   卡關時可以執行 .\coblings.cmd hint 看提示。
*> ============================================================
IDENTIFICATION DIVISION.
       PROGRAM-ID. TABLE.

*> PERFORM VARYING 會自動幫你維護計數器：
*>   PERFORM VARYING 計數器 FROM 起始 BY 步長 UNTIL 條件 ... END-PERFORM
*> 條件寫成「計數器 > 最後一次的值」時，迴圈剛好執行 起始到最後 這麼多次。

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-SCORE-TABLE.
      *>    05 層級是表格的每個元素，OCCURS 5 TIMES 表示有 5 格
           05  WS-SCORE-ITEM  PIC 9(3) OCCURS 5 TIMES.
       01  WS-I          PIC 9(3).
       01  WS-J          PIC 9(3).
       01  WS-QUOTIENT   PIC 9(3).
       01  WS-REMAINDER  PIC 9(3).
       01  WS-TOTAL      PIC 9(5).
       01  WS-LARGEST    PIC 9(3).
       01  WS-EVEN-COUNT PIC 9(3).
       01  WS-STEP-SUM   PIC 9(5).

       PROCEDURE DIVISION.

       LOAD-TABLE.
      *> 這段是給你參考的正確寫法：先把資料放進表格，後面三段才能取用。
           MOVE 40 TO WS-SCORE-ITEM (1)
           MOVE 75 TO WS-SCORE-ITEM (2)
           MOVE 20 TO WS-SCORE-ITEM (3)
           MOVE 90 TO WS-SCORE-ITEM (4)
           MOVE 55 TO WS-SCORE-ITEM (5).

       SUM-TABLE.
      *> TODO: 規格：把表格 5 格的成績全部加起來，總和 280 存進 WS-TOTAL。
      *>       請用 PERFORM VARYING WS-I FROM 1 BY 1 UNTIL WS-I > 5，
      *>       在迴圈體裡用 WS-SCORE-ITEM (WS-I) 取用第 I 格。
      *>       （OCCURS 的格子要用括號括住索引：WS-SCORE-ITEM (WS-I)）
           .

       FIND-LARGEST.
      *> TODO: 規格：找出表格裡最大的成績 90 存進 WS-LARGEST。
      *>       請用 PERFORM VARYING 走過全部 5 格，
      *>       在迴圈體裡用 IF 比較並更新 WS-LARGEST。
           .

       COUNT-EVEN.
      *> TODO: 規格：數一數表格裡有幾個偶數（答案是 3：40、20、90）存進 WS-EVEN-COUNT。
      *>       請用 PERFORM VARYING WS-I FROM 1 BY 1 UNTIL WS-I > 5，
      *>       在迴圈體裡用一條 IF 判斷該格是不是偶數
      *>       （除以 2 沒有餘數就是偶數：
      *>         DIVIDE WS-SCORE-ITEM (WS-I) BY 2
      *>             GIVING WS-QUOTIENT REMAINDER WS-REMAINDER
      *>         然後判斷 WS-REMAINDER = 0）。
           .
           EXIT.
