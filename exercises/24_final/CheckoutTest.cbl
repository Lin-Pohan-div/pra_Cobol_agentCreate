IDENTIFICATION DIVISION.
       PROGRAM-ID. CHECKOUT-TEST.

       *> 這份檢查器不需要修改，是這一題的驗收標準。
       *> 它會讓學生寫出 order.dat，再走完整條結帳流程檢查結果，
       *> 最後把 order.dat 清空。

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT CLEAN-FILE ASSIGN TO "order.dat".

       DATA DIVISION.
       FILE SECTION.
       FD  CLEAN-FILE.
       01  CLEAN-FILE   PIC X(12).

       WORKING-STORAGE SECTION.
       01  CT-SKU       PIC X(4).
       01  CT-QTY       PIC 9(3).
       01  CT-UNIT      PIC 9(4).
       01  CT-HIT       PIC X.
       01  CT-TOTAL     PIC 9(5).
       01  CT-ITEMS     PIC 9(3).
       01  CT-AVERAGE   PIC 9(5)V99.
       01  CT-CLAMPED   PIC X.

       PROCEDURE DIVISION.
       COBLINGS-TEST-MAIN.
           PERFORM WRITE-ORDER
           PERFORM READ-FIRST-LINE

           MOVE WS-SKU-TEXT TO CT-SKU
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "READ-FIRST-LINE：拆出來的商品代號"
                     BY CONTENT "B002" BY CONTENT CT-SKU
           MOVE WS-QTY-TEXT TO CT-QTY
           CALL "COBLINGS-EXPECT-LENGTH"
               USING BY CONTENT "READ-FIRST-LINE：數量欄位長度"
                     BY CONTENT 3 BY CONTENT 3

           PERFORM FIND-UNIT-PRICE
           MOVE WS-HIT TO CT-HIT
           MOVE WS-UNIT TO CT-UNIT
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "FIND-UNIT-PRICE：有查到 B002"
                     BY CONTENT "Y" BY CONTENT CT-HIT
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "FIND-UNIT-PRICE：LATTE 單價（分）"
                     BY CONTENT 1500 BY CONTENT CT-UNIT

           PERFORM SUM-ORDER
           MOVE WS-TOTAL TO CT-TOTAL
           MOVE WS-ITEMS TO CT-ITEMS
           MOVE WS-CLAMPED TO CT-CLAMPED
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "SUM-ORDER：訂單有幾件"
                     BY CONTENT 3 BY CONTENT CT-ITEMS
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "SUM-ORDER：小計溢位旗標"
                     BY CONTENT "Y" BY CONTENT CT-CLAMPED
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "SUM-ORDER：總金額（分）"
                     BY CONTENT 19439 BY CONTENT CT-TOTAL

           PERFORM AVERAGE-ORDER
           MOVE WS-AVERAGE TO CT-AVERAGE
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "AVERAGE-ORDER：平均單價（四捨五入到分）"
                     BY CONTENT 6479.67 BY CONTENT CT-AVERAGE

           PERFORM CLEAN-UP

           CALL "COBLINGS-DONE"
           GOBACK.

       *> 把題目資料夾裡的 order.dat 清空，避免污染版本控制。
       CLEAN-UP.
           OPEN OUTPUT CLEAN-FILE.
           CLOSE CLEAN-FILE.
           EXIT.