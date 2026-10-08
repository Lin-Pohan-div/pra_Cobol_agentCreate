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
      *> TODO: 規格要數出 "MISSISSIPPI" 裡有幾個字母 I（答案是 4）。
      *>       請用 INSPECT ... TALLYING 來數，不要自己寫 IF 一個字一個字數。
           .

       NORMALIZE-DATE.
           MOVE "2024-10-05" TO WS-FORMATTED
           INSPECT WS-FORMATTED REPLACING LEADING "-" BY "/"
      *> TODO: 現在的結果是 "2024-10-05"，但規格要 "2024/10/05"（三個 "-" 都要換掉）。
      *>       LEADING 只取代「開頭連續」出現的那幾個，中間的完全不動；
      *>       請改成能取代全部出現位置的寫法。
           .

       SWAP-DIGITS.
           MOVE "A10B01C11D00" TO WS-SWAPPED
      *> TODO: 規格要把這個字串裡所有的 0 與 1 互換，結果要是 "A01B10C00D11"。
      *>       請用 INSPECT ... CONVERTING "要找的字元們" TO "換成的字元們"：
      *>       前後兩個字串一樣長，同一個位置的字元兩兩成對，
      *>       而且所有對照同時生效。
           .
           EXIT.
