"""直譯器檔案敘述：OPEN／CLOSE／READ／WRITE／DELETE／REWRITE／SORT／MERGE／START。"""
from __future__ import annotations

import os
from decimal import Decimal, InvalidOperation
from functools import cmp_to_key

from .. import limits
from ..errors import RuntimeError_
from ..pic import CAT_ALPHANUMERIC
from .values import Reference


class FilesMixin:
    """檔案的執行（工作目錄＝題目資料夾）。

    支援循序檔與簡易的索引鍵存取（``READ ... KEY IS``、``START``）。
    """
    def initialize_files(self) -> None:
        self.file_store = {}
        self.file_of_record = {}
        for fd_name, fields in self.layout.records.items():
            # 記錄項的第一個名稱通常就是 FD 名稱，這裡記住它對應的檔案
            self.file_of_record[fd_name.upper()] = fd_name

    def _file_state(self, name: str) -> dict:
        key = name.upper()
        if key not in self.file_store:
            self.file_store[key] = {
                "records": [],
                "position": 0,
                "assign": "",
                "mode": None,
                "open": None,
                "loaded": False,
            }
        return self.file_store[key]

    def _load_disk_records(self, assign: str) -> list[str]:
        """從磁碟讀入一個檔案的全部紀錄（含空行，一行就是一筆）。"""
        records: list[str] = []
        path = self._data_path(assign)
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as handle:
                    for line in handle:
                        records.append(line.rstrip("\n").rstrip("\r"))
                        if len(records) > limits.MAX_INPUT_LINES:
                            raise RuntimeError_(
                                f"檔案 {assign} 超過 {limits.MAX_INPUT_LINES} 行，無法讀取"
                            )
            except OSError as error:
                raise RuntimeError_(f"讀取檔案 {assign} 失敗：{error}") from None
        return records

    def _exec_open(self, node) -> None:
        for mode, identifier in node.files:
            name = (identifier.name or "").upper()
            state = self._file_state(name)
            select = self.layout.selects.get(name)
            assign = select.get("assign") if select else name
            if not assign:
                assign = name
            state["assign"] = assign
            state["mode"] = mode
            state["open"] = mode
            state["fd"] = self.layout.fd_of_file.get(name, name)
            if mode == "OUTPUT":
                state["records"] = []
                state["position"] = 0
                state["loaded"] = True
            elif mode == "INPUT":
                state["records"] = self._load_disk_records(assign)
                state["position"] = 0
                state["loaded"] = True
            elif mode in ("I-O", "EXTEND"):
                # 保留記憶體裡已有的紀錄（同一次執行中寫過的）；全新的才從磁碟載入
                if not state.get("loaded"):
                    state["records"] = self._load_disk_records(assign)
                    state["loaded"] = True
                state["position"] = 0 if mode == "I-O" else len(state["records"])

    def _data_path(self, assign: str) -> str:
        """把 ASSIGN TO 的檔名解析成實際路徑，而且只能落在題目資料夾裡。

        學生程式不應該能用絕對路徑、``..`` 或符號連結寫到練習目錄外面，
        所以比對前先把兩邊都解析成真實路徑。
        """
        name = str(assign).strip().strip("\"'")
        if not name or os.path.isabs(name) or name.startswith("\\\\"):
            raise RuntimeError_("ASSIGN TO 只能使用題目資料夾裡的相對檔名")
        root = os.path.realpath(self.working_dir)
        path = os.path.realpath(os.path.join(self.working_dir, name))
        try:
            if os.path.commonpath([root, path]) != root:
                raise RuntimeError_("ASSIGN TO 不能寫到題目資料夾外面")
        except ValueError as error:
            raise RuntimeError_("ASSIGN TO 不能寫到題目資料夾外面") from error
        # 保護題目檔與檢查器：不可覆寫 *.cbl、.original/、exercise.json、expected.txt
        base = os.path.basename(path).lower()
        if base in ("exercise.json", "expected.txt") or base.endswith(".cbl"):
            raise RuntimeError_("ASSIGN TO 不能使用受保護的題目檔名")
        rel = os.path.relpath(path, root)
        parts = rel.split(os.sep)
        if parts and parts[0].lower() == ".original":
            raise RuntimeError_("ASSIGN TO 不能寫入 .original 資料夾")
        return path

    def _exec_close(self, node) -> None:
        for identifier in node.files:
            state = self._file_state((identifier.name or "").upper())
            # I-O 模式的 REWRITE／DELETE 也要寫回磁碟
            if state.get("mode") in ("OUTPUT", "EXTEND", "I-O") and state.get("assign"):
                path = self._data_path(state["assign"])
                try:
                    with open(path, "w", encoding="utf-8", newline="\n") as handle:
                        for record in state["records"]:
                            handle.write(record + "\n")
                except OSError as error:
                    raise RuntimeError_(f"寫入檔案 {state['assign']} 失敗：{error}") from None
            state["open"] = None
            state["mode"] = None

    def _exec_read(self, node) -> None:
        name = (node.file.name or "").upper()
        state = self._file_state(name)
        if node.key is not None:
            self._exec_read_key(node, state)
            return
        records = state["records"]
        position = state["position"]
        at_end = position >= len(records)
        if at_end:
            # 只有 AT END 子句才該在讀完時執行；NOT AT END 的敘述不能在這裡跑
            if node.at_end:
                self.execute_statements(node.get("at_end_body") or node.end_body)
            elif not node.not_at_end:
                raise RuntimeError_(f"READ 讀完 {name} 之後沒有下一筆紀錄")
            return
        record = records[position]
        state["position"] = position + 1
        if node.into is not None:
            self.set_reference(self.resolve(node.into), record)
        else:
            self._store_record(state.get("fd", ""), record)
        if node.not_at_end:
            self.execute_statements(node.get("not_at_end_body") or node.end_body)

    def _exec_read_key(self, node, state) -> None:
        """依鍵值直接讀取一筆（``READ file KEY IS key``）。"""
        name = (node.file.name or "").upper()
        self._ensure_records(name, state)
        wanted = self.get_reference(self.resolve(node.key))
        fd_name = state.get("fd", name)
        for index, record in enumerate(state["records"]):
            if self.compare(self._record_key(record, fd_name, node.key.name), wanted, "="):
                state["position"] = index + 1
                if node.into is not None:
                    self.set_reference(self.resolve(node.into), record)
                else:
                    self._store_record(fd_name, record)
                if node.not_at_end:
                    self.execute_statements(node.get("not_at_end_body") or node.end_body)
                return
        if node.get("invalid_key"):
            self.execute_statements(node.get("invalid_body") or [])
            return
        raise RuntimeError_(f"READ {name} 找不到鍵值 {self._raw_text(wanted)!r} 的紀錄")

    def _store_record(self, fd_name: str, record: str) -> None:
        """把讀到的一行填進 FD 的記錄區。

        同一個 FD 底下的每個 01 都共用同一塊記錄區，所以每個 01 都拿到整行；
        群組記錄會依版面拆給底下的基本項目。
        """
        fields = self.layout.records.get(fd_name.upper())
        if not fields:
            return
        for field in fields:
            reference = Reference(field, ())
            if field.is_group:
                self.set_group_text(reference, record)
            else:
                piece = record[: self.element_length(field)]
                self.storage.set(field, (), self.coerce(field, self.element_from_text(field, piece)))

    def record_text(self, reference: Reference) -> str:
        """記錄區目前的內容（WRITE／REWRITE 寫出去的那一行）。"""
        if reference.field.is_group:
            return self.group_text(reference)
        return self.element_text(reference.field, self.get_reference(reference))

    def _file_of_record(self, record_name: str) -> str:
        """找出某個記錄項目屬於哪一個檔案。"""
        for fd_name, fields in self.layout.records.items():
            for field in fields:
                for child in field.walk():
                    if child.name == (record_name or "").upper():
                        return fd_name
        for fd_name, fields in self.layout.records.items():
            if fd_name == (record_name or "").upper():
                return fd_name
        return record_name or ""

    def _exec_write(self, node) -> None:
        file_name = self._file_of_record(node.target.name)
        state = self._file_state(file_name)
        if len(state["records"]) >= limits.MAX_FILE_RECORDS:
            raise RuntimeError_(
                f"檔案 {file_name} 超過 {limits.MAX_FILE_RECORDS} 筆紀錄，可能是無窮迴圈一直在寫檔"
            )
        state["records"].append(self._record_for_output(node))

    def _exec_delete(self, node) -> None:
        state = self._file_state(self._file_of_record(node.target.name))
        position = state["position"] - 1
        if 0 <= position < len(state["records"]):
            del state["records"][position]
            return
        raise RuntimeError_("DELETE 之前要先 READ 到一筆紀錄")

    def _exec_rewrite(self, node) -> None:
        state = self._file_state(self._file_of_record(node.target.name))
        position = state["position"] - 1
        if not 0 <= position < len(state["records"]):
            raise RuntimeError_("REWRITE 之前要先 READ 到一筆紀錄")
        state["records"][position] = self._record_for_output(node)

    def _record_for_output(self, node) -> str:
        """WRITE／REWRITE：有 FROM 就先把來源搬進記錄區，再取出整筆記錄。"""
        target = self.resolve(node.target)
        if node.source is not None:
            self.set_reference(target, self.get_reference(self.resolve(node.source)))
        return self.record_text(target)

    # ---------------------------------------------------------------- 鍵值存取

    def _ensure_records(self, name: str, state) -> None:
        """確定記憶體裡有紀錄可查：沒開過檔就試著從磁碟載入。"""
        if state.get("loaded") or state["records"]:
            return
        select = self.layout.selects.get(name)
        assign = select.get("assign") if select else name
        state["records"] = self._load_disk_records(assign or name)
        state["assign"] = assign or name
        state["loaded"] = True

    def _record_spans(self, fd_name: str) -> list[tuple]:
        """把 FD 的記錄版面攤平成 ``[(欄位, 起始, 長度, 在表格裡)]``。"""
        fields = self.layout.records.get((fd_name or "").upper())
        if not fields:
            raise RuntimeError_(f"檔案 {fd_name} 沒有記錄描述（FD 裡沒有 01 項目）")
        spans: list[tuple] = []
        offset = 0
        for field in fields:
            offset = self._collect_spans(field, offset, False, spans)
        return spans

    def _collect_spans(self, field, offset: int, in_occurs: bool, spans: list) -> int:
        """記錄版面：長度和 WRITE 寫出的記錄一致（見 :meth:`element_length`）。"""
        in_occurs = in_occurs or field.has_occurs
        if not field.is_group:
            length = self.element_length(field)
            spans.append((field, offset, length, in_occurs))
            return offset + length * field.max_occurs
        start = offset
        for child in field.children:
            if child.redefines is not None:
                continue
            offset = self._collect_spans(child, offset, in_occurs, spans)
        # 群組本身有 OCCURS 時，整組重複 max_occurs 次
        return start + (offset - start) * field.max_occurs

    def _find_key_span(self, fd_name: str, key_name: str) -> tuple[int, int, object]:
        """找出鍵值欄位在紀錄字串裡的位置；表格裡的項目不能當鍵值用。"""
        simple = (key_name or "").upper().split(" OF ", 1)[0]
        for field, offset, length, in_occurs in self._record_spans(fd_name):
            if field.name == simple:
                if in_occurs:
                    raise RuntimeError_(
                        f"鍵值欄位 {key_name} 在表格裡，本系統只支援非表格的鍵值"
                    )
                return offset, length, field
        raise RuntimeError_(f"檔案 {fd_name} 的記錄裡找不到鍵值欄位 {key_name}")

    def _record_key(self, record: str, fd_name: str, key_name: str):
        """從一筆紀錄字串取出鍵值（不足長度時右邊補空白）。"""
        offset, length, _field = self._find_key_span(fd_name, key_name)
        return record[offset : offset + length].ljust(length)

    def _compare_key_triple(self, left_text: str, right_text: str, span) -> int:
        """三向比較兩個鍵值字串：-1／0／1。

        數字鍵值比數值（``007`` 和 ``7`` 視為相同），文字鍵值比字元
        （右邊空白不影響）。
        """
        _offset, _length, field = span
        pic = getattr(field, "pic", None)
        if pic is not None and pic.category != CAT_ALPHANUMERIC:
            try:
                left_num = Decimal(left_text.strip() or "0")
                right_num = Decimal(right_text.strip() or "0")
                return (left_num > right_num) - (left_num < right_num)
            except (InvalidOperation, RuntimeError_):
                pass
        width = max(len(left_text), len(right_text))
        left = left_text.ljust(width)
        right = right_text.ljust(width)
        return (left > right) - (left < right)

    # ---------------------------------------------------------------- SORT／MERGE／START

    def _sort_inputs(self, node, file_names: list) -> list[list[str]]:
        """依序讀入每個 USING 檔案的全部紀錄；使用中（沒 CLOSE）的檔案先報錯。"""
        grouped: list[list[str]] = []
        for identifier in file_names:
            name = (identifier.name or "").upper()
            state = self._file_state(name)
            if state.get("open") is not None:
                raise RuntimeError_(f"SORT／MERGE 之前要先把 {name} CLOSE 起來")
            select = self.layout.selects.get(name)
            assign = select.get("assign") if select else name
            grouped.append(self._load_disk_records(assign or name))
        return grouped

    def _sort_spec(self, node) -> tuple[str, list[tuple]]:
        """解析 SORT／MERGE 節點的檔案與鍵值，回傳 (fd 名稱, [(方向, [(起點, 長度, 欄位)])]。"""
        fd_name = (node.sort_file.name or "").upper()
        spec_keys = []
        for direction, key_list in node.keys:
            spans = []
            for key in key_list:
                spans.append(self._find_key_span(fd_name, key.name))
            spec_keys.append((direction, spans))
        return fd_name, spec_keys

    def _sort_records(self, records: list[str], spec_keys) -> list[str]:
        """依鍵值規格穩定排序（Python 的 sort 本來就是穩定的）。"""
        flat = [(direction, span) for direction, spans in spec_keys for span in spans]
        decorated = []
        for record in records:
            texts = [record[offset : offset + length].ljust(length) for _, (offset, length, _f) in flat]
            decorated.append((texts, record))

        def compare(left, right) -> int:
            for index, (direction, span) in enumerate(flat):
                result = self._compare_key_triple(left[0][index], right[0][index], span)
                if result:
                    return result if direction == "ASCENDING" else -result
            return 0

        decorated.sort(key=cmp_to_key(compare))
        return [record for _, record in decorated]

    def _write_sort_output(self, giving, records: list[str]) -> None:
        """把排序結果寫到 GIVING 檔案（磁碟＋記憶體都要更新）。"""
        name = (giving.name or "").upper()
        state = self._file_state(name)
        if state.get("open") is not None:
            raise RuntimeError_(f"SORT／MERGE 之前要先把 {name} CLOSE 起來")
        select = self.layout.selects.get(name)
        assign = select.get("assign") if select else name
        assign = assign or name
        path = self._data_path(assign)
        try:
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                for record in records:
                    handle.write(record + "\n")
        except OSError as error:
            raise RuntimeError_(f"寫入檔案 {assign} 失敗：{error}") from None
        state["assign"] = assign
        state["records"] = list(records)
        state["position"] = 0
        state["loaded"] = True
        state["fd"] = self.layout.fd_of_file.get(name, name)

    def _exec_sort(self, node) -> None:
        grouped = self._sort_inputs(node, node.using)
        records = [record for group in grouped for record in group]
        _fd_name, spec_keys = self._sort_spec(node)
        self._write_sort_output(node.giving, self._sort_records(records, spec_keys))

    def _exec_merge(self, node) -> None:
        grouped = self._sort_inputs(node, node.using)
        _fd_name, spec_keys = self._sort_spec(node)
        # MERGE 要求每個輸入檔各自已經排好：逐檔驗證，沒排好就報清楚的錯
        for group in grouped:
            if self._sort_records(list(group), spec_keys) != list(group):
                raise RuntimeError_("MERGE 的輸入檔必須先排好順序（和 ON ... KEY 的方向一致）")
        records = [record for group in grouped for record in group]
        self._write_sort_output(node.giving, self._sort_records(records, spec_keys))

    def _exec_start(self, node) -> None:
        name = (node.file.name or "").upper()
        state = self._file_state(name)
        self._ensure_records(name, state)
        if node.key is None:
            state["position"] = 0
            return
        wanted = self.get_reference(self.resolve(node.key))
        fd_name = state.get("fd") or name
        operator = node.operator or "="
        for index, record in enumerate(state["records"]):
            if self.compare(self._record_key(record, fd_name, node.key.name), wanted, operator):
                state["position"] = index
                return
        if node.get("invalid_key"):
            self.execute_statements(node.get("invalid_body") or [])
            return
        raise RuntimeError_(f"START 在 {name} 找不到符合的紀錄")
