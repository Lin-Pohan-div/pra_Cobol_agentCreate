"""直譯器的資源上限與數值精度。

這些上限避免錯誤（或惡意）的 COBOL 程式耗盡系統資源。放在 ``cobol`` 套件裡，
讓直譯器不必依賴 CLI 層的 ``coblings.constants``。
"""

from __future__ import annotations

#: 段落跳轉次數上限（防止 GO TO 無窮迴圈）
MAX_PARAGRAPH_JUMPS = 5_000_000

#: PICTURE 重複次數上限（如 X(999999)）
MAX_PIC_REPEAT = 100_000

#: OCCURS 次數上限
MAX_OCCURS = 100_000

#: 整支程式的基本項目儲存格總數上限（巢狀 OCCURS 的乘積也算在內）
MAX_STORAGE_CELLS = 1_000_000

#: 整支程式的資料區總位元組上限
MAX_STORAGE_BYTES = 16_000_000

#: 冪運算指數上限（如 2 ** 999999）
MAX_POWER_EXPONENT = 10_000

#: FACTORIAL 引數上限
MAX_FACTORIAL_ARG = 1_000

#: FACTORIAL 結果上限（超過則報錯）
MAX_FACTORIAL_RESULT = 10**18

#: 單一檔案最多保留幾筆紀錄
MAX_FILE_RECORDS = 50_000

#: 單一檔案最多讀幾行
MAX_INPUT_LINES = 100_000

#: 失敗訊息裡最多展開幾個表格元素
MAX_RENDERED_ELEMENTS = 100

#: 執行期 Decimal 運算的精度（位數）
NUMERIC_PRECISION = 60
