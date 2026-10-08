*> ============================================================
*> 開始之前：請先閱讀同一個資料夾裡的 README.md
*>   裡面有學習目標、觀念講解、常見錯誤與操作步驟。
*>   卡關時可以執行 .\coblings.cmd hint 看提示。
*> ============================================================
IDENTIFICATION DIVISION.
PROGRAM-ID. PRICES.

*> 這一題練習「表格」：OCCURS、下標、以及 OCCURS … DEPENDING ON。
*> 你要修的是下面三個段落，段落名稱不要改（檢查器會用名字呼叫它們）。

DATA DIVISION.
WORKING-STORAGE SECTION.

*> 表格的長度由 WS-PRICE-COUNT 決定，讀寫前要記得先給它正確的值。
01  WS-PRICE-COUNT  PIC 99 VALUE 5.
01  WS-PRICE-TABLE.
    05  WS-PRICE   PIC S9(4)V99 OCCURS 10 TIMES DEPENDING ON WS-PRICE-COUNT.

01  WS-ITEM-CODE.
    05  WS-CODE    PIC X(3) OCCURS 10 TIMES DEPENDING ON WS-PRICE-COUNT.

01  WS-I          PIC 99.
01  WS-J          PIC 99.

*> 檢查器讀得到的結果（01 層級）
01  WS-TOTAL      PIC S9(6)V99 VALUE 0.
01  WS-MAX-PRICE  PIC S9(4)V99 VALUE 0.
01  WS-MAX-POS    PIC 99 VALUE 0.
01  WS-LINE       PIC X(40).
01  WS-AMOUNT     PIC ZZZ9.99.

PROCEDURE DIVISION.

*> 段落一：把 5 筆單價寫進表格，並把每筆的貨號寫進另一個表格。
LOAD-PRICES.
    MOVE 5 TO WS-PRICE-COUNT
    MOVE 12.50 TO WS-PRICE (1)
    MOVE 7.25  TO WS-PRICE (2)
    MOVE 30.00 TO WS-PRICE (3)
    MOVE 4.99  TO WS-PRICE (4)
    MOVE 18.60 TO WS-PRICE (5)

    MOVE "A01" TO WS-CODE (1)
    MOVE "B02" TO WS-CODE (2)
    MOVE "C03" TO WS-CODE (3)
    MOVE "D04" TO WS-CODE (4)
    MOVE "E05" TO WS-CODE (5)
    EXIT.

*> 段落二：算出 5 筆單價的總和，放進 WS-TOTAL。
*> 迴圈要跑滿 WS-PRICE-COUNT 筆：條件「成立就停」，所以用 > 才對。
SUM-PRICES.
    MOVE 0 TO WS-TOTAL
    PERFORM VARYING WS-I FROM 1 BY 1 UNTIL WS-I > WS-PRICE-COUNT
        ADD WS-PRICE (WS-I) TO WS-TOTAL
    END-PERFORM
    EXIT.

*> 段落三：找出表格裡最貴的一筆。
*> 先把第 1 筆當成「目前冠軍」，再從第 2 筆一路比到最後一筆。
FIND-MAX.
    MOVE WS-PRICE (1) TO WS-MAX-PRICE
    MOVE 1 TO WS-MAX-POS
    PERFORM VARYING WS-I FROM 2 BY 1 UNTIL WS-I > WS-PRICE-COUNT
        IF WS-PRICE (WS-I) > WS-MAX-PRICE
            MOVE WS-PRICE (WS-I) TO WS-MAX-PRICE
            MOVE WS-I TO WS-MAX-POS
        END-IF
    END-PERFORM
    EXIT.

*> 段落四：把表格內容照「貨號 單價」逐筆印出來。
SHOW-TABLE.
    PERFORM VARYING WS-I FROM 1 BY 1 UNTIL WS-I > WS-PRICE-COUNT
        MOVE WS-PRICE (WS-I) TO WS-AMOUNT
        DISPLAY WS-CODE (WS-I) " " WS-AMOUNT
    END-PERFORM
    EXIT.
