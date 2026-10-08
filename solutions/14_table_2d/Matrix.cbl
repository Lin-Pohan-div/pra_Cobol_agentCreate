*> ============================================================
*> 開始之前：請先閱讀同一個資料夾裡的 README.md
*>   裡面有學習目標、觀念講解、常見錯誤與操作步驟。
*>   卡關時可以執行 .\coblings.cmd hint 看提示。
*> ============================================================
IDENTIFICATION DIVISION.
PROGRAM-ID. MATRIX.

*> 這一題練習「二維表格」：表格裡面再放表格，用兩個下標存取。
*> 你要修的是下面三個段落，段落名稱不要改（檢查器會用名字呼叫它們）。

DATA DIVISION.
WORKING-STORAGE SECTION.

01  WS-ROW-COUNT  PIC 99 VALUE 3.
01  WS-COL-COUNT  PIC 99 VALUE 4.

*> 3 列 4 欄的矩陣：外層是列，內層是欄。
01  WS-MATRIX.
    05  WS-ROW-ITEM OCCURS 3 TIMES.
        10  WS-CELL   PIC S9(3) OCCURS 4 TIMES.

01  WS-R          PIC 99.
01  WS-C          PIC 99.
01  WS-VALUE      PIC S9(4).

*> 檢查器讀得到的結果（01 層級）
01  WS-TOTAL      PIC S9(6) VALUE 0.
01  WS-ROW-SUM    PIC S9(6) VALUE 0.
01  WS-DIAGONAL   PIC S9(6) VALUE 0.
01  WS-MAX        PIC S9(3) VALUE 0.
01  WS-MAX-R      PIC 99 VALUE 0.
01  WS-MAX-C      PIC 99 VALUE 0.

PROCEDURE DIVISION.

*> 段落一：填入 3x4 的矩陣（1 到 12）。
LOAD-MATRIX.
    MOVE 1 TO WS-CELL (1, 1)
    MOVE 2 TO WS-CELL (1, 2)
    MOVE 3 TO WS-CELL (1, 3)
    MOVE 4 TO WS-CELL (1, 4)
    MOVE 5 TO WS-CELL (2, 1)
    MOVE 6 TO WS-CELL (2, 2)
    MOVE 7 TO WS-CELL (2, 3)
    MOVE 8 TO WS-CELL (2, 4)
    MOVE 9 TO WS-CELL (3, 1)
    MOVE 10 TO WS-CELL (3, 2)
    MOVE 11 TO WS-CELL (3, 3)
    MOVE 12 TO WS-CELL (3, 4)
    EXIT.

*> 段落二：算出整個矩陣所有格子的總和，放進 WS-TOTAL。
*> 內層迴圈跑的是「欄」，所以上界要用 WS-COL-COUNT。
SUM-MATRIX.
    MOVE 0 TO WS-TOTAL
    PERFORM VARYING WS-R FROM 1 BY 1 UNTIL WS-R > WS-ROW-COUNT
        PERFORM VARYING WS-C FROM 1 BY 1 UNTIL WS-C > WS-COL-COUNT
            ADD WS-CELL (WS-R, WS-C) TO WS-TOTAL
        END-PERFORM
    END-PERFORM
    EXIT.

*> 段落三：算出第 2 列的總和，放進 WS-ROW-SUM。
*> 只要第 2 列：外層固定在 2，內層跑全部 4 欄。
SUM-ROW-TWO.
    MOVE 0 TO WS-ROW-SUM
    PERFORM VARYING WS-R FROM 2 BY 1 UNTIL WS-R > 2
        PERFORM VARYING WS-C FROM 1 BY 1 UNTIL WS-C > WS-COL-COUNT
            ADD WS-CELL (WS-R, WS-C) TO WS-ROW-SUM
        END-PERFORM
    END-PERFORM
    EXIT.

*> 段落四：把左上到右下的對角線加起來，放進 WS-DIAGONAL。
*> 對角線的特徵是「列下標＝欄下標」，所以內層只跑 WS-R 那一格。
SUM-DIAGONAL.
    MOVE 0 TO WS-DIAGONAL
    PERFORM VARYING WS-R FROM 1 BY 1 UNTIL WS-R > WS-ROW-COUNT
        PERFORM VARYING WS-C FROM WS-R BY 1 UNTIL WS-C > WS-R
            ADD WS-CELL (WS-R, WS-C) TO WS-DIAGONAL
        END-PERFORM
    END-PERFORM
    EXIT.

*> 段落五：找出整個矩陣最大的數，值放進 WS-MAX，位置放進 WS-MAX-R / WS-MAX-C。
FIND-MAX.
    MOVE 0 TO WS-MAX
    MOVE 0 TO WS-MAX-R
    MOVE 0 TO WS-MAX-C
    PERFORM VARYING WS-R FROM 1 BY 1 UNTIL WS-R > WS-ROW-COUNT
        PERFORM VARYING WS-C FROM 1 BY 1 UNTIL WS-C > WS-COL-COUNT
            IF WS-CELL (WS-R, WS-C) > WS-MAX
                MOVE WS-CELL (WS-R, WS-C) TO WS-MAX
                MOVE WS-R TO WS-MAX-R
                MOVE WS-C TO WS-MAX-C
            END-IF
        END-PERFORM
    END-PERFORM
    EXIT.
