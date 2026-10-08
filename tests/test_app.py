"""CLI 周邊模組。

執行方式::

    python -m unittest discover -s tests -t .
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

from tests.support import DisplayMixin


class AppTest(DisplayMixin, unittest.TestCase):
    """CLI 周邊：題目辨識、JSON、主控台輸出。"""

    def test_classify_files_is_case_insensitive(self):
        import tempfile

        from coblings.model import classify_files

        with tempfile.TemporaryDirectory() as directory:
            for name in ("hellotest.cbl", "Main.cbl"):
                with open(os.path.join(directory, name), "w", encoding="utf-8") as handle:
                    handle.write("x")
            sources, checkers = classify_files(directory)
            self.assertEqual([os.path.basename(p) for p in checkers], ["hellotest.cbl"])
            self.assertEqual([os.path.basename(p) for p in sources], ["Main.cbl"])

    def test_json_surrogate_pair(self):
        from coblings import json_lite

        self.assertEqual(json_lite.parse('"\\uD83D\\uDE00"'), "\U0001F600")

    def test_console_write_without_buffer(self):
        import io

        from coblings import console

        saved = sys.stdout
        try:
            fake = io.StringIO()
            fake.isatty = lambda: False  # type: ignore[attr-defined]
            sys.stdout = fake  # type: ignore[assignment]
            console.print_text("hello")
            self.assertIn("hello", fake.getvalue())
        finally:
            sys.stdout = saved


class CliTest(unittest.TestCase):
    """指令列：選項解析、指令表、錯誤一律以結束碼回報。"""

    def setUp(self):
        from coblings import console

        console.enable_color(False)

    def test_parse_options_accepts_global_options_anywhere(self):
        from coblings.main import parse_options

        options = parse_options(["hint", "--no-color", "07", "--dir", "somewhere"])
        self.assertEqual(options.command, "hint")
        self.assertEqual(options.args, ["07"])
        self.assertEqual(options.directory, "somewhere")
        self.assertFalse(options.color)

    def test_aliases_map_to_commands(self):
        from coblings.main import COMMANDS, parse_options

        for alias, command in (("ls", "list"), ("r", "run"), ("v", "verify"), ("h", "hint")):
            self.assertEqual(parse_options([alias]).command, command)
            self.assertIn(command, COMMANDS)
        self.assertEqual(parse_options(["-h"]).command, "help")
        self.assertEqual(parse_options([]).command, "welcome")

    def test_version_works_outside_project(self):
        from coblings import main as cli

        with tempfile.TemporaryDirectory() as directory:
            saved = os.getcwd()
            os.chdir(directory)
            try:
                self.assertEqual(cli.main(["--version"]), 0)
            finally:
                os.chdir(saved)

    def test_unknown_command_returns_1(self):
        from coblings import main as cli

        self.assertEqual(cli.main(["no-such-command"]), 1)

    def test_unknown_exercise_returns_1_without_system_exit(self):
        from coblings import main as cli

        with tempfile.TemporaryDirectory() as root:
            exercise = os.path.join(root, "exercises", "01_a")
            os.makedirs(exercise)
            for name, text in (("A.cbl", "x"), ("ATest.cbl", "x"), ("exercise.json", "{}")):
                with open(os.path.join(exercise, name), "w", encoding="utf-8") as handle:
                    handle.write(text)
            exercises_dir = os.path.join(root, "exercises")
            self.assertEqual(cli.main(["--dir", exercises_dir, "verify", "99_nope"]), 1)
            self.assertEqual(cli.main(["--dir", exercises_dir, "hint", "99_nope"]), 1)
