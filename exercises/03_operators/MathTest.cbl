IDENTIFICATION DIVISION.
       PROGRAM-ID. MATH-TEST.

      *> 這份檢查器不需要修改，是這一題的驗收標準。
      *> 四則運算各有自己的段落，檢查器會依序執行並檢查結果。

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  CT-SUM         PIC 9(4).
       01  CT-DAYS        PIC 9(3).
       01  CT-BORROWED    PIC 9(3).
       01  CT-TOTAL-PRICE PIC 9(5)V99.
       01  CT-AVG         PIC 9(3)V99.
       01  CT-AVG-ROUND   PIC 9(3)V99.

       PROCEDURE DIVISION.
       COBLINGS-TEST-MAIN.
           PERFORM SUM-THREE
           MOVE WS-SUM TO CT-SUM
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "SUM-THREE：12 + 30 + 45 應等於 87"
                     BY CONTENT 87
                     BY CONTENT CT-SUM

           PERFORM TAKE-AWAY
           MOVE WS-DAYS TO CT-DAYS
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "TAKE-AWAY：借出 12 天後，30 天應剩下 18 天"
                     BY CONTENT 18
                     BY CONTENT CT-DAYS

           MOVE WS-BORROWED TO CT-BORROWED
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "TAKE-AWAY：借出的天數 WS-BORROWED 不該被改動"
                     BY CONTENT 12
                     BY CONTENT CT-BORROWED

           PERFORM LINE-TOTAL
           MOVE WS-TOTAL-PRICE TO CT-TOTAL-PRICE
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "LINE-TOTAL：12.50 x 4 應等於 50.00（要靠 GIVING）"
                     BY CONTENT 50.00
                     BY CONTENT CT-TOTAL-PRICE

           PERFORM AVERAGE-PRICE
           MOVE WS-AVG TO CT-AVG
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "AVERAGE-PRICE：100 除以 6 截斷後是 16.66"
                     BY CONTENT 16.66
                     BY CONTENT CT-AVG

           MOVE WS-AVG-ROUND TO CT-AVG-ROUND
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "AVERAGE-PRICE：加上 ROUNDED 後是 16.67"
                     BY CONTENT 16.67
                     BY CONTENT CT-AVG-ROUND

           CALL "COBLINGS-DONE"
           GOBACK.
