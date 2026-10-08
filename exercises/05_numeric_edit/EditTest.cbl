IDENTIFICATION DIVISION.
       PROGRAM-ID. EDIT-TEST.

      *> 這份檢查器不需要修改，是這一題的驗收標準。
      *> 數值斷言比對的是「沒有編輯的欄位」，因為編輯只影響顯示。
      *> 顯示出來的樣子則由 expected.txt 負責比對。

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  CT-PRICE PIC 9(3)V99.
       01  CT-FEE   PIC 9(3)V99.
       01  CT-LINE  PIC 9(5)V99.
       01  CT-BIG   PIC 9(5)V99.

       PROCEDURE DIVISION.
       COBLINGS-TEST-MAIN.
           PERFORM MAKE-PRICE
           MOVE WS-PRICE-VAL TO CT-PRICE
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "單價 12.50 經過編輯欄位後數值不該改變"
                     BY CONTENT 12.50
                     BY CONTENT CT-PRICE

           PERFORM MAKE-FEE
           MOVE WS-FEE-VAL TO CT-FEE
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "費用 0.50 經過編輯欄位後數值不該改變"
                     BY CONTENT 0.50
                     BY CONTENT CT-FEE

           PERFORM MAKE-LINE
           MOVE WS-LINE-VAL TO CT-LINE
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "單價 x 100 應是 1250.00，編輯欄位不能截掉高位"
                     BY CONTENT 1250.00
                     BY CONTENT CT-LINE

           PERFORM MAKE-BIG
           MOVE WS-BIG-VAL TO CT-BIG
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "99999.99 需要五位整數，編輯欄位不能截掉高位"
                     BY CONTENT 99999.99
                     BY CONTENT CT-BIG

           PERFORM SHOW-RECEIPT

           CALL "COBLINGS-DONE"
           GOBACK.
