*> ============================================================
*> 開始之前：請先閱讀同一個資料夾裡的 README.md
*>   裡面有學習目標、觀念講解、常見錯誤與操作步驟。
*>   卡關時可以執行 .\coblings.cmd hint 看提示。
*> ============================================================
IDENTIFICATION DIVISION.
       PROGRAM-ID. LEDGER.

       *> ============================================================
       *> 這一題練習「順序檔案（sequential file）」：
       *>   SELECT 檔名 ASSIGN TO "資料檔"   宣告檔案與磁碟檔名的對應
       *>   FD 檔名 / 01 記錄名              宣告記錄的版面
       *>   OPEN OUTPUT → WRITE → CLOSE      寫檔（OUTPUT 會先清空）
       *>   OPEN INPUT  → READ → CLOSE       讀檔
       *>   AT END                          讀完檔案時要另外標記
       *> 記得：檔案「關閉（CLOSE）」時才會真正寫到磁碟。
       *> ============================================================

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT LEDGER-FILE ASSIGN TO "ledger.dat".

       DATA DIVISION.
       FILE SECTION.
       *> 這一題的記錄就是一整行固定長度的文字，
       *> 所以記錄名稱沿用檔案名稱 LEDGER-FILE。
       FD  LEDGER-FILE.
       01  LEDGER-FILE   PIC X(12).

       WORKING-STORAGE SECTION.
       01  WS-EOF        PIC X VALUE "N".
       01  WS-COUNT      PIC 9(3) VALUE 0.
       01  WS-LINE       PIC X(12).

       PROCEDURE DIVISION.

       WRITE-LEDGER.
           OPEN OUTPUT LEDGER-FILE.
           MOVE "A01100.00   " TO LEDGER-FILE
           WRITE LEDGER-FILE
           MOVE "B02250.50   " TO LEDGER-FILE
           WRITE LEDGER-FILE
           MOVE "C03 99.99   " TO LEDGER-FILE
           WRITE LEDGER-FILE
           *> TODO: 資料還留在記憶體裡，磁碟上的 ledger.dat 是空的。
           *>       請在寫完之後加上 CLOSE LEDGER-FILE.，
           *>       檔案才會真正寫出來。
           EXIT.

       READ-LEDGER.
           OPEN INPUT LEDGER-FILE.
           MOVE "N" TO WS-EOF
           MOVE 0 TO WS-COUNT
           *> TODO: 檔案讀完之後 READ 會出錯，
           *>       必須用 AT END 標記「已經讀完了」。
           *>       請補上 AT END MOVE "Y" TO WS-EOF 與 END-READ，
           *>       並在迴圈裡真的讀到資料時把 WS-COUNT 加一。
           PERFORM UNTIL WS-EOF = "Y"
               READ LEDGER-FILE INTO WS-LINE
               IF WS-EOF = "N"
                   ADD 1 TO WS-COUNT
               END-IF
           END-PERFORM
           CLOSE LEDGER-FILE.
           EXIT.