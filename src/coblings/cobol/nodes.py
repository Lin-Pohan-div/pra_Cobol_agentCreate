"""抽象語法樹（AST）節點。

為了讓 parser 保持精簡，所有節點都共用 :class:`Node` 基類：以 ``kind`` 區分類別，
其餘欄位放在 ``__dict__``。欄位定義集中在每個產生節點的函式旁邊說明。
"""

from __future__ import annotations

import copy
from typing import Callable, Iterator


class Node:
    """通用 AST 節點。"""

    def __init__(self, kind: str, line: int = 0, column: int = 0, **fields) -> None:
        self.kind = kind
        self.line = line
        self.column = column
        self.__dict__.update(fields)

    def get(self, name: str, default=None):
        return self.__dict__.get(name, default)

    def iter_children(self) -> Iterator["Node"]:
        """依序產生直接子節點（包含放在 list／tuple／dict 裡的節點）。"""
        for value in self.__dict__.values():
            yield from _nodes_in(value)

    def walk(self) -> Iterator["Node"]:
        """前序走訪自己與所有子孫節點。"""
        yield self
        for child in self.iter_children():
            yield from child.walk()

    def map_children(self, transform: Callable[["Node"], "Node"]) -> "Node":
        """回傳一個淺層複本，其中每個直接子節點都換成 ``transform(child)``。

        原節點不會被修改；``transform`` 負責決定要不要往下遞迴。
        """
        clone = copy.copy(self)
        for key, value in self.__dict__.items():
            clone.__dict__[key] = _map_value(value, transform)
        return clone

    def __repr__(self) -> str:  # pragma: no cover - 除錯用
        fields = {
            k: v for k, v in self.__dict__.items() if k not in ("kind", "line", "column")
        }
        inner = ", ".join(f"{k}={v!r}" for k, v in fields.items())
        return f"{self.kind}({inner})"


def _nodes_in(value) -> Iterator[Node]:
    if isinstance(value, Node):
        yield value
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _nodes_in(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _nodes_in(item)


def _map_value(value, transform: Callable[[Node], Node]):
    if isinstance(value, Node):
        return transform(value)
    if isinstance(value, list):
        return [_map_value(item, transform) for item in value]
    if isinstance(value, tuple):
        return tuple(_map_value(item, transform) for item in value)
    if isinstance(value, dict):
        return {key: _map_value(item, transform) for key, item in value.items()}
    return value


class Program(Node):
    """整支程式。

    欄位：
    * ``program_id``：PROGRAM-ID 的名稱
    * ``special_names``：SPECIAL-NAMES 段落（保留給 ENVIRONMENT DIVISION）
    * ``selects``：SELECT 敘述（檔案控制）
    * ``files``：FILE SECTION 的 FD 定義，key 為 FD 名稱
    * ``sections``：``[(區段名稱, [DataDescription, ...]), ...]``
    * ``paragraphs``：PROCEDURE DIVISION 的段落清單
    * ``using_params``：PROCEDURE DIVISION USING 的參數
    * ``filename``：原始檔名（``parse_source`` 設定；連接後的程式沒有）
    """


class DataDescription(Node):
    """資料描述項。

    欄位：
    * ``level``：層級號（01/05/88/77…）
    * ``name``：名稱（FILLER 為 None）
    * ``picture``：PICTURE 原始文字
    * ``usage``：USAGE 子句
    * ``value``：VALUE 子句（``ValueSpec`` 或 None）
    * ``occurs``：OCCURS 次數（None 表示沒有）
    * ``depends_on``：OCCURS ... DEPENDING ON 的欄位名稱
    * ``redefines``：REDEFINES 的目標名稱
    * ``sign_separate``：SIGN IS SEPARATE
    * ``sign_leading``：SIGN IS LEADING（預設為 TRAILING）
    * ``justified``：JUSTIFIED RIGHT
    * ``blank_when_zero``：BLANK WHEN ZERO
    * ``children``：子描述項
    * ``conditions``：88 層級項目（``ConditionSpec`` 清單）
    * ``synonyms``：66 層級 RENAMES
    * ``line``：宣告位置
    """


class ValueSpec(Node):
    """VALUE 子句。

    欄位：``kind`` 為 literal／figurative／all_literal／expr，
    ``value``、``pattern``（ALL 的樣板文字）。
    """


class ConditionSpec(Node):
    """88 條件名稱。

    欄位：``name``、``values``（``[ValueSpec, ...]``）、``through``（THROUGH 對應的清單）。
    """


class RenameSpec(Node):
    """66 層級 RENAMES。"""

    def __init__(self, name: str, targets, line=0, column=0, **kw):
        super().__init__("rename", line, column, name=name, targets=list(targets), **kw)


class Paragraph(Node):
    """PROCEDURE DIVISION 的一個段落。

    欄位：``name``、``statements``、``section_name``（所屬 SECTION 的名稱）。
    """