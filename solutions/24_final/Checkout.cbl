*> ============================================================
*> 開始之前：請先閱讀同一個資料夾裡的 README.md
*>   裡面有學習目標、觀念講解、常見錯誤與操作步驟。
*>   卡關時可以執行 .\coblings.cmd hint 看提示。
*> ============================================================
IDENTIFICATION DIVISION.
       PROGRAM-ID. CHECKOUT.

       *> ============================================================
       *> 綜合演練：把前面幾題學過的東西合起來寫一個小結帳程式。
       *>
       *> 訂單檔 order.dat 裡每一行都是「商品代號,數量」，
       *> 商品代號跟數量之間用逗號隔開，每行固定 12 碼。
       *> 結帳流程：
       *>   1. WRITE-ORDER      寫出訂單（記得 CLOSE 才會落地）
       *>   2. READ-FIRST-LINE  讀回第一行，並用 UNSTRING 拆欄位
       *>   3. FIND-UNIT-PRICE  用 SEARCH 到商品表查單價
       *>   4. SUM-ORDER        逐行計算小計並加總（溢位要夾住）
       *>   5. AVERAGE-ORDER    算平均單價（四捨五入到分）
       *> ============================================================

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT ORDER-FILE ASSIGN TO "order.dat".

       DATA DIVISION.
       FILE SECTION.
       *> 每一筆訂單就是一整行固定長度的文字，
       *> 所以記錄名稱沿用檔案名稱 ORDER-FILE。
       FD  ORDER-FILE.
       01  ORDER-FILE   PIC X(12).

       WORKING-STORAGE SECTION.
       *> 商品表：代號 / 名稱 / 單價（以「分」為單位）
       01  WS-CATALOG.
           05  WS-PRODUCT OCCURS 5 TIMES.
               10  WS-SKU     PIC X(4).
               10  WS-NAME    PIC X(8).
               10  WS-PRICE   PIC 9(4).

       01  WS-LINE       PIC X(12).
       01  WS-SKU-TEXT   PIC X(4).
       01  WS-QTY-TEXT   PIC X(3).
       01  WS-SKU        PIC X(4).
       01  WS-QTY        PIC 9(3).
       01  WS-UNIT       PIC 9(4).
       01  WS-SUBTOTAL   PIC 9(4).
       01  WS-TOTAL      PIC 9(5).
       01  WS-ITEMS      PIC 9(3).
       01  WS-AVERAGE    PIC 9(5)V99.
       01  WS-CLAMPED    PIC X VALUE "N".
       01  WS-EOF        PIC X VALUE "N".
       01  WS-INDEX      PIC 9(2).
       01  WS-HIT        PIC X VALUE "N".

       PROCEDURE DIVISION.

       LOAD-CATALOG.
           MOVE "A001" TO WS-SKU (1)
           MOVE "MOCHA" TO WS-NAME (1)
           MOVE 1235 TO WS-PRICE (1)
           MOVE "B002" TO WS-SKU (2)
           MOVE "LATTE" TO WS-NAME (2)
           MOVE 1500 TO WS-PRICE (2)
           MOVE "P003" TO WS-SKU (3)
           MOVE "MATCHA" TO WS-NAME (3)
           MOVE 2250 TO WS-PRICE (3)
           EXIT.

       WRITE-ORDER.
           OPEN OUTPUT ORDER-FILE.
           MOVE "B002,7      " TO ORDER-FILE
           WRITE ORDER-FILE
           MOVE "P003,2      " TO ORDER-FILE
           WRITE ORDER-FILE
           MOVE "A001,4      " TO ORDER-FILE
           WRITE ORDER-FILE
           CLOSE ORDER-FILE.
           EXIT.

       READ-FIRST-LINE.
           OPEN INPUT ORDER-FILE.
           MOVE SPACES TO WS-LINE
           MOVE "N" TO WS-EOF
           READ ORDER-FILE INTO WS-LINE
               AT END
                   MOVE "Y" TO WS-EOF
           END-READ
           CLOSE ORDER-FILE.
           MOVE SPACES TO WS-SKU-TEXT, WS-QTY-TEXT
           UNSTRING WS-LINE DELIMITED BY ","
               INTO WS-SKU-TEXT DELIMITED BY ",",
                    WS-QTY-TEXT DELIMITED BY ","
           EXIT.

       FIND-UNIT-PRICE.
           PERFORM LOAD-CATALOG
           MOVE WS-SKU-TEXT TO WS-SKU
           MOVE "N" TO WS-HIT
           MOVE 0 TO WS-UNIT
           MOVE 0 TO WS-INDEX
           SEARCH WS-PRODUCT VARYING WS-INDEX FROM 1 BY 1 UNTIL WS-INDEX > 5
               WHEN WS-SKU (WS-INDEX) = WS-SKU-TEXT
                   MOVE "Y" TO WS-HIT
                   MOVE WS-PRICE (WS-INDEX) TO WS-UNIT
           END-SEARCH
           EXIT.

       SUM-ORDER.
           PERFORM LOAD-CATALOG
           OPEN INPUT ORDER-FILE.
           MOVE 0 TO WS-TOTAL
           MOVE 0 TO WS-ITEMS
           MOVE "N" TO WS-CLAMPED
           MOVE "N" TO WS-EOF
           PERFORM UNTIL WS-EOF = "Y"
               READ ORDER-FILE INTO WS-LINE
                   AT END
                       MOVE "Y" TO WS-EOF
               END-READ
               IF WS-EOF = "N"
                   MOVE SPACES TO WS-SKU-TEXT, WS-QTY-TEXT
                   UNSTRING WS-LINE DELIMITED BY ","
                       INTO WS-SKU-TEXT DELIMITED BY ",",
                            WS-QTY-TEXT DELIMITED BY ","
                   MOVE WS-QTY-TEXT TO WS-QTY
                   MOVE 0 TO WS-INDEX
                   SEARCH WS-PRODUCT VARYING WS-INDEX FROM 1 BY 1 UNTIL WS-INDEX > 5
                       WHEN WS-SKU (WS-INDEX) = WS-SKU-TEXT
                           MOVE WS-PRICE (WS-INDEX) TO WS-UNIT
                   END-SEARCH
                   COMPUTE WS-SUBTOTAL = WS-UNIT * WS-QTY
                       ON SIZE ERROR
                           MOVE 9999 TO WS-SUBTOTAL
                           MOVE "Y" TO WS-CLAMPED
                   END-COMPUTE
                   ADD WS-SUBTOTAL TO WS-TOTAL
                   ADD 1 TO WS-ITEMS
               END-IF
           END-PERFORM
           CLOSE ORDER-FILE.
           EXIT.

       AVERAGE-ORDER.
           DIVIDE WS-TOTAL BY WS-ITEMS GIVING WS-AVERAGE ROUNDED
           EXIT.