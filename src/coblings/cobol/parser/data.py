"""Parser 資料部：IDENTIFICATION／ENVIRONMENT／DATA DIVISION。"""
from __future__ import annotations

import re
from decimal import Decimal

from .. import nodes
from ..lexer import COMMA, NUMBER, OP, PERIOD, STRING, WORD
from .base import ParserBase, _EDITION_ONLY_OPS, _PICTURE_STOPPERS, _USAGE_WORDS


class DataParser(ParserBase):
    """解析程式開頭與資料描述項。"""
    def parse_program(self) -> nodes.Program:
        while self.at_period():
            self.advance()
        if self.at_word("IDENTIFICATION", "ID"):
            program_id = self.parse_identification()
        else:
            program_id = ""

        selects: list[dict] = []
        files: dict[str, list] = {}
        special_names: list = []

        if self.at_word("ENVIRONMENT"):
            self.advance()
            self.expect_word("DIVISION")
            self.eat_period()
            special_names, selects = self.parse_environment(selects)

        sections: list[tuple[str, list]] = []
        files: dict[str, list] = {}
        declaratives: list = []
        paragraphs: list[nodes.Paragraph] = []
        using_params: list[str] = []

        # FILE SECTION 可以寫在 INPUT-OUTPUT SECTION 之後（ENVIRONMENT DIVISION 後面），
        # 也可以寫在 DATA DIVISION 裡面；兩種位置都支援
        if self.at_word("FILE"):
            files = self.parse_file_section()
        if self.at_word("DATA"):
            sections, data_files = self.parse_data_division()
            if data_files:
                files = data_files

        if self.at_word("PROCEDURE"):
            self.advance()
            self.expect_word("DIVISION")
            if self.eat_word("USING"):
                using_params = self.parse_identifier_list(terminator_words=("SECTION",))
            self.eat_period()
            if self.at_word("USING"):
                self.advance()
                using_params = self.parse_identifier_list(terminator_words=("SECTION",))
            if self.at_word("DECLARATIVES"):
                self.advance()
                self.eat_period()
                declaratives, paragraphs = self.parse_body(end_declaratives=True)
            else:
                declaratives, paragraphs = self.parse_body(end_declaratives=False)

        return nodes.Program(
            "program",
            program_id=program_id,
            special_names=special_names,
            selects=selects,
            files=files,
            sections=sections,
            paragraphs=paragraphs,
            declaratives=declaratives,
            using_params=using_params,
        )

    def parse_identification(self) -> str:
        """解析 IDENTIFICATION DIVISION，取出 PROGRAM-ID。"""
        self.advance()
        self.expect_word("DIVISION")
        self.eat_period()
        program_id = ""
        while not self.at_eof():
            if self.at_word("PROGRAM-ID"):
                self.advance()
                self.eat_word("IS")
                if self.tok.kind in (WORD, STRING):
                    program_id = self.advance().value.upper()
                self.skip_to_period()
                continue
            if self.at_word("ENVIRONMENT", "DATA", "PROCEDURE"):
                return program_id
            if self.at_period():
                self.advance()
                continue
            # AUTHOR. / DATE-WRITTEN. 之類的識別段落
            self.skip_to_period()
        return program_id

    def skip_leading_divisions(self) -> None:
        while not self.at_eof():
            if self.at_word("ENVIRONMENT", "DATA", "PROCEDURE"):
                return
            if self.at_period():
                self.advance()
                continue
            self.skip_to_period()

    # ---------------------------------------------------------------- ENVIRONMENT

    def parse_environment(self, selects: list[dict]):
        """解析 ENVIRONMENT DIVISION，回傳 (SPECIAL-NAMES 段落, SELECT 敘述)。"""
        special_names: list = []
        while not self.at_eof() and not self.at_word("DATA", "PROCEDURE"):
            if self.at_word("CONFIGURATION"):
                self.advance()
                self.skip_to_section()
                continue
            if self.at_word("SPECIAL-NAMES"):
                self.advance()
                self.eat_period()
                while not self.at_eof() and not self.at_word("CONFIGURATION", "INPUT-OUTPUT", "DATA", "PROCEDURE"):
                    if self.at_period():
                        self.advance()
                        continue
                    special_names.append(self.parse_special_name_statement())
                continue
            if self.at_word("INPUT-OUTPUT"):
                self.advance()
                self.eat_period()
                continue
            if self.at_word("FILE-CONTROL"):
                self.advance()
                self.eat_period()
                selects = self.parse_file_control()
                continue
            self.skip_to_period()
        return special_names, selects

    def parse_special_name_statement(self) -> list:
        tokens: list[str] = []
        while not self.at_eof() and not self.at_period() and not self.at_word("INPUT-OUTPUT", "DATA", "PROCEDURE"):
            tokens.append(self.advance().value)
        self.eat_period()
        return tokens

    def parse_file_control(self) -> list[dict]:
        selects: list[dict] = []
        while not self.at_eof() and not self.at_word("I-O-CONTROL", "DATA", "PROCEDURE", "FILE"):
            if self.at_word("SELECT"):
                self.advance()
                self.eat_word("OPTIONAL")
                name = ""
                if self.tok.kind == WORD and not self.at_word("ASSIGN"):
                    name = self.advance().value.upper()
                assign = ""
                organization = "SEQUENTIAL"
                access_mode = "SEQUENTIAL"
                while not self.at_eof() and not self.at_period():
                    if self.at_word("ASSIGN"):
                        self.advance()
                        self.eat_word("TO")
                        if self.tok.kind in (STRING, WORD):
                            assign = self.advance().value
                    elif self.at_word("ORGANIZATION"):
                        self.advance()
                        self.eat_word("IS")
                        if self.at_word("SEQUENTIAL", "INDEXED", "RELATIVE", "LINE"):
                            organization = self.advance().upper
                    elif self.at_word("ACCESS"):
                        self.advance()
                        self.eat_word("MODE")
                        self.eat_word("IS")
                        if self.at_word("SEQUENTIAL", "RANDOM", "DYNAMIC", "DIRECT"):
                            access_mode = self.advance().upper
                    elif self.at_word("FILE", "STATUS", "RECORD", "LOCK", "PASSWORD", "VOLATILE", "RESERVE"):
                        # 逐詞略過到句點
                        while not self.at_eof() and not self.at_period():
                            self.advance()
                        break
                    else:
                        self.advance()
                self.eat_period()
                selects.append(
                    {
                        "name": name,
                        "assign": assign,
                        "organization": organization,
                        "access_mode": access_mode,
                    }
                )
                continue
            self.skip_to_period()
        return selects

    def parse_file_section(self) -> dict[str, list]:
        """解析接在 INPUT-OUTPUT SECTION 之後的 FILE SECTION。"""
        if not self.at_word("FILE"):
            return {}
        self.advance()
        self.eat_word("SECTION")
        self.eat_period()
        return self.parse_file_entries()

    def parse_file_entries(self) -> dict[str, list]:
        """解析一個以上的 FD 定義。"""
        files: dict[str, list] = {}
        while not self.at_eof() and not self.at_word("DATA", "PROCEDURE", "WORKING-STORAGE"):
            if not self.at_word("FD", "SD"):
                self.skip_to_period()
                continue
            self.advance()
            name = ""
            if self.tok.kind == WORD and not self.at_word(
                "RECORD", "BLOCK", "LABEL", "VALUE", "DATA", "LINAGE", "CODE-SET"
            ):
                name = self.advance().value.upper()
            self.eat_word("IS")
            # FD 的其他子句一律略過到句點
            self.skip_to_period()
            items: list = []
            while not self.at_eof() and not self.at_word(
                "FD", "SD", "DATA", "PROCEDURE", "WORKING-STORAGE", "LOCAL-STORAGE", "LINKAGE"
            ):
                if self.tok.kind == NUMBER and self.peek(1).kind in (WORD, PERIOD):
                    item = self.parse_data_item()
                    if item is not None:
                        items.append(item)
                    continue
                self.skip_to_period()
                break
            files[name or "FD-RECORD"] = items
        return files

    # ---------------------------------------------------------------- DATA DIVISION

    def parse_data_division(self):
        """解析 DATA DIVISION。

        回傳 ``(各區段的資料描述項, FILE SECTION 的 FD 定義)``。FILE SECTION 也可能
        寫在 ``ENVIRONMENT DIVISION`` 的 ``INPUT-OUTPUT SECTION`` 之後，呼叫端會在
        這裡沒有解析到時回頭再試一次，兩種寫法都能處理。
        """
        self.expect_word("DATA")
        self.expect_word("DIVISION")
        self.eat_period()
        sections: list[tuple[str, list]] = []
        files: dict[str, list] = {}
        section_names = (
            "WORKING-STORAGE",
            "LOCAL-STORAGE",
            "LINKAGE",
            "SCREEN",
            "REPORT",
            "COMMUNICATION",
        )
        while not self.at_eof() and not self.at_word("PROCEDURE"):
            if self.at_word("FILE"):
                self.advance()
                self.eat_word("SECTION")
                self.eat_period()
                files = self.parse_file_entries()
                continue
            section_name = "WORKING-STORAGE"
            if self.at_word(*section_names):
                section_name = self.advance().upper
                self.eat_period()
            items: list = []
            while not self.at_eof() and not self.at_word(
                *section_names, "PROCEDURE", "FILE"
            ):
                if self.tok.kind == NUMBER and self.peek(1).kind in (WORD, PERIOD):
                    item = self.parse_data_item()
                    if item is not None:
                        items.append(item)
                    continue
                # 看不懂的一行：略過到句點，避免整個題目都載入失敗
                self.skip_to_period()
            sections.append((section_name, items))
        return sections, files

    def parse_data_item(self) -> nodes.DataDescription | None:
        """解析一個資料描述項（含其所有子項）。"""
        level_token = self.tok
        if level_token.kind != NUMBER:
            return None
        level = int(Decimal(level_token.value))
        self.advance()
        if self.tok.kind == PERIOD:
            self.advance()
            return None

        name = None
        if self.tok.kind == WORD and self.tok.upper != "FILLER":
            name = self.advance().value.upper()
        elif self.at_word("FILLER"):
            self.advance()

        fields: dict = {
            "picture": None,
            "usage": "DISPLAY",
            "value": None,
            "occurs": None,
            "depends_on": None,
            "redefines": None,
            "sign_separate": False,
            "sign_leading": False,
            "justified": False,
            "blank_when_zero": False,
            "conditions": [],
            "synonyms": [],
            "children": [],
            "indexed_by": [],
        }

        while not self.at_eof() and not self.at_period():
            if self.at_word("PICTURE", "PIC"):
                self.advance()
                self.eat_word("IS")
                fields["picture"] = self.parse_picture_string()
            elif self.at_word("VALUE", "VALUES"):
                self.advance()
                self.eat_word("IS", "ARE")
                fields["value"] = self.parse_value_clause()
            elif self.at_word("USAGE"):
                self.advance()
                self.eat_word("IS")
                fields["usage"] = self.parse_usage_clause()
            elif self.tok.kind == WORD and self.tok.upper in _USAGE_WORDS:
                # 直接寫 COMP-3 / BINARY / COMPUTATIONAL 而沒有 USAGE 關鍵字
                fields["usage"] = self.parse_usage_clause()
            elif self.at_word("OCCURS"):
                self.advance()
                low = self.parse_integer_literal()
                high = low
                if self.eat_word("TO"):
                    high = self.parse_integer_literal()
                self.eat_word("TIMES")
                fields["occurs"] = {"min": low, "max": high}
                if self.at_word("DEPENDING"):
                    self.advance()
                    self.eat_word("ON")
                    if self.tok.kind == WORD:
                        fields["depends_on"] = self.advance().value.upper()
            elif self.at_word("REDEFINES"):
                self.advance()
                if self.tok.kind == WORD:
                    fields["redefines"] = self.advance().value.upper()
            elif self.at_word("JUSTIFIED", "JUST"):
                self.advance()
                self.eat_word("RIGHT")
                fields["justified"] = True
            elif self.at_word("SIGN"):
                self.advance()
                self.eat_word("IS")
                if self.at_word("LEADING"):
                    self.advance()
                    fields["sign_leading"] = True
                elif self.eat_word("TRAILING"):
                    fields["sign_leading"] = False
                if self.eat_word("SEPARATE"):
                    fields["sign_separate"] = True
                else:
                    self.eat_word("CHARACTER")
            elif self.at_word("BLANK"):
                self.advance()
                self.eat_word("WHEN")
                self.eat_word("ZERO", "ZEROS", "ZEROES")
                fields["blank_when_zero"] = True
            elif self.at_word("SYNCHRONIZED", "SYNC"):
                self.advance()
                self.eat_word("LEFT", "RIGHT")
            elif self.at_word("NATIONAL"):
                self.advance()
            elif self.at_word("INDEXED") and self.peek(1).is_word("BY"):
                # OCCURS … INDEXED BY 索引名稱：宣告表格專用的索引
                self.advance()
                self.advance()
                while self.tok.kind == WORD and not self._looks_like_clause_start() and not self.at_word(
                    "ASCENDING", "DESCENDING", "INDEXED", "OCCURS", "VALUE", "VALUES"
                ):
                    fields["indexed_by"].append(self.advance().value.upper())
                    if self.tok.kind == COMMA:
                        self.advance()
            elif self.at_word("INDEXED", "INDEX") or self.at_word("RELATIVE", "RELATIVE-INDEXED"):
                self.advance()
                fields["usage"] = "INDEX"
            elif self.at_word("EXTERNAL") or self.at_word("GLOBAL"):
                self.advance()
            elif self.tok.kind == STRING:
                # 沒預期到的字串：略過
                self.advance()
            elif self.at_word(
                "PROCEDURE", "DATA", "ENVIRONMENT", "IDENTIFICATION", "ID", "WORKING-STORAGE"
            ):
                # 資料描述項沒有句點、下一個詞形就是下一個 DIVISION
                break
            else:
                # 數字代表下一個資料描述項的層級號，這一項已經讀完了
                if self.tok.kind == NUMBER:
                    break
                # 其他子句：只跳過這個字，避免把後面的資料描述項一起吞掉
                # （COBOL 的資料描述項可以不加句點）
                self.advance()

        item = nodes.DataDescription(
            "data", line=level_token.line, column=level_token.column,
            level=level, name=name, filename=self.filename, **fields
        )

        # 88 / 66 是附屬在上一個項目上的
        while True:
            # 88/66 前面通常會有一個句點（`01 X PIC X VALUE "Y".` 的那個句點）
            offset = 1 if self.at_period() else 0
            level_token = self.peek(offset)
            name_token = self.peek(offset + 1)
            if (
                level_token.kind == NUMBER
                and name_token.kind == WORD
                and int(Decimal(level_token.value)) in (66, 88)
            ):
                if offset:
                    self.advance()
                sub_level = int(Decimal(level_token.value))
                self.advance()
                sub_name = self.advance().value.upper()
                if sub_level == 88:
                    item.conditions.append(self.parse_condition_name(sub_name))
                else:
                    item.synonyms.append(nodes.RenameSpec(sub_name, self.parse_rename_targets()))
                continue
            break

        # 群組標頭的句點（`01 X.` 後面接 05 子項）要先吃掉，否則看不到子項
        if (
            self.at_period()
            and self.peek(1).kind == NUMBER
            and self.peek(2).kind in (WORD, PERIOD)
            and int(Decimal(self.peek(1).value)) > level
            and int(Decimal(self.peek(1).value)) not in (66, 88)
        ):
            self.advance()

        # 子項
        if level not in (66, 77, 88):
            while self._at_child(level):
                if self.at_period():
                    self.advance()
                child = self.parse_data_item()
                if child is None:
                    break
                item.children.append(child)

        if level == 88 or level == 66:
            return None
        return item

    def _at_child(self, level: int) -> bool:
        """判斷下一個詞形是不是這個項目的子項（含子項句點的情況）。"""
        offset = 0
        if self.at_period():
            offset = 1
        token = self.peek(offset)
        following = self.peek(offset + 1)
        if token.kind != NUMBER or following.kind not in (WORD, PERIOD):
            return False
        child_level = int(Decimal(token.value))
        return child_level > level and child_level not in (66, 88)

    def parse_picture_string(self) -> str:
        """把 PICTURE 子句的詞形重新組合成字串，例如 ``S9(5)V99``。"""
        parts: list[str] = []
        while not self.at_eof() and not self.at_period():
            token = self.tok
            if token.kind == WORD:
                if token.upper in _PICTURE_STOPPERS:
                    break
                parts.append(token.value.upper())
                self.advance()
            elif token.kind == NUMBER:
                # 括號裡的重複次數優先：`9(03)` 的 03 不是層級號
                if parts and parts[-1].endswith("("):
                    parts[-1] = parts[-1] + token.value
                elif parts and re.match(r"^0\d+$", token.value):
                    # `01`、`05` 這種補零的層級號不會出現在 PICTURE 裡，
                    # 遇到它就代表這個資料描述項的 PICTURE 已經讀完了
                    break
                else:
                    parts.append(token.value)
                self.advance()
            elif token.kind == COMMA:
                # `ZZZ,ZZ9.99` 的千分位逗號也是 PICTURE 的一部分
                parts.append(",")
                self.advance()
            elif token.kind == OP and token.value == "**":
                # 兩個 `*` 是浮動抑制字元，不是冪運算子
                parts.append("**")
                self.advance()
            elif token.kind == OP and token.value in _EDITION_ONLY_OPS:
                if token.value == "(" and parts and len(parts[-1]) == 1:
                    parts[-1] = parts[-1] + "("
                elif token.value == ")":
                    # 把最近一個未完成的括號補起來
                    for index in range(len(parts) - 1, -1, -1):
                        if "(" in parts[index]:
                            parts[index] = parts[index] + ")"
                            break
                elif token.value == "$":
                    parts.append("$")
                else:
                    parts.append(token.value)
                self.advance()
            else:
                break
        return "".join(parts)

    def parse_usage_clause(self) -> str:
        if self.at_word(
            "DISPLAY", "COMP", "COMP-1", "COMP-2", "COMP-3", "COMP-4", "COMP-5",
            "BINARY", "PACKED-DECIMAL", "COMPUTATIONAL", "COMPUTATIONAL-1",
            "COMPUTATIONAL-2", "COMPUTATIONAL-3", "COMPUTATIONAL-4", "COMPUTATIONAL-5",
            "INDEX",
        ):
            return self.advance().upper
        if self.at_word("COMPUTATIONAL"):
            return "COMP"
        if self.at_word("FLOAT"):
            self.advance()
            if self.eat_word("LONG"):
                return "COMP-2"
            self.eat_word("SHORT", "BINARY-64")
            return "COMP-1"
        if self.tok.kind == WORD:
            return self.advance().upper
        return "DISPLAY"

    def parse_integer_literal(self) -> int:
        if self.tok.kind == NUMBER:
            return int(Decimal(self.advance().value))
        if self.tok.kind == OP and self.tok.value in "+-":
            sign = -1 if self.advance().value == "-" else 1
            return sign * self.parse_integer_literal()
        return 0

    def parse_value_clause(self) -> nodes.ValueSpec:
        """解析 VALUE 子句，支援多個值（表格初始化）。"""
        values: list[nodes.ValueSpec] = []
        while not self.at_eof() and not self.at_period():
            if self.at_word("ALL"):
                self.advance()
                literal = self.parse_literal()
                values.append(
                    nodes.ValueSpec("all_literal", line=literal.line, pattern=literal.value)
                )
            elif self.at_word("ZERO", "ZEROS", "ZEROES", "SPACES", "SPACE", "HIGH-VALUES", "LOW-VALUES",
                              "QUOTES", "NULL", "NULLS", "TRUE", "FALSE"):
                word = self.advance().upper
                values.append(nodes.ValueSpec("figurative", line=self.peek(-1).line, value=word))
            elif self.tok.kind in (STRING, NUMBER) or self.at_op_sign() or (
                self.tok.kind == WORD and not self._looks_like_clause_start()
            ):
                literal = self.parse_literal_or_expression()
                values.append(literal)
            else:
                break
            if self.at_period():
                break
        return nodes.ValueSpec(
            "multi" if len(values) > 1 else "single",
            values=values,
            line=values[0].line if values else self.tok.line,
        )

    def _looks_like_clause_start(self) -> bool:
        return self.tok.upper in _PICTURE_STOPPERS

    def at_op_sign(self) -> bool:
        return self.tok.kind == OP and self.tok.value in "+-"

    def parse_condition_name(self, name: str) -> nodes.ConditionSpec:
        """解析 88 層級：``VALUE a [THRU b] [, c [THRU d]] … [WHEN SET TO FALSE IS x]``。

        每個值（或 THRU 範圍）各自成為 ``ranges`` 裡的一筆 ``(下限, 上限或 None)``。
        """
        self.eat_word("VALUE", "VALUES")
        self.eat_word("IS", "ARE")
        ranges: list[tuple] = []
        false_value = None
        while not self.at_eof() and not self.at_period():
            if self.tok.kind == COMMA:
                self.advance()
                continue
            if self.at_word("WHEN"):
                # WHEN SET TO FALSE IS 值：SET 條件 TO FALSE 時要放進欄位的值
                self.advance()
                self.eat_word("SET")
                self.eat_word("TO")
                self.expect_word("FALSE")
                self.eat_word("IS")
                false_value = self.parse_value_spec_single()
                continue
            if self.tok.kind not in (STRING, NUMBER) and not self.at_op_sign() and not self.at_any_word():
                break
            low = self.parse_value_spec_single()
            high = None
            if self.at_word("THROUGH", "THRU"):
                self.advance()
                high = self.parse_value_spec_single()
            ranges.append((low, high))
        highs = [high for _, high in ranges if high is not None]
        return nodes.ConditionSpec(
            "condition",
            name=name,
            values=[low for low, _ in ranges],
            through=highs or None,
            ranges=ranges,
            false_value=false_value,
        )

    def parse_value_spec_single(self) -> nodes.ValueSpec:
        if self.at_word("ALL"):
            self.advance()
            literal = self.parse_literal()
            return nodes.ValueSpec("all_literal", line=literal.line, pattern=literal.value)
        if self.at_word("ZERO", "ZEROS", "ZEROES", "SPACES", "SPACE", "HIGH-VALUES", "LOW-VALUES",
                        "QUOTES", "NULL", "NULLS", "TRUE", "FALSE"):
            word = self.advance().upper
            return nodes.ValueSpec("figurative", line=self.tok.line, value=word)
        return self.parse_literal_or_expression()

    def parse_rename_targets(self) -> list[str]:
        targets: list[str] = []
        while not self.at_eof() and not self.at_period():
            if self.at_word("FOR"):
                self.advance()
                continue
            if self.at_word("THROUGH", "THRU"):
                self.advance()
                continue
            if self.tok.kind == WORD:
                targets.append(self.advance().value.upper())
                continue
            break
        return targets

    # ---------------------------------------------------------------- PROCEDURE DIVISION
