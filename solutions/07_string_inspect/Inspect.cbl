*> ============================================================
*> 開始之前：請先閱讀同一個資料夾裡的 README.md
*>   裡面有學習目標、觀念講解、常見錯誤與操作步驟。
*>   卡關時可以執行 .\coblings.cmd hint 看提示。
*> ============================================================
IDENTIFICATION DIVISION.
       PROGRAM-ID. INSPECT.

*> INSPECT 是一個句子就能做完「檢查」或「取代」的敘述：
*>   TALLYING  ── 數一數某個字串出現了幾次
*>   REPLACING ── 把某個字串換成另一個
*>   CONVERTING ── 依「字元對照表」逐字元翻譯

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-SOURCE    PIC X(12).
       01  WS-HITS      PIC 9(4).
       01  WS-FORMATTED PIC X(12).
       01  WS-SWAPPED   PIC X(12).

       PROCEDURE DIVISION.

       COUNT-LETTERS.
           MOVE "MISSISSIPPI" TO WS-SOURCE
           MOVE 0 TO WS-HITS
           INSPECT WS-SOURCE TALLYING WS-HITS FOR ALL "I".

       NORMALIZE-DATE.
           MOVE "2024-10-05" TO WS-FORMATTED
           INSPECT WS-FORMATTED REPLACING ALL "-" BY "/".

       SWAP-DIGITS.
           MOVE "A10B01C11D00" TO WS-SWAPPED
           INSPECT WS-SWAPPED CONVERTING "01" TO "10".
           EXIT.
