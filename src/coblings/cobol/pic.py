"""PICTURE 子句的解析、型別判定、數值轉換與編輯輸出。

這個模組決定了直譯器的資料模型（約定見 docs/spec/profile-cobol.md 第 5 章）：

* **字元數**：一個 COBOL character 等於一個 Unicode 碼點。因此 ``PIC X(20)`` 可以
  放 20 個中文字，不會因為底層編碼而被截斷。
* **數值**：以 ``decimal.Decimal`` 保存，精度與小數位數由 PICTURE 決定。
  正負號獨立保存，輸出時再依 USAGE 決定要不要寫出符號。
* **文字**：以 Python ``str`` 保存，長度由 PICTURE 的字元位置決定。

支援的 PICTURE 字元：

=============== ==============================================================
字元              意義
=============== ==============================================================
``X`` ``A`` ``N`` 文數字（alphanumeric）
``9`` ``1``      數字位置
``V``             小數點位置
``P``             隱含小數位置（scale position）
``S``             符號
``Z`` ``*``       前導零抑制（``*`` 用 ``*`` 取代空白）
``B`` ``0`` ``/`` 固定插入字元
``,`` ``.``       浮動插入字元（逗號為千分位，句點為小數點）
``+`` ``-``       符號插入
``CR`` ``DB``     尾端符號
``$``             貨幣符號（位置會填入貨幣符號）
``E``             科學記號浮點（搭配 ``USAGE FLOAT`` 之類的浮點 USAGE）
=============== ==============================================================
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import (
    Decimal,
    InvalidOperation,
    ROUND_DOWN,
    ROUND_HALF_UP,
    localcontext,
)

from . import limits
from .errors import SyntaxError_


#: 文數字類字元
ALPHA_CHARS = frozenset("XAN")
#: 會佔用一個數字位置的字元
DIGIT_CHARS = frozenset("91")
#: 浮動編輯字元（本身不佔數字位置）
FLOATING_INSERTION = frozenset(",.")
#: 固定插入字元（本身不佔數字位置）
FIXED_INSERTION = frozenset({"B", "0", "/", "-", "+", "CR", "DB"})

#: COBOL 的分類（category）
CAT_NUMERIC = "numeric"
CAT_NUMERIC_EDITED = "numeric-edited"
CAT_ALPHANUMERIC = "alphanumeric"


@dataclass(frozen=True)
class Unit:
    """PICTURE 字串中的一個單位：字元與重複次數。"""

    ch: str
    count: int = 1


_TOKEN = re.compile(
    r"""
    (?P<char>[\.E])
    | (?P<sym>[XAZ9SVPB0/,\+\*$\-1])
    | (?P<word>CR|DB)
    | (?P<open>\()
    | (?P<close>\))
    """,
    re.VERBOSE | re.IGNORECASE,
)


def _tokenize(text: str) -> list[Unit]:
    """把 PICTURE 字串切成 :class:`Unit` 清單。"""
    units: list[Unit] = []
    i = 0
    n = len(text)
    while i < n:
        m = _TOKEN.match(text, i)
        if m is None:
            raise SyntaxError_(f"PICTURE 無法解析的字元 '{text[i]}'（位置 {i}）")
        i = m.end()
        if m.group("open") or m.group("close"):
            raise SyntaxError_(f"PICTURE 中的括號必須接在字元後面：{text}", column=i)
        if m.group("word"):
            units.append(Unit(m.group("word").upper(), 1))
        elif m.group("char") == ".":
            units.append(Unit(".", 1))
        elif m.group("char") == "E":
            units.append(Unit("E", 1))
        else:
            units.append(Unit(m.group("sym").upper(), 1))
        # 括號內的重複次數
        if i < n and text[i] == "(":
            end = text.find(")", i)
            if end < 0:
                raise SyntaxError_(f"PICTURE 的括號沒有關閉：{text}", column=i)
            digits = text[i + 1 : end].strip()
            if not digits.isdigit():
                raise SyntaxError_(f"PICTURE 的重複次數必須是數字：{text[i:end + 1]}", column=i)
            count = int(digits)
            if count > limits.MAX_PIC_REPEAT:
                raise SyntaxError_(
                    f"PICTURE 的重複次數 {count} 太大（上限 {limits.MAX_PIC_REPEAT}）", column=i
                )
            units[-1] = Unit(units[-1].ch, count)
            i = end + 1
    return units


class Pic:
    """解析後的 PICTURE 子句。"""

    __slots__ = (
        "text",
        "units",
        "category",
        "int_digits",
        "dec_digits",
        "char_count",
        "has_sign",
        "sign_separate",
        "floating",
        "suppress_all",
        "positions",
    )

    def __init__(
        self,
        text: str,
        usage: str = "DISPLAY",
        sign_separate: bool = False,
    ) -> None:
        self.text = text.strip().upper()
        self.units = _tokenize(self.text)
        self.sign_separate = sign_separate

        units = self.units
        has_alpha = any(u.ch in ALPHA_CHARS for u in units)
        has_digit = any(u.ch in DIGIT_CHARS for u in units)
        editing = any(
            u.ch in FLOATING_INSERTION or u.ch in FIXED_INSERTION or u.ch in "Z*$"
            for u in units
        )
        self.has_sign = any(u.ch == "S" for u in units)
        self.floating = usage in ("COMP-1", "COMP-2") or any(u.ch == "E" for u in units)

        if has_alpha:
            self.category = CAT_ALPHANUMERIC
            self.char_count = sum(u.count for u in units if u.ch in ALPHA_CHARS)
            self.int_digits = 0
            self.dec_digits = 0
            self.positions = []
        elif has_digit and editing:
            self.category = CAT_NUMERIC_EDITED
            self.int_digits, self.dec_digits, self.char_count, self.positions = self._analyze()
        elif has_digit:
            self.category = CAT_NUMERIC
            self._analyze_numeric()
        else:
            raise SyntaxError_(f"PICTURE '{text}' 沒有任何數字或文數字位置：{text}")

    # ------------------------------------------------------------------ 分析

    def _analyze_numeric(self) -> None:
        """分析未編輯的數字 PICTURE（含 V 與 P）。"""
        before_v: list[Unit] = []
        after_v: list[Unit] = []
        seen_v = False
        for u in self.units:
            ch = u.ch
            if ch == "V":
                seen_v = True
            elif ch == "S":
                continue
            elif ch == "P":
                (after_v if seen_v else before_v).append(u)
            elif ch in DIGIT_CHARS:
                (after_v if seen_v else before_v).append(u)
            elif ch == "E":
                continue
            else:
                raise SyntaxError_(f"PICTURE '{self.text}' 的字元 '{ch}' 不能出現在數字欄位")
        self.int_digits = sum(u.count for u in before_v if u.ch in DIGIT_CHARS)
        self.int_digits += sum(u.count for u in before_v if u.ch == "P")
        self.dec_digits = sum(u.count for u in after_v if u.ch in DIGIT_CHARS)
        self.dec_digits += sum(u.count for u in after_v if u.ch == "P")
        self.char_count = self.int_digits + self.dec_digits

    def _analyze(self) -> tuple[int, int, int, list[tuple[str, bool]]]:
        """分析數字編輯 PICTURE。

        會產生一個 position 清單，每個元素是 ``(字元, 是否佔數字位置)``，
        輸出編輯字串時依此清單逐位置填入。
        """
        positions: list[tuple[str, bool]] = []
        for u in self.units:
            ch = u.ch
            if ch == "S":
                continue
            if ch in DIGIT_CHARS or ch in "Z*$":
                positions.extend((ch, True) for _ in range(u.count))
            elif ch in ("B", "0", "/", ",", ".", "+", "-", "CR", "DB", "P", "E"):
                positions.extend((ch, False) for _ in range(u.count))
            else:
                raise SyntaxError_(f"PICTURE '{self.text}' 的字元 '{ch}' 不能出現在編輯欄位")

        # 小數點：句點（若是浮動）或 COMMA 當小數點使用時的位置
        dot_index = -1
        for idx, (ch, _) in enumerate(positions):
            if ch == ".":
                dot_index = idx
                break
        if dot_index < 0:
            int_digits = sum(1 for _, is_digit in positions if is_digit)
            dec_digits = 0
        else:
            int_digits = sum(1 for _, is_digit in positions[:dot_index] if is_digit)
            dec_digits = sum(1 for _, is_digit in positions[dot_index + 1 :] if is_digit)
        char_count = len(positions)
        self.suppress_all = bool(positions) and all(ch in "-CRDB" for ch, _ in positions)
        return int_digits, dec_digits, char_count, positions

    # ------------------------------------------------------------------ 查詢

    @property
    def total_digits(self) -> int:
        """可以容納的數字總位數。"""
        if self.category == CAT_NUMERIC:
            return self.int_digits + self.dec_digits
        if self.category == CAT_NUMERIC_EDITED:
            return self.int_digits + self.dec_digits
        return self.char_count

    def storage_size(self, usage: str | None = None) -> int:
        """以字元（碼點）為單位，回傳儲存單元需要的大小。"""
        if self.category == CAT_ALPHANUMERIC:
            return self.char_count
        digits = self.total_digits
        use = (usage or "DISPLAY").upper()
        if use in ("COMP-1",):
            return 4
        if use in ("COMP-2",):
            return 8
        if use == "COMP-3":
            return digits // 2 + 1
        if use in ("COMP", "BINARY", "COMPUTATIONAL", "COMPUTATIONAL-3", "COMPUTATIONAL-4", "COMPUTATIONAL-5"):
            if digits <= 4:
                return 2
            if digits <= 9:
                return 4
            return 8
        # DISPLAY（含 SIGN TRAILING 的符號位置）
        return digits + (1 if (self.has_sign and not self.sign_separate) else 0)

    def __repr__(self) -> str:  # pragma: no cover - 除錯用
        return f"Pic({self.text!r}, {self.category}, int={self.int_digits}, dec={self.dec_digits})"

    # ------------------------------------------------------------------ 轉換

    @property
    def is_signed(self) -> bool:
        """欄位能不能保存負數（無號欄位只保存絕對值）。"""
        if self.floating:
            return True
        if self.category == CAT_NUMERIC_EDITED:
            return any(ch in ("+", "-", "CR", "DB") for ch, _ in self.positions)
        return self.has_sign

    def _scaled_digits(self, value: Decimal, rounding: bool) -> Decimal:
        """把數值放大成「只剩整數位」的形式（小數位先截斷或捨入）。"""
        with localcontext() as context:
            context.prec = limits.NUMERIC_PRECISION
            return value.scaleb(self.dec_digits).to_integral_value(
                rounding=ROUND_HALF_UP if rounding else ROUND_DOWN
            )

    def quantize(self, value: Decimal, rounding: bool = False) -> Decimal:
        """把數值截斷／捨入成這個欄位能容納的位數。

        COBOL 的預設行為是「截斷」：數字欄位放不下時，多餘的高位數字直接丟掉
        （這與 GnuCOBOL 的預設 ``truncate`` 相同）。溢位與否由
        :meth:`overflows` 判斷，供 ``ON SIZE ERROR`` 使用。
        無號欄位只保存絕對值（``PIC 9`` 收到 -5 會存成 5）。
        """
        if self.category == CAT_ALPHANUMERIC:
            return value
        digits = self.total_digits
        if digits <= 0:
            return Decimal(0)
        if value < 0 and not self.is_signed:
            value = -value
        with localcontext() as context:
            context.prec = limits.NUMERIC_PRECISION
            shifted = self._scaled_digits(value, rounding)
            # 整數位與小數位合起來最多 total_digits 個數字，多的高位數字丟掉
            limit = Decimal(1).scaleb(digits)
            if abs(shifted) >= limit:
                kept = abs(shifted) % limit
                shifted = -kept if shifted < 0 else kept
            return shifted.scaleb(-self.dec_digits)

    def overflows(self, value: Decimal, rounding: bool = False) -> bool:
        """這個數值放不進欄位（供 ``ON SIZE ERROR`` 使用）。

        依小數位截斷／捨入之後，整數部分超過 ``int_digits`` 位才算溢位。
        """
        if self.category == CAT_ALPHANUMERIC:
            return False
        digits = self.total_digits
        if digits <= 0:
            return True
        return abs(self._scaled_digits(value, rounding)) >= Decimal(1).scaleb(digits)

    def from_string(self, text: str, rounding: bool = False) -> Decimal:
        """把字串轉成數值（帶小數點、正負號或編輯字元皆可）。"""
        cleaned = text.strip()
        if cleaned == "":
            return Decimal(0)
        cleaned = cleaned.replace(",", "")
        sign = Decimal(1)
        if cleaned.startswith("+"):
            cleaned = cleaned[1:]
        elif cleaned.startswith("-"):
            sign = Decimal(-1)
            cleaned = cleaned[1:]
        cleaned = cleaned.lstrip("$").rstrip("$").strip()
        digits = "".join(ch for ch in cleaned if ch.isdigit())
        fraction = ""
        if "." in cleaned:
            fraction = "".join(ch for ch in cleaned.split(".", 1)[1] if ch.isdigit())
        if digits == "" and fraction == "":
            return Decimal(0)
        core = (digits or "0") + ("." + fraction if fraction else "")
        try:
            return sign * Decimal(core)
        except InvalidOperation:  # pragma: no cover - 防禦性
            return Decimal(0)

    def to_text(self, value: Decimal) -> str:
        """把數值輸出成這個欄位的字串表示（含編輯字元）。"""
        if self.category == CAT_ALPHANUMERIC:  # pragma: no cover - 呼叫端已判斷
            return str(value)
        if self.category == CAT_NUMERIC:
            return self._numeric_to_text(value)
        return self._edited_to_text(value)

    def _numeric_to_text(self, value: Decimal) -> str:
        if self.category == CAT_NUMERIC and self.int_digits == 0 and self.dec_digits == 0:
            return ""
        return format_decimal(value, self.dec_digits)

    def _edited_to_text(self, value: Decimal) -> str:
        """產生數字編輯欄位的字串。"""
        negative = value < 0
        magnitude = abs(value)
        int_text = format_decimal(magnitude.to_integral_value(rounding=ROUND_DOWN), 0)
        dec_text = ""
        if self.dec_digits > 0:
            whole = format_decimal(magnitude, 0)
            decimal_part = format_decimal(magnitude, self.dec_digits)
            if "." in decimal_part:
                dec_text = decimal_part.split(".", 1)[1]
            del whole
        digits = (int_text + dec_text).rjust(self.int_digits + self.dec_digits, "0")

        def _suppressed(upto: int) -> bool:
            """第 upto 個數字位置（含）之前是否全是前導零。"""
            return upto < self.int_digits and all(
                d == "0" for d in digits[: upto + 1]
            )

        # 依 picture 的數字位置填入
        out: list[str] = []
        dollar_leading: list[int] = []
        digit_index = 0
        int_seen = 0
        positions = self.positions
        for idx, (ch, is_digit) in enumerate(positions):
            if not is_digit:
                if ch == ".":
                    out.append(".")
                elif ch == ",":
                    # 左邊的整數位全是前導零時，逗號跟著一起被抑制
                    out.append(" " if _suppressed(int_seen - 1) else ",")
                elif ch == "B":
                    out.append(" ")
                elif ch == "0":
                    out.append("0")
                elif ch == "/":
                    out.append("/")
                elif ch in "+-":
                    out.append(ch if negative else " ")
                elif ch in ("CR", "DB"):
                    if ch == "CR":
                        out.append("CR" if negative else "  ")
                    else:
                        out.append("DB" if negative else "  ")
                elif ch == "P":
                    out.append("0")
                else:
                    out.append(" ")
                continue
            # 是數字位置
            if ch == "Z":
                char = digits[digit_index] if digit_index < len(digits) else "0"
                if _suppressed(digit_index) and char == "0":
                    char = " "
                out.append(char)
            elif ch == "*":
                char = digits[digit_index] if digit_index < len(digits) else "0"
                if _suppressed(digit_index) and char == "0":
                    char = "*"
                out.append(char)
            elif ch == "$":
                char = digits[digit_index] if digit_index < len(digits) else "0"
                if _suppressed(digit_index):
                    out.append("$")
                    dollar_leading.append(len(out) - 1)
                else:
                    out.append(char)
            else:  # 9 / 1
                out.append(digits[digit_index] if digit_index < len(digits) else "0")
            digit_index += 1
            int_seen += 1

        # 浮動的 $ 只留最右邊一個，左邊的改成空白（例如 $$,$$9.99 的 12.5 → "    $12.50"）
        for position in dollar_leading[:-1]:
            out[position] = " "

        text = "".join(out)
        if self.suppress_all:
            # 全部由正負號組成的欄位：正數不顯示任何符號
            text = text.rstrip()
        return text


def format_decimal(value: Decimal, dec: int) -> str:
    """把數值格式化為固定小數位數的字串。"""
    exp = Decimal(1).scaleb(-dec)
    with localcontext() as context:
        context.prec = limits.NUMERIC_PRECISION
        try:
            value = value.quantize(exp, rounding=ROUND_HALF_UP)
        except InvalidOperation:  # pragma: no cover - 防禦性
            value = Decimal(int(value))
    text = format(value, "f")
    if dec == 0:
        if text.startswith("-") and Decimal(text) == 0:
            return text[1:]
        return text
    return text


def parse_picture(text: str, usage: str = "DISPLAY", sign_separate: bool = False) -> Pic:
    """PICTURE 子句的進入點。"""
    return Pic(text, usage=usage, sign_separate=sign_separate)