"""COBOL 自由格式（free format）詞法分析器。

支援：

* 不分大小寫的關鍵字與識別字
* 以 ``-`` 連接的使用者定義字（``WS-TOTAL``）
* ``"..."`` 與 ``'...'`` 字串常數（以兩個同引號表示一個引號）
* 數字常數（``.5``、``3.14``、``-2``）
* 行內註解 ``*>`` 與第 1 欄的 ``*`` 整行註解
* 編譯指示 ``>>SOURCE``／``>>SET``（直接略過）
* 運算子與分隔符
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .errors import SyntaxError_

WORD = "WORD"
NUMBER = "NUMBER"
STRING = "STRING"
OP = "OP"
PERIOD = "PERIOD"
COMMA = "COMMA"
SEMICOLON = "SEMICOLON"
COLON = "COLON"
EOF = "EOF"

_DIGITS = "0123456789"

#: 由長到短的運算子
_OPERATORS = (
    "<=",
    ">=",
    "**",
    "==",
    "!=",
    "<>",
    "(",
    ")",
    "+",
    "-",
    "*",
    "/",
    "$",
    "=",
    "<",
    ">",
)


@dataclass
class Token:
    kind: str
    value: str
    line: int
    column: int
    #: NUMBER 用的實際數值
    number: Decimal | None = None

    @property
    def upper(self) -> str:
        return self.value.upper()

    def is_word(self, *words: str) -> bool:
        return self.kind == WORD and self.value.upper() in {w.upper() for w in words}

    def is_op(self, *ops: str) -> bool:
        return self.kind == OP and self.value in ops

    def __repr__(self) -> str:  # pragma: no cover - 除錯用
        return f"Token({self.kind}, {self.value!r}, {self.line}:{self.column})"


def _strip_line(line: str) -> str:
    """去掉整行註解與行內註解，並回傳處理後的文字。

    字串常數裡的 ``*>`` 不是註解（例如 ``DISPLAY "*> hi"``），掃描時要跳過引號區間。
    如果字串沒有關閉，會在這裡標記錯誤位置，讓後續的 tokenize 報更準確的錯。
    """
    if line[:1] == "*":
        # 固定格式的整行註解；自由格式雖不需要，但學生常沿用習慣
        return ""
    i = 0
    n = len(line)
    while i < n:
        ch = line[i]
        if ch in "\"'":
            quote = ch
            start = i
            i += 1
            closed = False
            while i < n:
                if line[i] == quote:
                    if i + 1 < n and line[i + 1] == quote:
                        i += 2
                        continue
                    i += 1
                    closed = True
                    break
                i += 1
            if not closed:
                # 字串沒有關閉：保留原樣，讓 tokenize 報錯時能指出正確位置
                # 這裡不把後面的內容當成註解，避免錯誤訊息的行號偏移
                return line
            continue
        if ch == "*" and i + 1 < n and line[i + 1] == ">":
            return line[:i] + " " * (n - i)
        i += 1
    return line


def tokenize(source: str, filename: str = "") -> list[Token]:
    """把 COBOL 原始碼轉成詞形（token）串列。"""
    tokens: list[Token] = []
    lines = source.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    for lineno, raw_line in enumerate(lines, start=1):
        if raw_line.lstrip().startswith(">>"):
            # >>SOURCE FORMAT FREE / >>SET SOURCEFORMAT"FREE" 之類的指示
            continue
        line = _strip_line(raw_line)
        i = 0
        n = len(line)
        while i < n:
            ch = line[i]
            if ch in " \t":
                i += 1
                continue
            column = i + 1

            # ---- 字串常數
            if ch in "\"'":
                quote = ch
                i += 1
                buf: list[str] = []
                closed = False
                while i < n:
                    if line[i] == quote:
                        if i + 1 < n and line[i + 1] == quote:
                            buf.append(quote)
                            i += 2
                            continue
                        i += 1
                        closed = True
                        break
                    buf.append(line[i])
                    i += 1
                if not closed:
                    raise SyntaxError_(
                        "字串常數沒有結束的引號", line=lineno, column=column
                    )
                tokens.append(Token(STRING, "".join(buf), lineno, column))
                continue

            # ---- 數字常數（也可能只是 01 這種層級號，parser 會自己判斷）
            # 只認 ASCII 數字：str.isdigit() 也接受「²」「１」，Decimal 卻轉不了
            if ch in _DIGITS or (
                ch in "."
                and i + 1 < n
                and line[i + 1] in _DIGITS
            ):
                start = i
                seen_dot = False
                while i < n:
                    c = line[i]
                    if c in _DIGITS:
                        i += 1
                    elif c == "." and not seen_dot and i + 1 < n and line[i + 1] in _DIGITS:
                        seen_dot = True
                        i += 1
                    else:
                        break
                text = line[start:i]
                tokens.append(Token(NUMBER, text, lineno, column, Decimal(text)))
                continue

            # ---- 識別字（含連字號）
            if ch.isalpha():
                start = i
                while i < n:
                    c = line[i]
                    if c.isalnum() or c == "-":
                        # 連字號只有在後面接著字母或數字時才屬於這個字
                        if c == "-" and not (i + 1 < n and line[i + 1].isalnum()):
                            break
                        i += 1
                    elif c == "_" and i + 1 < n and line[i + 1].isalnum():
                        i += 1
                    else:
                        break
                # 整數常數的負號，例如 PIC S9(3) 搭配 VALUE -12
                text = line[start:i]
                tokens.append(Token(WORD, text, lineno, column))
                continue

            # ---- 分隔符與運算子
            if ch == ".":
                tokens.append(Token(PERIOD, ".", lineno, column))
                i += 1
                continue
            if ch == ",":
                tokens.append(Token(COMMA, ",", lineno, column))
                i += 1
                continue
            if ch == ";":
                tokens.append(Token(SEMICOLON, ";", lineno, column))
                i += 1
                continue
            if ch == ":":
                tokens.append(Token(COLON, ":", lineno, column))
                i += 1
                continue

            matched = None
            for op in _OPERATORS:
                if line.startswith(op, i):
                    matched = op
                    break
            if matched is None:
                raise SyntaxError_(
                    f"無法辨識的字元 '{ch}'", line=lineno, column=column
                )
            tokens.append(Token(OP, matched, lineno, column))
            i += len(matched)

    tokens.append(Token(EOF, "<EOF>", len(lines) + 1, 1))
    return tokens
