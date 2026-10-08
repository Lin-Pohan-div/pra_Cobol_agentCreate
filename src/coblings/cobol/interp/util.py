"""直譯器共用小工具。"""
from __future__ import annotations

from .. import limits
from ..errors import RuntimeError_


def _apply(op: str, comparison: int) -> bool:
    if op in ("=", "=="):
        return comparison == 0
    if op in ("<>", "!="):
        return comparison != 0
    if op == "<":
        return comparison < 0
    if op == ">":
        return comparison > 0
    if op == "<=":
        return comparison <= 0
    if op == ">=":
        return comparison >= 0
    raise RuntimeError_(f"不支援的比較運算子 {op}")


def _describe(node) -> str:
    return f"{node.kind}（第 {node.line} 行）"


def _factorial(n: int) -> int:
    if n < 0:
        raise RuntimeError_("FACTORIAL 的引數不能是負數")
    result = 1
    for value in range(2, n + 1):
        result *= value
        if result > limits.MAX_FACTORIAL_RESULT:
            raise RuntimeError_("FACTORIAL 的結果太大")
    return result
