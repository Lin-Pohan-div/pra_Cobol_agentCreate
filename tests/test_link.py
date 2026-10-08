"""學生檔與檢查器的連接。

執行方式::

    python -m unittest discover -s tests -t .
"""

from __future__ import annotations

import os
import tempfile
import unittest

from tests.support import run_program

from coblings.cobol.errors import RuntimeError_  # noqa: E402
from coblings.cobol.parser import parse_source  # noqa: E402


class LinkTest(unittest.TestCase):
    def test_duplicate_data_item_names_rejected(self):
        from coblings.cobol.pipeline import link_programs

        header = "IDENTIFICATION DIVISION.\n       PROGRAM-ID. T.\n"
        storage = "DATA DIVISION.\n       WORKING-STORAGE SECTION.\n       01 WS-A PIC X.\n"
        procedure = "       PROCEDURE DIVISION.\n       P1. EXIT.\n"
        student = parse_source(header + storage + procedure, "S.cbl")
        checker = parse_source(header + storage + procedure, "C.cbl")
        with self.assertRaises(RuntimeError_) as caught:
            link_programs(student, checker)
        self.assertIn("WS-A", str(caught.exception))

    def test_nested_duplicate_data_item_names_rejected(self):
        from coblings.cobol.pipeline import link_programs

        header = "IDENTIFICATION DIVISION.\n       PROGRAM-ID. T.\n"
        procedure = "       PROCEDURE DIVISION.\n       P1. EXIT.\n"
        student_storage = (
            "DATA DIVISION.\n       WORKING-STORAGE SECTION.\n"
            "       01 WS-G.\n           05 WS-NESTED PIC X.\n"
        )
        checker_storage = (
            "DATA DIVISION.\n       WORKING-STORAGE SECTION.\n"
            "       01 CK-G.\n           05 WS-NESTED PIC X.\n"
        )
        student = parse_source(header + student_storage + procedure, "S.cbl")
        checker = parse_source(header + checker_storage + procedure, "C.cbl")
        with self.assertRaises(RuntimeError_) as caught:
            link_programs(student, checker)
        self.assertIn("WS-NESTED", str(caught.exception))

    def test_student_stop_run_is_dropped(self):
        lines, code, _ = run_program(
            '       P1. PERFORM WORK\n           CALL "COBLINGS-DONE" GOBACK.\n',
            student='01 WS-X PIC X(2) VALUE "hi".\n       WORK. DISPLAY WS-X STOP RUN.\n',
        )
        self.assertEqual(code, 0)
        self.assertEqual(lines, ["hi"])

    def test_nested_stop_run_is_removed(self):
        from coblings.cobol.pipeline import link_programs

        student = parse_source(
            "IDENTIFICATION DIVISION.\n       PROGRAM-ID. S.\n"
            "       DATA DIVISION.\n       WORKING-STORAGE SECTION.\n"
            "       01 WS-N PIC 9 VALUE 1.\n"
            "       PROCEDURE DIVISION.\n"
            "       WORK.\n"
            "           IF WS-N = 1\n"
            "               STOP RUN\n"
            "           END-IF\n"
            "           DISPLAY \"after\".\n",
            "S.cbl",
        )
        checker = parse_source(
            "IDENTIFICATION DIVISION.\n       PROGRAM-ID. C.\n"
            "       PROCEDURE DIVISION.\n"
            "       P1. PERFORM WORK\n"
            "           CALL \"COBLINGS-DONE\"\n"
            "           GOBACK.\n",
            "C.cbl",
        )
        program = link_programs(student, checker)
        nested = program.paragraphs[-1].statements[0]
        self.assertEqual(nested.then_body[0].kind, "continue")

    def test_parse_stage_reports_duplicates(self):
        from coblings import verify as verify_module
        from coblings.model import Exercise

        with tempfile.TemporaryDirectory() as directory:
            student = os.path.join(directory, "A.cbl")
            checker = os.path.join(directory, "ATest.cbl")
            files = {
                student: (
                    "IDENTIFICATION DIVISION. PROGRAM-ID. A. "
                    "DATA DIVISION. WORKING-STORAGE SECTION. 01 WS-X PIC X. "
                    "PROCEDURE DIVISION. P1. EXIT."
                ),
                checker: (
                    "IDENTIFICATION DIVISION. PROGRAM-ID. B. "
                    "DATA DIVISION. WORKING-STORAGE SECTION. 01 WS-X PIC X. "
                    "PROCEDURE DIVISION. Q1. CALL \"COBLINGS-DONE\" GOBACK."
                ),
                os.path.join(directory, "exercise.json"): "{}",
            }
            for path, text in files.items():
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write(text)
            exercise = Exercise("t", "t", directory, student, checker, 1)
            diagnostics = verify_module.parse_stage(exercise)
            self.assertEqual(len(diagnostics), 1)
            self.assertIn("WS-X", diagnostics[0])

    def test_student_checker_paragraph_conflict_rejected(self):
        from coblings.cobol.pipeline import link_programs

        header = "IDENTIFICATION DIVISION.\n       PROGRAM-ID. T.\n"
        procedure = "       PROCEDURE DIVISION.\n"
        student = parse_source(
            header + procedure + "       P1. DISPLAY \"student\".\n",
            "S.cbl",
        )
        checker = parse_source(
            header + procedure + "       P1. DISPLAY \"checker\".\n",
            "C.cbl",
        )
        with self.assertRaises(RuntimeError_) as caught:
            link_programs(student, checker)
        self.assertIn("P1", str(caught.exception))
        self.assertIn("段落", str(caught.exception))
