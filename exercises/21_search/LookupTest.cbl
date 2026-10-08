IDENTIFICATION DIVISION.
       PROGRAM-ID. LOOKUP-TEST.

       *> 這份檢查器不需要修改，是這一題的驗收標準。
       *> 它會依序執行學生寫的三個段落，再檢查查表結果。

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  CT-NAME     PIC X(8).
       01  CT-PRICE    PIC 9(4).
       01  CT-HIT      PIC X.
       01  CT-CNT      PIC 9(3).
       01  CT-BEST     PIC 9(4).

       PROCEDURE DIVISION.
       COBLINGS-TEST-MAIN.
           PERFORM FIND-ITEM
           MOVE WS-HIT TO CT-HIT
           MOVE WS-HIT-NAME TO CT-NAME
           MOVE WS-HIT-PRICE TO CT-PRICE
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "FIND-ITEM：有找到 P003"
                     BY CONTENT "Y" BY CONTENT CT-HIT
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "FIND-ITEM：商品名稱"
                     BY CONTENT "MATCHA" BY CONTENT CT-NAME
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "FIND-ITEM：價格"
                     BY CONTENT 2200 BY CONTENT CT-PRICE

           PERFORM COUNT-PREMIUM
           MOVE WS-PREMIUM-CNT TO CT-CNT
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "COUNT-PREMIUM：進階商品共有幾筆"
                     BY CONTENT 1 BY CONTENT CT-CNT

           PERFORM HIGHEST-PRICE
           MOVE WS-BEST TO CT-BEST
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "HIGHEST-PRICE：最高價"
                     BY CONTENT 2200 BY CONTENT CT-BEST

           CALL "COBLINGS-DONE"
           GOBACK.