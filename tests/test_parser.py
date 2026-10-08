"""詞形分析與語法分析。

執行方式::

    python -m unittest discover -s tests -t .
"""

from __future__ import annotations

import unittest

from tests.support import DisplayMixin, build_source

from coblings.cobol.errors import SyntaxError_  # noqa: E402
from coblings.cobol.parser import parse_source  # noqa: E402


class LexerParserTest(DisplayMixin, unittest.TestCase):
    def test_comment_styles(self):
        program = parse_source(
            "IDENTIFICATION DIVISION.\n"
            "       PROGRAM-ID. T.\n"
            "* 整行註解\n"
            "       PROCEDURE DIVISION.\n"
            "       P1. DISPLAY \"a\" *> 行內註解\n"
            "           DISPLAY \"b\".\n",
            "T.cbl",
        )
        self.assertEqual([p.name for p in program.paragraphs], ["P1"])

    def test_free_format_without_periods(self):
        program = parse_source(
            "IDENTIFICATION DIVISION.\n"
            "       PROGRAM-ID. T.\n"
            "       DATA DIVISION.\n"
            "       WORKING-STORAGE SECTION.\n"
            "       01 A PIC 9(3)\n"
            "       01 B PIC 9(3)\n"
            "       PROCEDURE DIVISION.\n"
            "       P1. MOVE 1 TO A\n"
            "           ADD A TO B\n"
            "           DISPLAY B\n",
            "T.cbl",
        )
        self.assertEqual(len(program.paragraphs[0].statements), 3)

    def test_nested_group_is_nested(self):
        program = parse_source(
            "IDENTIFICATION DIVISION.\n"
            "       PROGRAM-ID. T.\n"
            "       DATA DIVISION.\n"
            "       WORKING-STORAGE SECTION.\n"
            "       01 G.\n"
            "           05 A PIC 9(3).\n"
            "           05 B PIC X(4).\n"
            "       PROCEDURE DIVISION.\n"
            "       P1. DISPLAY A.\n",
            "T.cbl",
        )
        names = [item.name for item in program.sections[0][1]]
        self.assertEqual(names, ["G"])

    def test_condition_name_attached(self):
        program = parse_source(
            "IDENTIFICATION DIVISION.\n"
            "       PROGRAM-ID. T.\n"
            "       DATA DIVISION.\n"
            "       WORKING-STORAGE SECTION.\n"
            "       01 F PIC X VALUE \"Y\".\n"
            "       88 YES VALUE \"Y\".\n"
            "       PROCEDURE DIVISION.\n"
            "       P1. IF F IS-YES DISPLAY \"y\". END-IF.\n",
            "T.cbl",
        )
        item = program.sections[0][1][0]
        self.assertEqual([c.name for c in item.conditions], ["YES"])

    def test_syntax_error_reports_position(self):
        with self.assertRaises(SyntaxError_) as caught:
            parse_source(
                "IDENTIFICATION DIVISION.\n"
                "       PROGRAM-ID. T.\n"
                "       PROCEDURE DIVISION.\n"
                "       P1. DISPLAY.\n",
                "Bad.cbl",
            )
        self.assertIn("error:", caught.exception.format("Bad.cbl"))

    def test_unbalanced_end_keyword_is_error(self):
        with self.assertRaises(SyntaxError_):
            parse_source(
                "IDENTIFICATION DIVISION.\n"
                "       PROGRAM-ID. T.\n"
                "       PROCEDURE DIVISION.\n"
                "       P1. DISPLAY \"a\".\n"
                "       END-IF.\n",
                "Bad.cbl",
            )

    def test_end_divide_with_size_error(self):
        lines = self.display(
            '01 R PIC 9(2) VALUE 5.\n'
            '01 F PIC X(3).\n'
            '       P1. DIVIDE 7 BY 0 GIVING R\n'
            '           ON SIZE ERROR MOVE "YES" TO F\n'
            '       END-DIVIDE\n'
            '           DISPLAY R " " F GOBACK.\n'
        )
        self.assertEqual(lines, ["5 YES"])

    def test_comment_marker_inside_string(self):
        lines = self.display(
            '       P1. DISPLAY "x *> not comment".\n'
        )
        self.assertEqual(lines, ["x *> not comment"])

    def test_same_line_paragraph_header(self):
        program = parse_source(
            build_source(
                "01 N PIC 9 VALUE 1.\n"
                "       P1. ADD 1 TO N EXIT. NEXT-PARA. DISPLAY N.\n"
            ),
            "T.cbl",
        )
        self.assertEqual(
            [p.name for p in program.paragraphs], ["P1", "NEXT-PARA"]
        )

    # ---- 6. 不會再冒出 Python 例外
    def test_unicode_digit_is_a_syntax_error(self):
        with self.assertRaises(SyntaxError_):
            parse_source(build_source('01 A PIC 9.\n       P1. MOVE ² TO A GOBACK.\n'), "T.cbl")


class VerbBoundaryTest(DisplayMixin, unittest.TestCase):
    """清單解析必須在下一個敘述動詞前停下來。"""

    def test_move_does_not_swallow_next_verb(self):
        # 接收欄位清單必須在下一個敘述動詞前停下來
        cases = (
            ("SUBTRACT 1 FROM WS-A", "8 3"),
            ("MULTIPLY 2 BY WS-A", "18 3"),
            ("DIVIDE WS-A BY WS-B", "9 3"),
        )
        for verb, expected in cases:
            lines = self.display(
                '01 WS-A PIC 9(3) VALUE 0.\n'
                '01 WS-B PIC 9(3) VALUE 3.\n'
                f'       P1. MOVE 9 TO WS-A\n           {verb}\n'
                '           DISPLAY WS-A " " WS-B GOBACK.\n'
            )
            self.assertEqual(lines, [expected], f"{verb} 的結果不對")

    def test_every_verb_is_registered(self):
        from coblings.cobol.parser import VERBS

        for word in (
            "ACCEPT", "ADD", "CALL", "CLOSE", "COMPUTE", "CONTINUE", "DELETE",
            "DISPLAY", "DIVIDE", "EVALUATE", "EXIT", "GOBACK", "GO", "IF",
            "INITIALIZE", "INSPECT", "MOVE", "MULTIPLY", "OPEN", "PERFORM",
            "READ", "SET", "SORT", "STOP", "STRING", "SUBTRACT", "UNSTRING",
            "WRITE",
        ):
            self.assertIn(word, VERBS, f"{word} 沒有列在 VERBS 裡")


class SentenceScopeTest(DisplayMixin, unittest.TestCase):
    """句點的範圍與 NEXT SENTENCE。"""

    # ---- 句點結束整個句子；NEXT SENTENCE
    def test_period_ends_if(self):
        lines = self.display(
            '01 A PIC 9 VALUE 0.\n'
            '       P1. IF A = 1\n'
            '               DISPLAY "IN-IF".\n'
            '           DISPLAY "AFTER".\n'
            '           GOBACK.\n'
        )
        self.assertEqual(lines, ["AFTER"])

    def test_stray_period_before_end_if_is_tolerated(self):
        lines = self.display(
            '01 A PIC 9 VALUE 1.\n'
            '       P1. IF A = 1\n'
            '               DISPLAY "IN-IF".\n'
            '           END-IF\n'
            '           DISPLAY "AFTER" GOBACK.\n'
        )
        self.assertEqual(lines, ["IN-IF", "AFTER"])

    def test_next_sentence(self):
        lines = self.display(
            '01 A PIC 9 VALUE 1.\n'
            '       P1. IF A = 1\n'
            '               NEXT SENTENCE\n'
            '           ELSE\n'
            '               DISPLAY "ELSE"\n'
            '           END-IF\n'
            '           DISPLAY "SAME-SENTENCE".\n'
            '           DISPLAY "NEXT".\n'
            '           GOBACK.\n'
        )
        self.assertEqual(lines, ["NEXT"])
