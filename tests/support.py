"""測試共用的輔助函式：組原始碼、連接檢查器與學生檔、執行並擷取 DISPLAY。"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from coblings.cobol.interp import Interpreter  # noqa: E402
from coblings.cobol.layout import build_layout  # noqa: E402
from coblings.cobol.parser import parse_source  # noqa: E402
from coblings.cobol.pipeline import link_programs  # noqa: E402

HEADER = """IDENTIFICATION DIVISION.
       PROGRAM-ID. T.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
"""
PROCEDURE = "       PROCEDURE DIVISION.\n"

#: 段落標頭（`P1.`、`P-A.` …）；資料描述項都以數字開頭，所以不會誤判
_PARAGRAPH = re.compile(r"^\s*[A-Z][A-Z0-9-]*\.")

#: 兩個帶 88 條件名稱的欄位（條件運算的測試共用）
COND_ITEMS = (
    '01 A PIC 9 VALUE 1.\n'
    '   88 A-ON VALUE 1.\n'
    '01 B PIC 9 VALUE 0.\n'
    '   88 B-ON VALUE 1.\n'
)


def split_declarations(text: str) -> tuple[str, str]:
    """把測試片段切成 (資料描述項, 敘述) 兩段。"""
    lines = text.split("\n")
    for index, line in enumerate(lines):
        if _PARAGRAPH.match(line):
            return "\n".join(lines[:index]), "\n".join(lines[index:])
    return text, ""


def build_source(text: str) -> str:
    data, code = split_declarations(text)
    return HEADER + data + "\n" + PROCEDURE + code


def run_program(source: str, *, student: str = "", timeout: float | None = 5.0):
    """把檢查器與學生檔接起來執行，回傳 (顯示的內容, 結束碼, 直譯器)。"""
    checker = parse_source(build_source(source), "Test.cbl")
    program = link_programs(parse_source(build_source(student), "Student.cbl"), checker)
    layout = build_layout(program)
    lines: list[str] = []
    interpreter = Interpreter(program, layout, display=lines, timeout=timeout)
    code = interpreter.run()
    return lines, code, interpreter


def display(source: str, student: str = "") -> list[str]:
    """執行一段程式並回傳 DISPLAY 的內容。"""
    lines, _code, _interp = run_program(source, student=student)
    return lines


def run_full(procedure: str, data: str = "") -> list[str]:
    """執行完整原始碼（可以寫 SECTION），回傳 DISPLAY 的內容。"""
    source = (
        "       IDENTIFICATION DIVISION.\n"
        "       PROGRAM-ID. T.\n"
        "       DATA DIVISION.\n"
        "       WORKING-STORAGE SECTION.\n"
        + data
        + "       PROCEDURE DIVISION.\n"
        + procedure
    )
    program = parse_source(source, "T.cbl")
    lines: list[str] = []
    Interpreter(program, build_layout(program), display=lines, timeout=5).run()
    return lines


class DisplayMixin:
    def display(self, source: str, student: str = "") -> list[str]:
        return display(source, student)
