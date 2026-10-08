# Coblings

**透過修正有問題的 COBOL 程式來學習 COBOL。**

這是一個「改到通過為止」的練習系統（用法與 Rustlings／Javalings 一樣）：
每一題都是一個故意寫壞的小程式，你把它改到能執行、而且通過驗收測試，
系統就自動跳到下一題。

```text
Coblings 0.1.0
透過修正有問題的 COBOL 程式來學習 COBOL。

目前進度: 3/24 完成

目前練習: 05_numeric_edit — 數字編輯
  檔案: C:\...\coblings\exercises\05_numeric_edit\Edit.cbl
  指令: run 開始監看（存檔自動檢查）/ hint 看提示 / list 看全部
```

## 為什麼不用裝 GnuCOBOL，也不用 COBOL 外掛？

因為這個系統**自帶了一個用 Python 寫的 COBOL 直譯器**。

| 你需要準備的 | 說明 |
| --- | --- |
| Python 3.11 以上 | 唯一的執行環境需求 |
| 一個文字編輯器 | 任何都行；VS Code 對 `.cbl` 有內建語法高亮，不需要裝外掛 |

| 你**不需要**的 | |
| --- | --- |
| GnuCOBOL／任何 COBOL 編譯器 | 題目是用內建直譯器解析與執行的 |
| COBOL 編輯器外掛 | 語法高亮用編輯器內建的就好 |
| 任何第三方套件 | 只用 Python 標準庫 |

## 快速開始

```bash
# Windows
.\coblings.cmd

# Linux / macOS（第一次要先 chmod +x coblings.sh）
./coblings.sh
```

第一次執行會顯示歡迎畫面。接著：

```bash
.\coblings.cmd run        # 監看目前這題，存檔就自動檢查，通過後跳下一題
.\coblings.cmd hint       # 看這題的提示
.\coblings.cmd list       # 看看全部題目與進度
.\coblings.cmd guide      # 新手教學
```

沒看懂指令就跑 `.\coblings.cmd help`。

## 指令一覽

| 指令 | 說明 |
| --- | --- |
| `run [id]` | 監看練習檔，存檔就自動檢查，通過後跟到下一題 |
| `verify [id]` | 只檢查一次並回傳 exit code（適合 CI） |
| `list` | 列出所有練習與進度 |
| `hint [id]` | 顯示提示 |
| `reset [id]` | 將練習標記為未完成，並把原始碼還原成原題 |
| `reset --all` | 清除所有進度（不還原原始碼） |
| `guide` | 新手教學 |
| `help` / `version` | 說明與版本 |

全域選項：`--no-color`（關閉色彩）、`--dir <路徑>`（指定練習目錄）。

## 題目一覽（24 題）

| # | 練習 id | 主題 | 難度 |
| --- | --- | --- | --- |
| 01 | [`01_hello`](exercises/01_hello/README.md) | 段落與 `STRING` | ★ |
| 02 | [`02_variables`](exercises/02_variables/README.md) | 資料項目與 `MOVE` | ★ |
| 03 | [`03_operators`](exercises/03_operators/README.md) | 四則運算與 `GIVING` | ★ |
| 04 | [`04_picture`](exercises/04_picture/README.md) | `PICTURE`、截斷與 `ON SIZE ERROR` | ★★ |
| 05 | [`05_numeric_edit`](exercises/05_numeric_edit/README.md) | 數字編輯（`ZZZ9.99`…） | ★★ |
| 06 | [`06_string_string`](exercises/06_string_string/README.md) | `STRING`、`POINTER`、`ON OVERFLOW` | ★★ |
| 07 | [`07_string_inspect`](exercises/07_string_inspect/README.md) | `INSPECT` 的三種用法 | ★ |
| 08 | [`08_if_else`](exercises/08_if_else/README.md) | `IF`／`ELSE` 與 `88` 條件名稱 | ★ |
| 09 | [`09_evaluate`](exercises/09_evaluate/README.md) | `EVALUATE` 多分支 | ★ |
| 10 | [`10_loop_times`](exercises/10_loop_times/README.md) | `PERFORM n TIMES`／`UNTIL` | ★★ |
| 11 | [`11_loop_varying`](exercises/11_loop_varying/README.md) | `PERFORM VARYING` | ★★ |
| 12 | [`12_loop_nested`](exercises/12_loop_nested/README.md) | 巢狀 `AFTER` | ★★★ |
| 13 | [`13_tables`](exercises/13_tables/README.md) | `OCCURS` 表格與下標 | ★★ |
| 14 | [`14_table_2d`](exercises/14_table_2d/README.md) | 二維表格 | ★★★ |
| 15 | [`15_paragraphs`](exercises/15_paragraphs/README.md) | 段落與 `PERFORM … THRU` | ★★ |
| 16 | [`16_go_to`](exercises/16_go_to/README.md) | `GO TO` 與 `DEPENDING ON` | ★★ |
| 17 | [`17_intrinsics`](exercises/17_intrinsics/README.md) | 內建函式 | ★★ |
| 18 | [`18_comp`](exercises/18_comp/README.md) | `COMP`／`COMP-3`／`INDEX` 與 `SET` | ★★★ |
| 19 | [`19_math`](exercises/19_math/README.md) | `ROUNDED` 與溢位處理 | ★★ |
| 20 | [`20_unstring`](exercises/20_unstring/README.md) | `UNSTRING` 拆解字串 | ★★ |
| 21 | [`21_search`](exercises/21_search/README.md) | `SEARCH` 查表 | ★★ |
| 22 | [`22_file_io`](exercises/22_file_io/README.md) | 順序檔 `OPEN`／`READ`／`WRITE` | ★★★ |
| 23 | [`23_error`](exercises/23_error/README.md) | 執行期錯誤與 `ON SIZE ERROR` | ★★★ |
| 24 | [`24_final`](exercises/24_final/README.md) | 綜合演練 | ★★★★ |

## 題目是怎麼檢查的？

每題有兩個檔案：

* `NN_xxx/YourName.cbl` — **你要改的就是這個**
* `NN_xxx/YourNameTest.cbl` — 驗收測試，不要改
* `NN_xxx/README.md` — 這一題的說明文件（學習目標、要做什麼、觀念講解、常見錯誤、操作步驟），**動手前先讀**

檢查分兩個階段：

1. **解析**：用內建直譯器解析你的程式與測試，語法錯誤會直接報出檔名與行號。
2. **執行**：在獨立行程執行測試。測試會 `PERFORM` 你寫的段落，然後斷言結果。
   全部斷言通過時，測試呼叫 `COBLINGS-DONE` 印出通過標記。

檢查器提供了這些斷言內建（學生不用寫，但你寫題目時會用到）：

| 內建 | 用途 |
| --- | --- |
| `COBLINGS-EXPECT-EQUALS` | 相等（文字會先補空白再比） |
| `COBLINGS-EXPECT-TRUE` / `-FALSE` | 布林值 |
| `COBLINGS-EXPECT-CLOSE` | 浮點數接近 |
| `COBLINGS-EXPECT-PRESENT` | 值不是全空白 |
| `COBLINGS-EXPECT-LENGTH` | 長度 |
| `COBLINGS-EXPECT-ERROR` / `-NO-ERROR` | 執行期錯誤的有無 |
| `COBLINGS-DONE` | 印出通過標記（**檢查器必須呼叫**） |

題目也可以放一個 `expected.txt`，用來比對程式的 `DISPLAY` 輸出。

## 進度存在哪？

`<專案根目錄>/.coblings/progress.txt`。刪掉就重新開始。
`reset <id>` 會把某一題還原成原題（你改過的版本會備份到 `.coblings/backup/`）。
`reset --all` 只清除進度，不會動任何原始碼。

## 想寫題目？

看 [`docs/authoring.md`](docs/authoring.md)。寫完跑一次：

```bash
python tools/check_exercise.py 01_hello      # 單題：原題必敗、解答必過
python tools/selftest.py                    # 全部題目
```

## 規格文件

* [`docs/spec/core-spec.md`](docs/spec/core-spec.md) — 系統的行為契約（與語言無關）
* [`docs/spec/profile-cobol.md`](docs/spec/profile-cobol.md) — COBOL 實作規格（含與核心規格的所有差異）
* [`docs/uml/`](docs/uml/) — 架構圖（PlantUML：套件圖、類別圖、時序圖、活動圖、狀態機；含 Mermaid 預覽）

## 專案結構

```text
coblings.cmd / coblings.sh     啟動腳本（含增量建置）
src/coblings/                  CLI（Python 3，僅用標準庫）
  main.py                      指令列介面與各指令
  model.py                     練習載入、進度管理
  verify.py                    兩階段檢查（解析 + 執行）
  console.py                   色彩、編碼、表格
  json_lite.py                 JSON 子集解析器
  cobol/                       COBOL 直譯器
    lexer.py nodes.py
    pic.py                     PICTURE 與數值轉換
    layout.py                  資料版面（OCCURS／REDEFINES／88）
    parser/                  語法分析器（base／data／expr／procedure／statements）
    interp/                  執行期（core／values／expr／arith／flow／datastmt／files）
    builtins.py                斷言函式庫
    runner.py                  獨立行程的進入點
exercises/                     題目
solutions/                     參考解答
tools/                         build.py / selftest.py / check_exercise.py
tests/                         直譯器的單元測試（117 個案例）
docs/                          authoring.md、spec/、uml/
```

## 目前的 COBOL 子集

資料描述：層級 `01/05/10/49/66/77/88`、`PICTURE`（`X A N 9 V P S Z * B 0 , . + - CR DB $` 與括號重複）、
`USAGE`（`DISPLAY`／`COMP`／`COMP-3`／`COMP-1`／`COMP-2`／`INDEX`）、
`VALUE`、`OCCURS … DEPENDING ON`、`REDEFINES`、`SIGN IS SEPARATE`、`JUSTIFIED`、`BLANK WHEN ZERO`

敘述：`DISPLAY`、`MOVE`、`COMPUTE`、`ADD`、`SUBTRACT`、`MULTIPLY`、`DIVIDE`、
`IF`／`ELSE`、`EVALUATE`、`PERFORM`（`THROUGH`／`n TIMES`／`UNTIL`／`VARYING`／`AFTER`）、
`GO TO`、`STOP RUN`、`GOBACK`、`EXIT`、`SET`、`INITIALIZE`、`INSPECT`、
`STRING`、`UNSTRING`、`SEARCH`、`CALL`、`ACCEPT`、`OPEN`／`CLOSE`／`READ`／`WRITE`、`DELETE`、`REWRITE`、`SORT`、`MERGE`、`START`

內建函式：`LENGTH`、`NUMVAL`、`TRIM`、`UPPER-CASE`、`LOWER-CASE`、`MOD`、`MAX`、`MIN`、
`ORD`、`CHAR`、`SUM`、`INTEGER`、`PART`、`REVERSE`、`ABS`、`SQRT`、`RANDOM`

不支援：`SCREEN SECTION`、`REPORT`、`INPUT／OUTPUT PROCEDURE`、`RELEASE／RETURN`、`FUNCTION CURRENT-DATE`、隨機存取中的重複鍵檢查。
