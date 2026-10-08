IDENTIFICATION DIVISION.
       PROGRAM-ID. INSPECT-TEST.

*> 這份檢查器不需要修改，是這一題的驗收標準。
*> 它依序執行三個段落，再檢查學生寫進 01 層級項目的結果。

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  CK-HITS      PIC 9(4).
       01  CK-FORMATTED PIC X(12).
       01  CK-SWAPPED   PIC X(12).

       PROCEDURE DIVISION.
       COBLINGS-TEST-MAIN.
           PERFORM COUNT-LETTERS
           MOVE WS-HITS TO CK-HITS
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "COUNT-LETTERS：數到的字母 I 有幾個"
                     BY CONTENT 4
                     BY CONTENT CK-HITS

           PERFORM NORMALIZE-DATE
           MOVE WS-FORMATTED TO CK-FORMATTED
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "NORMALIZE-DATE：取代後的日期"
                     BY CONTENT "2024/10/05"
                     BY CONTENT CK-FORMATTED

           PERFORM SWAP-DIGITS
           MOVE WS-SWAPPED TO CK-SWAPPED
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "SWAP-DIGITS：0 與 1 互換後的結果"
                     BY CONTENT "A01B10C00D11"
                     BY CONTENT CK-SWAPPED

           *> 只有 TALLYING 的 INSPECT 不會改動被檢查的字串本身。
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "COUNT-LETTERS：WS-SOURCE 應維持原樣"
                     BY CONTENT "MISSISSIPPI"
                     BY CONTENT WS-SOURCE

           CALL "COBLINGS-DONE"
           GOBACK.
