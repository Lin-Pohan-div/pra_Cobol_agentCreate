"""判定流程與架構邊界的測試（verify / pipeline / runner / model / CLI）。

執行方式::

    python -m unittest discover -s tests -t .
"""

from __future__ import annotations

import decimal
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from coblings import main as cli  # noqa: E402
from coblings import verify  # noqa: E402
from coblings.cobol.errors import RuntimeError_, SyntaxError_  # noqa: E402
from coblings.cobol.interp import Interpreter  # noqa: E402
from coblings.cobol.layout import build_layout  # noqa: E402
from coblings.cobol.parser import parse_source  # noqa: E402
from coblings.cobol.pipeline import link_programs  # noqa: E402
from coblings.cobol.runner import RunResult  # noqa: E402
from coblings.model import Exercise  # noqa: E402

CHECKER = """       IDENTIFICATION DIVISION.
       PROGRAM-ID. T-TEST.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-ACTUAL  PIC X(5).
       PROCEDURE DIVISION.
       TEST-MAIN.
           PERFORM GET-WORD
           MOVE WS-WORD TO WS-ACTUAL
           CALL "COBLINGS-EXPECT-EQUALS"
               USING BY CONTENT "GET-WORD"
                     BY CONTENT "HELLO"
                     BY CONTENT WS-ACTUAL
           CALL "COBLINGS-DONE"
           GOBACK.
"""

STUDENT_HEADER = """       IDENTIFICATION DIVISION.
       PROGRAM-ID. T.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-WORD  PIC X(5).
       PROCEDURE DIVISION.
"""

SOLUTION = STUDENT_HEADER + """       GET-WORD.
           MOVE "HELLO" TO WS-WORD.
"""


class ExerciseDirectory:
    """在暫存資料夾建立一題（學生檔 + 檢查器）。"""

    def __init__(self, student: str, checker: str = CHECKER) -> None:
        self._temp = tempfile.TemporaryDirectory()
        directory = self._temp.name
        self.student = os.path.join(directory, "Word.cbl")
        self.checker = os.path.join(directory, "WordTest.cbl")
        for path, text in ((self.student, student), (self.checker, checker)):
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(text)
        self.exercise = Exercise("t", "t", directory, self.student, self.checker, 1)

    def __enter__(self) -> Exercise:
        return self.exercise

    def __exit__(self, *exc) -> None:
        self._temp.cleanup()


class PassDecisionTest(unittest.TestCase):
    """問題 1：通過與否只能由檢查器決定。"""

    def test_solution_passes(self):
        with ExerciseDirectory(SOLUTION) as exercise:
            self.assertEqual(verify.verify(exercise).status, verify.STATUS_PASSED)

    def test_wrong_answer_fails(self):
        wrong = STUDENT_HEADER + '       GET-WORD.\n           MOVE "WORLD" TO WS-WORD.\n'
        with ExerciseDirectory(wrong) as exercise:
            self.assertEqual(verify.verify(exercise).status, verify.STATUS_TEST_FAILED)

    def test_student_cannot_call_checker_builtins(self):
        cheat = STUDENT_HEADER + (
            "       GET-WORD.\n"
            '           CALL "COBLINGS-DONE"\n'
            "           GO TO ZZ-END.\n"
            "       ZZ-END.\n"
            "           CONTINUE.\n"
        )
        with ExerciseDirectory(cheat) as exercise:
            result = verify.verify(exercise)
        self.assertEqual(result.status, verify.STATUS_PARSE_ERROR)
        self.assertIn("COBLINGS-DONE", result.errors[0])
        self.assertTrue(result.errors[0].startswith("Word.cbl:"))

    def test_printed_marker_and_go_to_escape_do_not_pass(self):
        # 學生印出通過標記、再用 GO TO 跳過檢查器的斷言：stdout 不再是判定依據
        cheat = STUDENT_HEADER + (
            "       GET-WORD.\n"
            '           DISPLAY "COBLINGS_TESTS_PASSED"\n'
            "           GO TO ZZ-END.\n"
            "       ZZ-END.\n"
            "           CONTINUE.\n"
        )
        with ExerciseDirectory(cheat) as exercise:
            self.assertEqual(verify.verify(exercise).status, verify.STATUS_TEST_FAILED)

    def test_run_result_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "result.txt")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(RunResult(passed=True, return_code=0, checks=3).dump())
            loaded = RunResult.load(path)
            self.assertIsNotNone(loaded)
            self.assertTrue(loaded.passed)
            self.assertEqual(loaded.checks, 3)
            self.assertIsNone(RunResult.load(os.path.join(directory, "missing.txt")))


class PipelineTest(unittest.TestCase):
    def test_link_does_not_mutate_student_ast(self):
        student = parse_source(
            STUDENT_HEADER + "       GET-WORD.\n           IF 1 = 1\n               STOP RUN\n           END-IF.\n",
            "Word.cbl",
        )
        checker = parse_source(CHECKER, "WordTest.cbl")
        link_programs(student, checker)
        kinds = [node.kind for node in student.paragraphs[0].walk()]
        self.assertIn("stop_run", kinds)

    def test_linked_program_has_no_stop_from_student(self):
        student = parse_source(
            STUDENT_HEADER + "       GET-WORD.\n           IF 1 = 1\n               STOP RUN\n           END-IF.\n",
            "Word.cbl",
        )
        program = link_programs(student, parse_source(CHECKER, "WordTest.cbl"))
        kinds = [node.kind for node in program.paragraphs[-1].walk()]
        self.assertNotIn("stop_run", kinds)


class LimitsTest(unittest.TestCase):
    """問題 4：巢狀 OCCURS 的乘積也有上限。"""

    def test_nested_occurs_product_is_capped(self):
        source = STUDENT_HEADER.replace(
            "       01  WS-WORD  PIC X(5).\n",
            "       01  T.\n"
            "           05  ROW OCCURS 2000 TIMES.\n"
            "               10  COL PIC X OCCURS 2000 TIMES.\n",
        ) + "       P1.\n           EXIT.\n"
        program = parse_source(source, "Big.cbl")
        with self.assertRaises(SyntaxError_) as caught:
            build_layout(program)
        self.assertIn("資料區太大", caught.exception.message)

    def test_runner_environment_is_whitelisted(self):
        os.environ["COBLINGS_SECRET_FOR_TEST"] = "x"
        try:
            environment = verify.runner_environment()
        finally:
            del os.environ["COBLINGS_SECRET_FOR_TEST"]
        self.assertNotIn("COBLINGS_SECRET_FOR_TEST", environment)
        self.assertIn("PYTHONPATH", environment)


class BoundaryTest(unittest.TestCase):
    """問題 3、5、6：直譯器不碰全域狀態，錯誤介面一致。"""

    def test_decimal_context_is_not_modified(self):
        before = decimal.getcontext().prec
        program = parse_source(SOLUTION, "Word.cbl")
        Interpreter(program, build_layout(program)).run()
        self.assertEqual(decimal.getcontext().prec, before)

    def test_interpreter_output_is_injected(self):
        program = parse_source(STUDENT_HEADER + '       P1.\n           DISPLAY "HI".\n', "T.cbl")
        captured: list[str] = []
        Interpreter(program, build_layout(program), output=captured.append).run()
        self.assertEqual(captured, ["HI"])

    def test_error_format_signature_is_uniform(self):
        syntax = SyntaxError_("bad", line=3, column=2, filename="A.cbl")
        self.assertEqual(syntax.format(), "A.cbl:3:2: error: bad")
        self.assertEqual(syntax.format("B.cbl"), "B.cbl:3:2: error: bad")
        self.assertEqual(SyntaxError_("bad").format(), "exercise: error: bad")
        self.assertEqual(RuntimeError_("boom", "move（第 1 行）").format("ignored"), "move（第 1 行）: boom")

    def test_dir_option_without_value_is_an_error(self):
        self.assertEqual(cli.main(["--no-color", "--dir"]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
