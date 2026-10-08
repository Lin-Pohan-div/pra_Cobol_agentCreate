"""Parser 敘述（下）：PERFORM／GO TO／SET／字串／查表／檔案。"""
from __future__ import annotations

from .. import nodes
from ..lexer import COMMA, NUMBER, OP, STRING, WORD
from .base import ParserBase, SCOPED_TERMINATORS, VERBS


class StmtParser(ParserBase):
    """解析後半段敘述。"""
    def parse_perform(self, line: int, column: int):
        self.advance()

        test_after = False
        if self.at_word("WITH"):
            self.advance()
            self.eat_word("TEST")
            test_after = self.eat_word("AFTER")
            if not test_after:
                self.eat_word("BEFORE")

        target = None
        thru = None
        # `PERFORM 5 TIMES` / `PERFORM N TIMES`：數字或「後面接 TIMES 的字」
        # 是次數，不是段落名稱
        looks_like_count = (
            self.tok.kind == NUMBER and self.peek(1).is_word("TIMES")
        ) or (self.tok.kind == WORD and self.peek(1).is_word("TIMES"))
        if not looks_like_count and self.tok.kind == WORD and self.tok.upper not in VERBS and not self.at_word(
            "TIMES", "UNTIL", "VARYING", "FOREVER", "WITH", "END-PERFORM"
        ):
            target = self.parse_identifier()
            if self.eat_word("THROUGH", "THRU"):
                thru = self.parse_identifier()

        times = None
        until = None
        varying: list[tuple] = []
        inline: list = []

        if self.tok.kind == NUMBER or (
            self.tok.kind == WORD and self.peek(1).is_word("TIMES")
        ):
            times = self.parse_operand()
            self.eat_word("TIMES")
        elif self.at_word("TIMES"):
            self.advance()
            times = self.parse_operand()
        elif self.at_word("UNTIL"):
            self.advance()
            if self.at_word("FOREVER"):
                self.advance()
                until = nodes.Node("cond_forever", line, column)
            else:
                until = self.parse_condition()
        elif self.at_word("VARYING"):
            self.advance()
            varying = self.parse_varying_chain()
        elif self.at_word("FOREVER"):
            self.advance()
            until = nodes.Node("cond_forever", line, column)

        if self.at_word("END-PERFORM"):
            self.advance()
            return nodes.Node(
                "perform_forever", line, column, body=[], test_after=test_after
            )

        body: list = []
        if target is None:
            body = self.parse_statement_list(("END-PERFORM",))
            # 容忍「最後一個敘述多打一個句點，下一行就是 END-PERFORM」的常見筆誤
            self._eat_period_before("END-PERFORM")
            self.eat_word("END-PERFORM")

        return nodes.Node(
            "perform", line, column, target=target, thru=thru, times=times,
            until=until, varying=varying, body=body, test_after=test_after
        )

    def parse_varying_chain(self) -> list[tuple]:
        """解析 PERFORM VARYING ... AFTER ... 的巢狀迴圈標頭。"""
        chain: list[tuple] = []
        index = self.parse_identifier()
        self.eat_word("FROM")
        start = self.parse_operand()
        self.eat_word("BY")
        step = self.parse_operand()
        self.eat_word("UNTIL")
        until = self.parse_condition()
        chain.append((index, start, step, until))
        while self.at_word("AFTER"):
            self.advance()
            index = self.parse_identifier()
            self.eat_word("FROM")
            start = self.parse_operand()
            self.eat_word("BY")
            step = self.parse_operand()
            self.eat_word("UNTIL")
            until = self.parse_condition()
            chain.append((index, start, step, until))
        return chain

    # ---- 其他簡單敘述

    def parse_exit(self, line: int, column: int):
        self.advance()
        if self.at_word("PROGRAM"):
            self.advance()
            return nodes.Node("exit_program", line, column)
        if self.at_word("PERFORM"):
            self.advance()
            cycle = self.eat_word("CYCLE")
            return nodes.Node("exit_perform", line, column, cycle=cycle)
        if self.at_word("SECTION"):
            self.advance()
            return nodes.Node("exit_section", line, column)
        if self.at_word("PARAGRAPH"):
            self.advance()
            return nodes.Node("exit_paragraph", line, column)
        # 單獨的 EXIT 是空敘述（只是段落的結尾標記）
        return nodes.Node("continue", line, column)

    def parse_go_to(self, line: int, column: int):
        """GO TO 的目標清單。

        支援兩種寫法（兩種都有人用，GnuCOBOL 也都接受）::

            GO TO A B C DEPENDING ON X
            GO TO DEPENDING ON X A B C
        """
        self.advance()
        self.eat_word("TO")

        if self.at_word("DEPENDING"):
            self.advance()
            self.eat_word("ON")
            subject = self.parse_operand()
            targets = self._parse_go_to_targets()
            return nodes.Node(
                "go_to_depending", line, column, subject=subject, targets=targets
            )

        targets = self._parse_go_to_targets()
        if self.at_word("DEPENDING"):
            self.advance()
            self.eat_word("ON")
            subject = self.parse_operand()
            return nodes.Node(
                "go_to_depending", line, column, subject=subject, targets=targets
            )
        return nodes.Node("go_to", line, column, targets=targets)

    def _parse_go_to_targets(self) -> list:
        """讀出 GO TO 的目標段落（用空白或逗號隔開）。"""
        targets = [self.parse_identifier()]
        while True:
            if self.tok.kind == COMMA:
                self.advance()
                targets.append(self.parse_identifier())
                continue
            if self.tok.kind == WORD and not self._at_go_to_end():
                targets.append(self.parse_identifier())
                continue
            break
        return targets

    def _at_go_to_end(self) -> bool:
        """GO TO 的目標清單在這裡結束。"""
        if self.at_eof() or self.at_period():
            return True
        if self._at_paragraph_header():
            return True
        if self.at_word("DEPENDING", "WHEN"):
            return True
        if self.tok.kind != WORD:
            return False
        upper = self.tok.upper
        return upper in VERBS or upper in SCOPED_TERMINATORS

    def parse_set(self, line: int, column: int):
        self.advance()
        targets = self.parse_identifier_list(terminator_words=("TO", "UP", "DOWN"))
        self.eat_word("TO")
        if self.at_word("TRUE", "FALSE"):
            value = nodes.Node("figurative", line, column, name=self.advance().upper)
            return nodes.Node("set_condition", line, column, targets=targets, value=value)
        # `SET i UP BY 1` / `SET i DOWN BY 1`：方向要在讀運算元之前判斷，
        # 否則 UP 會被當成一個運算元吃掉
        if self.at_word("UP", "DOWN"):
            direction = self.advance().upper
            self.eat_word("BY")
            step = self.parse_operand()
            return nodes.Node("set_index", line, column, targets=targets, direction=direction, step=step)
        # `SET i TO i + 1` 的右邊可以是整個算式
        value = self.parse_arithmetic()
        return nodes.Node("set_index", line, column, targets=targets, direction="TO", step=value)

    def parse_initialize(self, line: int, column: int):
        self.advance()
        targets = self.parse_receiving_list()
        replacements = self._parse_replacing()
        return nodes.Node("initialize", line, column, targets=targets, replacing=replacements)

    def _parse_replacing(self) -> list[tuple]:
        if not self.at_word("REPLACING"):
            return []
        self.advance()
        pairs: list[tuple] = []
        while not self.at_period() and not self.at_eof():
            if self._at_replacing_end():
                break
            source = self.parse_operand()
            self.eat_word("BY")
            target = self.parse_operand()
            pairs.append((source, target))
            if self.tok.kind == COMMA:
                self.advance()
                continue
            if self.at_period() or self._at_replacing_end():
                break
        return pairs

    def _at_replacing_end(self) -> bool:
        """REPLACING 清單在這裡結束（句點、下一個敘述、段落標頭）。"""
        if self.at_eof() or self.at_period():
            return True
        if self._at_paragraph_header():
            return True
        return self.tok.kind == WORD and (
            self.tok.upper in SCOPED_TERMINATORS or self.tok.upper in VERBS
        )

    # ---- INSPECT / STRING / UNSTRING / SEARCH

    def parse_inspect(self, line: int, column: int):
        """INSPECT … TALLYING／REPLACING／CONVERTING（可搭配 BEFORE／AFTER INITIAL）。"""
        self.advance()
        target = self.parse_identifier()
        operations: list[dict] = []
        while not self.at_eof() and not self.at_period():
            if self.at_word("TALLYING"):
                self.advance()
                self._parse_tallying(operations)
                continue
            if self.at_word("REPLACING"):
                self.advance()
                self._parse_inspect_replacing(operations)
                continue
            if self.at_word("CONVERTING"):
                self.advance()
                # CONVERTING "ab" TO "XY" ：a→X、b→Y，兩邊都是成對的字元
                from_text = self.parse_literal()
                self.eat_word("TO")
                to_text = self.parse_literal()
                mapping: list[tuple] = []
                for source_char, target_char in zip(str(from_text.value), str(to_text.value)):
                    mapping.append((source_char, target_char))
                operations.append(
                    {"kind": "convert", "mapping": mapping, "bounds": self._parse_inspect_bounds()}
                )
                continue
            break
        return nodes.Node("inspect", line, column, target=target, operations=operations)

    def _parse_inspect_bounds(self) -> dict:
        """``BEFORE INITIAL x`` / ``AFTER INITIAL y``：限制 INSPECT 作用的範圍。"""
        bounds: dict = {}
        while self.at_word("BEFORE", "AFTER"):
            which = self.advance().upper.lower()
            self.eat_word("INITIAL")
            bounds[which] = self.parse_operand()
        return bounds

    def _parse_tallying(self, operations: list) -> None:
        """``TALLYING 計數器 FOR {ALL|LEADING} x | CHARACTERS …``，可以有多個計數器。"""
        while True:
            counter = self.parse_identifier()
            if counter is None:
                self.fail("INSPECT TALLYING 後面需要計數用的欄位")
            self.expect_word("FOR")
            how = None
            while True:
                if self.at_word("CHARACTERS", "CHARACTER"):
                    self.advance()
                    how, pattern = "CHARACTERS", None
                elif self.at_word("ALL", "LEADING"):
                    how = self.advance().upper
                    pattern = self.parse_operand()
                elif how is not None and self._at_inspect_operand():
                    # `FOR ALL "A" "B"`：同一個 ALL／LEADING 後面接多個樣式
                    pattern = self.parse_operand()
                else:
                    break
                operations.append({
                    "kind": "tally", "how": how, "counter": counter,
                    "pattern": pattern, "bounds": self._parse_inspect_bounds(),
                })
            if how is None:
                self.fail("INSPECT TALLYING … FOR 後面需要 ALL、LEADING 或 CHARACTERS")
            # 下一個計數器：`TALLYING A FOR ALL "x" B FOR ALL "y"`
            if self.tok.kind == WORD and self.peek(1).is_word("FOR"):
                continue
            return

    def _parse_inspect_replacing(self, operations: list) -> None:
        """``REPLACING {ALL|LEADING|FIRST} x BY y … | CHARACTERS BY y``。"""
        how = None
        while not self.at_period() and not self.at_eof():
            if self.at_word("CHARACTERS", "CHARACTER"):
                self.advance()
                self.expect_word("BY")
                replacement = self.parse_operand()
                operations.append({
                    "kind": "replace", "how": "CHARACTERS", "pattern": None,
                    "replacement": replacement, "bounds": self._parse_inspect_bounds(),
                })
                how = "CHARACTERS"
                continue
            if self.at_word("ALL", "LEADING", "FIRST"):
                how = self.advance().upper
            elif how in (None, "CHARACTERS") or not self._at_inspect_operand():
                break
            pattern = self.parse_operand()
            self.expect_word("BY")
            replacement = self.parse_operand()
            operations.append({
                "kind": "replace", "how": how, "pattern": pattern,
                "replacement": replacement, "bounds": self._parse_inspect_bounds(),
            })
        if how is None:
            self.fail("INSPECT REPLACING 後面需要 ALL、LEADING、FIRST 或 CHARACTERS")

    def _at_inspect_operand(self) -> bool:
        """接下來是不是另一個樣式（常數、象徵常數或欄位名稱）。"""
        if self.tok.kind in (STRING, NUMBER):
            return True
        if self.tok.kind != WORD:
            return False
        word = self.tok.upper
        if word in VERBS or word in SCOPED_TERMINATORS or word.startswith("END-"):
            return False
        if word in ("TALLYING", "REPLACING", "CONVERTING", "BEFORE", "AFTER", "ALL", "LEADING",
                    "FIRST", "CHARACTERS", "CHARACTER", "BY", "FOR"):
            return False
        # 下一個計數器（`B FOR ALL …`）不是樣式
        return not self.peek(1).is_word("FOR")

    def _parse_delimiter(self):
        """解析 DELIMITED BY 後面的界標；``SIZE`` 表示不設界標。"""
        if self.at_word("SIZE"):
            self.advance()
            return None
        return self.parse_operand()

    def parse_string(self, line: int, column: int):
        self.advance()
        sources: list[tuple] = []
        while not self.at_eof() and not self.at_period() and not self._at_paragraph_header():
            if self.tok.kind == WORD and self.tok.upper in VERBS:
                break
            if self.at_word("INTO"):
                self.advance()
                break
            if self.at_word("DELIMITED"):
                self.advance()
                self.eat_word("BY")
                delimiter = self._parse_delimiter()
                if not sources:
                    self.fail("STRING 的 DELIMITED BY 前面缺少傳送項目")
                sources[-1] = (sources[-1][0], delimiter)
                continue
            sources.append((self.parse_operand(), None))
            if self.tok.kind == COMMA:
                self.advance()
        if not sources:
            self.fail("STRING 敘述缺少要串接的項目")
        target = self.parse_identifier()
        pointer = None
        delimiter = None
        if self.at_word("WITH"):
            self.advance()
            self.eat_word("POINTER")
            pointer = self.parse_identifier()
        if self.at_word("DELIMITED"):
            self.advance()
            self.eat_word("BY")
            delimiter = self._parse_delimiter()
        on_overflow = self._parse_size_error_phrases().get("overflow", [])
        self.eat_word("END-STRING")
        return nodes.Node(
            "string", line, column, sources=sources, target=target,
            pointer=pointer, delimiter=delimiter, on_overflow=on_overflow
        )

    def _at_unstring_end(self) -> bool:
        """UNSTRING 的接收欄位清單在這裡結束。"""
        if self.at_eof() or self.at_period():
            return True
        if self.at_word("DELIMITED", "WITH", "POINTER", "ON", "END-UNSTRING", "TALLYING"):
            return True
        if self._at_paragraph_header():
            return True
        return self.tok.kind == WORD and self.tok.upper in VERBS

    def parse_unstring(self, line: int, column: int):
        """UNSTRING 來源 [DELIMITED BY [ALL] a [OR [ALL] b]…] INTO 目標 [DELIMITER IN d] [COUNT IN c] …"""
        self.advance()
        source = self.parse_operand()
        delimiters: list[tuple] = []
        if self.at_word("DELIMITED"):
            self.advance()
            self.eat_word("BY")
            while True:
                all_flag = self.eat_word("ALL")
                delimiters.append((self.parse_operand(), all_flag))
                if self.at_word("OR"):
                    self.advance()
                    continue
                break
        self.expect_word("INTO")
        targets: list = []
        while True:
            target = self.parse_identifier()
            if target is None:
                self.fail("UNSTRING INTO 後面需要接收欄位")
            spec: dict = {"target": target, "delimiter": None, "delimiter_in": None, "count_in": None}
            while True:
                if self.at_word("DELIMITED"):
                    # 舊寫法：每個接收欄位自己指定界標
                    self.advance()
                    self.eat_word("BY")
                    spec["delimiter"] = self.parse_operand()
                elif self.at_word("DELIMITER"):
                    self.advance()
                    self.eat_word("IN")
                    spec["delimiter_in"] = self.parse_identifier()
                elif self.at_word("COUNT"):
                    self.advance()
                    self.eat_word("IN")
                    spec["count_in"] = self.parse_identifier()
                else:
                    break
            targets.append(spec)
            if self.tok.kind == COMMA:
                self.advance()
                continue
            # `INTO A B C` 這種用空白隔開的接收欄位
            if self.tok.kind == WORD and not self._at_unstring_end():
                continue
            break
        pointer = None
        tallying = None
        while self.at_word("WITH", "POINTER", "TALLYING"):
            if self.at_word("TALLYING"):
                self.advance()
                self.eat_word("IN")
                tallying = self.parse_identifier()
                continue
            self.eat_word("WITH")
            self.eat_word("POINTER")
            pointer = self.parse_identifier()
        on_overflow = self._parse_size_error_phrases().get("overflow", [])
        self.eat_word("END-UNSTRING")
        return nodes.Node(
            "unstring", line, column, source=source, delimiters=delimiters,
            targets=targets, pointer=pointer, tallying=tallying, on_overflow=on_overflow
        )

    def parse_search(self, line: int, column: int):
        """SEARCH [ALL] 表格 [VARYING 索引] [AT END …] WHEN 條件 … [WHEN …] [END-SEARCH]。

        另外保留本系統早期的寫法 ``SEARCH 表格 VARYING i FROM a BY b UNTIL 條件``。
        """
        self.advance()
        search_all = self.eat_word("ALL")
        target = self.parse_identifier()
        legacy: list = []
        varying_index = None
        if self.at_word("VARYING"):
            self.advance()
            index = self.parse_identifier()
            if self.at_word("FROM", "BY", "UNTIL"):
                self.eat_word("FROM")
                start = self.parse_operand()
                self.eat_word("BY")
                step = self.parse_operand()
                self.eat_word("UNTIL")
                until = self.parse_condition()
                legacy.append((index, start, step, until))
            else:
                varying_index = index
        at_end: list = []
        if self.at_word("AT", "END"):
            self.eat_word("AT")
            self.expect_word("END")
            at_end = self.parse_statement_list(("WHEN", "END-SEARCH"))
        whens: list[tuple] = []
        while self.at_word("WHEN"):
            self.advance()
            condition = self.parse_condition()
            body = self.parse_statement_list(("WHEN", "END-SEARCH"))
            whens.append((condition, body))
        if not whens:
            self.fail("SEARCH 至少需要一個 WHEN")
        self.eat_word("END-SEARCH")
        return nodes.Node(
            "search", line, column, target=target, varying=legacy, varying_index=varying_index,
            search_all=search_all, at_end=at_end, whens=whens,
        )

    # ---- CALL / ACCEPT / 檔案

    def _at_call_end(self) -> bool:
        """CALL 的 USING 清單在 RETURNING／ON EXCEPTION／下一個敘述／句點處結束。"""
        if self.at_eof() or self.at_period():
            return True
        if self.at_word("RETURNING", "ON", "EXCEPTION", "END-CALL"):
            return True
        if self._at_paragraph_header():
            return True
        return self.tok.kind == WORD and self.tok.upper in VERBS

    def parse_call(self, line: int, column: int):
        self.advance()
        if self.tok.kind == STRING:
            name = self.advance().value
        else:
            name = self.parse_identifier()
        using: list[tuple] = []
        returning = None
        if self.at_word("USING"):
            self.advance()
            while not self.at_eof() and not self._at_call_end():
                if self.at_word("BY"):
                    self.advance()
                    mode = self.advance().upper
                    ref = self.parse_operand()
                    using.append((mode, ref))
                else:
                    using.append(("BY REFERENCE", self.parse_operand()))
                if self.tok.kind == COMMA:
                    self.advance()
                    continue
        if self.at_word("RETURNING"):
            self.advance()
            self.eat_word("VALUE")
            returning = self.parse_identifier()
        self._parse_size_error_phrases()
        return nodes.Node(
            "call", line, column, name=name, using=using, returning=returning
        )

    def parse_accept(self, line: int, column: int):
        self.advance()
        target = self.parse_identifier()
        source = None
        if self.at_word("FROM"):
            self.advance()
            if self.at_word("DATE", "TIME", "DAY-OF-WEEK", "DAY", "COMMAND-LINE", "ENVIRONMENT"):
                source = self.advance().upper
                if source == "ENVIRONMENT":
                    if self.tok.kind == STRING:
                        source = ("ENVIRONMENT", self.advance().value)
            elif self.tok.kind == STRING:
                source = ("ENVIRONMENT", self.advance().value)
        return nodes.Node("accept", line, column, target=target, source=source)

    def _at_open_end(self) -> bool:
        """OPEN 的檔案清單在這裡結束（句點、下一個敘述或段落標頭）。"""
        if self.at_eof() or self.at_period():
            return True
        if self._at_paragraph_header():
            return True
        if self.at_word("WITH", "REVERSED", "NO", "LOCK", "END-OPEN"):
            return True
        return self.tok.kind == WORD and self.tok.upper in VERBS

    def parse_open(self, line: int, column: int):
        self.advance()
        modes: list[tuple[str, str]] = []
        # `OPEN INPUT A B OUTPUT C`：模式套用到後面的每個檔案，直到出現下一個模式
        mode = "INPUT"
        while not self._at_open_end():
            if self.at_word("INPUT", "OUTPUT", "I-O", "EXTEND"):
                mode = self.advance().upper
                continue
            if self.at_word("WITH", "REVERSED", "NO", "LOCK"):
                self.advance()
                continue
            if self.tok.kind == COMMA:
                self.advance()
                continue
            name = self.parse_identifier()
            if name is None:
                break
            modes.append((mode, name))
        self.eat_word("END-OPEN")
        return nodes.Node("open", line, column, files=modes)

    def parse_read(self, line: int, column: int):
        self.advance()
        name = self.parse_identifier()
        into = None
        if self.eat_word("INTO"):
            into = self.parse_identifier()
        self.eat_word("NEXT")
        self.eat_word("RECORD")
        key = None
        if self.at_word("KEY"):
            self.advance()
            self.eat_word("IS")
            key = self.parse_identifier()
        # `READ f KEY IS k INTO x` 和 `READ f INTO x KEY IS k` 兩種順序都可以
        if into is None and self.eat_word("INTO"):
            into = self.parse_identifier()
        at_end = False
        not_at_end = False
        invalid_key = False
        at_end_body: list = []
        not_at_end_body: list = []
        invalid_body: list = []
        while (
            self.at_word("AT")
            or (self.at_word("NOT") and self.peek(1).is_word("AT"))
            or self.at_word("INVALID")
        ):
            if self.at_word("NOT"):
                self.advance()
                self.eat_word("AT")
                self.eat_word("END")
                not_at_end = True
                not_at_end_body = self.parse_statement_list(("END-READ", "AT", "NOT", "INVALID"))
                continue
            if self.at_word("INVALID"):
                self.advance()
                self.eat_word("KEY")
                invalid_key = True
                invalid_body = self.parse_statement_list(("END-READ", "AT", "NOT"))
                continue
            self.advance()
            self.eat_word("END")
            self.eat_word("OF")
            self.eat_word("FILE")
            at_end = True
            at_end_body = self.parse_statement_list(("END-READ", "NOT", "INVALID"))
        if at_end or not_at_end or invalid_key:
            self.eat_word("END-READ")
        return nodes.Node(
            "read", line, column, file=name, into=into, key=key, at_end=at_end,
            not_at_end=not_at_end, end_body=at_end_body or not_at_end_body,
            at_end_body=at_end_body, not_at_end_body=not_at_end_body,
            invalid_key=invalid_key, invalid_body=invalid_body,
        )

    def parse_sort_merge(self, line: int, column: int, kind: str):
        """解析 ``SORT``／``MERGE``（只支援檔案對檔案的形式）。

        ::

            SORT sort-file
                ON ASCENDING KEY key-1 [key-2 ...]
                [ON DESCENDING KEY ...]
                USING in-file [...] GIVING out-file.

        ``INPUT／OUTPUT PROCEDURE`` 超出教學範圍，會直接報錯。
        """
        self.advance()
        sort_file = self.parse_identifier()
        keys: list[tuple] = []
        while self.at_word("ON"):
            self.advance()
            if self.at_word("ASCENDING"):
                self.advance()
                direction = "ASCENDING"
            elif self.at_word("DESCENDING"):
                self.advance()
                direction = "DESCENDING"
            else:
                self.fail("SORT 的 ON 後面要接 ASCENDING 或 DESCENDING")
            self.eat_word("KEY")
            self.eat_word("IS")
            key_list = self._parse_key_list()
            if not key_list:
                self.fail("KEY 後面至少要有一個鍵值欄位")
            keys.append((direction, key_list))
        if self.at_word("INPUT", "OUTPUT"):
            self.fail(
                f"{kind} 的 INPUT／OUTPUT PROCEDURE 太複雜，本系統只支援 USING／GIVING 檔案對檔案"
            )
        using: list = []
        if self.eat_word("USING"):
            using = self._parse_file_list(("GIVING", "INPUT", "OUTPUT"))
        giving = None
        if self.eat_word("GIVING"):
            giving = self.parse_identifier()
        if self.at_word("INPUT", "OUTPUT"):
            self.fail(
                f"{kind} 的 INPUT／OUTPUT PROCEDURE 太複雜，本系統只支援 USING／GIVING 檔案對檔案"
            )
        if not keys:
            self.fail(f"{kind} 至少要有一個 ON ... KEY")
        if not using:
            self.fail(f"{kind} 需要 USING 指定輸入檔")
        if giving is None:
            self.fail(f"{kind} 需要 GIVING 指定輸出檔")
        self.eat_word("END-SORT" if kind == "SORT" else "END-MERGE")
        return nodes.Node(
            kind.lower(), line, column, sort_file=sort_file, keys=keys,
            using=using, giving=giving,
        )

    def _parse_key_list(self) -> list:
        """讀出空白或逗號隔開的鍵值欄位，遇到子句關鍵字就停。"""
        keys = []
        while True:
            if self.at_eof() or self.at_period():
                break
            if self.tok.kind == COMMA:
                self.advance()
                continue
            if self.tok.kind != WORD or self._at_sort_key_end():
                break
            key = self.parse_identifier()
            if key is None:
                break
            keys.append(key)
        return keys

    def _at_sort_key_end(self) -> bool:
        if self._at_paragraph_header():
            return True
        if self.at_word("ON", "USING", "GIVING", "INPUT", "OUTPUT"):
            return True
        return self.tok.kind == WORD and self.tok.upper in VERBS

    def _parse_file_list(self, extra_stops: tuple[str, ...]) -> list:
        """讀出空白或逗號隔開的檔案清單。"""
        names = []
        while True:
            if self.at_eof() or self.at_period():
                break
            if self.tok.kind == COMMA:
                self.advance()
                continue
            if self.tok.kind != WORD or self._at_paragraph_header():
                break
            if self.at_word(*extra_stops):
                break
            if self.tok.upper in VERBS:
                break
            name = self.parse_identifier()
            if name is None:
                break
            names.append(name)
        return names

    def parse_start(self, line: int, column: int):
        """解析 ``START file [KEY IS op key] [INVALID KEY ...] [END-START]``。"""
        self.advance()
        name = self.parse_identifier()
        operator = None
        key = None
        if self.at_word("KEY"):
            self.advance()
            self.eat_word("IS")
            if self.tok.kind == OP and self.tok.value in ("=", ">", "<", ">=", "<="):
                operator = self.advance().value
            else:
                self.fail("START 的 KEY 後面要接 =、>、<、>=、<= 其中一種比較")
            key = self.parse_identifier()
        invalid_key = False
        invalid_body: list = []
        if self.at_word("INVALID"):
            self.advance()
            self.eat_word("KEY")
            invalid_key = True
            invalid_body = self.parse_statement_list(("END-START",))
        self.eat_word("END-START")
        return nodes.Node(
            "start", line, column, file=name, operator=operator, key=key,
            invalid_key=invalid_key, invalid_body=invalid_body,
        )

    def parse_write(self, line: int, column: int):
        self.advance()
        target = self.parse_identifier()
        source = None
        if self.eat_word("FROM"):
            source = self.parse_identifier()
        after_advancing = False
        if self.at_word("AFTER"):
            self.advance()
            self.eat_word("ADVANCING")
            after_advancing = True
        end_write = []
        if self.at_word("INVALID"):
            self.advance()
            self.eat_word("KEY")
            end_write = self.parse_statement_list(("END-WRITE",))
        self.eat_word("END-WRITE")
        return nodes.Node(
            "write", line, column, target=target, source=source, end_write=end_write
        )

    # ---------------------------------------------------------------- 運算式

    def parse_statement_list(self, terminators: tuple[str, ...]) -> list:
        statements: list = []
        stop = set(terminators) | SCOPED_TERMINATORS
        while not self.at_eof():
            token = self.tok
            if token.kind == WORD and token.upper in stop:
                break
            # 段落標頭一定另起一行：任何敘述清單（包含 ON SIZE ERROR 的
            # 內文）都必須在這裡停下來，否則會把下一個段落名稱當成敘述吃掉
            at_para = getattr(self, "_at_paragraph_header", None)
            if callable(at_para) and self._at_paragraph_header():
                break
            # 下一個 ON/NOT 短語的開頭也不是敘述：留給外層的
            # _parse_size_error_phrases 處理，避免把 NOT 當成動詞報錯
            at_phrase = getattr(self, "_at_size_phrase_start", None)
            if callable(at_phrase) and self._at_size_phrase_start():
                break
            if self.at_period():
                # 句點結束整個句子：所有還沒關閉的 IF／PERFORM／EVALUATE 都在這裡結束，
                # 句點留給最外層處理（它也是 NEXT SENTENCE 的跳轉點）
                break
            before = self.pos
            statement = self.parse_statement()
            if statement is not None:
                statements.append(statement)
            if self.pos == before:
                # 保險：避免看不懂的敘述沒有吃掉任何詞形時陷入迴圈
                self.advance()
        return statements
