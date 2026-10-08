# 01 打招呼 ★

主題：段落、字串、`STRING`

## 學習目標

完成這一題後，你會：

- 看懂一支 COBOL 程式的基本骨架：`IDENTIFICATION`、`DATA`、`PROCEDURE` 三個 DIVISION。
- 知道「段落」是什麼，以及檢查器怎麼用 `PERFORM` 呼叫你寫的段落。
- 會用 `STRING … DELIMITED BY SIZE … INTO …` 把好幾段文字接成一句話。
- 了解 `PIC X(n)` 文字欄位「靠左對齊、右邊補空白」的特性。

## 這題要做什麼

要修改的檔案：`Hello.cbl`（不要改 `HelloTest.cbl`）

| 段落 | 完成後應該達成 |
| --- | --- |
| `GET-GREET` | `WS-RESULT` 的內容是 `Hello, Coblings!` |
| `SHOW-GREET` | 已經寫好，不用改；它會把 `WS-RESULT` 印出來 |

這題還會比對 `DISPLAY` 的輸出，畫面上要剛好印出一行 `Hello, Coblings!`（見 `expected.txt`）。

規則：段落名稱不要改，檢查器是用名字呼叫它們的。

## 觀念講解

### 1. 程式的骨架

```cobol
IDENTIFICATION DIVISION.        *> 身分：程式叫什麼名字
PROGRAM-ID. DEMO.

DATA DIVISION.                  *> 資料：宣告會用到的變數
WORKING-STORAGE SECTION.
01  WS-CITY   PIC X(10).

PROCEDURE DIVISION.             *> 程序：真正要執行的敘述
SAY-CITY.                       *> ← 這是一個「段落」
    MOVE "Tainan" TO WS-CITY
    DISPLAY WS-CITY.
```

- `*>` 之後到行尾都是註解。
- 段落名稱寫在行首、以句點結尾。下一個段落名稱出現之前的敘述都屬於這個段落。
- 檢查器執行 `PERFORM SAY-CITY` 時，只會跑這一個段落，跑完就回到檢查器。

### 2. 文字欄位：`PIC X(n)`

`PIC X(10)` 代表「可以放 10 個任意字元」。放進去的字串比較短時，**右邊補空白**；比較長時，**右邊的字被截掉**。

```text
MOVE "Tainan" TO WS-CITY      →  "Tainan    "（後面補 4 個空白）
```

### 3. 用 `STRING` 接字串

```cobol
STRING "Good"    DELIMITED BY SIZE
       " "       DELIMITED BY SIZE
       "morning" DELIMITED BY SIZE
   INTO WS-TEXT
END-STRING
```

- 來源會**依照寫的順序**一段一段接到 `INTO` 的欄位裡。
- `DELIMITED BY SIZE`：把這個來源「整個」接上去。
- 標點、空白也是字元，想讓它們出現在結果裡，就得自己寫成一段來源，`STRING` 不會幫你補。
- `STRING` 不會清掉目標欄位原本的內容，所以通常會先 `MOVE SPACES TO 目標`。

## 常見錯誤

- **只看到 `Hello` 或字黏在一起**：`STRING` 只會接你列出來的東西，標點和空白要自己加。
- **字串中間多出一堆空白**：來源如果是 `PIC X(n)` 欄位，`DELIMITED BY SIZE` 會連補位的空白一起接進去。要停在第一個空白，可以改用 `DELIMITED BY " "`。
- **大小寫或標點不同**：斷言是逐字比較的，`hello` 和 `Hello`、全形和半形的逗號都算不同。
- **改了段落名稱**：檢查器會找不到段落，直接報錯。

## 操作步驟

1. 在專案根目錄執行 `.\coblings.cmd run 01_hello`（Linux／macOS：`./coblings.sh run 01_hello`），開始監看這一題。
2. 用編輯器打開本資料夾的 `Hello.cbl`，照「這題要做什麼」修改。**不要改 `HelloTest.cbl`**，它是這一題的驗收標準。
3. 存檔後系統會自動檢查：
   - **解析錯誤**：訊息裡有檔名和行號，照著修正語法。
   - **期望／實際不符**：看斷言的標籤，找出是哪個段落的結果不對。
   - **全部通過**：自動跳到下一題。
4. 卡關時執行 `.\coblings.cmd hint 01_hello` 看提示。
5. 改亂了想重來，執行 `.\coblings.cmd reset 01_hello` 還原成原題（你改過的版本會備份到 `.coblings/backup/`）。
