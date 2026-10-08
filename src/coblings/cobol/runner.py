"""COBOL 執行器的行程進入點。

這支程式會在**獨立行程**中執行（core-spec CORE-VER-06），流程：

1. 用 :func:`pipeline.load_program` 讀入、解析並連接學生檔與檢查器
2. 執行連接後的程式，``DISPLAY`` 與斷言內建的標記即時印到 stdout
3. 在產物目錄寫下兩個檔案：

   * ``display.txt``：``DISPLAY`` 的內容，供 ``expected.txt`` 比對
   * ``result.txt``：結構化的執行結果（``passed`` / ``return_code`` / ``checks``），
     是判定通過的唯一依據——不再從 stdout 搜尋通過標記

用法（由 ``coblings`` CLI 以子行程呼叫）::

    python -m coblings.cobol.runner --dir <題目資料夾> --student <學生檔> \\
        --checker <檢查器> --out <產物目錄> [--timeout 9]
"""

from __future__ import annotations

import argparse
import os
import sys

if __package__ in (None, ""):  # 直接以腳本方式執行時補上套件路徑
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from coblings.cobol.errors import AssertionFailure, RuntimeError_, StopRun, SyntaxError_
from coblings.cobol.interp import Interpreter
from coblings.cobol.pipeline import describe_error, load_program

DISPLAY_FILENAME = "display.txt"
RESULT_FILENAME = "result.txt"


# ------------------------------------------------------------------ 結果檔

class RunResult:
    """子行程寫給 CLI 的執行結果。"""

    def __init__(self, passed: bool = False, return_code: int = 1, checks: int = 0) -> None:
        self.passed = passed
        self.return_code = return_code
        self.checks = checks

    def dump(self) -> str:
        return (
            f"passed:{'true' if self.passed else 'false'}\n"
            f"return_code:{self.return_code}\n"
            f"checks:{self.checks}\n"
        )

    @classmethod
    def load(cls, path: str) -> "RunResult | None":
        """讀取結果檔；檔案不存在或格式不對時回傳 None。"""
        try:
            with open(path, "r", encoding="utf-8") as handle:
                content = handle.read()
        except (OSError, UnicodeDecodeError):
            return None
        values: dict[str, str] = {}
        for line in content.splitlines():
            key, _, value = line.partition(":")
            values[key.strip()] = value.strip()
        try:
            return cls(
                passed=values["passed"] == "true",
                return_code=int(values["return_code"]),
                checks=int(values["checks"]),
            )
        except (KeyError, ValueError):
            return None


def _write_text(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _echo(text: str) -> None:
    sys.stdout.write(text + "\n")
    sys.stdout.flush()


# ------------------------------------------------------------------ 主流程

def run_exercise(
    directory: str,
    student_path: str,
    checker_path: str,
    artifact_dir: str,
    timeout: float | None = None,
) -> int:
    os.makedirs(artifact_dir, exist_ok=True)
    result = RunResult()
    display: list[str] = []
    try:
        try:
            program, layout = load_program(student_path, checker_path)
        except Exception as error:  # noqa: BLE001 - 直譯器缺陷也要變成可讀的訊息
            sys.stderr.write(describe_error(error) + "\n")
            return 1

        interpreter = Interpreter(
            program, layout, display=display, timeout=timeout,
            working_dir=directory, output=_echo,
        )
        return_code = 0
        try:
            return_code = interpreter.run()
        except AssertionFailure as failure:
            # 斷言失敗：訊息走 stdout，CLI 會當成「測試輸出」顯示
            _echo(failure.message)
            return_code = 1
        except SyntaxError_ as error:
            sys.stderr.write(error.format(os.path.basename(checker_path)) + "\n")
            return_code = 1
        except RuntimeError_ as error:
            sys.stderr.write("COBLINGS_RUNTIME_ERROR: " + error.format() + "\n")
            return_code = 1
        except StopRun as stop:
            return_code = stop.return_code
        except RecursionError:
            sys.stderr.write(
                "COBLINGS_RUNTIME_ERROR: 執行時遞迴太深，可能是段落互相 PERFORM 形成無窮遞迴\n"
            )
            return_code = 1
        except Exception as error:  # noqa: BLE001 - 直譯器缺陷改成可讀的訊息
            sys.stderr.write(
                f"COBLINGS_RUNTIME_ERROR: 直譯器內部錯誤（{type(error).__name__}）：{error}\n"
            )
            return_code = 1
        result = RunResult(
            passed=interpreter.passed and return_code == 0,
            return_code=return_code,
            checks=interpreter.checks,
        )
        return return_code
    finally:
        # 結果檔最後才寫，蓋掉學生程式可能用 ASSIGN TO 偷寫的同名檔
        _write_text(
            os.path.join(artifact_dir, DISPLAY_FILENAME),
            "\n".join(display) + ("\n" if display else ""),
        )
        _write_text(os.path.join(artifact_dir, RESULT_FILENAME), result.dump())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="COBOL 練習執行器")
    parser.add_argument("--dir", required=True, help="題目資料夾（檔案 I/O 的工作目錄）")
    parser.add_argument("--student", required=True, help="學生可編輯檔")
    parser.add_argument("--checker", required=True, help="檢查器")
    parser.add_argument("--out", required=True, help="產物目錄（寫 display.txt 與 result.txt）")
    parser.add_argument("--timeout", type=float, default=None, help="逾時秒數")
    args = parser.parse_args(argv)
    return run_exercise(
        os.path.abspath(args.dir),
        os.path.abspath(args.student),
        os.path.abspath(args.checker),
        os.path.abspath(args.out),
        args.timeout,
    )


if __name__ == "__main__":
    sys.exit(main())
