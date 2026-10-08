IDENTIFICATION DIVISION.
       PROGRAM-ID. BRANCH-TEST.

*> 這份檢查器不需要修改，是這一題的驗收標準。
*> 學生檔的 88 條件名稱只有學生自己看得到，所以這裡一律檢查
*> 學生段落寫進 01 層級項目的結果。

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  CK-LABEL  PIC X(8).
       01  CK-ADVICE PIC X(10).

       PROCEDURE DIVISION.
       COBLINGS-TEST-MAIN.
           PERFORM LABEL-OF-SCORE
           MOVE WS-LABEL TO CK-LABEL
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "LABEL-OF-SCORE：85 分的等級"
                     BY CONTENT "B"
                     BY CONTENT CK-LABEL

           PERFORM ADVICE-OF-TEMP
           MOVE WS-ADVICE TO CK-ADVICE
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "ADVICE-OF-TEMP：35 度的建議"
                     BY CONTENT "HOT"
                     BY CONTENT CK-ADVICE

           PERFORM USE-88-NAME
           MOVE WS-ADVICE TO CK-ADVICE
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "USE-88-NAME：用 88 條件名稱判斷 85 分"
                     BY CONTENT "PASS"
                     BY CONTENT CK-ADVICE

           CALL "COBLINGS-DONE"
           GOBACK.
