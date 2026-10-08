"""直譯器資料敘述：INITIALIZE／INSPECT／STRING／SEARCH／CALL／ACCEPT。"""
from __future__ import annotations

import os
import sys
import time
from decimal import Decimal

from ..builtins import call_builtin
from ..errors import RuntimeError_
from ..pic import CAT_ALPHANUMERIC
from .values import Reference


class DataStmtMixin:
    """資料處理敘述的執行。"""
    def _exec_initialize(self, node) -> None:
        for target in node.targets:
            reference = self.resolve(target)
            self._initialize_group(reference.field, reference.path)
        for source, target in node.replacing:
            pattern = self._raw_text(self.eval(source))
            replacement = self._raw_text(self.eval(target))
            for target_node in node.targets:
                reference = self.resolve(target_node)
                self._replace_in(reference, pattern, replacement)

    def _replace_in(self, reference: Reference, pattern: str, replacement: str) -> None:
        """INITIALIZE … REPLACING：把欄位裡出現的 pattern 換成 replacement。"""
        field = reference.field
        if field.is_group:
            for child in field.children:
                self._replace_in(Reference(child, reference.path), pattern, replacement)
            return
        if not pattern:
            return
        if field.pic is not None and field.pic.category != CAT_ALPHANUMERIC:
            try:
                if self.to_decimal(self.get_reference(reference)) == self.to_decimal(pattern):
                    self.set_reference(reference, self.to_decimal(replacement))
            except RuntimeError_:
                pass
            return
        current = self._raw_text(self.get_reference(reference))
        self.set_reference(reference, current.replace(pattern, replacement))

    def _exec_inspect(self, node) -> None:
        reference = self.resolve(node.target)
        current = self._raw_text(self.get_reference(reference))
        changed = False
        for operation in node.operations:
            low, high = self._inspect_region(current, operation.get("bounds") or {})
            segment = current[low:high]
            kind = operation["kind"]
            if kind == "tally":
                count = self._inspect_count(segment, operation)
                counter = self.resolve(operation["counter"])
                # TALLYING 是「加到」計數器上，不會先把計數器歸零
                total = self.to_decimal(self.get_reference(counter)) + count
                self.set_reference(counter, total)
                continue
            if kind == "replace":
                segment = self._inspect_replace(segment, operation)
            elif kind == "convert":
                # parser 已經把對照表展開成 (來源字元, 目標字元) 的清單
                mapping = dict(operation["mapping"])
                segment = "".join(mapping.get(char, char) for char in segment)
            current = current[:low] + segment + current[high:]
            changed = True
        if changed:
            self.set_reference(reference, current)

    def _inspect_region(self, text: str, bounds: dict) -> tuple[int, int]:
        """BEFORE／AFTER INITIAL 限定的範圍 ``[low, high)``。"""
        low, high = 0, len(text)
        after = bounds.get("after")
        if after is not None:
            marker = self._raw_text(self.eval(after))
            index = text.find(marker) if marker else -1
            if index < 0:
                return len(text), len(text)
            low = index + len(marker)
        before = bounds.get("before")
        if before is not None:
            marker = self._raw_text(self.eval(before))
            index = text.find(marker, low) if marker else -1
            if index >= 0:
                high = index
        return low, high

    def _inspect_count(self, segment: str, operation) -> int:
        how = operation.get("how") or "ALL"
        if how == "CHARACTERS":
            return len(segment)
        pattern = self._raw_text(self.eval(operation["pattern"]))
        if not pattern:
            return 0
        if how == "LEADING":
            count = 0
            while segment.startswith(pattern, count * len(pattern)):
                count += 1
            return count
        return segment.count(pattern)

    def _inspect_replace(self, segment: str, operation) -> str:
        how = operation["how"]
        replacement = self._raw_text(self.eval(operation["replacement"]))
        if how == "CHARACTERS":
            return (replacement[:1] or " ") * len(segment)
        pattern = self._raw_text(self.eval(operation["pattern"]))
        if not pattern:
            return segment
        # COBOL 規定替換字串和樣式一樣長；長度不同時補空白或截斷，避免欄位長度跑掉
        replacement = replacement[: len(pattern)].ljust(len(pattern))
        if how == "LEADING":
            count = 0
            while segment.startswith(pattern, count * len(pattern)):
                count += 1
            return replacement * count + segment[count * len(pattern):]
        if how == "FIRST":
            return segment.replace(pattern, replacement, 1)
        return segment.replace(pattern, replacement)

    def _exec_string(self, node) -> None:
        pointer_reference = self.resolve(node.pointer) if node.pointer else None
        target_reference = self.resolve(node.target)
        text = self._raw_text(self.get_reference(target_reference))
        pointer = self.to_int(self.get_reference(pointer_reference), "POINTER") - 1 if pointer_reference else 0
        if pointer < 0 or pointer > len(text):
            raise RuntimeError_("STRING 的 POINTER 超出範圍")
        room = len(text) - pointer
        delimiter = node.delimiter
        buffer: list[str] = []
        for source, source_delimiter in node.sources:
            piece = self._raw_text(self.eval(source))
            marker = source_delimiter if source_delimiter is not None else delimiter
            marker_text = self._raw_text(self.eval(marker)) if marker is not None else ""
            if marker_text:
                index = piece.find(marker_text)
                if index >= 0:
                    piece = piece[:index]
            joined = "".join(buffer) + piece
            if len(joined) > room:
                buffer.append(piece[: max(0, room - len("".join(buffer)))])
                self.execute_statements(node.on_overflow)
                break
            buffer.append(piece)
        text_added = "".join(buffer)
        result = text[:pointer] + text_added + text[pointer + len(text_added) :]
        self.set_reference(target_reference, result)
        if pointer_reference:
            self.set_reference(pointer_reference, pointer + 1 + len(text_added))

    def _exec_unstring(self, node) -> None:
        source = self._raw_text(self.eval(node.source))
        delimiters = [
            (self._raw_text(self.eval(item)), all_flag) for item, all_flag in node.delimiters
        ]
        pointer_reference = self.resolve(node.pointer) if node.pointer else None
        pointer = self.to_int(self.get_reference(pointer_reference), "POINTER") - 1 if pointer_reference else 0
        if pointer < 0 or pointer >= len(source):
            # 指標超出來源範圍是溢位，不是程式錯誤
            self.execute_statements(node.on_overflow)
            return
        position = pointer
        filled = 0
        for spec in node.targets:
            if position >= len(source):
                # 來源用完了：剩下的接收欄位維持原值
                break
            target_reference = self.resolve(spec["target"])
            own = spec.get("delimiter")
            candidates = [(self._raw_text(self.eval(own)), False)] if own is not None else delimiters
            candidates = [(text, flag) for text, flag in candidates if text]
            if candidates:
                found = -1
                matched = ""
                matched_all = False
                for text, all_flag in candidates:
                    index = source.find(text, position)
                    if index >= 0 and (found < 0 or index < found):
                        found, matched, matched_all = index, text, all_flag
                if found < 0:
                    piece, matched, end = source[position:], "", len(source)
                else:
                    piece, end = source[position:found], found + len(matched)
                    if matched_all:
                        while source.startswith(matched, end):
                            end += len(matched)
            else:
                # 沒有界標：依接收欄位的長度切
                size = self._length_of(target_reference)
                piece, matched, end = source[position : position + size], "", position + size
            self.set_reference(target_reference, piece)
            if spec.get("delimiter_in") is not None:
                self.set_reference(self.resolve(spec["delimiter_in"]), matched)
            if spec.get("count_in") is not None:
                self.set_reference(self.resolve(spec["count_in"]), len(piece))
            position = end
            filled += 1
        if pointer_reference:
            self.set_reference(pointer_reference, position + 1)
        if node.get("tallying") is not None:
            tally = self.resolve(node.tallying)
            self.set_reference(tally, self.to_decimal(self.get_reference(tally)) + filled)
        if position < len(source) and filled == len(node.targets):
            self.execute_statements(node.on_overflow)

    def _exec_search(self, node) -> None:
        table = self.resolve(node.target).field
        limit = self._occurs_max(table)
        if node.varying:
            self._search_legacy(node, limit)
            return
        index_reference = None
        if table.indexed_by:
            index_reference = self.resolve_field(self.layout.lookup(table.indexed_by[0]), ())
        varying_reference = self.resolve(node.varying_index) if node.get("varying_index") else None
        if index_reference is None:
            index_reference = varying_reference
        if index_reference is None:
            raise RuntimeError_(
                f"SEARCH {table.name} 需要索引：請在 OCCURS 加上 INDEXED BY，或寫 SEARCH … VARYING"
            )
        if node.get("search_all"):
            # SEARCH ALL 本來是二分搜尋；結果相同，這裡從第一筆開始找
            self.set_reference(index_reference, Decimal(1))
        current = self.to_int(self.get_reference(index_reference), "SEARCH 索引")
        while 1 <= current <= limit:
            self.tick()
            if varying_reference is not None and varying_reference is not index_reference:
                self.set_reference(varying_reference, Decimal(current))
            for condition, body in node.whens:
                if self.eval_condition(condition):
                    self.execute_statements(body)
                    return
            current += 1
            self.set_reference(index_reference, Decimal(min(current, 9999)))
        self.execute_statements(node.at_end)

    def _search_legacy(self, node, limit: int) -> None:
        """早期寫法：SEARCH 表格 VARYING i FROM a BY b UNTIL 條件。"""
        index, from_expr, by_expr, until = node.varying[0]
        index_reference = self.resolve(index)
        current = self.to_int(self.eval(from_expr), "SEARCH 起始值")
        step = self.to_int(self.eval(by_expr), "SEARCH 步數") or 1
        while 1 <= current <= limit:
            self.tick()
            self.set_reference(index_reference, Decimal(current))
            if self.eval_condition(until):
                break
            for condition, body in node.whens:
                if self.eval_condition(condition):
                    self.execute_statements(body)
                    return
            current += step
        self.execute_statements(node.at_end)

    def _exec_call(self, node) -> None:
        args: list[tuple] = []
        for mode, operand in node.using:
            if operand.kind == "identifier":
                reference = self.resolve(operand)
                value = self.get_reference(reference)
                args.append((value, reference.field))
            else:
                args.append((self.eval(operand), None))
        name = node.name
        if isinstance(name, str):
            result = self.invoke_builtin(name.upper(), args)
            if node.returning is not None:
                self.set_reference(self.resolve(node.returning), result)
            return
        # 變數名稱的 CALL：本系統沒有外部程式，一律視為無效
        raise RuntimeError_(f"不支援的 CALL 目標 {name}")

    def invoke_builtin(self, name: str, args: list[tuple]):
        return call_builtin(self, name, args)

    def _exec_accept(self, node) -> None:
        source = node.source
        if isinstance(source, tuple) and source[0] == "ENVIRONMENT":
            value = os.environ.get(source[1], "")
            self.set_reference(self.resolve(node.target), value)
            return
        if source == "DATE":
            self.set_reference(self.resolve(node.target), time.strftime("%Y%m%d"))
            return
        if source == "TIME":
            self.set_reference(self.resolve(node.target), time.strftime("%H%M%S"))
            return
        if source == "COMMAND-LINE":
            self.set_reference(self.resolve(node.target), " ".join(sys.argv[1:]))
            return
        self.set_reference(self.resolve(node.target), "")

    # ---------------------------------------------------------------- 檔案
