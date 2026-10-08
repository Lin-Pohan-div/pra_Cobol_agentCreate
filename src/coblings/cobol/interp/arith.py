"""直譯器算術敘述：COMPUTE／ADD／SUBTRACT／MULTIPLY／DIVIDE。"""
from __future__ import annotations

from decimal import Decimal

from ..errors import RuntimeError_
from ..pic import CAT_ALPHANUMERIC


class ArithMixin:
    """算術敘述的執行（含 ON SIZE ERROR）。"""
    def _store_result(
        self, target, value: Decimal, rounding: bool = False
    ) -> bool:
        """把算術結果寫進欄位；放不下時回傳 False 且不寫入（欄位維持原值）。"""
        reference = self.resolve(target)
        field = reference.field
        if field.pic is not None and field.pic.category != CAT_ALPHANUMERIC:
            if field.pic.overflows(value, rounding):
                return False
        self.set_reference(reference, value, rounding)
        return True

    def _finish_arithmetic(self, node, overflowed: bool) -> None:
        """算式全部寫完後，依有無溢位執行 SIZE ERROR 短語（只執行一次）。"""
        if overflowed:
            body = node.on_size_error.get("size_error")
            if body:
                self.execute_statements(body)
        else:
            body = node.on_size_error.get("not_size_error")
            if body:
                self.execute_statements(body)

    def _exec_compute(self, node) -> None:
        try:
            value = self.to_decimal(self.eval(node.expr))
        except RuntimeError_:
            # 算式本身出錯（例如除以零）：有 ON SIZE ERROR 就交給它處理，
            # 否則照樣把錯誤往上丟，不可以被 NOT ON SIZE ERROR 吃掉
            body = node.on_size_error.get("size_error")
            if body:
                self.execute_statements(body)
                return
            raise
        overflowed = False
        for target, rounded in node.targets:
            if not self._store_result(target, value, rounded):
                overflowed = True
        self._finish_arithmetic(node, overflowed)

    def _exec_add(self, node) -> None:
        numbers = [self.to_decimal(self.eval(o)) for o in node.operands]
        total = Decimal(0)
        for number in numbers:
            total += number
        overflowed = False
        if node.giving:
            for target, rounded in node.giving:
                if not self._store_result(target, total, rounded):
                    overflowed = True
        else:
            for target, rounded in node.to_targets:
                current = self._current_value(target)
                if not self._store_result(target, current + total, rounded):
                    overflowed = True
        self._finish_arithmetic(node, overflowed)

    def _exec_subtract(self, node) -> None:
        """SUBTRACT a [b …] FROM c [GIVING d]。

        COBOL 的寫法是「從 c 減掉 a（和 b…）」，所以 ``SUBTRACT 3 FROM A GIVING D``
        的意思是 ``D = A - 3``。
        """
        subtrahend = Decimal(0)
        for operand in node.operands:
            subtrahend += self.to_decimal(self.eval(operand))
        overflowed = False
        if node.giving:
            base = Decimal(0)
            if node.from_targets:
                base = self._current_value(node.from_targets[0][0])
            for target, rounded in node.giving:
                value = base - subtrahend
                if not self._store_result(target, value, rounded):
                    overflowed = True
        else:
            for target, rounded in node.from_targets:
                value = self._current_value(target) - subtrahend
                if not self._store_result(target, value, rounded):
                    overflowed = True
        self._finish_arithmetic(node, overflowed)

    def _exec_multiply(self, node) -> None:
        """MULTIPLY x BY y [GIVING z]。

        沒有 GIVING 時，接收欄位是 ``y`` 本身（``MULTIPLY 2 BY PRICE`` 會把 PRICE 乘 2）。
        """
        left = self.to_decimal(self.eval(node.left))
        right = self.to_decimal(self.eval(node.right))
        product = left * right
        overflowed = False
        if node.giving:
            for target, rounded in node.giving:
                if not self._store_result(target, product, rounded):
                    overflowed = True
        elif not self._store_result(node.right, product):
            overflowed = True
        self._finish_arithmetic(node, overflowed)

    def _exec_divide(self, node) -> None:
        left = self.to_decimal(self.eval(node.left))
        right = self.to_decimal(self.eval(node.right))
        by_form = bool(node.get("by_form"))

        if by_form:
            divisor = right
            dividend = left
        else:
            divisor = left
            dividend = right
        if divisor == 0:
            # 有寫 ON SIZE ERROR 時，除以零算是一種 size error（GnuCOBOL 的做法）；
            # 只有 NOT ON SIZE ERROR 不能把錯誤吃掉
            if node.on_size_error.get("size_error"):
                self.execute_statements(node.on_size_error["size_error"])
                return
            raise RuntimeError_("DIVIDE BY ZERO：除數為零")

        overflowed = False
        if node.giving:
            for target, rounded in node.giving:
                if not self._store_result(target, dividend / divisor, rounded):
                    overflowed = True
        else:
            # 沒有寫 GIVING（或 INTO 清單）時，接收欄位就是關鍵字後面那個
            raw_targets = node.into or ([node.right] if node.right is not None else [])
            targets = [
                item if isinstance(item, tuple) else (item, False) for item in raw_targets
            ]
            for target, rounded in targets:
                current = self._current_value(target)
                # INTO 的接收欄位自己就是被除數；BY 的接收欄位只是存放結果
                value = current / divisor if not by_form else dividend / divisor
                if not self._store_result(target, value, rounded):
                    overflowed = True
        if node.remainder is not None:
            remainder = dividend - divisor * (dividend / divisor).to_integral_value(
                rounding="ROUND_DOWN"
            )
            if not self._store_result(node.remainder, remainder):
                overflowed = True
        self._finish_arithmetic(node, overflowed)

    def _current_value(self, target) -> Decimal:
        if target.kind != "identifier":
            return Decimal(0)
        reference = self.resolve(target)
        if reference.field.usage == "INDEX":
            return Decimal(self.to_int(self.get_reference(reference), "索引"))
        return self.to_decimal(self.get_reference(reference))
