"""Parser 敘述（上）：段落結構、DISPLAY／MOVE／算術／IF／EVALUATE。"""
from __future__ import annotations

from .. import nodes
from ..lexer import COMMA, NUMBER, OP, PERIOD, STRING, WORD
from .base import (
    ParserBase,
    SCOPED_TERMINATORS,
    VERBS,
    _PICTURE_STOPPERS,
    _RELATIONS,
)

_PHRASE_AFTER_NOT = frozenset({"ON", "AT", "INVALID", "SIZE", "OVERFLOW", "END", "EXCEPTION"})

#: ON SIZE ERROR／ON OVERFLOW／ON EXCEPTION 短語的關鍵字（ON 可省略）
_PHRASE_HEADS = ("SIZE", "OVERFLOW", "EXCEPTION")


class ProcParser(ParserBase):
    """解析段落與前半段敘述。"""
    def parse_body(self, end_declaratives: bool) -> tuple[list, list]:
        """解析段落串列；回傳 (declaratives, paragraphs)。"""
        declaratives: list = []
        paragraphs: list = []
        current_section = ""
        target = declaratives if end_declaratives else paragraphs
        current: nodes.Paragraph | None = None
        #: 句子編號：每遇到一個句點（或新段落）就加一，NEXT SENTENCE 依此跳轉
        sentence = 0

        while not self.at_eof():
            if end_declaratives and self.at_word("END") and self.peek(1).is_word("DECLARATIVES"):
                self.advance()
                self.advance()
                self.eat_period()
                end_declaratives = False
                target = paragraphs
                current = None
                current_section = ""
                continue

            if self.at_word("USE"):
                self.skip_to_period()
                continue

            # SECTION 標頭
            if (
                self.tok.kind == WORD
                and self.peek(1).is_word("SECTION")
                and self.tok.upper not in _PICTURE_STOPPERS
                # `EXIT SECTION` 是敘述，不是名叫 EXIT 的 SECTION
                and self.tok.upper not in VERBS
            ):
                current_section = self.advance().value.upper()
                self.advance()
                self.eat_period()
                current = None
                continue

            # 段落標頭：WORD + PERIOD，且不是動詞
            if self._at_paragraph_name():
                name = self.advance().value.upper()
                self.eat_period()
                current = nodes.Paragraph("paragraph", line=self.tok.line, name=name, statements=[], section_name=current_section)
                target.append(current)
                sentence += 1
                continue

            if self.at_period():
                self.advance()
                sentence += 1
                continue

            before_pos = self.pos
            statement = self.parse_statement()
            if statement is None:
                if self.pos == before_pos:
                    self.advance()
                continue
            if current is None:
                # 沒有段落標頭就開始寫：隱含段落
                current = nodes.Paragraph("paragraph", line=statement.line, name="", statements=[], section_name=current_section)
                target.append(current)
            statement.sentence = sentence
            current.statements.append(statement)

        return declaratives, paragraphs

    def _at_paragraph_header(self) -> bool:
        """下一個詞形是不是段落標頭（``P-A.``）。

        段落標頭長得像一般的識別字，所以凡是「一路讀到句點為止」的清單都要
        在這裡停下來，否則會把段落名稱當成接收欄位或檔名。
        判斷依據是「行首」：段落標頭一定另起一行，因此不會把 ``DISPLAY T.``
        的運算元或 ``MOVE X TO A B`` 同一行的第二個接收項誤判；
        而自由格式允許段落之間不寫結束句點（只換行），這種一定要認得，
        否則段落名會被吃成上一個敘述的接收欄位。
        """
        if self.tok.kind != WORD or self.peek(1).kind != PERIOD:
            return False
        if self.pos > 0 and self.tokens[self.pos - 1].line == self.tok.line:
            return False
        return self._at_paragraph_name()

    def _at_paragraph_name(self) -> bool:
        if self.tok.kind != WORD or self.tok.upper in VERBS:
            return False
        if self.tok.upper in SCOPED_TERMINATORS:
            return False
        if self.tok.upper in ("END", "EJECT", "SKIP1", "SKIP2", "SKIP3", "TITLE"):
            return False
        if self.tok.upper in ("SECTION", "DECLARATIVES"):
            return False
        return self.peek(1).kind == PERIOD

    # ---------------------------------------------------------------- 敘述

    def parse_statement(self):
        token = self.tok
        if token.kind != WORD:
            self.fail(f"預期一個敘述動詞，但讀到 '{token.value}'")
        verb = token.upper
        line, column = token.line, token.column

        if verb in SCOPED_TERMINATORS:
            self.fail(f"這裡沒有可以結束的結構，但讀到 {verb}")

        if verb == "DISPLAY":
            return self.parse_display(line, column)
        if verb == "MOVE":
            return self.parse_move(line, column)
        if verb == "COMPUTE":
            return self.parse_compute(line, column)
        if verb == "ADD":
            return self.parse_add(line, column)
        if verb == "SUBTRACT":
            return self.parse_subtract(line, column)
        if verb == "MULTIPLY":
            return self.parse_multiply(line, column)
        if verb == "DIVIDE":
            return self.parse_divide(line, column)
        if verb == "IF":
            return self.parse_if(line, column)
        if verb == "EVALUATE":
            return self.parse_evaluate(line, column)
        if verb == "PERFORM":
            return self.parse_perform(line, column)
        if verb == "EXIT":
            return self.parse_exit(line, column)
        if verb == "CONTINUE":
            self.advance()
            return nodes.Node("continue", line, column)
        if verb == "NEXT":
            self.advance()
            self.expect_word("SENTENCE")
            return nodes.Node("next_sentence", line, column)
        if verb in ("GO", "GOTO"):
            return self.parse_go_to(line, column)
        if verb == "STOP":
            self.advance()
            self.eat_word("RUN")
            code = None
            if self.at_word("WITH") or self.at_word("RUN"):
                pass
            return nodes.Node("stop_run", line, column, code=code)
        if verb == "GOBACK":
            self.advance()
            return nodes.Node("goback", line, column)
        if verb == "RETURN-CODE":
            return None
        if verb == "SET":
            return self.parse_set(line, column)
        if verb == "INITIALIZE":
            return self.parse_initialize(line, column)
        if verb == "INSPECT":
            return self.parse_inspect(line, column)
        if verb == "STRING":
            return self.parse_string(line, column)
        if verb == "UNSTRING":
            return self.parse_unstring(line, column)
        if verb == "SEARCH":
            return self.parse_search(line, column)
        if verb == "CALL":
            return self.parse_call(line, column)
        if verb == "ACCEPT":
            return self.parse_accept(line, column)
        if verb == "OPEN":
            return self.parse_open(line, column)
        if verb == "CLOSE":
            self.advance()
            # `CLOSE A B` 或 `CLOSE A, B`：檔名之間可以只用空白隔開
            names: list = []
            while not self._at_open_end():
                if self.tok.kind == COMMA or self.at_word("WITH", "LOCK", "NO", "REWIND"):
                    self.advance()
                    continue
                name = self.parse_identifier()
                if name is None:
                    break
                names.append(name)
            return nodes.Node("close", line, column, files=names)
        if verb == "READ":
            return self.parse_read(line, column)
        if verb == "WRITE":
            return self.parse_write(line, column)
        if verb == "DELETE":
            self.advance()
            self.eat_word("FILE")
            target = self.parse_identifier()
            self.eat_word("RECORD")
            return nodes.Node("delete", line, column, target=target)
        if verb == "REWRITE":
            self.advance()
            target = self.parse_identifier()
            self.eat_word("RECORD")
            source = None
            if self.eat_word("FROM"):
                source = self.parse_identifier()
            return nodes.Node("rewrite", line, column, target=target, source=source)
        if verb == "SORT":
            return self.parse_sort_merge(line, column, "SORT")
        if verb == "MERGE":
            return self.parse_sort_merge(line, column, "MERGE")
        if verb == "START":
            return self.parse_start(line, column)
        if verb == "RELEASE":
            # RELEASE 需要搭配 SORT 的 INPUT PROCEDURE，本系統不支援那種形式
            self.advance()
            self.skip_to_period()
            return None
        self.fail(f"不支援的敘述：{verb}")
        return None

    # ---- DISPLAY

    def _at_list_end(self) -> bool:
        """判斷一個「一路讀到句點為止」的清單是否已經讀完。

        自由格式的程式常常不寫句點，所以遇到下一個敘述動詞、
        或某個結構的結束關鍵字時就必須停下來。
        """
        if self.at_eof() or self.at_period():
            return True
        if self._at_paragraph_header():
            return True
        if self.tok.kind == WORD:
            if self.tok.upper in SCOPED_TERMINATORS:
                return True
            if self.tok.upper == "NOT" and self.peek(1).kind == WORD and self.peek(1).upper in _PHRASE_AFTER_NOT:
                return True
            return self.tok.upper in VERBS
        return False

    def parse_display(self, line: int, column: int):
        self.advance()
        items: list = []
        upon = None
        no_advancing = False
        while not self._at_list_end():
            if self.at_word("UPON"):
                self.advance()
                if self.tok.kind == WORD:
                    upon = self.advance().upper
                continue
            if self.at_word("WITH"):
                self.advance()
                self.eat_word("NO")
                self.eat_word("ADVANCING")
                no_advancing = True
                continue
            items.append(self.parse_operand())
            if self.tok.kind == COMMA:
                self.advance()
                continue
        if not items:
            self.fail("DISPLAY 敘述缺少要顯示的內容")
        return nodes.Node("display", line, column, items=items, upon=upon, no_advancing=no_advancing)

    # ---- MOVE

    def parse_move(self, line: int, column: int):
        self.advance()
        corresponding = False
        if self.at_word("CORRESPONDING", "CORR"):
            self.advance()
            corresponding = True
        source = self.parse_operand()
        if not self.eat_word("TO"):
            self.fail("MOVE 敘述缺少 TO")
        targets = self.parse_receiving_list()
        return nodes.Node(
            "move", line, column, source=source, targets=targets, corresponding=corresponding
        )

    def parse_receiving_list(self) -> list:
        """接收欄位清單：`MOVE SPACES TO A B C` 的空白也能當分隔符。"""
        targets = [self.parse_operand()]
        while True:
            if self.tok.kind == COMMA:
                self.advance()
                targets.append(self.parse_operand())
                continue
            if self.tok.kind == WORD and not self._at_receiving_end():
                targets.append(self.parse_operand())
                continue
            break
        return targets

    def _at_receiving_end(self) -> bool:
        """接收欄位清單在這裡結束（句點、下一個敘述、段落標頭、關鍵字）。"""
        if self.at_eof() or self.at_period():
            return True
        if self._at_paragraph_header():
            return True
        if self.tok.kind == WORD:
            if self.tok.upper in SCOPED_TERMINATORS or self.tok.upper in VERBS:
                return True
            return self.tok.upper in (
                "BY", "GIVING", "ON", "NOT", "TO", "FROM", "INTO", "REPLACING",
                "REMAINDER",
            ) + _PHRASE_HEADS
        return self.tok.kind == OP and self.tok.value in "+-*/=<>"

    # ---- COMPUTE

    def parse_compute(self, line: int, column: int):
        self.advance()
        targets: list[tuple] = []
        while True:
            target = self.parse_identifier()
            rounded = self._eat_rounded()
            targets.append((target, rounded))
            if self.tok.kind == COMMA:
                self.advance()
                continue
            # `COMPUTE A B = ...` 的多個接收欄位可以用空白隔開；
            # 遇到 =、動詞、段落標頭就停
            if self.tok.kind == WORD and not self._at_compute_end():
                continue
            break
        if not self.eat_word("EQUAL", "EQUALS"):
            if self.tok.kind == OP and self.tok.value == "=":
                self.advance()
            else:
                self.fail("COMPUTE 敘述缺少 =")
        expr = self.parse_arithmetic()
        on_size_error = self._parse_size_error_phrases()
        self.eat_word("END-COMPUTE")
        return nodes.Node(
            "compute", line, column, targets=targets, expr=expr, on_size_error=on_size_error
        )

    def _at_compute_end(self) -> bool:
        """COMPUTE 的接收欄位清單在這裡結束（=、句點、下一個敘述）。"""
        if self.at_eof() or self.at_period():
            return True
        if self._at_paragraph_header():
            return True
        if self.tok.kind == OP and self.tok.value == "=":
            return True
        if self.tok.kind == WORD:
            if self.tok.upper in SCOPED_TERMINATORS or self.tok.upper in VERBS:
                return True
            return self.tok.upper in ("EQUAL", "EQUALS", "ROUNDED", "ON", "NOT")
        return True

    def _eat_rounded(self) -> bool:
        if self.at_word("ROUNDED"):
            self.advance()
            # ROUNDED 後面可能有 MODE [IS] 捨入方式，但本系統一律用四捨五入；
            # 只在明確寫了 MODE 時才吃掉這三個字，否則會把下一個敘述的動詞吃掉。
            if self.eat_word("MODE"):
                self.eat_word("IS")
                if self.tok.kind == WORD:
                    self.advance()
            return True
        return False

    def _at_size_phrase_start(self) -> bool:
        """下一個詞形是不是 ON/NOT 短語的開頭（不消耗任何詞形）。

        供敘述清單在短語邊界停下來：`ON SIZE ERROR`、`ON OVERFLOW`、
        `ON EXCEPTION` 以及各自的 `NOT` 形式（含 `AT` 變體）。
        標準裡 ON 可以省略，所以 `SIZE ERROR`、`NOT SIZE ERROR` 也算。
        """
        if self.tok.kind != WORD or self.tok.upper not in ("ON", "AT", "NOT") + _PHRASE_HEADS:
            return False
        save = self.pos
        if self.tok.kind == WORD and self.tok.upper == "NOT":
            self.pos += 1
            if self.at_eof():
                self.pos = save
                return False
        if self.tok.kind == WORD and self.tok.upper in ("ON", "AT"):
            self.pos += 1
            if self.at_eof():
                self.pos = save
                return False
        is_phrase = self.tok.kind == WORD and self.tok.upper in _PHRASE_HEADS
        self.pos = save
        return is_phrase

    def _parse_size_error_phrases(self):
        """解析 ON SIZE ERROR / ON OVERFLOW 與 NOT ON SIZE ERROR。"""
        result = {}
        while self._at_size_phrase_start():
            negated = bool(self.eat_word("NOT"))
            self.eat_word("ON", "AT")  # ON 可以省略
            if self.eat_word("SIZE"):
                self.eat_word("ERROR")
                kind = "size_error"
            elif self.eat_word("OVERFLOW"):
                kind = "overflow"
            else:
                self.eat_word("EXCEPTION")
                kind = "exception"
            if negated:
                kind = "not_" + kind
            if kind == "exception" or kind == "not_exception":
                self.skip_to_period()
                continue
            body = self.parse_statement_list(("END-IF",))
            if self.at_word("END-IF"):
                self.advance()
            result[kind] = body
        return result

    # ---- ADD / SUBTRACT / MULTIPLY / DIVIDE

    def _parse_operand_list(self, stop_words: tuple[str, ...]) -> list:
        """解析「用空白或逗號隔開」的運算元清單，遇到關鍵字就停。"""
        operands = [self.parse_operand()]
        while True:
            if self.at_eof() or self.at_period():
                break
            if self.tok.kind == COMMA:
                self.advance()
                continue
            if self.tok.kind == OP and self.tok.value in "+-*/":
                # 算式裡的運算子屬於前一個運算元，不切斷清單
                break
            if self.tok.kind == WORD:
                upper = self.tok.upper
                if upper in stop_words or upper in SCOPED_TERMINATORS or upper in VERBS:
                    break
            operands.append(self.parse_operand())
        return operands


    def _parse_rounded_targets(self) -> list[tuple]:
        """接收欄位清單：``A ROUNDED, B C ROUNDED``，逗號可省略。"""
        targets = []
        while True:
            target = self.parse_identifier()
            targets.append((target, self._eat_rounded()))
            if self.tok.kind == COMMA:
                self.advance()
                continue
            if self.tok.kind == WORD and not self._at_receiving_end():
                continue
            return targets

    def parse_add(self, line: int, column: int):
        self.advance()
        operands = self._parse_operand_list(("TO", "GIVING", "ON", "AT", "NOT"))
        to_targets: list[tuple] = []
        giving: list[tuple] = []
        while True:
            if self.at_word("TO"):
                self.advance()
                to_targets.extend(self._parse_rounded_targets())
                continue
            if self.at_word("GIVING"):
                self.advance()
                giving.extend(self._parse_rounded_targets())
                continue
            break
        if not to_targets and not giving:
            self.fail("ADD 敘述缺少 TO 或 GIVING")
        on_size_error = self._parse_size_error_phrases()
        self.eat_word("END-ADD")
        return nodes.Node(
            "add", line, column, operands=operands, to_targets=to_targets,
            giving=giving, on_size_error=on_size_error
        )

    def parse_subtract(self, line: int, column: int):
        self.advance()
        operands = self._parse_operand_list(("FROM", "GIVING", "ON", "AT", "NOT"))
        from_targets: list[tuple] = []
        giving: list[tuple] = []
        if self.eat_word("FROM"):
            from_targets.extend(self._parse_rounded_targets())
        if self.eat_word("GIVING"):
            giving.extend(self._parse_rounded_targets())
        on_size_error = self._parse_size_error_phrases()
        self.eat_word("END-SUBTRACT")
        return nodes.Node(
            "subtract", line, column, operands=operands, from_targets=from_targets,
            giving=giving, on_size_error=on_size_error
        )

    def parse_multiply(self, line: int, column: int):
        self.advance()
        left = self.parse_operand()
        self.eat_word("BY")
        right = self.parse_operand()
        right_rounded = self._eat_rounded()
        giving: list[tuple] = []
        if self.eat_word("GIVING"):
            giving.extend(self._parse_rounded_targets())
        on_size_error = self._parse_size_error_phrases()
        self.eat_word("END-MULTIPLY")
        return nodes.Node(
            "multiply", line, column, left=left, right=right, right_rounded=right_rounded,
            giving=giving, on_size_error=on_size_error
        )

    def parse_divide(self, line: int, column: int):
        self.advance()
        left = self.parse_operand()
        # `DIVIDE a INTO b` 是把 a 除進 b（b = b / a）；
        # `DIVIDE a BY b` 是 a 除以 b（結果 = a / b）。兩者方向相反。
        by_form = False
        if self.at_word("BY"):
            self.advance()
            by_form = True
        else:
            self.eat_word("INTO")
        right = self.parse_operand()
        right_rounded = self._eat_rounded()
        into: list[tuple] = []
        giving: list[tuple] = []
        remainder_target = None
        while True:
            if self.at_word("INTO"):
                self.advance()
                into.extend(self._parse_rounded_targets())
                continue
            if self.at_word("GIVING"):
                self.advance()
                giving.extend(self._parse_rounded_targets())
                continue
            if self.at_word("REMAINDER"):
                self.advance()
                remainder_target = self.parse_identifier()
                continue
            break
        on_size_error = self._parse_size_error_phrases()
        self.eat_word("END-DIVIDE")
        return nodes.Node(
            "divide", line, column, left=left, right=right, right_rounded=right_rounded,
            into=into, giving=giving, remainder=remainder_target,
            on_size_error=on_size_error, by_form=by_form
        )

    # ---- IF

    def parse_if(self, line: int, column: int):
        self.advance()
        condition = self.parse_condition()
        self.eat_word("THEN")
        then_body = self.parse_statement_list(("ELSE", "END-IF"))
        else_body: list = []
        self._eat_period_before("ELSE", "END-IF")
        if self.at_word("ELSE"):
            self.advance()
            if self.at_word("IF"):
                nested = self.parse_if(self.tok.line, self.tok.column)
                else_body = [nested]
                return nodes.Node("if", line, column, condition=condition, then_body=then_body, else_body=else_body)
            else_body = self.parse_statement_list(("END-IF",))
            self._eat_period_before("END-IF")
        self.eat_word("END-IF")
        return nodes.Node("if", line, column, condition=condition, then_body=then_body, else_body=else_body)

    # ---- EVALUATE

    def parse_compare(self):
        """解析「運算式 [關係運算子 運算式]」；沒有運算子時就只回傳運算式。"""
        left = self.parse_arithmetic()
        while self.tok.kind == OP and self.tok.value in _RELATIONS:
            token = self.advance()
            right = self.parse_arithmetic()
            left = nodes.Node("relation", token.line, token.column, op=token.value, left=left, right=right)
        if self.at_word("AND", "OR"):
            token = self.advance()
            right = self.parse_compare()
            left = nodes.Node("logical", token.line, token.column, op=token.upper, left=left, right=right)
        return left

    def parse_evaluate(self, line: int, column: int):
        self.advance()
        subjects: list = [self._parse_evaluate_subject()]
        while self.at_word("ALSO"):
            self.advance()
            subjects.append(self._parse_evaluate_subject())
        whens: list[tuple] = []
        when_other: list = []
        pending: list = []          # 連續 WHEN 累積的條件（共用下一個 body）
        while not self.at_eof() and not self.at_word("END-EVALUATE"):
            if self.at_word("WHEN"):
                self.advance()
                if self.at_word("OTHER"):
                    self.advance()
                    when_other = self.parse_statement_list(("WHEN", "END-EVALUATE"))
                    self._eat_period_before("WHEN", "END-EVALUATE")
                    # OTHER 的 body 與前面累積的空 WHEN 共用
                    if pending:
                        whens.extend((cond, when_other) for cond in pending)
                        pending = []
                    continue
                conditions: list = []
                while True:
                    index = len(conditions)
                    if self.at_word("TRUE"):
                        self.advance()
                        conditions.append(nodes.Node("cond_true", line, column))
                    elif self.at_word("FALSE"):
                        self.advance()
                        conditions.append(nodes.Node("cond_false", line, column))
                    elif self.at_word("ANY"):
                        self.advance()
                        conditions.append(nodes.Node("cond_any", line, column))
                    elif index < len(subjects) and _is_boolean_subject(subjects[index]):
                        # 主體是 TRUE／FALSE 或條件時，WHEN 後面是一個完整的條件
                        conditions.append(self.parse_condition())
                    else:
                        conditions.append(self.parse_compare())
                    if self.at_word("ALSO"):
                        self.advance()
                        continue
                    break
                body = self.parse_statement_list(("WHEN", "END-EVALUATE"))
                self._eat_period_before("WHEN", "END-EVALUATE")
                if not body and self.at_word("WHEN"):
                    # 空分支：與下一個 WHEN 共用敘述
                    pending.append(conditions)
                    continue
                if pending:
                    whens.extend((cond, body) for cond in pending)
                    pending = []
                whens.append((conditions, body))
                continue
            break
        # 迴圈結束前，把剩下的 pending 以空 body 補進 whens
        for cond in pending:
            whens.append((cond, []))
        self.eat_word("END-EVALUATE")
        return nodes.Node("evaluate", line, column, subjects=subjects, whens=whens, when_other=when_other)

    def _parse_evaluate_subject(self):
        """EVALUATE 的主體可以是運算式、TRUE／FALSE，或是一個條件（``A = 1``）。"""
        subject = self.parse_condition()
        # 單純的運算式會被 parse_condition 包成「IS_TRUE」節點，這裡拆回原本的運算式
        if subject.kind == "relation" and subject.get("op") == "IS_TRUE" and subject.get("right") is None:
            return subject.left
        return subject

    def _looks_like_operand_start(self) -> bool:
        return self.tok.kind == OP or self.tok.kind in (STRING, NUMBER)

    # ---- PERFORM


def _is_boolean_subject(subject) -> bool:
    """EVALUATE 主體是不是布林值（TRUE／FALSE 或條件運算式）。"""
    if subject.kind == "figurative" and subject.get("name") in ("TRUE", "FALSE"):
        return True
    return subject.kind in ("relation", "logical", "class_condition", "sign_condition")
