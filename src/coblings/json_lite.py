"""中繼資料用的 JSON 子集解析器（不使用任何第三方套件）。

支援物件、陣列、字串、數字、``true``／``false``／``null``，錯誤訊息與位置都會指出
是哪裡寫錯了，方便出題者排查（CORE-FMT-09、CORE-CLI-12）。
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

_WHITESPACE = " \t\r\n"
_ESCAPES = {
    '"': '"',
    "\\": "\\",
    "/": "/",
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
}


class JsonError(ValueError):
    """JSON 格式錯誤。"""


class _Parser:
    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0

    # ---------------------------------------------------------------- 基本

    def error(self, message: str, pos: int | None = None) -> JsonError:
        return JsonError(f"{message}，位置 {self.pos if pos is None else pos}")

    def peek(self) -> str:
        return self.text[self.pos] if self.pos < len(self.text) else ""

    def skip_space(self) -> None:
        while self.pos < len(self.text) and self.text[self.pos] in _WHITESPACE:
            self.pos += 1

    def expect(self, char: str) -> None:
        if self.peek() != char:
            raise self.error(f"預期 '{char}' 但讀到 '{self.peek() or '檔案結尾'}'")
        self.pos += 1

    # ---------------------------------------------------------------- 解析

    def parse(self):
        self.skip_space()
        value = self.parse_value()
        self.skip_space()
        return value

    def parse_value(self):
        self.skip_space()
        char = self.peek()
        if char == "":
            raise self.error("JSON 內容意外結尾")
        if char == "{":
            return self.parse_object()
        if char == "[":
            return self.parse_array()
        if char == '"':
            return self.parse_string()
        if char == "-" or char.isdigit():
            return self.parse_number()
        for word, value in (("true", True), ("false", False), ("null", None)):
            if self.text.startswith(word, self.pos):
                self.pos += len(word)
                return value
        raise self.error(f"JSON 字面值錯誤，位置 {self.pos}")

    def parse_object(self) -> dict:
        self.expect("{")
        result: dict = {}
        self.skip_space()
        if self.peek() == "}":
            self.pos += 1
            return result
        while True:
            self.skip_space()
            if self.peek() != '"':
                raise self.error(f"JSON 物件格式錯誤，位置 {self.pos}")
            key = self.parse_string()
            self.skip_space()
            self.expect(":")
            result[key] = self.parse_value()
            self.skip_space()
            if self.peek() == ",":
                self.pos += 1
                continue
            if self.peek() == "}":
                self.pos += 1
                return result
            raise self.error(f"JSON 物件格式錯誤，位置 {self.pos}")

    def parse_array(self) -> list:
        self.expect("[")
        result: list = []
        self.skip_space()
        if self.peek() == "]":
            self.pos += 1
            return result
        while True:
            result.append(self.parse_value())
            self.skip_space()
            if self.peek() == ",":
                self.pos += 1
                continue
            if self.peek() == "]":
                self.pos += 1
                return result
            raise self.error(f"JSON 陣列格式錯誤，位置 {self.pos}")

    def parse_string(self) -> str:
        self.expect('"')
        buf: list[str] = []
        while True:
            if self.pos >= len(self.text):
                raise self.error("JSON 內容意外結尾")
            char = self.text[self.pos]
            if char == '"':
                self.pos += 1
                return "".join(buf)
            if char != "\\":
                buf.append(char)
                self.pos += 1
                continue
            self.pos += 1
            if self.pos >= len(self.text):
                raise self.error("JSON 內容意外結尾")
            escape = self.text[self.pos]
            if escape in _ESCAPES:
                buf.append(_ESCAPES[escape])
                self.pos += 1
                continue
            if escape == "u":
                start = self.pos + 1
                digits = self.text[start : start + 4]
                if len(digits) != 4 or any(d not in "0123456789abcdefABCDEF" for d in digits):
                    raise self.error(f"JSON \\u 跳脫字元格式錯誤，位置 {self.pos}")
                code = int(digits, 16)
                self.pos += 5
                # 代理對（surrogate pair）：\uD83D\uDE00 要併成一個字，
                # 否則會留下寫不進 UTF-8 的孤立代理字
                if 0xD800 <= code <= 0xDBFF and self.text[self.pos : self.pos + 2] == "\\u":
                    low = self.text[self.pos + 2 : self.pos + 6]
                    if len(low) == 4 and all(d in "0123456789abcdefABCDEF" for d in low):
                        low_code = int(low, 16)
                        if 0xDC00 <= low_code <= 0xDFFF:
                            code = 0x10000 + ((code - 0xD800) << 10) + (low_code - 0xDC00)
                            self.pos += 6
                buf.append(chr(code))
                continue
            raise self.error(f"不支援的跳脫字元 \\{escape}")

    def parse_number(self) -> Decimal:
        start = self.pos
        allowed = set("-+.eE0123456789")
        while self.pos < len(self.text) and self.text[self.pos] in allowed:
            self.pos += 1
        chunk = self.text[start : self.pos]
        try:
            return Decimal(chunk)
        except InvalidOperation:
            raise self.error(f"JSON 數值或格式錯誤，位置 {start}") from None


def parse(text: str):
    """解析一段 JSON；格式錯誤時丟出 :class:`JsonError`。"""
    return _Parser(text).parse()


def parse_object(text: str) -> dict:
    """解析 JSON，並要求根值必須是物件；不是物件時回傳空物件（套用預設值）。"""
    value = parse(text)
    return value if isinstance(value, dict) else {}


def to_text(value) -> str:
    """把 JSON 值轉成字串（中繼資料的非字串欄位會用到）。"""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, Decimal):
        text = format(value, "f")
        return text
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return ", ".join(to_text(item) for item in value)
    return str(value)
