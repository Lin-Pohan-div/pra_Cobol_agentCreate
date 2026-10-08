*> ============================================================
*> 開始之前：請先閱讀同一個資料夾裡的 README.md
*>   裡面有學習目標、觀念講解、常見錯誤與操作步驟。
*>   卡關時可以執行 .\coblings.cmd hint 看提示。
*> ============================================================
IDENTIFICATION DIVISION.
PROGRAM-ID. REPORT.

*> 這一題練習「段落結構」：段落像 subroutine 一樣被 PERFORM 呼叫，
*> 以及 PERFORM A THRU B 會依序執行範圍內的每一段。
*> 你要修的是下面兩個段落，段落名稱與順序都不要改。

DATA DIVISION.
WORKING-STORAGE SECTION.

01  WS-ROW-COUNT  PIC 99 VALUE 4.
01  WS-I          PIC 99.

01  WS-NUM-TABLE.
    05  WS-NUM   PIC S9(4) OCCURS 4 TIMES.

*> 檢查器讀得到的結果（01 層級）
01  WS-SUM        PIC S9(6) VALUE 0.
01  WS-DOUBLED    PIC S9(6) VALUE 0.
01  WS-LABEL      PIC X(12).

PROCEDURE DIVISION.

*> ------------------------------------------------------------------
*> 段落零：把表格填滿。檢查器會先執行這段。
*> ------------------------------------------------------------------
LOAD-NUMS.
    MOVE 4 TO WS-ROW-COUNT
    MOVE 10 TO WS-NUM (1)
    MOVE 20 TO WS-NUM (2)
    MOVE 30 TO WS-NUM (3)
    MOVE 40 TO WS-NUM (4)
    EXIT.

*> ------------------------------------------------------------------
*> 段落一：最普通的用法——段落像 subroutine 一樣被呼叫。
*> 這段是正確的，請當成範例參考。
*> ------------------------------------------------------------------
MAKE-SUM.
    MOVE 0 TO WS-SUM
    PERFORM VARYING WS-I FROM 1 BY 1 UNTIL WS-I > WS-ROW-COUNT
        ADD WS-NUM (WS-I) TO WS-SUM
    END-PERFORM
    EXIT.

*> ------------------------------------------------------------------
*> 段落二：用 PERFORM A THRU B 依序執行三段。
*> THRU 的結束段落要是「最後要執行的那一段」，三段都會依序跑到。
*> ------------------------------------------------------------------
MAKE-DOUBLED.
    MOVE 0 TO WS-DOUBLED
    PERFORM DOUBLING THRU FINISH-DOUBLING
    EXIT.

*> 第一步：把第 1 筆乘以 2（10 * 2 = 20）。
DOUBLING.
    COMPUTE WS-DOUBLED = WS-NUM (1) * 2.

*> 第二步：加 7（20 + 7 = 27）。
FINISH-ADD.
    ADD 7 TO WS-DOUBLED.

*> 第三步：收尾，也就是 THRU 應該指的結束段落。
FINISH-DOUBLING.
    EXIT.

*> ------------------------------------------------------------------
*> 段落三：示範「PERFORM 的範圍太大」會怎樣。
*> 範圍太大就會執行到不該跑的段落，所以要剛好停在 SETUP-LABEL。
*> ------------------------------------------------------------------
MAKE-LABEL.
    MOVE SPACES TO WS-LABEL
    PERFORM SETUP-LABEL THRU SETUP-LABEL
    EXIT.

*> 真正要執行的那一段。
SETUP-LABEL.
    MOVE "REPORT-OK" TO WS-LABEL.

*> 這一段不是這次要跑的（它會把 WS-LABEL 改掉）。
NOISE-PARA.
    MOVE "WRONG" TO WS-LABEL
    EXIT.

*> 最後一段用 EXIT. 收尾，避免 PERFORM 掉進後面的段落。
LAST-STOP.
    EXIT.
