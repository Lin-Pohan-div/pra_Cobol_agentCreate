"""執行期錯誤與檢查器斷言內建。

執行方式::

    python -m unittest discover -s tests -t .
"""

from __future__ import annotations

import unittest

from tests.support import run_program

from coblings.cobol.errors import AssertionFailure, RuntimeError_  # noqa: E402


class RuntimeErrorTest(unittest.TestCase):
    def test_subscript_out_of_range(self):
        with self.assertRaises(RuntimeError_) as caught:
            run_program(
                '01 T PIC 9(2) OCCURS 2 TIMES.\n'
                '01 X PIC 9(2).\n'
                '       P1. MOVE T (5) TO X.\n'
            )
        self.assertIn("SUBSCRIPT", str(caught.exception))

    def test_size_error_without_phrase_keeps_value(self):
        # 沒有寫 ON SIZE ERROR 時，接收欄位一樣維持原值（COBOL 標準的「內容未定」，
        # GnuCOBOL 選擇不變）
        source = '01 R PIC 9(2).\n       P1. COMPUTE R = 99 * 99 DISPLAY R GOBACK.\n'
        lines, _code, _interp = run_program(source)
        self.assertEqual(lines, ["0"])

    def test_divide_by_zero(self):
        with self.assertRaises(RuntimeError_):
            run_program(
                '01 A PIC 9(2) VALUE 1.\n'
                '01 B PIC 9(2) VALUE 0.\n'
                '01 C PIC 9(2).\n'
                '       P1. DIVIDE A BY B GIVING C.\n'
            )

    def test_unknown_data_item(self):
        with self.assertRaises(RuntimeError_) as caught:
            run_program('       P1. DISPLAY WS-NOPE.\n')
        self.assertIn("WS-NOPE", str(caught.exception))

    def test_timeout(self):
        with self.assertRaises(RuntimeError_):
            run_program(
                '01 I PIC 9(4) VALUE 0.\n'
                '       P1. PERFORM UNTIL I > 999999999 ADD 1 TO I END-PERFORM.\n',
                timeout=1.0,
            )


class BuiltinTest(unittest.TestCase):
    CHECKER = (
        '01 CK PIC X(20) VALUE "{value}".\n'
        '       P1. CALL "COBLINGS-EXPECT-EQUALS"\n'
        '               USING BY CONTENT "值"\n'
        '                     BY CONTENT "{expected}"\n'
        '                     BY CONTENT CK\n'
        '           CALL "COBLINGS-DONE"\n'
        '           GOBACK.\n'
    )

    def test_expect_equals_passes(self):
        lines, code, _ = run_program(self.CHECKER.format(value="hi", expected="hi"))
        self.assertEqual(code, 0)

    def test_expect_equals_pads_blanks(self):
        lines, code, _ = run_program(self.CHECKER.format(value="hi", expected="hi        "))
        self.assertEqual(code, 0)

    def test_expect_equals_fails(self):
        with self.assertRaises(AssertionFailure) as caught:
            run_program(self.CHECKER.format(value="hi", expected="no"))
        self.assertIn("期望: no", caught.exception.message)

    def test_missing_done_does_not_pass(self):
        source = (
            '01 CK PIC X(4) VALUE "ok".\n'
            '       P1. CALL "COBLINGS-EXPECT-TRUE"\n'
            '               USING BY CONTENT "旗標" BY CONTENT 1\n'
            '           GOBACK.\n'
        )
        _lines, code, _interp = run_program(source)
        self.assertEqual(code, 0)  # 斷言通過但沒呼叫 DONE：CLI 仍會判為不通過

    def test_expect_error(self):
        source = (
            '01 T PIC 9(2) OCCURS 2 TIMES.\n'
            '01 X PIC 9(2).\n'
        '       P1. CALL "COBLINGS-EXPECT-ERROR"\n'
        '               USING BY CONTENT "下標" BY CONTENT "BAD" BY CONTENT "SUBSCRIPT"\n'
        '           CALL "COBLINGS-DONE"\n'
        '           GOBACK.\n'
        '       BAD. MOVE T (9) TO X.\n'
        )
        _lines, code, _ = run_program(source)
        self.assertEqual(code, 0)

    def test_table_rendered_in_message(self):
        source = (
            '01 T PIC X(2) OCCURS 3 TIMES.\n'
        '       P1. MOVE "ab" TO T (1) MOVE "cd" TO T (2)\n'
        '           CALL "COBLINGS-EXPECT-EQUALS"\n'
        '               USING BY CONTENT "表格" BY CONTENT T BY CONTENT "zz"\n'
        '           GOBACK.\n'
        )
        with self.assertRaises(AssertionFailure) as caught:
            run_program(source)
        self.assertIn("[ab, cd", caught.exception.message)

    def test_expect_no_error_with_exit_program(self):
        lines, code, _ = run_program(
            "01 CK PIC X VALUE \"N\".\n"
            "       P1. CALL \"COBLINGS-EXPECT-NO-ERROR\"\n"
            '               USING BY CONTENT "離開" BY CONTENT "LEAVER"\n'
            "           CALL \"COBLINGS-DONE\"\n"
            "           GOBACK.\n"
            "       LEAVER. EXIT PROGRAM.\n",
        )
        self.assertEqual(code, 0)

    def test_large_table_truncated_in_message(self):
        from coblings import constants

        # 建立一個超過 MAX_RENDERED_ELEMENTS 的表格斷言失敗
        source = (
            f'01 T PIC X(2) OCCURS {constants.MAX_RENDERED_ELEMENTS + 10} TIMES.\n'
            '       P1. CALL "COBLINGS-EXPECT-EQUALS"\n'
            '               USING BY CONTENT "表格" BY CONTENT T BY CONTENT "zz"\n'
            '           GOBACK.\n'
        )
        with self.assertRaises(AssertionFailure) as caught:
            run_program(source)
        message = caught.exception.message
        # 應該包含截斷標記
        self.assertIn("共", message)
        self.assertIn("個", message)
