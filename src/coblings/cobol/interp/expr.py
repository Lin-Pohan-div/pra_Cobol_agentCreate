"""直譯器求值層：運算式、條件、內建函式。"""
from __future__ import annotations

from decimal import Decimal, DivisionByZero, InvalidOperation, localcontext

from .. import limits
from ..errors import RuntimeError_
from ..pic import CAT_ALPHANUMERIC, CAT_NUMERIC
from .util import _apply, _factorial
from .values import Fill, Reference


class ExprMixin:
    """運算式與條件求值。"""
    def eval(self, node):
        """求值一個運算式節點。"""
        kind = node.kind
        if kind == "literal":
            return node.value
        if kind == "figurative":
            if node.name == "ALL":
                # ALL "樣式"：重複樣式填滿接收端，長度由使用的地方決定
                return Fill(str(node.pattern) if node.pattern else " ")
            return self._figurative_value(None, node.name)
        if kind == "identifier":
            return self.get_reference(self.resolve(node))
        if kind == "unary":
            value = self.to_decimal(self.eval(node.operand))
            return -value if node.op == "-" else value
        if kind == "binary":
            return self.eval_binary(node)
        if kind == "function":
            return self.eval_function(node)
        if kind == "logical":
            return self.eval_condition(node)
        if kind in (
            "relation", "class_condition", "sign_condition",
            "cond_true", "cond_false", "cond_any", "cond_forever",
        ):
            return self.eval_condition(node)
        raise RuntimeError_(f"不支援的運算式：{kind}")

    def eval_binary(self, node):
        op = node.op
        left = self.to_decimal(self.eval(node.left))
        right = self.to_decimal(self.eval(node.right))
        with localcontext() as ctx:
            ctx.prec = 40
            try:
                if op == "+":
                    return left + right
                if op == "-":
                    return left - right
                if op == "*":
                    return left * right
                if op == "/":
                    if right == 0:
                        raise RuntimeError_("DIVIDE BY ZERO：除以零")
                    return left / right
                if op == "**":
                    exponent = int(right)
                    if abs(exponent) > limits.MAX_POWER_EXPONENT:
                        raise RuntimeError_(
                            f"** 的指數 {exponent} 太大，超出可計算範圍"
                        )
                    return Decimal(left) ** exponent
            except DivisionByZero:
                raise RuntimeError_("DIVIDE BY ZERO：除以零") from None
            except InvalidOperation:
                raise RuntimeError_(f"算式無法計算：{left} {op} {right}") from None
        raise RuntimeError_(f"不支援的運算子 {op}")

    def eval_function(self, node):
        name = node.name.upper()
        if name == "LENGTH" and node.args and node.args[0].kind == "identifier":
            # 不先取值：群組項目沒有單一值，但仍然有長度
            return Decimal(self._length_of(self.resolve(node.args[0])))
        args = [self.eval(a) for a in node.args]

        def need(count: int, what: str) -> None:
            if len(args) < count:
                raise RuntimeError_(f"FUNCTION {name} 至少需要 {what}")

        if name == "LENGTH":
            need(1, "一個引數")
            return Decimal(len(self._raw_text(args[0])))
        if name == "NUMVAL":
            need(1, "一個引數")
            text = self._raw_text(args[0])
            if len(args) > 1:
                text = text[: self.to_int(args[1])]
            try:
                return Decimal(text.strip() or "0")
            except InvalidOperation:
                raise RuntimeError_(f"NUMVAL 無法轉換 '{text}'") from None
        if name == "NUMVAL-C":
            need(1, "一個引數")
            return self._numval_c(self._raw_text(args[0]))
        if name in ("MAX", "MIN"):
            need(1, "一個引數")
            numbers = [self.to_decimal(a) for a in args]
            return (max if name == "MAX" else min)(numbers)
        if name == "MOD":
            need(2, "兩個引數")
            divisor = self.to_decimal(args[1])
            if divisor == 0:
                raise RuntimeError_("DIVIDE BY ZERO：MOD 的除數為零")
            return self.to_decimal(args[0]) % divisor
        if name == "ORD":
            need(1, "一個引數")
            text = self._raw_text(args[0])
            position = self.to_int(args[1]) if len(args) > 1 else 1
            if position < 1 or position > len(text):
                return Decimal(0)
            return Decimal(ord(text[position - 1]))
        if name == "CHAR":
            need(1, "一個引數")
            code = self.to_int(args[0])
            if code < 0 or code > 0x10FFFF:
                raise RuntimeError_(f"CHAR 的引數 {code} 超出有效範圍")
            return chr(code)
        if name == "SUM":
            total = Decimal(0)
            for arg in args:
                total += self.to_decimal(arg)
            return total
        if name == "INTEGER":
            need(1, "一個引數")
            return self.to_decimal(args[0]).to_integral_value(rounding="ROUND_DOWN")
        if name == "PART":
            need(1, "一個引數")
            value = self.to_decimal(args[0])
            return value - value.to_integral_value(rounding="ROUND_DOWN")
        if name in ("UPPER-CASE", "LOWER-CASE"):
            need(1, "一個引數")
            text = self._raw_text(args[0])
            return text.upper() if name == "UPPER-CASE" else text.lower()
        if name == "TRIM":
            need(1, "一個引數")
            text = self._raw_text(args[0])
            mode = self._raw_text(args[1]).upper() if len(args) > 1 else ""
            if mode.startswith("L"):
                return text.lstrip(" ")
            if mode.startswith("R"):
                return text.rstrip(" ")
            return text.strip(" ")
        if name == "REVERSE":
            need(1, "一個引數")
            return self._raw_text(args[0])[::-1]
        if name == "ABS":
            need(1, "一個引數")
            return abs(self.to_decimal(args[0]))
        if name == "FACTORIAL":
            need(1, "一個引數")
            number = self.to_int(args[0])
            if number > limits.MAX_FACTORIAL_ARG:
                raise RuntimeError_(f"FACTORIAL 的引數 {number} 太大，超出可計算範圍")
            return Decimal(_factorial(number))
        if name == "SQRT":
            need(1, "一個引數")
            value = self.to_decimal(args[0])
            if value < 0:
                raise RuntimeError_("SQRT 的引數不能是負數")
            return value.sqrt()
        if name == "LENGTH-CHECK":
            raise RuntimeError_("FUNCTION LENGTH-CHECK 在本練習系統中不支援（請改用 FUNCTION LENGTH）")
        if name in ("CURRENT-DATE", "WHEN-COMPILED"):
            raise RuntimeError_(f"FUNCTION {name} 在本練習系統中不支援")
        if name == "RANDOM":
            if len(args) > 1:
                raise RuntimeError_("FUNCTION RANDOM 最多接受一個引數（種子）")
            if args:
                seed = self.to_decimal(args[0])
                if seed != 0:
                    try:
                        self._random.seed(int(seed))
                    except (ValueError, OverflowError):
                        raise RuntimeError_("FUNCTION RANDOM 的種子太大") from None
            return Decimal(str(self._random.random()))
        raise RuntimeError_(f"不支援的內建函式 FUNCTION {name}")

    def _numval_c(self, text: str) -> Decimal:
        """轉換帶貨幣符號與千分位的數字字串，例如 ``$1,234.56``。"""
        cleaned = text.strip()
        negative = False
        if cleaned.startswith("(") and cleaned.endswith(")"):
            negative = True
            cleaned = cleaned[1:-1]
        kept = "".join(ch for ch in cleaned if ch.isdigit() or ch in ".-")
        if kept in ("", ".", "-", "-."):
            raise RuntimeError_(f"NUMVAL-C 無法轉換 '{text}'")
        try:
            value = Decimal(kept)
        except InvalidOperation:
            raise RuntimeError_(f"NUMVAL-C 無法轉換 '{text}'") from None
        return -value if negative else value

    def _length_of(self, reference: Reference) -> int:
        field = reference.field
        if reference.span:
            total = 0
            for item in reference.span:
                total += self._length_of(Reference(item, ()))
            return total
        if field.has_occurs and not reference.path:
            return self._occurs_max(field) * (
                field.size if field.is_group or field.pic is None
                else field.pic.char_count
            )
        if reference.refmod is not None:
            return len(self._raw_text(self.get_reference(reference)))
        if field.is_group:
            return field.size // field.max_occurs if field.has_occurs else field.size
        pic = field.pic
        if pic is None:
            return len(self._raw_text(self.get_reference(reference)))
        if pic.category == CAT_NUMERIC and field.usage == "DISPLAY":
            # 數字欄位的長度是 PICTURE 的位數，不是目前數值的位數
            return pic.total_digits + (1 if field.sign_separate and pic.has_sign else 0)
        if pic.category == CAT_NUMERIC:
            return pic.storage_size(field.usage)
        return pic.char_count

    # ================================================================ 條件

    def eval_condition(self, node) -> bool:
        self.tick()
        kind = node.kind
        if kind == "logical":
            op = node.op
            if op == "NOT":
                return not self.eval_condition(node.left)
            if op == "AND":
                if not self.eval_condition(node.left):
                    return False
                return self.eval_condition(node.right)
            if self.eval_condition(node.left):
                return True
            return self.eval_condition(node.right)
        if kind == "cond_forever":
            return True
        if kind == "cond_true":
            return True
        if kind == "cond_false":
            return False
        if kind == "cond_any":
            return True
        if kind == "class_condition":
            return self.eval_class(node)
        if kind == "sign_condition":
            return self.eval_sign(node)
        if kind == "relation":
            return self.eval_relation(node)
        if kind in ("identifier", "unary", "binary", "literal", "figurative", "function"):
            return self.to_bool(self.eval(node))
        raise RuntimeError_(f"不支援的條件：{kind}")

    def eval_relation(self, node) -> bool:
        op = node.op
        if op == "IS_TRUE":
            target = node.left
            if target.kind == "identifier":
                return self.eval_condition_name(target.name.upper(), target.subscripts)
            return self.to_bool(self.eval(target))
        left = self.eval(node.left)
        right = self.eval(node.right)
        text_only = self._is_alphanumeric_operand(node.left) and self._is_alphanumeric_operand(node.right)
        return self.compare(left, right, op, text_only=text_only)

    def eval_class(self, node) -> bool:
        result = self._eval_class(node)
        return not result if node.get("negated") else result

    def _eval_class(self, node) -> bool:
        name = node.class_name.upper()
        if node.target.kind == "identifier":
            reference = self.resolve(node.target)
            if reference.field.usage == "INDEX":
                return True
            value = self.get_reference(reference)
            pic = reference.field.pic
            if (
                name == "NUMERIC"
                and pic is not None
                and pic.category == CAT_NUMERIC
                and isinstance(value, Decimal)
                and reference.refmod is None
            ):
                # 數字欄位本身存的就是數值：有號欄位可以是負數，V 欄位可以有小數
                return value >= 0 or pic.is_signed
        else:
            value = self.eval(node.target)
        text = self._raw_text(value)
        if name == "NUMERIC":
            text = text.strip()
            return text != "" and all(ch.isdigit() for ch in text)
        if name == "ALPHABETIC":
            return text.strip() != "" and all(ch.isalpha() for ch in text)
        if name == "ALPHABETIC-UPPER":
            return text.strip() != "" and all(ch.isupper() for ch in text)
        if name == "ALPHABETIC-LOWER":
            return text.strip() != "" and all(ch.islower() for ch in text)
        raise RuntimeError_(f"不支援的類別條件 {name}")

    def eval_sign(self, node) -> bool:
        result = self._eval_sign(node)
        return not result if node.get("negated") else result

    def _eval_sign(self, node) -> bool:
        if node.target.kind == "identifier":
            reference = self.resolve(node.target)
            if reference.field.usage == "INDEX":
                return True
            value = self.get_reference(reference)
        else:
            value = self.eval(node.target)
        number = self.to_decimal(value)
        name = node.class_name.upper()
        if name == "POSITIVE":
            return number > 0
        if name == "NEGATIVE":
            return number < 0
        if name == "ZERO":
            return number == 0
        if name == "NONZERO":
            return number != 0
        raise RuntimeError_(f"不支援的符號條件 {name}")

    def compare(self, left, right, op: str, text_only: bool = False) -> bool:
        """依 COBOL 規則比較兩個值。

        * 兩邊都是數字 → 直接比較數值
        * 一邊數字一邊文字 → 先把數字轉成顯示形式，再靠右補空白後比較
        * 兩邊都是文字 → 靠左補空白到一樣長後比較

        ``text_only`` 表示兩邊都是文數字資料（欄位或字串常數）：即使內容看起來像數字，
        也要照文字比較（``"1 "`` 和 ``"01"`` 不相等）。
        """
        # 象徵常數（SPACES、ALL "X"…）要展開成和另一邊一樣長再比較
        if isinstance(left, Fill) and not isinstance(right, Fill):
            left = self._expand_fill(left, right)
        elif isinstance(right, Fill) and not isinstance(left, Fill):
            right = self._expand_fill(right, left)
        left_num = None if text_only else self._as_number(left)
        right_num = None if text_only else self._as_number(right)
        if left_num is not None and right_num is not None:
            return _apply(op, left_num.compare(right_num))
        left_text = self._raw_text(left)
        right_text = self._raw_text(right)
        width = max(len(left_text), len(right_text))
        if not text_only and (left_num is None) != (right_num is None):
            # 一邊數字一邊文字：數字靠右對齊
            left_text = left_text.rjust(width)
            right_text = right_text.rjust(width)
        else:
            left_text = left_text.ljust(width)
            right_text = right_text.ljust(width)
        if op in ("=", "=="):
            return left_text == right_text
        if op in ("<>", "!="):
            return left_text != right_text
        if op == "<":
            return left_text < right_text
        if op == ">":
            return left_text > right_text
        if op == "<=":
            return left_text <= right_text
        if op == ">=":
            return left_text >= right_text
        raise RuntimeError_(f"不支援的比較運算子 {op}")

    def _expand_fill(self, fill: Fill, other) -> str:
        """把象徵常數展開成和另一個運算元一樣長的文字。"""
        width = max(1, len(self._raw_text(other)))
        return (fill.char * width)[:width]

    def _as_number(self, value):
        if isinstance(value, Decimal):
            return value
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return Decimal(value)
        if isinstance(value, str):
            text = value.strip()
            if text and (text[0].isdigit() or text[0] in "+-.") and self._looks_numeric(value):
                try:
                    return Decimal(text.replace(",", ""))
                except InvalidOperation:
                    return None
        return None

    def _looks_numeric(self, value) -> bool:
        if isinstance(value, (Decimal, int)):
            return True
        if not isinstance(value, str):
            return False
        text = value.strip()
        if not text:
            return False
        return all(ch.isdigit() or ch in "+-., " for ch in text)

    def _is_alphanumeric_operand(self, node) -> bool:
        """運算元是不是文數字資料：文數字欄位、字串常數或文字類的象徵常數。"""
        if node is None:
            return False
        if node.kind == "literal":
            return isinstance(node.value, str)
        if node.kind == "figurative":
            return node.name in (
                "SPACE", "SPACES", "HIGH-VALUES", "LOW-VALUES", "QUOTES", "ALL"
            )
        if node.kind == "identifier":
            if self._is_condition_name(node.name):
                return False
            try:
                reference = self.resolve(node)
            except RuntimeError_:
                return False
            # 群組項目和參考修改都是文數字資料
            if reference.refmod is not None or reference.span or reference.field.is_group:
                return True
            pic = reference.field.pic
            return pic is not None and pic.category == CAT_ALPHANUMERIC
        return False

    def _find_condition(self, name: str):
        """找出 88 條件名稱：回傳 ``(所屬欄位, 條件)``，找不到時回傳 None。"""
        key = (name or "").upper()
        for field in self._all_fields():
            for condition in field.conditions:
                if condition.name.upper() == key:
                    return field, condition
        return None

    def _is_condition_name(self, name: str) -> bool:
        """判斷某個名稱是不是 88 條件名稱。"""
        return self._find_condition(name) is not None

    def condition_reference(self, field, subscripts=()) -> Reference:
        """條件名稱所屬欄位的參考（條件名稱的下標就是欄位的下標）。"""
        if subscripts:
            return self.resolve_field(field, subscripts, field.name or "")
        return Reference(field, ())

    def eval_condition_name(self, name: str, subscripts=()) -> bool:
        found = self._find_condition(name)
        if found is None:
            raise RuntimeError_(f"找不到條件名稱 {name}")
        field, condition = found
        return self.match_condition(condition, self.condition_reference(field, subscripts))

    @staticmethod
    def condition_ranges(condition) -> list:
        """88 條件的值清單：``[(下限, 上限或 None), …]``。"""
        ranges = condition.get("ranges")
        if ranges is not None:
            return list(ranges)
        return [(spec, None) for spec in condition.values]

    def match_condition(self, condition, reference: Reference) -> bool:
        field = reference.field
        ranges = self.condition_ranges(condition)
        if ranges and ranges[0][0].kind == "figurative":
            word = ranges[0][0].value.upper()
            if word in ("TRUE", "FALSE"):
                return word == "TRUE"
        current = self.get_reference(reference)
        alphanumeric = field.pic is not None and field.pic.category == CAT_ALPHANUMERIC
        for low_spec, high_spec in ranges:
            if low_spec.kind == "all_literal":
                current_text = self._raw_text(current)
                pattern = str(low_spec.pattern)
                repeated = (pattern * (len(current_text) // max(1, len(pattern)) + 1))[: len(current_text)]
                if pattern and current_text == repeated:
                    return True
                continue
            low = self._condition_value(low_spec, reference)
            # 文數字欄位配上文字值時照文字比較（THRU "A" "Z" 這種範圍也一樣）
            text_only = alphanumeric and not isinstance(low, Decimal)
            if high_spec is None:
                if self.compare(current, low, "=", text_only=text_only):
                    return True
                continue
            high = self._condition_value(high_spec, reference)
            if self.compare(current, low, ">=", text_only=text_only) and self.compare(
                current, high, "<=", text_only=text_only
            ):
                return True
        return False

    def _condition_value(self, spec, reference: Reference):
        if spec.kind == "figurative":
            return self._figurative_value(reference.field, spec.value)
        return self.eval(spec)

    # ================================================================ 敘述執行
