"""資料版面與資料搬移。

執行方式::

    python -m unittest discover -s tests -t .
"""

from __future__ import annotations

import unittest

from tests.support import DisplayMixin, build_source

from coblings.cobol.errors import RuntimeError_, SyntaxError_  # noqa: E402
from coblings.cobol.layout import build_layout  # noqa: E402
from coblings.cobol.parser import parse_source  # noqa: E402


class DataAndTableTest(DisplayMixin, unittest.TestCase):
    """資料版面：OCCURS、REDEFINES、重複定義、SET 索引與 SEARCH。"""

    def test_set_up_by(self):
        lines = self.display(
            '01 I PIC 9(3) VALUE 1.\n'
            '       P1. SET I UP BY 4 DISPLAY I GOBACK.\n'
        )
        self.assertEqual(lines, ["5"])

    def test_set_down_by(self):
        lines = self.display(
            '01 I PIC 9(3) VALUE 9.\n'
            '       P1. SET I DOWN BY 3 DISPLAY I GOBACK.\n'
        )
        self.assertEqual(lines, ["6"])

    def test_set_to_expression(self):
        lines = self.display(
            '01 I PIC 9(3) VALUE 2.\n'
            '01 K PIC 9(3) VALUE 3.\n'
            '       P1. SET I TO I + K DISPLAY I GOBACK.\n'
        )
        self.assertEqual(lines, ["5"])

    def test_occurs_cap(self):
        program = parse_source(
            build_source("01 T PIC X OCCURS 100001 TIMES.\n       P1. EXIT.\n"),
            "T.cbl",
        )
        with self.assertRaises(SyntaxError_):
            build_layout(program)

    # ---- 3. OCCURS 的初值與 INITIALIZE 涵蓋最後一個元素
    def test_occurs_value_and_initialize_cover_last_element(self):
        lines = self.display(
            '01 T.\n'
            '   05 F PIC 9 OCCURS 3 VALUE 7.\n'
            '01 U.\n'
            '   05 G PIC X OCCURS 3.\n'
            '       P1. DISPLAY F(1) F(2) F(3)\n'
            '           MOVE "A" TO G(1) G(2) G(3)\n'
            '           INITIALIZE U\n'
            '           DISPLAY "[" G(1) G(2) G(3) "]"\n'
            '           INITIALIZE T DISPLAY F(1) F(2) F(3) GOBACK.\n'
        )
        self.assertEqual(lines, ["777", "[   ]", "000"])

    # ---- 13. SEARCH 與 UNSTRING 的標準語法
    def test_search_standard_syntax(self):
        lines = self.display(
            '01 T.\n'
            '   05 E PIC X OCCURS 3 INDEXED BY IX.\n'
            '01 K PIC 9.\n'
            '       P1. MOVE "A" TO E(1) MOVE "B" TO E(2) MOVE "C" TO E(3)\n'
            '           SET IX TO 1\n'
            '           SEARCH E VARYING K\n'
            '             AT END DISPLAY "NOT-FOUND"\n'
            '             WHEN E(IX) = "B" DISPLAY "FOUND " K\n'
            '             WHEN E(IX) = "C" DISPLAY "C?"\n'
            '           END-SEARCH\n'
            '           SET IX TO 1\n'
            '           SEARCH E AT END DISPLAY "MISS" WHEN E(IX) = "Z" DISPLAY "Z" END-SEARCH\n'
            '           SEARCH ALL E WHEN E(IX) = "C" DISPLAY "ALL-C" END-SEARCH\n'
            '           GOBACK.\n'
        )
        self.assertEqual(lines, ["FOUND 2", "MISS", "ALL-C"])

    # ---- M2：重複的 01、REDEFINES
    def test_duplicate_top_level_item_is_a_syntax_error(self):
        with self.assertRaises(SyntaxError_):
            self.display('01 A PIC 9 VALUE 1.\n01 A PIC 9 VALUE 2.\n       P1. GOBACK.\n')

    def test_unknown_redefines_target_is_a_syntax_error(self):
        with self.assertRaises(SyntaxError_):
            self.display('01 A PIC X(4).\n01 B REDEFINES NOPE PIC 9(4).\n       P1. GOBACK.\n')

    def test_redefines_shares_storage(self):
        lines = self.display(
            '01 D PIC X(8) VALUE "20261008".\n'
            '01 D-PARTS REDEFINES D.\n'
            '   05 YYYY PIC 9(4).\n'
            '   05 MM PIC 99.\n'
            '   05 DD PIC 99.\n'
            '       P1. DISPLAY YYYY "/" MM "/" DD\n'
            '           MOVE 12 TO MM DISPLAY D\n'
            '           MOVE "ABCD1231" TO D DISPLAY MM DD\n'
            '           IF YYYY IS NUMERIC DISPLAY "NUM" ELSE DISPLAY "NOT-NUM" END-IF\n'
            '           GOBACK.\n'
        )
        self.assertEqual(lines, ["2026/10/8", "20261208", "1231", "NOT-NUM"])


class MoveTest(DisplayMixin, unittest.TestCase):
    """MOVE、INITIALIZE、群組搬移與數字文字的轉換。"""

    def test_move_to_several_targets(self):
        lines = self.display(
            '01 A PIC X(2).\n'
            '01 B PIC X(2).\n'
            '01 C PIC X(2).\n'
            '       P1. MOVE "ab" TO A B C DISPLAY A B C GOBACK.\n'
        )
        self.assertEqual(lines, ["ababab"])

    def test_move_corresponding(self):
        lines = self.display(
            '01 SRC.\n'
            '    05 F-NAME PIC X(3) VALUE "xyz".\n'
            '    05 F-AGE PIC 9(2) VALUE 42.\n'
            '    05 F-ONLY-SRC PIC X(2) VALUE "qq".\n'
            '01 DST.\n'
            '    05 F-AGE PIC 9(2).\n'
            '    05 F-NAME PIC X(3).\n'
            '    05 F-OTHER PIC X(2) VALUE "zz".\n'
            '       P1. MOVE CORRESPONDING SRC TO DST\n'
            '           DISPLAY F-NAME OF DST " " F-AGE OF DST " " F-OTHER GOBACK.\n'
        )
        # 依名稱配對（不是依位置）；名稱對不上的欄位維持原值
        self.assertEqual(lines, ["xyz 42 zz"])

    def test_initialize_replacing(self):
        # INITIALIZE 先把欄位重設成預設值（空白／零），REPLACING 再作用在結果上
        lines = self.display(
            "01 G.\n"
            "    05 A PIC X(4) VALUE \"aXbX\".\n"
            "       P1. INITIALIZE G DISPLAY \"[\" A \"]\".\n"
        )
        self.assertEqual(lines, ["[    ]"])
        lines = self.display(
            "01 G.\n"
            "    05 A PIC X(4) VALUE \"aXbX\".\n"
            "       P1. INITIALIZE G REPLACING SPACE BY \"Y\" DISPLAY A.\n"
        )
        self.assertEqual(lines, ["YYYY"])

    # ---- 11. MOVE CORRESPONDING（巢狀群組）
    def test_move_corresponding_nested_groups(self):
        lines = self.display(
            '01 S.\n'
            '   05 HDR.\n'
            '      10 ID PIC 9(3) VALUE 7.\n'
            '   05 AMT PIC 9(3)V99 VALUE 12.5.\n'
            '01 T.\n'
            '   05 AMT PIC 9(5)V99.\n'
            '   05 HDR.\n'
            '      10 ID PIC 9(3).\n'
            '       P1. MOVE CORRESPONDING S TO T\n'
            '           DISPLAY ID OF HDR OF T "/" AMT OF T GOBACK.\n'
        )
        self.assertEqual(lines, ["7/12.50"])

    # ---- C2：群組項目當成一整段文字；群組記錄的 READ／WRITE
    def test_group_move_and_display(self):
        lines = self.display(
            '01 G.\n'
            '   05 GID PIC 99.\n'
            '   05 GNAME PIC X(4).\n'
            '   05 GAMT PIC 9(3)V99.\n'
            '01 T PIC X(11).\n'
            '       P1. MOVE "42ABCD01250" TO G\n'
            '           DISPLAY GID "|" GNAME "|" GAMT\n'
            '           MOVE 7 TO GID MOVE G TO T DISPLAY T\n'
            '           IF G = "07ABCD01250" DISPLAY "EQ" END-IF GOBACK.\n'
        )
        self.assertEqual(lines, ["42|ABCD|12.50", "07ABCD01250", "EQ"])

    # ---- M5：文字轉數值不能悄悄丟掉字母
    def test_invalid_numeric_text_is_an_error(self):
        with self.assertRaises(RuntimeError_):
            self.display(
                '01 S PIC X(4) VALUE "1A2B".\n'
                '01 N PIC 9(4).\n'
                '       P1. COMPUTE N = S GOBACK.\n'
            )

    def test_numeric_text_with_sign_and_point(self):
        lines = self.display(
            '01 S PIC X(8) VALUE " 12.50- ".\n'
            '01 N PIC S9(3)V99.\n'
            '       P1. COMPUTE N = S DISPLAY N GOBACK.\n'
        )
        self.assertEqual(lines, ["-12.50"])

    # ---- M6：ALL "樣式"、LENGTH-CHECK
    def test_all_literal(self):
        lines = self.display(
            '01 A PIC X(5).\n'
            '01 N PIC 9(3).\n'
            '       P1. MOVE ALL "AB" TO A\n'
            '           MOVE ALL "7" TO N\n'
            '           DISPLAY A " " N\n'
            '           IF A = ALL "AB" DISPLAY "ALL-EQ" END-IF GOBACK.\n'
        )
        self.assertEqual(lines, ["ABABA 777", "ALL-EQ"])
