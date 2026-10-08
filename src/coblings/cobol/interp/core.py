"""直譯器核心：生命週期、段落執行、DISPLAY。"""
from __future__ import annotations

import random
import time
from decimal import Decimal, localcontext
from typing import Callable

from .. import limits
from ..errors import RuntimeError_, StopRun
from ..layout import Field, Layout
from ..nodes import Program
from ..pic import CAT_NUMERIC, CAT_NUMERIC_EDITED, format_decimal
from .util import _describe
from .values import (
    ExitParagraphSignal,
    ExitPerformSignal,
    ExitSectionSignal,
    GoToSignal,
    NextSentenceSignal,
)


class CoreMixin:
    """執行器的主流程（需要其他 mixin 補齊求值與敘述）。"""
    def __init__(
        self,
        program: Program,
        layout: Layout,
        *,
        display: list[str] | None = None,
        timeout: float | None = None,
        paragraph_lookup=None,
        working_dir: str = ".",
        output: Callable[[str], None] | None = None,
    ) -> None:
        self.program = program
        self.layout = layout
        self.storage = layout.storage
        self.display_lines: list[str] = display if display is not None else []
        self.timeout = timeout
        self.deadline = time.monotonic() + timeout if timeout else None
        self.working_dir = working_dir
        #: 程式輸出（DISPLAY 與斷言內建的標記）要送去哪裡；None 表示不輸出
        self.output = output
        self.paragraphs = [p for p in program.paragraphs]
        self.para_index: dict[str, int] = {}
        for index, paragraph in enumerate(self.paragraphs):
            name = (paragraph.name or "").upper()
            if name and name not in self.para_index:
                self.para_index[name] = index
        self.return_code = 0
        self.checks = 0
        #: 檢查器呼叫了 COBLINGS-DONE（學生程式不能呼叫，見 pipeline.link_programs）
        self.passed = False
        self.file_store: dict[str, dict] = {}
        # FUNCTION RANDOM 用的亂數器（每支程式獨立，不影響全域 random）
        self._random = random.Random()

    # ================================================================ 進入點

    def run(self) -> int:
        # 精度只在執行期間生效，不改動整個行程的 decimal 環境
        with localcontext() as context:
            context.prec = limits.NUMERIC_PRECISION
            self.initialize_storage()
            self.initialize_condition_names()
            self.initialize_files()
            try:
                self.execute_main()
            except StopRun as stop:
                return stop.return_code
            return self.return_code

    def emit(self, text: str) -> None:
        """把一行文字送到程式輸出。"""
        if self.output is not None:
            self.output(text)

    def execute_main(self) -> None:
        index = 0
        guard = 0
        limit = limits.MAX_PARAGRAPH_JUMPS
        while 0 <= index < len(self.paragraphs):
            guard += 1
            if guard > limit:
                raise RuntimeError_("程式陷入迴圈：段落跳轉次數過多")
            try:
                self.run_paragraph(self.paragraphs[index])
            except GoToSignal as signal:
                target = self.para_index.get(signal.target.upper())
                if target is None:
                    raise RuntimeError_(f"GO TO 找不到段落 {signal.target}") from None
                index = target
                continue
            except ExitSectionSignal:
                index = self.section_end(index) + 1
                continue
            index += 1

    def run_paragraph(self, paragraph) -> None:
        """執行一個段落：處理 NEXT SENTENCE 與 EXIT PARAGRAPH。"""
        statements = paragraph.statements
        position = 0
        while position < len(statements):
            statement = statements[position]
            try:
                self.execute(statement)
            except NextSentenceSignal:
                # 跳過同一個句子裡剩下的敘述
                sentence = statement.get("sentence", 0)
                position += 1
                while position < len(statements) and statements[position].get("sentence", 0) <= sentence:
                    position += 1
                continue
            except ExitParagraphSignal:
                return
            except ExitPerformSignal:
                raise RuntimeError_(
                    "EXIT PERFORM 只能寫在 PERFORM … END-PERFORM（內嵌 PERFORM）裡面"
                ) from None
            position += 1

    def section_end(self, index: int) -> int:
        """第 ``index`` 個段落所屬 SECTION 的最後一個段落；不在 SECTION 裡就是自己。"""
        section = self.paragraphs[index].get("section_name") or ""
        if not section:
            return index
        last = index
        while last + 1 < len(self.paragraphs) and (
            self.paragraphs[last + 1].get("section_name") or ""
        ) == section:
            last += 1
        return last

    def tick(self) -> None:
        """檢查逾時；每個敘述都會呼叫。"""
        if self.deadline is not None and time.monotonic() > self.deadline:
            raise RuntimeError_("執行時間超過上限，可能有無窮迴圈")

    # ================================================================ 儲存初始化

    def initialize_storage(self) -> None:
        for section_fields in self.layout.sections.values():
            for field in section_fields:
                self._init_field(field, ())
        for records in self.layout.records.values():
            for field in records:
                self._init_field(field, ())
        self._init_overlays()

    def _init_overlays(self) -> None:
        """REDEFINES 的項目一開始的內容就是原本項目的內容（原本的項目排第一個）。"""
        seen: set[int] = set()
        for group in self.layout.overlays.values():
            if id(group) in seen:
                continue
            seen.add(id(group))
            root = group[0]
            if root.has_occurs or any(node.has_occurs for node in self._ancestors(root)):
                continue  # 表格裡的 REDEFINES：初值各自保留
            self.sync_overlay(root, ())

    @staticmethod
    def _ancestors(field):
        node = field.parent
        while node is not None:
            yield node
            node = node.parent

    def _init_field(self, field: Field, path: tuple) -> None:
        if field.occurs_max is not None:
            for index in range(field.max_occurs):
                self.tick()
                # 下標從 1 開始，必須和 resolve() 產生的路徑一致
                child_path = path + (index + 1,)
                if field.is_group:
                    for child in field.children:
                        self._init_field(child, child_path)
                else:
                    self._init_elementary(field, child_path, index)
            return
        if field.is_group:
            for child in field.children:
                self._init_field(child, path)
            return
        self._init_elementary(field, path, 0)

    def _init_elementary(self, field: Field, path: tuple, occurrence: int) -> None:
        if field.usage == "INDEX":
            self.storage.set(field, path, 1)
            return
        values = field.value_spec.values if field.value_spec is not None else []
        if not values:
            self.storage.set(field, path, self.storage.default_for(field))
            return
        spec = values[occurrence] if occurrence < len(values) else values[-1]
        self.storage.set(field, path, self._value_from_spec(field, spec))

    def initialize_condition_names(self) -> None:
        for field in self._all_fields():
            for condition in field.conditions:
                self.storage.set(condition, (), False)

    def _all_fields(self):
        for section_fields in self.layout.sections.values():
            for field in section_fields:
                yield from field.walk()
        for records in self.layout.records.values():
            for field in records:
                yield from field.walk()

    # ================================================================ 值的存取

    def execute_statements(self, statements: list) -> None:
        for statement in statements:
            self.execute(statement)

    def execute(self, node) -> None:
        self.tick()
        handler = getattr(self, "_exec_" + node.kind, None)
        if handler is None:
            raise RuntimeError_(f"尚未實作的敘述：{node.kind}", _describe(node))
        handler(node)

    def perform_paragraph(self, name: str) -> None:
        """執行單一段落（供斷言內建使用）。"""
        index = self.para_index.get(name.upper())
        if index is None:
            raise RuntimeError_(f"找不到段落 {name}")
        try:
            self.run_paragraph(self.paragraphs[index])
        except ExitSectionSignal:
            return
        except GoToSignal as signal:
            target = self.para_index.get(signal.target.upper())
            if target is None:
                raise RuntimeError_(f"GO TO 找不到段落 {signal.target}") from None
            self.run_paragraph(self.paragraphs[target])

    def _exec_display(self, node) -> None:
        parts: list[str] = []
        for item in node.items:
            if item.kind == "identifier":
                value = self.get_reference(self.resolve(item))
            else:
                value = self.eval(item)
            parts.append(self.render_for_display(value, item))
        text = "".join(parts)
        self.display_lines.append(text)
        self.emit(text)

    def render_for_display(self, value, item) -> str:
        """把值轉成 DISPLAY 會印出的字串（含數字編輯欄位格式）。"""
        if item.kind == "identifier":
            reference = self.resolve(item)
            field = reference.field
            if field.blank_when_zero:
                number = self.to_decimal(value)
                if number == 0:
                    return ""
            if field.pic is not None and field.pic.category == CAT_NUMERIC_EDITED:
                return field.pic.to_text(self.to_decimal(value))
            if field.pic is not None and field.pic.category == CAT_NUMERIC and isinstance(value, Decimal):
                pic = field.pic
                # SIGN IS SEPARATE：符號佔用額外位置，數字部分需補零到 int_digits 位
                if field.sign_separate and pic.has_sign:
                    return self._format_separate_sign(value, pic, field.sign_leading)
                text = pic.to_text(abs(value))
                if value < 0 and pic.has_sign:
                    return "-" + text
                return text
        return self._raw_text(value)

    def _format_separate_sign(self, value: Decimal, pic, sign_leading: bool) -> str:
        """格式化 SIGN IS SEPARATE 的數值：數字補零，符號獨立顯示。"""
        magnitude = abs(value)
        # 整數部分補零到 int_digits 位
        int_part = format_decimal(magnitude.to_integral_value(), 0).zfill(pic.int_digits)
        # 小數部分
        if pic.dec_digits > 0:
            dec_part = format_decimal(magnitude, pic.dec_digits)
            if "." in dec_part:
                dec_part = "." + dec_part.split(".", 1)[1]
            else:
                dec_part = "." + "0" * pic.dec_digits
        else:
            dec_part = ""
        number_text = int_part + dec_part
        # 符號：負數顯示 -，正數顯示空格（佔位）
        sign = "-" if value < 0 else " "
        if sign_leading:
            return sign + number_text
        return number_text + sign
