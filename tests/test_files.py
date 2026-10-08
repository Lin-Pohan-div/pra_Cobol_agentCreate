"""FILE SECTION、順序檔、SORT／MERGE 與隨機存取。

執行方式::

    python -m unittest discover -s tests -t .
"""

from __future__ import annotations

import os
import tempfile
import unittest
from decimal import Decimal

from tests.support import DisplayMixin

from coblings.cobol.errors import RuntimeError_, SyntaxError_  # noqa: E402
from coblings.cobol.interp import Interpreter  # noqa: E402
from coblings.cobol.layout import build_layout  # noqa: E402
from coblings.cobol.parser import parse_source  # noqa: E402


class FileSectionTest(DisplayMixin, unittest.TestCase):
    """FILE SECTION 與順序檔。"""

    SOURCE = (
        "IDENTIFICATION DIVISION.\n"
        "       PROGRAM-ID. T.\n"
        "       ENVIRONMENT DIVISION.\n"
        "       INPUT-OUTPUT SECTION.\n"
        "       FILE-CONTROL.\n"
        "           SELECT F1 ASSIGN TO \"t1.dat\".\n"
        "       DATA DIVISION.\n"
        "       FILE SECTION.\n"
        "       FD  F1.\n"
        "       01  REC1  PIC X(4).\n"
        "       WORKING-STORAGE SECTION.\n"
        "       01  WS-GOT  PIC X(4).\n"
        "       PROCEDURE DIVISION.\n"
        "       P1. OPEN INPUT F1\n"
        "           READ F1 INTO WS-GOT\n"
        "           CLOSE F1\n"
        "           DISPLAY \"[\" WS-GOT \"]\".\n"
        "           GOBACK.\n"
    )

    def test_file_section_is_parsed(self):
        program = parse_source(self.SOURCE, "T.cbl")
        layout = build_layout(program)
        self.assertIn("F1", layout.records)
        self.assertEqual([field.name for field in layout.records["F1"]], ["REC1"])

    def test_file_section_in_data_division_also_works(self):
        source = self.SOURCE.replace(
            "       DATA DIVISION.\n       FILE SECTION.\n       FD  F1.\n"
            "       01  REC1  PIC X(4).\n       WORKING-STORAGE SECTION.\n",
            "       DATA DIVISION.\n       FILE SECTION.\n       FD  F1.\n"
            "       01  REC1  PIC X(4).\n       WORKING-STORAGE SECTION.\n",
        )
        program = parse_source(source, "T.cbl")
        self.assertIn("F1", build_layout(program).records)

    def test_open_statement_stops_at_next_statement(self):
        """OPEN 後面直接換一行寫別的敘述，不能被當成檔名。"""
        lines = self.display(
            '01 A PIC 9(2) VALUE 7.\n'
            '       P1. MOVE 5 TO A DISPLAY A GOBACK.\n'
        )
        self.assertEqual(lines, ["5"])


class FileIoTest(DisplayMixin, unittest.TestCase):
    """檔案 I/O：ASSIGN 路徑防護、讀寫、REWRITE。"""

    def test_assign_cannot_escape_exercise_dir(self):
        from coblings.cobol.errors import RuntimeError_
        from coblings.cobol.interp import Interpreter
        from coblings.cobol.layout import build_layout

        program = parse_source(
            "IDENTIFICATION DIVISION.\n       PROGRAM-ID. T.\n"
            "       PROCEDURE DIVISION.\n       P1. EXIT.\n",
            "T.cbl",
        )
        interpreter = Interpreter(program, build_layout(program), working_dir=os.getcwd())
        with self.assertRaises(RuntimeError_):
            interpreter._data_path(r"..\outside.dat")
        with self.assertRaises(RuntimeError_):
            interpreter._data_path(r"C:\Windows\note.dat")

    def test_read_not_at_end_does_not_run_when_empty(self):
        import tempfile

        from coblings.cobol.interp import Interpreter
        from coblings.cobol.layout import build_layout

        source = (
            "IDENTIFICATION DIVISION.\n"
            "       PROGRAM-ID. T.\n"
            "       ENVIRONMENT DIVISION.\n"
            "       INPUT-OUTPUT SECTION.\n"
            "       FILE-CONTROL.\n"
            '           SELECT F1 ASSIGN TO "empty.dat".\n'
            "       DATA DIVISION.\n"
            "       FILE SECTION.\n"
            "       FD F1.\n"
            "       01 REC PIC X(4).\n"
            "       WORKING-STORAGE SECTION.\n"
            "       01 FLAG PIC X VALUE \"N\".\n"
            "       PROCEDURE DIVISION.\n"
            "       P1.\n"
            "           OPEN INPUT F1\n"
            "           READ F1\n"
            "               NOT AT END\n"
            "                   MOVE \"Y\" TO FLAG\n"
            "           END-READ\n"
            "           CLOSE F1\n"
            "           DISPLAY FLAG\n"
            "           GOBACK.\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            program = parse_source(source, "T.cbl")
            lines: list[str] = []
            interpreter = Interpreter(
                program, build_layout(program), display=lines, working_dir=directory
            )
            interpreter.run()
        self.assertEqual(lines, ["N"])

    def test_record_read_is_left_justified(self):
        import tempfile

        from coblings.cobol.interp import Interpreter

        source = (
            "IDENTIFICATION DIVISION.\n"
            "       PROGRAM-ID. T.\n"
            "       ENVIRONMENT DIVISION.\n"
            "       INPUT-OUTPUT SECTION.\n"
            "       FILE-CONTROL.\n"
            '           SELECT F1 ASSIGN TO "r.dat".\n'
            "       DATA DIVISION.\n"
            "       FILE SECTION.\n"
            "       FD F1.\n"
            "       01 REC1 PIC X(4).\n"
            "       WORKING-STORAGE SECTION.\n"
            "       01 GOT PIC X(4).\n"
            "       PROCEDURE DIVISION.\n"
            "       P1.\n"
            "           OPEN INPUT F1\n"
            "           READ F1\n"
            "           CLOSE F1\n"
            '           MOVE REC1 TO GOT\n'
            "           DISPLAY \"[\" GOT \"]\"\n"
            "           GOBACK.\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            with open(os.path.join(directory, "r.dat"), "w", encoding="utf-8") as handle:
                handle.write("AB\n")
            program = parse_source(source, "T.cbl")
            lines: list[str] = []
            Interpreter(
                program, build_layout(program), display=lines, working_dir=directory
            ).run()
        self.assertEqual(lines, ["[AB  ]"])

    # ---- 16. I-O 模式的 REWRITE 要寫回磁碟
    def test_rewrite_in_io_mode_is_persisted(self):
        import tempfile

        from coblings.cobol.interp import Interpreter

        source = (
            "       IDENTIFICATION DIVISION.\n"
            "       PROGRAM-ID. T.\n"
            "       ENVIRONMENT DIVISION.\n"
            "       INPUT-OUTPUT SECTION.\n"
            "       FILE-CONTROL.\n"
            "           SELECT DATA-F ASSIGN TO \"data.dat\".\n"
            "       DATA DIVISION.\n"
            "       FILE SECTION.\n"
            "       FD DATA-F.\n"
            "       01 DATA-REC PIC X(3).\n"
            "       PROCEDURE DIVISION.\n"
            "       P1.\n"
            "           OPEN I-O DATA-F\n"
            "           READ DATA-F AT END CONTINUE END-READ\n"
            "           MOVE \"ZZZ\" TO DATA-REC\n"
            "           REWRITE DATA-REC\n"
            "           CLOSE DATA-F\n"
            "           GOBACK.\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "data.dat")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("AAA\nBBB\n")
            program = parse_source(source, "T.cbl")
            Interpreter(program, build_layout(program), timeout=10, working_dir=directory).run()
            with open(path, encoding="utf-8") as handle:
                self.assertEqual(handle.read(), "ZZZ\nBBB\n")

    def test_group_record_read_and_write(self):
        import tempfile

        from coblings.cobol.interp import Interpreter

        source = (
            "       IDENTIFICATION DIVISION.\n"
            "       PROGRAM-ID. T.\n"
            "       ENVIRONMENT DIVISION.\n"
            "       INPUT-OUTPUT SECTION.\n"
            "       FILE-CONTROL.\n"
            "           SELECT IN-F ASSIGN TO \"in.dat\".\n"
            "           SELECT OUT-F ASSIGN TO \"out.dat\".\n"
            "       DATA DIVISION.\n"
            "       FILE SECTION.\n"
            "       FD IN-F.\n"
            "       01 IN-REC.\n"
            "           05 IN-ID PIC 99.\n"
            "           05 IN-NAME PIC X(4).\n"
            "       FD OUT-F.\n"
            "       01 OUT-REC.\n"
            "           05 OUT-ID PIC 999.\n"
            "           05 OUT-NAME PIC X(5).\n"
            "       PROCEDURE DIVISION.\n"
            "       P1.\n"
            "           OPEN INPUT IN-F OUTPUT OUT-F\n"
            "           READ IN-F AT END CONTINUE END-READ\n"
            "           DISPLAY IN-ID \"|\" IN-NAME\n"
            "           MOVE IN-ID TO OUT-ID\n"
            "           MOVE IN-NAME TO OUT-NAME\n"
            "           WRITE OUT-REC\n"
            "           CLOSE IN-F OUT-F\n"
            "           GOBACK.\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            with open(os.path.join(directory, "in.dat"), "w", encoding="utf-8") as handle:
                handle.write("42ABCD\n")
            program = parse_source(source, "T.cbl")
            lines: list[str] = []
            Interpreter(
                program, build_layout(program), display=lines, timeout=10, working_dir=directory
            ).run()
            with open(os.path.join(directory, "out.dat"), encoding="utf-8") as handle:
                written = handle.read()
        self.assertEqual(lines, ["42|ABCD"])
        self.assertEqual(written, "042ABCD \n")


class SortMergeRandomTest(DisplayMixin, unittest.TestCase):
    """SORT／MERGE／隨機存取／FUNCTION RANDOM。"""

    FILE_PREAMBLE = (
        "IDENTIFICATION DIVISION.\n"
        "       PROGRAM-ID. T.\n"
        "       ENVIRONMENT DIVISION.\n"
        "       INPUT-OUTPUT SECTION.\n"
        "       FILE-CONTROL.\n"
        '           SELECT IN-F ASSIGN TO "in.dat".\n'
        '           SELECT IN-2 ASSIGN TO "in2.dat".\n'
        '           SELECT OUT-F ASSIGN TO "out.dat".\n'
        '           SELECT SORT-F ASSIGN TO "sort.tmp".\n'
        "       DATA DIVISION.\n"
        "       FILE SECTION.\n"
        "       FD IN-F.\n"
        "       01 IN-REC PIC X(3).\n"
        "       FD IN-2.\n"
        "       01 IN2-REC PIC X(3).\n"
        "       FD OUT-F.\n"
        "       01 OUT-REC PIC X(3).\n"
        "       SD SORT-F.\n"
        "       01 SORT-REC PIC X(3).\n"
        "       WORKING-STORAGE SECTION.\n"
        "       01 WS-LINE PIC X(3).\n"
        "       01 WS-EOF PIC X VALUE \"N\".\n"
        "       01 WS-RND PIC 9V9(5) VALUE 0.\n"
        "       PROCEDURE DIVISION.\n"
    )

    def run_files(self, code_lines, data_files):
        """在暫存目錄建資料檔、執行程式，回傳 (顯示內容, 產生的檔案)。"""
        import tempfile

        from coblings.cobol.interp import Interpreter

        with tempfile.TemporaryDirectory() as directory:
            for name, content in data_files.items():
                with open(os.path.join(directory, name), "w", encoding="utf-8") as handle:
                    handle.write(content)
            program = parse_source(self.FILE_PREAMBLE + code_lines, "T.cbl")
            lines: list[str] = []
            return_code = Interpreter(
                program, build_layout(program), display=lines,
                timeout=10, working_dir=directory,
            ).run()
            produced = {}
            for name in os.listdir(directory):
                if name not in data_files:
                    with open(os.path.join(directory, name), encoding="utf-8") as handle:
                        produced[name] = handle.read()
            return lines, return_code, produced

    def test_sort_ascending(self):
        lines, code, produced = self.run_files(
            "       P1.\n"
            "           SORT SORT-F ON ASCENDING KEY SORT-REC\n"
            "               USING IN-F GIVING OUT-F.\n"
            "           DISPLAY \"done\".\n"
            "           GOBACK.\n",
            {"in.dat": "C03\nA01\nB02\n"},
        )
        self.assertEqual(code, 0)
        self.assertEqual(produced["out.dat"], "A01\nB02\nC03\n")

    def test_sort_descending(self):
        _lines, code, produced = self.run_files(
            "       P1.\n"
            "           SORT SORT-F ON DESCENDING KEY SORT-REC\n"
            "               USING IN-F GIVING OUT-F.\n"
            "           GOBACK.\n",
            {"in.dat": "A01\nC03\nB02\n"},
        )
        self.assertEqual(code, 0)
        self.assertEqual(produced["out.dat"], "C03\nB02\nA01\n")

    def test_sort_requires_closed_files(self):
        with self.assertRaises(RuntimeError_):
            self.run_files(
                "       P1.\n"
                "           OPEN OUTPUT OUT-F.\n"
                "           SORT SORT-F ON ASCENDING KEY SORT-REC\n"
                "               USING IN-F GIVING OUT-F.\n"
                "           GOBACK.\n",
                {"in.dat": "B\nA\n"},
            )

    def test_sort_input_procedure_rejected(self):
        with self.assertRaises(SyntaxError_):
            parse_source(
                self.FILE_PREAMBLE
                + "       P1. SORT SORT-F ON ASCENDING KEY SORT-REC\n"
                "           INPUT PROCEDURE SORT-IN.\n",
                "T.cbl",
            )

    def test_merge_sorted_inputs(self):
        _lines, code, produced = self.run_files(
            "       P1.\n"
            "           MERGE SORT-F ON ASCENDING KEY SORT-REC\n"
            "               USING IN-F IN-2 GIVING OUT-F.\n"
            "           GOBACK.\n",
            {"in.dat": "A01\nC03\n", "in2.dat": "B02\nD04\n"},
        )
        self.assertEqual(code, 0)
        self.assertEqual(produced["out.dat"], "A01\nB02\nC03\nD04\n")

    def test_merge_rejects_unsorted_input(self):
        with self.assertRaises(RuntimeError_) as caught:
            self.run_files(
                "       P1.\n"
                "           MERGE SORT-F ON ASCENDING KEY SORT-REC\n"
                "               USING IN-F GIVING OUT-F.\n"
                "           GOBACK.\n",
                {"in.dat": "C03\nA01\n"},
            )
        self.assertIn("排好", str(caught.exception))

    def test_read_key_and_start(self):
        lines, code, _produced = self.run_files(
            "       P1.\n"
            "           OPEN INPUT OUT-F.\n"
            "           MOVE \"B02\" TO OUT-REC.\n"
            "           READ OUT-F KEY IS OUT-REC INTO WS-LINE.\n"
            "           DISPLAY \"[\" WS-LINE \"]\".\n"
            "           START OUT-F KEY IS > OUT-REC.\n"
            "           READ OUT-F INTO WS-LINE.\n"
            "           DISPLAY \"[\" WS-LINE \"]\".\n"
            "           CLOSE OUT-F.\n"
            "           GOBACK.\n",
            {"out.dat": "A01\nB02\nC03\n"},
        )
        self.assertEqual(code, 0)
        self.assertEqual(lines, ["[B02]", "[C03]"])

    def test_read_key_missing_runs_invalid_key(self):
        lines, code, _produced = self.run_files(
            "       P1.\n"
            "           OPEN INPUT OUT-F.\n"
            "           MOVE \"Z99\" TO OUT-REC.\n"
            "           READ OUT-F KEY IS OUT-REC INTO WS-LINE\n"
            "               INVALID KEY DISPLAY \"missed\"\n"
            "           END-READ.\n"
            "           CLOSE OUT-F.\n"
            "           GOBACK.\n",
            {"out.dat": "A01\n"},
        )
        self.assertEqual(code, 0)
        self.assertEqual(lines, ["missed"])

    def test_rewrite_and_delete_need_current_record(self):
        with self.assertRaises(RuntimeError_):
            self.run_files(
                "       P1.\n"
                "           OPEN I-O OUT-F.\n"
                "           MOVE \"ZZ\" TO OUT-REC.\n"
                "           REWRITE OUT-REC.\n"
                "           GOBACK.\n",
                {"out.dat": "A01\n"},
            )

    def test_random_in_range_and_seeded(self):
        lines = self.display(
            "01 R PIC 9V9(5) VALUE 0.\n"
            "01 S PIC 9V9(5) VALUE 0.\n"
            "       P1. COMPUTE R = FUNCTION RANDOM (7)\n"
            "           COMPUTE S = FUNCTION RANDOM (7)\n"
            "           DISPLAY R.\n"
        )
        value = Decimal(lines[0])
        self.assertTrue(Decimal(0) <= value < Decimal(1))
        self.assertEqual(lines, self.display(
            "01 R PIC 9V9(5) VALUE 0.\n"
            "01 S PIC 9V9(5) VALUE 0.\n"
            "       P1. COMPUTE R = FUNCTION RANDOM (7)\n"
            "           COMPUTE S = FUNCTION RANDOM (7)\n"
            "           DISPLAY R.\n"
        ))
