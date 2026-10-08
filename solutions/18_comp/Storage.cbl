*> ============================================================
*> 開始之前：請先閱讀同一個資料夾裡的 README.md
*>   裡面有學習目標、觀念講解、常見錯誤與操作步驟。
*>   卡關時可以執行 .\coblings.cmd hint 看提示。
*> ============================================================
IDENTIFICATION DIVISION.
PROGRAM-ID. STORAGE.

*> 這一題練習數字的儲存方式：COMP、COMP-3、USAGE INDEX、以及 SET。
*> 你要修的是下面三個段落，段落名稱不要改。

DATA DIVISION.
WORKING-STORAGE SECTION.

*> 一般數字欄位（用字元存）
01  WS-CNT        PIC 9(4) VALUE 5.

*> COMP：以二進位存整數
01  WS-BIN-COUNT  PIC S9(5)V99 COMP.

*> COMP-3：壓縮十進位（packed decimal）
01  WS-PACKED-RATE PIC S9(5)V99 COMP-3.

*> 表格項目也常用 COMP-3
01  WS-ITEM-TABLE.
    05  WS-ITEM    PIC S9(4) COMP-3 OCCURS 5 TIMES.

*> USAGE INDEX：專門當表格下標用的欄位
01  WS-IDX        USAGE INDEX.

01  WS-I          PIC 9(4).

*> 檢查器讀得到的結果（01 層級）
01  WS-TOTAL      PIC S9(9)V99 COMP VALUE 0.
01  WS-LARGEST    PIC S9(4) COMP VALUE 0.
01  WS-LARGEST-IDX PIC 9(4) VALUE 0.

PROCEDURE DIVISION.

*> ------------------------------------------------------------------
*> 段落一：把表格的五筆金額放進 COMP-3 欄位。
*> 表格還沒有初始化，COMP-3 欄位在沒有給值之前是 0，
*> 所以現在只放進去兩筆就結束，後面三格會是 0。
*> 請把五筆金額（100 / 200 / 300 / 400 / 500）依序放進表格。
*> ------------------------------------------------------------------
LOAD-ITEMS.
    MOVE 100 TO WS-ITEM (1)
    MOVE 200 TO WS-ITEM (2)
    MOVE 300 TO WS-ITEM (3)
    MOVE 400 TO WS-ITEM (4)
    MOVE 500 TO WS-ITEM (5)
    EXIT.

*> ------------------------------------------------------------------
*> 段落二：用 USAGE INDEX 當下標，把表格從第 1 格加到第 WS-CNT 格。
*> INDEX 欄位一開始要 SET 到 1，表格下標是 1 起始、不能從 0 跑。
*> ------------------------------------------------------------------
SUM-ITEMS.
    MOVE 0 TO WS-TOTAL
    SET WS-IDX TO 1
    PERFORM VARYING WS-IDX FROM 1 BY 1 UNTIL WS-IDX > WS-CNT
        ADD WS-ITEM (WS-IDX) TO WS-TOTAL
    END-PERFORM
    EXIT.

*> ------------------------------------------------------------------
*> 段落三：用 SET 把 INDEX 移到最後一筆，放進 WS-LARGEST 與 WS-LARGEST-IDX。
*> SET 可以把索引設成另一個欄位的值，所以設成 WS-CNT 就會停在最後一格。
*> ------------------------------------------------------------------
FIND-LARGEST.
    SET WS-IDX TO WS-CNT
    MOVE WS-ITEM (WS-IDX) TO WS-LARGEST
    MOVE WS-IDX TO WS-LARGEST-IDX
    EXIT.

*> 段落四：示範 COMP 與 COMP-3 存起來的數值是一樣的。
*> 這段是正確的，請當成範例參考。
COPY-TO-BOTH.
    MOVE -1234.56 TO WS-BIN-COUNT
    MOVE -1234.56 TO WS-PACKED-RATE
    EXIT.

*> 最後一段用 EXIT. 收尾。
LAST-STOP.
    EXIT.
