"""直譯器流程敘述：MOVE／IF／EVALUATE／PERFORM／GO TO／SET。"""
from __future__ import annotations

from ..errors import RuntimeError_, StopRun
from ..layout import Field
from ..pic import CAT_NUMERIC_EDITED
from .values import (
    ExitParagraphSignal,
    ExitPerformSignal,
    ExitSectionSignal,
    GoToSignal,
    NextSentenceSignal,
    Reference,
)


class FlowMixin:
    """流程控制與 MOVE／SET 的執行。"""
    def _exec_move(self, node) -> None:
        if node.corresponding:
            self._move_corresponding(node)
            return
        if node.source.kind == "identifier":
            reference = self.resolve(node.source)
            value = self.get_reference(reference)
            if reference.field.pic is not None and reference.field.pic.category == CAT_NUMERIC_EDITED:
                value = self.to_decimal(value)
            for target in node.targets:
                if target.kind == "identifier":
                    self.set_reference(self.resolve(target), value)
                else:
                    self._assign_placeholder(target, value)
            return
        source = self.eval(node.source)
        for target in node.targets:
            if target.kind == "identifier":
                self.set_reference(self.resolve(target), source)
            else:
                self._assign_placeholder(target, source)

    def _assign_placeholder(self, target, value) -> None:  # pragma: no cover - 防禦性
        raise RuntimeError_("MOVE 的接收端必須是資料項目")

    def _move_corresponding(self, node) -> None:
        """MOVE CORRESPONDING：把兩邊群組裡**名稱相同**的子項一對一搬移。"""
        if node.source.kind != "identifier" or not node.targets:
            raise RuntimeError_("MOVE CORRESPONDING 的來源與接收端都必須是資料項目")
        source_ref = self.resolve(node.source)
        source_field = source_ref.field
        for target in node.targets:
            target_ref = self.resolve(target)
            if not source_field.is_group or not target_ref.field.is_group:
                raise RuntimeError_("MOVE CORRESPONDING 的兩邊都必須是群組項目")
            pairs: list = []
            self._correspond_pairs(source_field, target_ref.field, pairs)
            for source_child, target_child in pairs:
                value = self.get_reference(Reference(source_child, source_ref.path))
                if source_child.pic is not None and source_child.pic.category == CAT_NUMERIC_EDITED:
                    value = self.to_decimal(value)
                self.set_reference(Reference(target_child, target_ref.path), value)

    @staticmethod
    def _corresponding_candidates(field: Field) -> dict:
        """可以參與 CORRESPONDING 的子項：有名稱、不是 FILLER、沒有 REDEFINES 或 OCCURS。"""
        return {
            child.name: child
            for child in field.children
            if child.name and child.name != "FILLER" and child.redefines is None and not child.has_occurs
        }

    def _correspond_pairs(self, source_field: Field, target_field: Field, pairs: list) -> None:
        """名稱相同的子項配對：兩邊都是基本項目就搬，兩邊都是群組就往下找。"""
        targets = self._corresponding_candidates(target_field)
        for name, source_child in self._corresponding_candidates(source_field).items():
            target_child = targets.get(name)
            if target_child is None:
                continue
            if source_child.is_group and target_child.is_group:
                self._correspond_pairs(source_child, target_child, pairs)
            elif not source_child.is_group and not target_child.is_group:
                pairs.append((source_child, target_child))

    def _exec_if(self, node) -> None:
        if self.eval_condition(node.condition):
            self.execute_statements(node.then_body)
        else:
            self.execute_statements(node.else_body)

    def _exec_evaluate(self, node) -> None:
        subjects = [self._evaluate_subject(subject) for subject in node.subjects]
        for conditions, body in node.whens:
            matched = True
            for index, condition in enumerate(conditions):
                subject = subjects[index] if index < len(subjects) else None
                subject_node = node.subjects[index] if index < len(node.subjects) else None
                if not self._when_matches(subject, subject_node, condition):
                    matched = False
                    break
            if matched:
                self.execute_statements(body)
                return
        self.execute_statements(node.when_other)

    def _evaluate_subject(self, subject) -> tuple[str, object]:
        """把 EVALUATE 的一個主體求值成 ``("bool", 真假)`` 或 ``("value", 值)``。"""
        if subject.kind == "figurative" and subject.name in ("TRUE", "FALSE"):
            return "bool", subject.name == "TRUE"
        if subject.kind in ("relation", "logical", "class_condition", "sign_condition"):
            return "bool", self.eval_condition(subject)
        if subject.kind == "identifier" and self._is_condition_name(subject.name):
            return "bool", self.eval_condition_name(subject.name, subject.subscripts)
        return "value", self.eval(subject)

    def _when_matches(self, subject, subject_node, condition) -> bool:
        """一個 WHEN 物件是否符合對應的主體。"""
        if condition.kind == "cond_any":
            return True
        if subject is None:
            return False
        mode, value = subject
        if condition.kind in ("cond_true", "cond_false"):
            actual = value if mode == "bool" else self.to_bool(value)
            return actual == (condition.kind == "cond_true")
        if mode == "bool":
            # EVALUATE TRUE／FALSE（或條件主體）：WHEN 的條件真假要和主體一致
            return self.eval_condition(condition) == value
        if condition.kind in ("logical", "class_condition", "sign_condition"):
            return self.eval_condition(condition)
        if condition.kind == "relation" and condition.op != "IS_TRUE":
            return self.compare(value, self.eval(condition.right), condition.op)
        if condition.kind == "identifier" and self._is_condition_name(condition.name):
            return self.eval_condition_name(condition.name, condition.subscripts)
        return self.compare(
            value,
            self.eval(condition),
            "=",
            text_only=self._is_alphanumeric_operand(subject_node)
            and self._is_alphanumeric_operand(condition),
        )

    def _exec_perform(self, node) -> None:
        start, end = 0, len(self.paragraphs) - 1
        if node.target is not None:
            name = (node.target.name or "").upper()
            start = self.para_index.get(name)
            if start is None:
                raise RuntimeError_(f"PERFORM 找不到段落 {node.target.name}")
            end = start
            if node.thru is not None:
                thru_name = (node.thru.name or "").upper()
                if thru_name not in self.para_index:
                    raise RuntimeError_(f"PERFORM THROUGH 找不到段落 {node.thru.name}")
                end = self.para_index[thru_name]
            if end < start:
                raise RuntimeError_("PERFORM THROUGH 的結束段落比開始段落前面")
        self._run_loop(start, end, node)

    def _exec_perform_forever(self, node) -> None:
        self._run_loop(0, len(self.paragraphs) - 1, node)

    def _run_loop(self, start: int, end: int, node) -> None:
        """執行 PERFORM 的迴圈（段落範圍或內文）。"""
        body = node.body if node.target is None else None
        test_after = node.test_after
        varying = node.varying
        until = node.until
        times = node.times

        if varying:
            self._run_varying_chain(0, varying, start, end, body, test_after)
            return

        if until is not None and until.kind == "cond_forever":
            while True:
                self.tick()
                if not self._execute_range(start, end, body):
                    return

        if until is None and times is None:
            # 沒有 UNTIL／TIMES／VARYING 的 PERFORM 只執行一次
            self._execute_range(start, end, body)
            return

        iterations = 0
        limit = None if times is None else max(0, self.to_int(self.eval(times), "TIMES"))
        while True:
            self.tick()
            if not test_after:
                # PERFORM UNTIL 的條件「成立」就代表要停
                if until is not None and self.eval_condition(until):
                    return
                if limit is not None and iterations >= limit:
                    return
            if not self._execute_range(start, end, body):
                return
            iterations += 1
            if test_after:
                if until is not None and self.eval_condition(until):
                    return
                if limit is not None and iterations >= limit:
                    return

    def _run_varying_chain(self, level, varying, start, end, body, test_after) -> bool:
        if level >= len(varying):
            return self._execute_range(start, end, body)
        index, from_expr, by_expr, until = varying[level]
        self.set_reference(self.resolve(index), self.eval(from_expr))
        while True:
            self.tick()
            if self.eval_condition(until):
                return True
            if not self._run_varying_chain(level + 1, varying, start, end, body, test_after):
                return False
            current = self.to_decimal(self.get_reference(self.resolve(index)))
            step = self.to_decimal(self.eval(by_expr))
            self.set_reference(self.resolve(index), current + step)

    def _execute_range(self, start: int, end: int, body) -> bool:
        """執行一個段落範圍或內文；回傳 False 表示 GO TO 跳出了範圍。"""
        if body is not None:
            # 內嵌 PERFORM 裡的 GO TO 一定會離開迴圈：交給外層處理跳轉
            try:
                self.execute_statements(body)
            except ExitPerformSignal as signal:
                # EXIT PERFORM CYCLE：跳到下一輪；EXIT PERFORM：結束整個迴圈
                return signal.cycle
            return True
        index = start
        while index <= end:
            paragraph = self.paragraphs[index]
            try:
                self.run_paragraph(paragraph)
            except ExitSectionSignal:
                index = min(self.section_end(index), end) + 1
                continue
            except GoToSignal as signal:
                target = self.para_index.get(signal.target.upper())
                if target is None:
                    raise RuntimeError_(f"GO TO 找不到段落 {signal.target}") from None
                if start <= target <= end:
                    index = target
                    continue
                # 跳到 PERFORM 範圍外：PERFORM 被放棄，控制權轉移到目標段落
                raise
            index += 1
        return True

    def _exec_continue(self, node) -> None:
        return None

    def _exec_exit_paragraph(self, node) -> None:
        raise ExitParagraphSignal()

    def _exec_exit_section(self, node) -> None:
        raise ExitSectionSignal()

    def _exec_next_sentence(self, node) -> None:
        raise NextSentenceSignal()

    def _exec_exit_program(self, node) -> None:
        raise StopRun(self.return_code)

    def _exec_exit_perform(self, node) -> None:
        raise ExitPerformSignal(bool(node.get("cycle")))

    def _exec_go_to(self, node) -> None:
        if not node.targets:
            raise RuntimeError_("GO TO 缺少目標段落")
        raise GoToSignal(node.targets[0].name)

    def _exec_go_to_depending(self, node) -> None:
        index = self.to_int(self.eval(node.subject), "GO TO DEPENDING ON")
        if index < 1 or index > len(node.targets):
            return None
        raise GoToSignal(node.targets[index - 1].name)

    def _exec_stop_run(self, node) -> None:
        raise StopRun(self.return_code)

    def _exec_goback(self, node) -> None:
        raise StopRun(self.return_code)

    def _exec_set_condition(self, node) -> None:
        """SET 條件名稱 TO TRUE／FALSE：把所屬欄位設成讓條件成立（或不成立）的值。"""
        wanted = node.value.name == "TRUE"
        for target in node.targets:
            name = (target.name or "").upper()
            found = self._find_condition(name)
            if found is None:
                raise RuntimeError_(f"SET 找不到條件名稱 {name}")
            field, condition = found
            self.storage.set(condition, (), wanted)
            ranges = self.condition_ranges(condition)
            if ranges and ranges[0][0].kind == "figurative" and ranges[0][0].value in ("TRUE", "FALSE"):
                continue
            reference = self.condition_reference(field, target.get("subscripts") or [])
            if wanted:
                # TO TRUE：放入第一個值（THRU 範圍就放下限）
                spec = ranges[0][0]
            else:
                spec = condition.get("false_value")
                if spec is None:
                    raise RuntimeError_(
                        f"SET {name} TO FALSE 需要在 88 宣告寫上 WHEN SET TO FALSE IS 值"
                    )
            self.set_reference(reference, self._value_from_spec(field, spec))

    def _exec_set_index(self, node) -> None:
        for target in node.targets:
            reference = self.resolve(target)
            current = self.to_int(self.get_reference(reference), "索引")
            if node.direction == "TO":
                self.set_reference(reference, self.to_int(self.eval(node.step), "索引"))
            elif node.direction == "UP":
                step = self.to_int(self.eval(node.step), "索引")
                if current + step > 9999:
                    raise RuntimeError_("SET 讓索引超過可用範圍")
                self.set_reference(reference, current + step)
            else:
                step = self.to_int(self.eval(node.step), "索引")
                if current - step < 1:
                    raise RuntimeError_("SET 讓索引小於 1")
                self.set_reference(reference, current - step)
