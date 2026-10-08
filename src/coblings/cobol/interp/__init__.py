"""COBOL 直譯器的執行期（由職責拆檔的 mixin 組成）。

數值語意以 :class:`decimal.Decimal` 實作。對外介面與舊的 ``interp.py`` 相同：
``Interpreter``、``Reference``、``GoToSignal``、``Fill`` 都可以照舊 import。
"""
from __future__ import annotations

from .arith import ArithMixin
from .core import CoreMixin
from .datastmt import DataStmtMixin
from .expr import ExprMixin
from .files import FilesMixin
from .flow import FlowMixin
from .values import (
    HIGH_FILL,
    LOW_FILL,
    SPACE_FILL,
    ZERO_FILL,
    Fill,
    GoToSignal,
    Reference,
    ValuesMixin,
)


class Interpreter(
    CoreMixin, ValuesMixin, ExprMixin, ArithMixin, FlowMixin, DataStmtMixin, FilesMixin
):
    """執行一支 :class:`Program`。"""


__all__ = [
    "Interpreter",
    "Reference",
    "GoToSignal",
    "Fill",
    "ZERO_FILL",
    "SPACE_FILL",
    "HIGH_FILL",
    "LOW_FILL",
]
