"""PROCEDURE DIVISION 的敘述。

執行方式::

    python -m unittest discover -s tests -t .
"""

from __future__ import annotations

import unittest

from tests.support import COND_ITEMS, DisplayMixin, run_full, run_program

from coblings.cobol.errors import RuntimeError_  # noqa: E402


class StatementTest(DisplayMixin, unittest.TestCase):
    def test_move_pads_right(self):
        lines = self.display(
            '01 X PIC X(6).\n'
            '       P1. MOVE "ab" TO X DISPLAY "[" X "]".\n'
        )
        self.assertEqual(lines, ["[ab    ]"])

    def test_move_truncates_right(self):
        lines = self.display(
            '01 X PIC X(3).\n'
            '       P1. MOVE "abcdef" TO X DISPLAY "[" X "]".\n'
        )
        self.assertEqual(lines, ["[abc]"])

    def test_move_numeric_truncates(self):
        lines = self.display(
            '01 X PIC 9(3).\n'
            '       P1. MOVE 1234 TO X DISPLAY X.\n'
        )
        self.assertEqual(lines, ["234"])

    def test_justified_right(self):
        lines = self.display(
            '01 X PIC X(5) JUSTIFIED.\n'
            '       P1. MOVE "ab" TO X DISPLAY "[" X "]".\n'
        )
        self.assertEqual(lines, ["[   ab]"])

    def test_arithmetic(self):
        lines = self.display(
            '01 A PIC 9(4) VALUE 10.\n'
            '01 B PIC 9(4) VALUE 3.\n'
            '01 C PIC 9(4).\n'
            '01 D PIC 9(4).\n'
            '01 E PIC 9(4).\n'
            '01 F PIC 9(4).\n'
            '01 G PIC 9(4).\n'
            '       P1. ADD A B GIVING C\n'
            '           SUBTRACT B FROM A GIVING D\n'
            '           MULTIPLY A BY B GIVING E\n'
            '           DIVIDE A BY B GIVING F\n'
            '           DISPLAY C " " D " " E " " F.\n'
        )
        self.assertEqual(lines, ["13 7 30 3"])

    def test_divide_truncates_unless_rounded(self):
        lines = self.display(
            '01 A PIC 9(2) VALUE 7.\n'
            '01 B PIC 9(2) VALUE 2.\n'
            '01 C PIC 9(2).\n'
            '01 D PIC 9(2).\n'
            '       P1. DIVIDE A BY B GIVING C\n'
            '           DIVIDE A BY B GIVING D ROUNDED\n'
            '           DISPLAY C " " D.\n'
        )
        self.assertEqual(lines, ["3 4"])

    def test_add_to_accumulates(self):
        lines = self.display(
            '01 A PIC 9(3) VALUE 5.\n'
            '01 T PIC 9(3) VALUE 0.\n'
            '       P1. ADD A TO T ADD 2 TO T DISPLAY T.\n'
        )
        self.assertEqual(lines, ["7"])

    def test_compute_expression(self):
        lines = self.display(
            '01 R PIC S9(5).\n'
            '       P1. COMPUTE R = (3 + 4) * 2 - 1 DISPLAY R GOBACK.\n'
        )
        self.assertEqual(lines, ["13"])

    def test_if_else(self):
        lines = self.display(
            '01 N PIC 9(2) VALUE 5.\n'
            '       P1. IF N > 10 DISPLAY "big"\n'
            '           ELSE IF N > 3 DISPLAY "mid"\n'
            '           ELSE DISPLAY "small"\n'
            '           END-IF.\n'
        )
        self.assertEqual(lines, ["mid"])

    def test_condition_name(self):
        lines = self.display(
            '01 F PIC X VALUE "Y".\n'
            '88 IS-YES VALUE "Y".\n'
            '01 R PIC 9 VALUE 0.\n'
            '       P1. IF F IS-YES ADD 1 TO R END-IF DISPLAY R.\n'
        )
        self.assertEqual(lines, ["1"])

    def test_class_and_sign_conditions(self):
        lines = self.display(
            '01 N PIC 9(3) VALUE 123.\n'
            '01 T PIC 9(2) VALUE 0.\n'
            '       P1. IF N IS NUMERIC ADD 1 TO T END-IF\n'
            '           IF N IS POSITIVE ADD 1 TO T END-IF\n'
            '           DISPLAY T.\n'
        )
        self.assertEqual(lines, ["2"])

    def test_evaluate(self):
        lines = self.display(
            '01 N PIC 9(2) VALUE 70.\n'
            '       P1. EVALUATE TRUE\n'
            '               WHEN N >= 90 DISPLAY "A"\n'
            '               WHEN N >= 60 DISPLAY "B"\n'
            '               WHEN OTHER DISPLAY "C"\n'
            '           END-EVALUATE.\n'
        )
        self.assertEqual(lines, ["B"])

    def test_perform_times_and_until(self):
        lines = self.display(
            '01 I PIC 9(2) VALUE 0.\n'
            '01 T PIC 9(3) VALUE 0.\n'
            '       P1. PERFORM 3 TIMES ADD 2 TO T END-PERFORM\n'
            '           PERFORM UNTIL I >= 4 ADD 1 TO I END-PERFORM\n'
            '           DISPLAY T " " I.\n'
        )
        self.assertEqual(lines, ["6 4"])

    def test_perform_varying(self):
        lines = self.display(
            '01 I PIC 9(2).\n'
            '01 T PIC 9(3) VALUE 0.\n'
            '       P1. PERFORM VARYING I FROM 1 BY 1 UNTIL I > 5\n'
            '               ADD I TO T\n'
            '           END-PERFORM\n'
            '           DISPLAY T.\n'
        )
        self.assertEqual(lines, ["15"])

    def test_perform_nested_after(self):
        lines = self.display(
            '01 I PIC 9(2).\n'
            '01 J PIC 9(2).\n'
            '01 T PIC 9(4) VALUE 0.\n'
            '       P1. PERFORM VARYING I FROM 1 BY 1 UNTIL I > 2\n'
            '               AFTER J FROM 1 BY 1 UNTIL J > 3\n'
            '                   ADD 1 TO T\n'
            '               END-PERFORM\n'
            '           DISPLAY T.\n'
        )
        self.assertEqual(lines, ["6"])

    def test_perform_through(self):
        lines = self.display(
            '       P1. PERFORM P-A THRU P-B GOBACK.\n'
            '       P-A. DISPLAY "A".\n'
            '       P-B. DISPLAY "B".\n',
        )
        self.assertEqual(lines, ["A", "B"])

    def test_perform_paragraph_falls_through_inside_range(self):
        """PERFORM 單一段落會回到呼叫端；PERFORM … THRU 才會把範圍內的段落跑完。"""
        lines = self.display(
            '       P1. PERFORM P-A GOBACK.\n',
            student='       P-A. DISPLAY "A".\n       P-B. DISPLAY "B".\n       P-C. EXIT.\n',
        )
        self.assertEqual(lines, ["A"])
        lines = self.display(
            '       P1. PERFORM P-A THRU P-B GOBACK.\n',
            student='       P-A. DISPLAY "A".\n       P-B. DISPLAY "B".\n       P-C. DISPLAY "C".\n',
        )
        self.assertEqual(lines, ["A", "B"])

    def test_table_and_subscript(self):
        lines = self.display(
            '01 T PIC 9(3) OCCURS 4 TIMES.\n'
            '01 I PIC 9(2).\n'
            '01 S PIC 9(4) VALUE 0.\n'
            '       P1. PERFORM VARYING I FROM 1 BY 1 UNTIL I > 4\n'
            '               COMPUTE T (I) = I * 2\n'
            '           END-PERFORM\n'
            '           DISPLAY T (1) " " T (4) " " S.\n'
        )
        self.assertEqual(lines, ["2 8 0"])

    def test_table_of_groups(self):
        lines = self.display(
            '01 G OCCURS 3 TIMES.\n'
            '    05 ID PIC 9(2).\n'
            '    05 NM PIC X(3).\n'
            '01 I PIC 9(2).\n'
            '       P1. PERFORM VARYING I FROM 1 BY 1 UNTIL I > 3\n'
            '               MOVE I TO ID (I)\n'
            '               MOVE "ab" TO NM (I)\n'
            '           END-PERFORM\n'
            '           DISPLAY ID (2) NM (2).\n'
        )
        self.assertEqual(lines, ["2ab "])

    def test_string_with_delimiter(self):
        lines = self.display(
            '01 S PIC X(10) VALUE "Hello World".\n'
            '01 O PIC X(20).\n'
            '01 P PIC 9(2) VALUE 1.\n'
            '       P1. MOVE SPACES TO O\n'
            '           STRING S DELIMITED BY " " INTO O END-STRING\n'
            '           DISPLAY "[" O "]".\n'
        )
        self.assertEqual(lines, ["[Hello" + " " * 15 + "]"])

    def test_string_with_pointer(self):
        lines = self.display(
            '01 O PIC X(10) VALUE "abcdefghij".\n'
            '01 P PIC 9(2) VALUE 4.\n'
            '       P1. STRING "XY" DELIMITED BY SIZE INTO O WITH POINTER P END-STRING\n'
            '           DISPLAY O " " P.\n'
        )
        self.assertEqual(lines, ["abcXYfghij 6"])

    def test_unstring(self):
        lines = self.display(
            '01 S PIC X(10) VALUE "12,34".\n'
            '01 A PIC 9(2).\n'
            '01 B PIC 9(2).\n'
            '       P1. UNSTRING S DELIMITED BY "," INTO A B END-UNSTRING\n'
            '           DISPLAY A " " B.\n'
        )
        self.assertEqual(lines, ["12 34"])

    def test_inspect_tally_and_replace(self):
        lines = self.display(
            '01 S PIC X(9) VALUE "banana".\n'
            '01 N PIC 9(2) VALUE 0.\n'
            '01 T PIC X(9) VALUE "banana".\n'
            '       P1. INSPECT S TALLYING N FOR ALL "an"\n'
            '           INSPECT T REPLACING ALL "a" BY "o"\n'
            '           DISPLAY N " " T.\n'
        )
        self.assertEqual(lines, ["2 bonono   "])

    def test_search_table(self):
        lines = self.display(
            '01 T PIC X(4) OCCURS 3 TIMES.\n'
            '01 I PIC 9(2).\n'
            '01 F PIC X(4) VALUE "cd".\n'
            '       P1. MOVE "ab" TO T (1) MOVE "cd" TO T (2) MOVE "ef" TO T (3)\n'
            '           SEARCH T VARYING I FROM 1 BY 1 UNTIL I > 3\n'
            '               WHEN T (I) = F DISPLAY I\n'
            '           END-SEARCH.\n'
        )
        self.assertEqual(lines, ["2"])

    def test_set_condition_name(self):
        lines = self.display(
            '01 F PIC X VALUE "N".\n'
            '88 IS-YES VALUE "Y".\n'
            '       P1. SET IS-YES TO TRUE\n'
            '           DISPLAY F.\n'
        )
        self.assertEqual(lines, ["Y"])

    def test_initialize(self):
        lines = self.display(
            '01 G.\n'
            '    05 A PIC 9(3) VALUE 7.\n'
            '    05 B PIC X(3) VALUE "xy".\n'
            '       P1. INITIALIZE G DISPLAY A "/" B.\n'
        )
        self.assertEqual(lines, ["0/   "])

    def test_go_to_and_exit(self):
        lines = self.display(
            '       P1. GO TO P-B.\n'
            '       P-A. DISPLAY "A".\n'
            '       P-B. DISPLAY "B".\n'
            '           EXIT.\n'
        )
        self.assertEqual(lines, ["B"])

    def test_intrinsics(self):
        lines = self.display(
            '01 S PIC X(6) VALUE "  ab  ".\n'
            '       P1. DISPLAY FUNCTION LENGTH (S) " " FUNCTION TRIM (S) "|".\n'
            '           DISPLAY FUNCTION UPPER-CASE ("a") " " FUNCTION ORD ("A").\n'
            '           DISPLAY FUNCTION MOD (7, 3) " " FUNCTION LENGTH (FUNCTION TRIM (S)).\n'
        )
        self.assertEqual(lines, ["6 ab|", "A 65", "1 2"])

    def test_blank_when_zero(self):
        lines = self.display(
            '01 N PIC ZZZ9 VALUE 0.\n'
            '01 M PIC ZZZ9 VALUE 5.\n'
            '       P1. DISPLAY "[" N "][" M "]".\n'
        )
        self.assertEqual(lines, ["[   0][   5]"])

    def test_display_spaces_prints_blank(self):
        lines = self.display(
            '01 X PIC X(4) VALUE "ab".\n'
            '       P1. DISPLAY "[" SPACES "]".\n'
        )
        self.assertEqual(lines, ["[ ]"])


class ArithmeticTest(DisplayMixin, unittest.TestCase):
    """算術敘述、DIVIDE 的方向、ON SIZE ERROR 與資源上限。"""

    def test_divide_by(self):
        # DIVIDE a BY b → 結果 = a / b
        lines = self.display(
            '01 A PIC 9(3) VALUE 100.\n'
            '01 R PIC 9(4)V99.\n'
            '       P1. DIVIDE 7 BY 3 GIVING R DISPLAY R GOBACK.\n'
        )
        self.assertEqual(lines, ["2.33"])

    def test_divide_into(self):
        # DIVIDE a INTO b → b = b / a
        lines = self.display(
            '01 R PIC 9(4)V99.\n'
            '       P1. DIVIDE 7 INTO 100 GIVING R DISPLAY R GOBACK.\n'
        )
        self.assertEqual(lines, ["14.28"])

    def test_divide_into_updates_target(self):
        lines = self.display(
            '01 R PIC 9(4) VALUE 100.\n'
            '       P1. DIVIDE 4 INTO R DISPLAY R GOBACK.\n'
        )
        self.assertEqual(lines, ["25"])

    def test_divide_by_remainder(self):
        lines = self.display(
            '01 R PIC 9(4).\n'
            '01 M PIC 9(2).\n'
            '       P1. DIVIDE 7 BY 3 GIVING R REMAINDER M DISPLAY R " " M GOBACK.\n'
        )
        self.assertEqual(lines, ["2 1"])

    def test_huge_power_is_clean_error(self):
        with self.assertRaises(RuntimeError_):
            run_program(
                "01 N PIC 9(5) VALUE 0.\n"
                "       P1. COMPUTE N = 2 ** 999999 DISPLAY N.\n"
            )

    def test_not_on_size_error_runs_on_success(self):
        lines = self.display(
            "01 R PIC 9(4) VALUE 0.\n"
            "01 F PIC X(3) VALUE \"NO\".\n"
            "       P1. COMPUTE R = 2 + 3\n"
            "           NOT ON SIZE ERROR MOVE \"YES\" TO F\n"
            "           END-COMPUTE\n"
            "           DISPLAY R \" \" F.\n"
        )
        self.assertEqual(lines, ["5 YES"])

    def test_on_size_error_runs_once_for_many_targets(self):
        lines = self.display(
            "01 A PIC 9(2) VALUE 0.\n"
            "01 B PIC 9(2) VALUE 0.\n"
            "01 C PIC 9(2) VALUE 0.\n"
            "       P1. COMPUTE A B = 99 * 99\n"
            "           ON SIZE ERROR ADD 1 TO C\n"
            "           END-COMPUTE\n"
            "           DISPLAY A \" \" B \" \" C.\n"
        )
        self.assertEqual(lines, ["0 0 1"])

    def test_divide_by_zero_with_only_not_phrase_raises(self):
        with self.assertRaises(RuntimeError_):
            run_program(
                "01 R PIC 9(2) VALUE 5.\n"
                "       P1. DIVIDE 7 BY 0 GIVING R\n"
                "           NOT ON SIZE ERROR CONTINUE\n"
                "           END-DIVIDE.\n"
            )

    # ---- 4. 有 V 的 PICTURE 也要截斷／偵測溢位
    def test_implied_decimal_truncation_and_size_error(self):
        lines = self.display(
            '01 N PIC 9(3)V99.\n'
            '01 F PIC X VALUE "N".\n'
            '01 R PIC 9V9.\n'
            '01 G PIC X VALUE "N".\n'
            '       P1. MOVE 12345.67 TO N DISPLAY N\n'
            '           COMPUTE N = 1500 ON SIZE ERROR MOVE "Y" TO F END-COMPUTE\n'
            '           COMPUTE R ROUNDED = 9.96 ON SIZE ERROR MOVE "Y" TO G END-COMPUTE\n'
            '           DISPLAY N " " F " " G GOBACK.\n'
        )
        self.assertEqual(lines, ["345.67", "345.67 Y Y"])


class ConditionTest(DisplayMixin, unittest.TestCase):
    """條件運算、88 條件名稱、EVALUATE、比較規則。"""

    # ---- 1. 條件名稱後面接 OR／AND／THEN
    def test_condition_names_with_or_and_then(self):
        lines = self.display(
            COND_ITEMS
            + '       P1. IF B-ON OR A-ON DISPLAY "OR" END-IF\n'
            '           IF A-ON AND B-ON DISPLAY "AND" ELSE DISPLAY "NOT-AND" END-IF\n'
            '           IF A-ON THEN DISPLAY "THEN" END-IF\n'
            '           IF A-ON OR B = 1 DISPLAY "MIXED" END-IF\n'
            '           GOBACK.\n'
        )
        self.assertEqual(lines, ["OR", "NOT-AND", "THEN", "MIXED"])

    def test_perform_until_condition_names_with_or(self):
        lines = self.display(
            '01 N PIC 9 VALUE 0.\n'
            '   88 N-DONE VALUE 3.\n'
            '01 E PIC 9 VALUE 0.\n'
            '   88 E-EOF VALUE 1.\n'
            '       P1. PERFORM UNTIL N-DONE OR E-EOF ADD 1 TO N END-PERFORM\n'
            '           DISPLAY N GOBACK.\n'
        )
        self.assertEqual(lines, ["3"])

    # ---- 5. EVALUATE：WHEN TRUE／FALSE、EVALUATE FALSE、條件主體
    def test_evaluate_when_true_does_not_recurse(self):
        lines = self.display(
            '01 A PIC 9 VALUE 1.\n'
            '       P1. EVALUATE A WHEN TRUE DISPLAY "HIT" WHEN OTHER DISPLAY "NO" END-EVALUATE\n'
            '           GOBACK.\n'
        )
        self.assertEqual(lines, ["HIT"])

    def test_evaluate_false_and_condition_subjects(self):
        lines = self.display(
            '01 A PIC 9 VALUE 7.\n'
            '       P1. EVALUATE FALSE\n'
            '             WHEN A = 7 DISPLAY "WRONG"\n'
            '             WHEN A = 1 DISPLAY "FALSE-HIT"\n'
            '           END-EVALUATE\n'
            '           EVALUATE A > 5 ALSO A < 3\n'
            '             WHEN TRUE ALSO FALSE DISPLAY "BOTH"\n'
            '             WHEN OTHER DISPLAY "OTHER"\n'
            '           END-EVALUATE\n'
            '           EVALUATE TRUE\n'
            '             WHEN NOT A > 5 DISPLAY "LOW"\n'
            '             WHEN A = 7 DISPLAY "SEVEN"\n'
            '           END-EVALUATE GOBACK.\n'
        )
        self.assertEqual(lines, ["FALSE-HIT", "BOTH", "SEVEN"])

    def test_alphanumeric_thru_condition(self):
        lines = self.display(
            '01 C PIC X VALUE "M".\n'
            '   88 C-UP VALUE "A" THRU "Z".\n'
            '       P1. IF C-UP DISPLAY "UP" ELSE DISPLAY "NO" END-IF GOBACK.\n'
        )
        self.assertEqual(lines, ["UP"])

    # ---- 7. SET 條件名稱 TO TRUE／FALSE
    def test_set_condition_true_with_multiple_values_and_subscript(self):
        lines = self.display(
            '01 C PIC X VALUE "Z".\n'
            '   88 C-OK VALUE "A" "B".\n'
            '01 T.\n'
            '   05 F PIC X OCCURS 3 VALUE "N".\n'
            '      88 F-Y VALUE "Y".\n'
            '       P1. SET C-OK TO TRUE DISPLAY C\n'
            '           SET F-Y(2) TO TRUE DISPLAY F(1) F(2) F(3)\n'
            '           IF F-Y(2) DISPLAY "Y2" END-IF\n'
            '           IF NOT F-Y(3) DISPLAY "N3" END-IF GOBACK.\n'
        )
        self.assertEqual(lines, ["A", "NYN", "Y2", "N3"])

    def test_set_condition_false(self):
        lines = self.display(
            '01 C PIC X VALUE "A".\n'
            '   88 C-OK VALUE "A" "B" WHEN SET TO FALSE IS "N".\n'
            '       P1. SET C-OK TO FALSE DISPLAY C GOBACK.\n'
        )
        self.assertEqual(lines, ["N"])

    def test_set_condition_false_without_clause_is_an_error(self):
        with self.assertRaises(RuntimeError_):
            self.display(
                '01 C PIC X VALUE "A".\n'
                '   88 C-OK VALUE "A" "B".\n'
                '       P1. SET C-OK TO FALSE GOBACK.\n'
            )

    # ---- 8. 88 的多段 THRU
    def test_condition_with_several_ranges(self):
        lines = self.display(
            '01 N PIC 99 VALUE 15.\n'
            '   88 N-OK VALUE 1 THRU 5, 10 THRU 20.\n'
            '       P1. IF N-OK DISPLAY "OK" END-IF\n'
            '           MOVE 7 TO N IF NOT N-OK DISPLAY "GAP" END-IF GOBACK.\n'
        )
        self.assertEqual(lines, ["OK", "GAP"])

    # ---- 9. 有號／有小數的數字欄位是 NUMERIC
    def test_signed_and_decimal_fields_are_numeric(self):
        lines = self.display(
            '01 N PIC S99 VALUE -12.\n'
            '01 D PIC 9V9 VALUE 1.5.\n'
            '       P1. IF N IS NUMERIC DISPLAY "N" END-IF\n'
            '           IF D IS NUMERIC DISPLAY "D" END-IF GOBACK.\n'
        )
        self.assertEqual(lines, ["N", "D"])

    # ---- 10. 兩邊都是文數字時照文字比較
    def test_alphanumeric_comparison_is_textual(self):
        lines = self.display(
            '01 C PIC X(2) VALUE "1".\n'
            '   88 C-01 VALUE "01".\n'
            '01 N PIC 99 VALUE 1.\n'
            '       P1. IF C = "01" DISPLAY "EQ" ELSE DISPLAY "NE" END-IF\n'
            '           IF C-01 DISPLAY "C88" ELSE DISPLAY "NOT-C88" END-IF\n'
            '           IF N = 1 DISPLAY "NUM-EQ" END-IF GOBACK.\n'
        )
        self.assertEqual(lines, ["NE", "NOT-C88", "NUM-EQ"])


class ControlFlowTest(DisplayMixin, unittest.TestCase):
    """PERFORM 範圍、GO TO、EXIT PERFORM／PARAGRAPH／SECTION。"""

    def test_go_to_depending_picks_target(self):
        lines = self.display(
            '01 N PIC 9(2) VALUE 2.\n'
            '       P1. GO TO T-1 T-2 DEPENDING ON N\n'
            '           DISPLAY "skip".\n'
            '       T-1. DISPLAY "one".\n'
            '       T-2. DISPLAY "two".\n'
            '           EXIT.\n'
        )
        self.assertEqual(lines, ["two"])

    def test_go_to_depending_out_of_range_falls_through(self):
        # 索引超出目標範圍時不跳，接著執行下一句；段落結束後照 COBOL 規則
        # 繼續執行後面的段落
        lines = self.display(
            '01 N PIC 9(2) VALUE 9.\n'
            '       P1. GO TO T-1 DEPENDING ON N\n'
            '           DISPLAY "fallthrough".\n'
            '       T-1. DISPLAY "one".\n'
            '           EXIT.\n'
        )
        self.assertEqual(lines, ["fallthrough", "one"])

    def test_go_to_depending_targets_first(self):
        lines = self.display(
            '01 N PIC 9(2) VALUE 2.\n'
            '       P1. GO TO T-1 T-2 DEPENDING ON N\n'
            '           DISPLAY "skip".\n'
            '       T-1. DISPLAY "one".\n'
            '       T-2. DISPLAY "two".\n'
            '           EXIT.\n'
        )
        self.assertEqual(lines, ["two"])

    def test_go_to_depending_subject_first(self):
        # `GO TO DEPENDING ON x A B` 這種寫法也有人用；
        # 跳到 T-1 後照 COBOL 規則繼續往下一段執行，所以會印兩行
        lines = self.display(
            '01 N PIC 9(2) VALUE 1.\n'
            '       P1. GO TO DEPENDING ON N T-1 T-2\n'
            '           DISPLAY "skip".\n'
            '       T-1. DISPLAY "one".\n'
            '       T-2. DISPLAY "two".\n'
            '           EXIT.\n'
        )
        self.assertEqual(lines, ["one", "two"])

    def test_go_to_inside_if_does_not_eat_end_if(self):
        lines = self.display(
            '01 N PIC 9(2) VALUE 1.\n'
            '       P1. IF N = 1\n'
            '               GO TO T-1\n'
            '           END-IF\n'
            '           DISPLAY "after".\n'
            '       T-1. DISPLAY "jumped".\n'
            '           EXIT.\n'
        )
        self.assertEqual(lines, ["jumped"])

    def test_bare_exit_before_paragraph_header(self):
        lines = self.display(
            '01 N PIC 9(2) VALUE 3.\n'
            '       P1. ADD 1 TO N\n'
            '           EXIT.\n'
            '       NEXT-PARA. DISPLAY N.\n'
            '           EXIT.\n'
        )
        self.assertEqual(lines, ["4"])

    # ---- 2. GO TO 跳出 PERFORM 範圍
    def test_go_to_out_of_perform_transfers_control(self):
        lines = self.display(
            '01 N PIC 9 VALUE 0.\n'
            '       MAIN-P. PERFORM CHECK-P\n'
            '           DISPLAY "AFTER-PERFORM" GOBACK.\n'
            '       CHECK-P. GO TO ERR-P.\n'
            '       ERR-P. DISPLAY "ERR" GOBACK.\n'
        )
        self.assertEqual(lines, ["ERR"])

    def test_go_to_out_of_inline_perform(self):
        lines = self.display(
            '01 N PIC 9 VALUE 0.\n'
            '       MAIN-P. PERFORM 3 TIMES\n'
            '               ADD 1 TO N\n'
            '               IF N = 2 GO TO DONE-P END-IF\n'
            '           END-PERFORM\n'
            '           DISPLAY "LOOP-END" GOBACK.\n'
            '       DONE-P. DISPLAY "DONE " N GOBACK.\n'
        )
        self.assertEqual(lines, ["DONE 2"])

    def test_go_to_inside_perform_thru_range(self):
        lines = self.display(
            '01 N PIC 9 VALUE 0.\n'
            '       MAIN-P. PERFORM A-P THRU A-EXIT DISPLAY "N=" N GOBACK.\n'
            '       A-P. ADD 1 TO N GO TO A-EXIT.\n'
            '       A-MID. ADD 5 TO N.\n'
            '       A-EXIT. EXIT.\n'
        )
        self.assertEqual(lines, ["N=1"])

    # ---- C1：EXIT PERFORM [CYCLE]／EXIT PARAGRAPH／EXIT SECTION
    def test_exit_perform_and_cycle(self):
        lines = self.display(
            '01 N PIC 99 VALUE 0.\n'
            '01 S PIC 99 VALUE 0.\n'
            '       P1. PERFORM VARYING N FROM 1 BY 1 UNTIL N > 5\n'
            '               IF N = 2 EXIT PERFORM CYCLE END-IF\n'
            '               IF N = 4 EXIT PERFORM END-IF\n'
            '               ADD N TO S\n'
            '           END-PERFORM\n'
            '           DISPLAY N " " S GOBACK.\n'
        )
        self.assertEqual(lines, ["4 4"])

    def test_exit_perform_outside_inline_perform_is_an_error(self):
        with self.assertRaises(RuntimeError_):
            self.display('       P1. EXIT PERFORM GOBACK.\n')

    def test_exit_paragraph(self):
        lines = self.display(
            '01 N PIC 999 VALUE 0.\n'
            '       FIRST-P. ADD 1 TO N EXIT PARAGRAPH ADD 10 TO N.\n'
            '       SECOND-P. ADD 100 TO N DISPLAY N GOBACK.\n'
        )
        self.assertEqual(lines, ["101"])

    def test_exit_section(self):
        lines = run_full(
            "       MAIN-S SECTION.\n"
            "       M1.\n"
            "           PERFORM WORK-S1 THRU WORK-S3\n"
            "           DISPLAY N\n"
            "           GOBACK.\n"
            "       WORK SECTION.\n"
            "       WORK-S1.\n"
            "           ADD 1 TO N\n"
            "           EXIT SECTION.\n"
            "       WORK-S2.\n"
            "           ADD 10 TO N.\n"
            "       WORK-S3.\n"
            "           ADD 100 TO N.\n",
            "       01 N PIC 999 VALUE 0.\n",
        )
        self.assertEqual(lines, ["1"])

    def test_plain_exit_is_a_no_op(self):
        lines = self.display('       P1. EXIT\n           DISPLAY "AFTER" GOBACK.\n')
        self.assertEqual(lines, ["AFTER"])


class StringStatementTest(DisplayMixin, unittest.TestCase):
    """STRING、UNSTRING、INSPECT 與參照修飾。"""

    def test_reference_modification(self):
        # X (a : b) = 從第 a 個字開始取 b 個字
        lines = self.display(
            '01 S PIC X(10) VALUE "ABCDEFGHIJ".\n'
            '       P1. DISPLAY "[" S (2 : 3) "]" GOBACK.\n'
        )
        self.assertEqual(lines, ["[BCD]"])

    def test_reference_modification_zero_length_is_error(self):
        with self.assertRaises(RuntimeError_):
            run_program(
                "01 S PIC X(10) VALUE \"ABCDEFGHIJ\".\n"
                "       P1. DISPLAY S (2 : 0).\n"
            )

    # ---- 12. INSPECT
    def test_inspect_tallying_accumulates_and_variants(self):
        lines = self.display(
            '01 A PIC X(5) VALUE "  ABA".\n'
            '01 N PIC 99 VALUE 10.\n'
            '01 L PIC 99 VALUE 0.\n'
            '01 C PIC 99 VALUE 0.\n'
            '       P1. INSPECT A TALLYING N FOR ALL "A"\n'
            '           INSPECT A TALLYING L FOR LEADING SPACES C FOR CHARACTERS\n'
            '           DISPLAY N " " L " " C GOBACK.\n'
        )
        self.assertEqual(lines, ["12 2 5"])

    def test_inspect_replacing_leading_first_characters_and_bounds(self):
        lines = self.display(
            '01 A PIC X(5) VALUE "AAAAB".\n'
            '01 B PIC X(5) VALUE "AAAAB".\n'
            '01 C PIC X(10) VALUE "AA-BB-AA".\n'
            '       P1. INSPECT A REPLACING LEADING "A" BY "B"\n'
            '           INSPECT B REPLACING LEADING "A" BY "A"\n'
            '           INSPECT C REPLACING FIRST "B" BY "X" AFTER INITIAL "-"\n'
            '           INSPECT C REPLACING CHARACTERS BY "*" AFTER INITIAL "X" BEFORE INITIAL "A"\n'
            '           DISPLAY A " " B " " C GOBACK.\n'
        )
        self.assertEqual(lines, ["BBBBB AAAAB AA-X**AA  "])

    def test_unstring_all_or_delimiter_in_count_in(self):
        lines = self.display(
            '01 S PIC X(12) VALUE "AB,CDE;F".\n'
            '01 W PIC X(10) VALUE "AB   CD".\n'
            '01 X1 PIC X(4).\n'
            '01 X2 PIC X(4).\n'
            '01 D1 PIC X.\n'
            '01 C2 PIC 99.\n'
            '01 P PIC 99 VALUE 1.\n'
            '01 T PIC 99 VALUE 0.\n'
            '       P1. UNSTRING S DELIMITED BY "," OR ";"\n'
            '              INTO X1 DELIMITER IN D1 X2 COUNT IN C2\n'
            '              WITH POINTER P TALLYING IN T\n'
            '           END-UNSTRING\n'
            '           DISPLAY X1 "|" D1 "|" X2 "|" C2 "|" P "|" T\n'
            '           UNSTRING W DELIMITED BY ALL SPACE INTO X1 X2\n'
            '           DISPLAY X1 "|" X2 GOBACK.\n'
        )
        self.assertEqual(lines, ["AB  |,|CDE |3|8|2", "AB  |CD  "])


class IntrinsicTest(DisplayMixin, unittest.TestCase):
    """FUNCTION 內建函式。"""

    def test_intrinsic_wrong_arg_count_is_clean_error(self):
        with self.assertRaises(RuntimeError_):
            run_program(
                "01 N PIC 9 VALUE 0.\n"
                "       P1. COMPUTE N = FUNCTION MOD (7) DISPLAY N.\n"
            )
        with self.assertRaises(RuntimeError_):
            run_program(
                "01 N PIC 9 VALUE 0.\n"
                "       P1. COMPUTE N = FUNCTION SQRT () DISPLAY N.\n"
            )

    def test_numval_c_with_currency(self):
        lines = self.display(
            "01 N PIC 9(6)V99 VALUE 0.\n"
            '       P1. COMPUTE N = FUNCTION NUMVAL-C ("$1,234.56") DISPLAY N.\n'
        )
        self.assertEqual(lines, ["1234.56"])
        with self.assertRaises(RuntimeError_):
            run_program(
                "01 N PIC 9(6)V99 VALUE 0.\n"
                '       P1. COMPUTE N = FUNCTION NUMVAL-C ("abc") DISPLAY N.\n'
            )

    def test_huge_factorial_is_clean_error(self):
        with self.assertRaises(RuntimeError_):
            run_program(
                "01 N PIC 9(5) VALUE 0.\n"
                "       P1. COMPUTE N = FUNCTION FACTORIAL (99999) DISPLAY N.\n"
            )

    def test_max_multiple_args(self):
        lines = self.display(
            '01 R PIC 9(2).\n'
            '       P1. COMPUTE R = FUNCTION MAX (3, 7, 2) DISPLAY R.\n'
        )
        self.assertEqual(lines, ["7"])

    def test_min_multiple_args(self):
        lines = self.display(
            '01 R PIC 9(2).\n'
            '       P1. COMPUTE R = FUNCTION MIN (3, 7, 2) DISPLAY R.\n'
        )
        self.assertEqual(lines, ["2"])

    def test_max_single_arg(self):
        lines = self.display(
            '01 R PIC 9(2).\n'
            '       P1. COMPUTE R = FUNCTION MAX (5) DISPLAY R.\n'
        )
        self.assertEqual(lines, ["5"])

    # ---- 15. FUNCTION LENGTH 回傳欄位長度
    def test_function_length_of_numeric_and_group(self):
        lines = self.display(
            '01 N PIC 9(5) VALUE 42.\n'
            '01 G.\n'
            '   05 A PIC X(3).\n'
            '   05 B PIC 9(4).\n'
            '01 L PIC 99.\n'
            '01 M PIC 99.\n'
            '       P1. COMPUTE L = FUNCTION LENGTH(N)\n'
            '           COMPUTE M = FUNCTION LENGTH(G)\n'
            '           DISPLAY L " " M GOBACK.\n'
        )
        self.assertEqual(lines, ["5 7"])

    def test_length_check_is_reported_as_unsupported(self):
        with self.assertRaises(RuntimeError_):
            self.display('01 N PIC 9.\n       P1. COMPUTE N = FUNCTION LENGTH-CHECK("AB") GOBACK.\n')
