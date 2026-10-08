*> ============================================================
*> 開始之前：請先閱讀同一個資料夾裡的 README.md
*>   裡面有學習目標、觀念講解、常見錯誤與操作步驟。
*>   卡關時可以執行 .\coblings.cmd hint 看提示。
*> ============================================================
IDENTIFICATION DIVISION.
       PROGRAM-ID. LOOKUP.

       *> ============================================================
       *> 這一題練習「表格 + SEARCH + 88 條件名稱」：
       *>   1. OCCURS n TIMES 會把一筆資料變成 n 個副本，
       *>      用「表格名(第幾筆)」或「子項目(第幾筆)」來存取。
       *>   2. SEARCH ... VARYING 索引 FROM 起始 BY 步數 UNTIL 界限
       *>      會從頭到尾掃過表格，比自己寫迴圈更清楚。
       *>   3. 88 條件名稱可以幫一個欄位取名字，讓 IF 讀起來像英文。
       *> ============================================================

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-CATALOG.
           05  WS-ITEM OCCURS 5 TIMES.
               10  WS-SKU     PIC X(4).
               10  WS-NAME    PIC X(8).
               10  WS-PRICE   PIC 9(4).
               10  WS-KIND    PIC X.

       01  WS-KEY         PIC X(4).
       01  WS-INDEX       PIC 9(2).
       01  WS-HIT-NAME    PIC X(8).
       01  WS-HIT-PRICE   PIC 9(4).
       01  WS-HIT         PIC X VALUE "N".
       01  WS-LEVEL       PIC X.
         88  IS-PREMIUM    VALUE "P".
         88  IS-BASIC      VALUE "B".
       01  WS-PREMIUM-CNT PIC 9(3) VALUE 0.
       01  WS-BEST        PIC 9(4).

       PROCEDURE DIVISION.

       LOAD-CATALOG.
           MOVE "A001" TO WS-SKU (1)
           MOVE "MOCHA" TO WS-NAME (1)
           MOVE 1800 TO WS-PRICE (1)
           MOVE "B" TO WS-KIND (1)
           MOVE "B002" TO WS-SKU (2)
           MOVE "LATTE" TO WS-NAME (2)
           MOVE 1500 TO WS-PRICE (2)
           MOVE "B" TO WS-KIND (2)
           MOVE "P003" TO WS-SKU (3)
           MOVE "MATCHA" TO WS-NAME (3)
           MOVE 2200 TO WS-PRICE (3)
           MOVE "P" TO WS-KIND (3)
           EXIT.

       FIND-ITEM.
           PERFORM LOAD-CATALOG
           MOVE "P003" TO WS-KEY
           MOVE "N" TO WS-HIT
           MOVE SPACES TO WS-HIT-NAME
           MOVE 0 TO WS-HIT-PRICE
           *> TODO: SEARCH 如果沒有搭配 VARYING，索引就不會前進，
           *>       WS-INDEX 會停在 0，之後用 WS-INDEX 取資料就會出錯。
           *>       請補上 VARYING WS-INDEX FROM 1 BY 1 UNTIL WS-INDEX > 5。
           SEARCH WS-ITEM
               WHEN WS-SKU = WS-KEY
                   MOVE "Y" TO WS-HIT
                   MOVE WS-NAME TO WS-HIT-NAME
                   MOVE WS-PRICE TO WS-HIT-PRICE
           END-SEARCH
           EXIT.

       COUNT-PREMIUM.
           PERFORM LOAD-CATALOG
           MOVE 0 TO WS-PREMIUM-CNT
           *> TODO: 表格雖然有 5 格，但目前只填了 3 筆資料。
           *>       迴圈上界寫成 2 會漏掉第 3 筆。
           PERFORM VARYING WS-INDEX FROM 1 BY 1 UNTIL WS-INDEX > 2
               MOVE WS-KIND (WS-INDEX) TO WS-LEVEL
               IF WS-LEVEL IS-PREMIUM
                   ADD 1 TO WS-PREMIUM-CNT
               END-IF
           END-PERFORM
           EXIT.

       HIGHEST-PRICE.
           PERFORM LOAD-CATALOG
           *> TODO: WS-BEST 一開始是 0，比任何價格都小，
           *>       所以第一輪的「>」永遠不會成立，結果會一直是 0。
           *>       請先把 WS-BEST 設成第 1 筆的價格再開始迴圈。
           MOVE 0 TO WS-BEST
           PERFORM VARYING WS-INDEX FROM 2 BY 1 UNTIL WS-INDEX > 3
               IF WS-PRICE (WS-INDEX) > WS-BEST
                   MOVE WS-PRICE (WS-INDEX) TO WS-BEST
               END-IF
           END-PERFORM
           EXIT.