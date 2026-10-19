"""PICTURE 字元、數字編輯與 SIGN SEPARATE。

執行方式::

    python -m unittest discover -s tests -t .
"""

from __future__ import annotations

import unittest
from decimal import Decimal

from tests.support import DisplayMixin, build_source

from coblings.cobol.errors import SyntaxError_  # noqa: E402
from coblings.cobol.parser import parse_source  # noqa: E402
from coblings.cobol.pic import Pic  # noqa: E402


class PicTest(DisplayMixin, unittest.TestCase):
    def test_numeric_digits(self):
        pic = Pic("S9(5)V99")
        self.assertEqual(pic.int_digits, 5)
        self.assertEqual(pic.dec_digits, 2)
        self.assertEqual(pic.total_digits, 7)
        self.assertTrue(pic.has_sign)

    def test_alphanumeric_length(self):
        self.assertEqual(Pic("X(20)").char_count, 20)
        self.assertEqual(Pic("A(4)").char_count, 4)

    def test_edited_positions(self):
        pic = Pic("ZZZ9.99")
        self.assertEqual(pic.int_digits, 4)
        self.assertEqual(pic.dec_digits, 2)
        self.assertEqual(pic.char_count, 7)

    def test_quantize_truncates_and_rounds(self):
        pic = Pic("9(3)")
        self.assertEqual(pic.quantize(Decimal("123.9")), Decimal("123"))
        self.assertEqual(pic.quantize(Decimal("123.6"), rounding=True), Decimal("124"))

    def test_edit_suppresses_leading_zero(self):
        self.assertEqual(Pic("ZZZ9.99").to_text(Decimal("12.5")), "  12.50")
        self.assertEqual(Pic("ZZZ9.99").to_text(Decimal("0")), "   0.00")

    def test_edit_trailing_sign(self):
        self.assertEqual(Pic("S9(3)CR").to_text(Decimal("-12")), "012CR")
        self.assertEqual(Pic("S9(3)CR").to_text(Decimal("12")), "012  ")

    def test_picture_repeat_with_leading_zero(self):
        program = parse_source(
            build_source("01 X PIC 9(03) VALUE 7.\n       P1. DISPLAY X.\n"),
            "T.cbl",
        )
        pics = [item.picture for _, items in program.sections for item in items]
        self.assertEqual(pics, ["9(03)"])
        lines = self.display("01 X PIC 9(03) VALUE 7.\n       P1. DISPLAY X.\n")
        self.assertEqual(lines, ["7"])

    def test_comma_suppressed_for_small_values(self):
        self.assertEqual(Pic("ZZZ,ZZ9.99").to_text(Decimal("12.5")), "     12.50")
        self.assertEqual(Pic("ZZZ,ZZ9.99").to_text(Decimal("1234.5")), "  1,234.50")

    def test_picture_repeat_cap(self):
        with self.assertRaises(SyntaxError_):
            Pic("X(100001)")

    def test_pic_quantize_uses_integer_digits(self):
        pic = Pic("9(3)V99")
        self.assertEqual(pic.quantize(Decimal("12345.678")), Decimal("345.67"))
        self.assertTrue(pic.overflows(Decimal("1000")))
        self.assertFalse(pic.overflows(Decimal("999.999")))
        self.assertTrue(pic.overflows(Decimal("999.996"), rounding=True))

    def test_bad_picture_parentheses_are_syntax_errors(self):
        for text in ("9)", "X(2)(3)", "9(3)(2)"):
            with self.subTest(text=text):
                with self.assertRaises(SyntaxError_):
                    Pic(text)

    # ---- 14. 無號欄位不保存負號
    def test_unsigned_field_drops_sign(self):
        lines = self.display(
            '01 N PIC 9(3).\n'
            '       P1. MOVE -5 TO N DISPLAY N\n'
            '           IF N < 0 DISPLAY "NEGATIVE" END-IF GOBACK.\n'
        )
        self.assertEqual(lines, ["5"])


class SignSeparateTest(DisplayMixin, unittest.TestCase):
    """SIGN IS SEPARATE 的 LEADING / TRAILING 顯示測試（問題 #3 修復）。"""

    def test_sign_leading_separate_negative(self):
        lines = self.display(
            '01 N PIC S9(3) VALUE -12 SIGN IS LEADING SEPARATE.\n'
            '       P1. DISPLAY "[" N "]".\n'
        )
        self.assertEqual(lines, ["[-012]"])

    def test_sign_leading_separate_positive(self):
        lines = self.display(
            '01 N PIC S9(3) VALUE 12 SIGN IS LEADING SEPARATE.\n'
            '       P1. DISPLAY "[" N "]".\n'
        )
        # 正數時符號位置顯示空格
        self.assertEqual(lines, ["[ 012]"])

    def test_sign_trailing_separate_negative(self):
        lines = self.display(
            '01 N PIC S9(3) VALUE -12 SIGN IS TRAILING SEPARATE.\n'
            '       P1. DISPLAY "[" N "]".\n'
        )
        self.assertEqual(lines, ["[012-]"])

    def test_sign_trailing_separate_positive(self):
        lines = self.display(
            '01 N PIC S9(3) VALUE 12 SIGN IS TRAILING SEPARATE.\n'
            '       P1. DISPLAY "[" N "]".\n'
        )
        # 正數時符號位置顯示空格
        self.assertEqual(lines, ["[012 ]"])

    def test_sign_not_separate_still_works(self):
        lines = self.display(
            '01 N PIC S9(3) VALUE -12.\n'
            '       P1. DISPLAY "[" N "]".\n'
        )
        self.assertEqual(lines, ["[-12]"])

    def test_sign_separate_does_not_round_integer_part(self):
        lines = self.display(
            '01 N PIC S99V9 VALUE 13.5 SIGN IS LEADING SEPARATE.\n'
            '01 M PIC S99V9 VALUE 99.9 SIGN IS LEADING SEPARATE.\n'
            '       P1. DISPLAY "[" N "][" M "]".\n'
        )
        self.assertEqual(lines, ["[ 13.5][ 99.9]"])


class FloatingInsertionTest(unittest.TestCase):
    """浮動插入：n 個 $／+／- 只代表 n-1 個數字位置。"""

    def test_floating_dollar_keeps_symbol_when_digits_fill(self):
        self.assertEqual(Pic("$$9").int_digits, 2)
        self.assertEqual(Pic("$$9").to_text(Decimal("99")), "$99")
        self.assertEqual(Pic("$$9").to_text(Decimal("5")), " $5")
        self.assertEqual(Pic("$$,$$9.99").to_text(Decimal("12.5")), "   $12.50")
        self.assertEqual(Pic("$$,$$9.99").to_text(Decimal("1234.5")), "$1,234.50")

    def test_single_dollar_is_fixed_insertion(self):
        self.assertEqual(Pic("$999").to_text(Decimal("12")), "$012")
        self.assertEqual(Pic("$ZZ9").to_text(Decimal("5")), "$  5")

    def test_floating_minus_and_plus(self):
        self.assertEqual(Pic("--9").to_text(Decimal("-5")), " -5")
        self.assertEqual(Pic("--9").to_text(Decimal("25")), " 25")
        self.assertEqual(Pic("++9").to_text(Decimal("7")), " +7")
        self.assertEqual(Pic("+ZZ9").to_text(Decimal("4")), "+  4")

    def test_floating_sign_across_comma(self):
        self.assertEqual(Pic("--,--9").int_digits, 4)
        self.assertEqual(Pic("--,--9").to_text(Decimal("-1234")), "-1,234")
        self.assertEqual(Pic("--,--9").to_text(Decimal("-12")), "   -12")
