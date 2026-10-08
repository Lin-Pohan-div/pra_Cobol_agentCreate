*> ============================================================
*> 開始之前：請先閱讀同一個資料夾裡的 README.md
*>   裡面有學習目標、觀念講解、常見錯誤與操作步驟。
*>   卡關時可以執行 .\coblings.cmd hint 看提示。
*> ============================================================
IDENTIFICATION DIVISION.
PROGRAM-ID. HELPER.

*> 這一題練習內建函式：LENGTH、TRIM、UPPER-CASE、NUMVAL、MOD、MAX、MIN。
*> 你要修的是下面三個段落，段落名稱不要改。

DATA DIVISION.
WORKING-STORAGE SECTION.

01  WS-RAW-NUM   PIC X(12) VALUE "  0012.50  ".
01  WS-RAW-TEXT  PIC X(12) VALUE "  coblings  ".
01  WS-WORD      PIC X(12).

01  WS-I         PIC 99.

*> 檢查器讀得到的結果（01 層級）
01  WS-NUM       PIC S9(7)V99 VALUE 0.
01  WS-LEN       PIC 99 VALUE 0.
01  WS-REM       PIC 99 VALUE 0.
01  WS-BIG       PIC S9(5) VALUE 0.
01  WS-SMALL     PIC S9(5) VALUE 0.
01  WS-CLEAN     PIC X(12).

PROCEDURE DIVISION.

*> ------------------------------------------------------------------
*> 段落一：NUMVAL 把文字轉成數值；先用 TRIM 清理資料是比較保險的習慣。
*> ------------------------------------------------------------------
PARSE-NUMBER.
    MOVE FUNCTION NUMVAL (FUNCTION TRIM (WS-RAW-NUM)) TO WS-NUM
    EXIT.

*> ------------------------------------------------------------------
*> 段落二：LENGTH 量的是「實際字串」，所以要先 TRIM；
*>         產生新字串的順序是「先 TRIM、再 UPPER-CASE」。
*> ------------------------------------------------------------------
CLEAN-TEXT.
    MOVE FUNCTION LENGTH (FUNCTION TRIM (WS-RAW-TEXT)) TO WS-LEN
    MOVE FUNCTION UPPER-CASE (FUNCTION TRIM (WS-RAW-TEXT)) TO WS-CLEAN
    EXIT.

*> ------------------------------------------------------------------
*> 段落三：MOD(a, b) 是 a 除以 b 的餘數，所以要寫 17 MOD 5。
*> ------------------------------------------------------------------
MATH-HELPERS.
    COMPUTE WS-REM = FUNCTION MOD (17, 5)
    COMPUTE WS-BIG = FUNCTION MAX (10, 42, 7)
    COMPUTE WS-SMALL = FUNCTION MIN (10, 42, 7)
    EXIT.

*> 最後一段用 EXIT. 收尾。
LAST-STOP.
    EXIT.
