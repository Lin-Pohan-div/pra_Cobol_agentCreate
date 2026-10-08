IDENTIFICATION DIVISION.
       PROGRAM-ID. VARIABLES-TEST.

      *> 這份檢查器不需要修改，是這一題的驗收標準。
      *> 它依序執行學生寫的三個段落，再檢查搬到輸出欄位的結果。

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  CT-ACTUAL-TEXT PIC X(10).
       01  CT-ACTUAL-NUM  PIC 9(3).
       01  CT-ACTUAL-AMT  PIC 9(3)V99.

       PROCEDURE DIVISION.
       COBLINGS-TEST-MAIN.
           PERFORM FILL-FIELDS
           PERFORM COPY-FIELDS

           MOVE WS-NAME-OUT TO CT-ACTUAL-TEXT
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "WS-NAME-OUT（PIC X(10) 文字靠左對齊，右邊補空白）"
                     BY CONTENT "Amy"
                     BY CONTENT CT-ACTUAL-TEXT

           MOVE WS-COUNT-OUT TO CT-ACTUAL-NUM
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "WS-COUNT-OUT（MOVE 方向要對，45 應該被完整搬過去）"
                     BY CONTENT 45
                     BY CONTENT CT-ACTUAL-NUM

           MOVE WS-PRICE-OUT TO CT-ACTUAL-AMT
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "WS-PRICE-OUT（PIC 9(3)V99 的 12.50 元）"
                     BY CONTENT 12.50
                     BY CONTENT CT-ACTUAL-AMT

           PERFORM SHOW-FIELDS

           CALL "COBLINGS-DONE"
           GOBACK.
