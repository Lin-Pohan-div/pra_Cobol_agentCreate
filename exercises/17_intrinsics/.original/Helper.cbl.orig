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
*> 段落一：把文字欄位裡的數字字串轉成真正的數值。
*> "  0012.50  " 去掉前後空白後是 "0012.50"，應該要變成 12.50。
*> TODO: NUMVAL 其實會略過前後空白，所以這行現在就能轉出 12.50。
*>       但實務上資料來源常夾雜多餘字元，請養成「先清理再轉換」的習慣：
*>       改成先用 FUNCTION TRIM 清乾淨，再交給 NUMVAL。
*> ------------------------------------------------------------------
PARSE-NUMBER.
    MOVE FUNCTION NUMVAL (WS-RAW-NUM) TO WS-NUM
    EXIT.

*> ------------------------------------------------------------------
*> 段落二：量「實際文字」的長度，並清乾淨、轉大寫。
*> "  coblings  " 去掉空白後是 "coblings"，長度 8、內容 "coblings"。
*> TODO: (1) FUNCTION LENGTH 量的是「欄位長度」而不是字串長度，
*>           所以要先 TRIM 再量。
*>       (2) WS-CLEAN 只做了 UPPER-CASE，忘了 TRIM，
*>           结果會保留前後空白。
*>       正確順序是：先 TRIM，再 UPPER-CASE。
*> ------------------------------------------------------------------
CLEAN-TEXT.
    MOVE FUNCTION LENGTH (WS-RAW-TEXT) TO WS-LEN
    MOVE FUNCTION UPPER-CASE (WS-RAW-TEXT) TO WS-CLEAN
    EXIT.

*> ------------------------------------------------------------------
*> 段落三：用 MOD / MAX / MIN 做數學處理。
*>   17 MOD 5 = 2
*>   10 / 42 / 7 中最大的是 42、最小的是 7
*> TODO: MOD 的引數順序顛倒了（MOD(a, b) 是 a 除以 b 的餘數），
*>       所以現在算成 5 MOD 17 = 5。請把兩個數字對調。
*> ------------------------------------------------------------------
MATH-HELPERS.
    COMPUTE WS-REM = FUNCTION MOD (5, 17)
    COMPUTE WS-BIG = FUNCTION MAX (10, 42, 7)
    COMPUTE WS-SMALL = FUNCTION MIN (10, 42, 7)
    EXIT.

*> 最後一段用 EXIT. 收尾。
LAST-STOP.
    EXIT.
