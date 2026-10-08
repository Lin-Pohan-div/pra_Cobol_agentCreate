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
*> TODO: 表格還沒有初始化。COMP-3 欄位在沒有給值之前是 0，
*>       所以現在只放進去兩筆就結束了。
*>       請把五筆金額（100 / 200 / 300 / 400 / 500）依序放進表格，
*>       並把 WS-CNT 設成 5。
*> ------------------------------------------------------------------
LOAD-ITEMS.
    MOVE 100 TO WS-ITEM (1)
    MOVE 200 TO WS-ITEM (2)
    EXIT.

*> ------------------------------------------------------------------
*> 段落二：用 INDEX 當下標，把表格全部加起來，放進 WS-TOTAL。
*> INDEX 的用法：先 SET 到 1，再用 PERFORM VARYING 讓它自己前進。
*> TODO: 目前迴圈的下標是普通欄位 WS-I，而且從 0 開始跑。
*>       表格下標是 1 起始，直接從 0 開始會造成「少算一筆」的結果不對。
*>       請改用 USAGE INDEX 的 WS-IDX，並讓它從 1 跑到 WS-CNT。
*> ------------------------------------------------------------------
SUM-ITEMS.
    MOVE 0 TO WS-TOTAL
    MOVE 0 TO WS-I
    PERFORM VARYING WS-I FROM 0 BY 1 UNTIL WS-I > WS-CNT
        ADD WS-ITEM (WS-I) TO WS-TOTAL
    END-PERFORM
    EXIT.

*> ------------------------------------------------------------------
*> 段落三：用 SET 把 INDEX 移到最後一筆，放進 WS-LARGEST 與 WS-LARGEST-IDX。
*> TODO: SET 現在設成 1，所以取到的是第一筆 100，不是最後一筆 500。
*>       SET 可以把索引設成另一個欄位的值，請設成 WS-CNT。
*> ------------------------------------------------------------------
FIND-LARGEST.
    SET WS-IDX TO 1
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
