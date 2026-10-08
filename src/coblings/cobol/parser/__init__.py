"""COBOL 自由格式語法分析器：把詞形串列轉成 AST。

涵蓋範圍以 docs/spec/profile-cobol.md 第 6 章列出的子集為準。設計原則是
「寬鬆解析、嚴格求值」：看不懂的段落盡量跳過，讓學生先把程式寫出來再處理語法細節。

本套件由數個 mixin 組成（按職責拆檔），對外介面與舊的 ``parser.py`` 相同。
"""
from __future__ import annotations

from ..errors import SyntaxError_
from ..lexer import tokenize
from .base import ParserBase, SCOPED_TERMINATORS, VERBS
from .data import DataParser
from .expr import ExprParser
from .procedure import ProcParser
from .statements import StmtParser


class Parser(DataParser, ProcParser, StmtParser, ExprParser):
    """遞迴下降解析器（各 mixin 的組合）。"""


def parse_source(source: str, filename: str = "") -> "Program":
    """把 COBOL 原始碼解析成 :class:`Program`。"""
    from ..nodes import Program

    try:
        program = Parser(tokenize(source, filename), filename).parse_program()
    except SyntaxError_ as error:
        error.filename = error.filename or filename
        raise
    program.filename = filename
    return program


__all__ = ["Parser", "ParserBase", "parse_source", "VERBS", "SCOPED_TERMINATORS"]
