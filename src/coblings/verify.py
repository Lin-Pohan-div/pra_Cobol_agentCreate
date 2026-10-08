"""檢查一題：解析階段 + 執行階段。

對應 core-spec 第 3 章。與 Java 版一樣有兩個階段，只是第一階段不是編譯，
而是用內建的 COBOL 直譯器做解析（syntax check）：

1. ``parse``（建置類，無逾時）：解析學生檔與檢查器 → 語法錯誤就是「建置失敗」
2. ``run``（測試類，逾時 10 秒）：在獨立行程執行檢查器 → 通過／測試失敗／內部錯誤

另外每題可以放一個 ``expected.txt``，用來比對學生程式的 ``DISPLAY`` 輸出
（見 docs/spec/profile-cobol.md 第 3 章）。
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

from . import constants
from .cobol.builtins import FAIL_MARKER, PASS_MARKER
from .cobol.pipeline import describe_error, load_program
from .cobol.runner import DISPLAY_FILENAME, RESULT_FILENAME, RunResult
from .model import Exercise

ARTIFACT_DIRNAME = constants.ARTIFACT_DIRNAME
EXPECTED_FILENAME = "expected.txt"

STATUS_PASSED = "PASSED"
STATUS_PARSE_ERROR = "PARSE_ERROR"
STATUS_TEST_FAILED = "TEST_FAILED"
STATUS_INTERNAL_ERROR = "INTERNAL_ERROR"

#: 子行程只繼承這些環境變數（其餘不傳，學生程式用 ACCEPT FROM ENVIRONMENT 也讀不到）
INHERITED_ENVIRONMENT = (
    "PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC",
    "TEMP", "TMP", "TMPDIR", "HOME", "USERPROFILE", "LANG", "LC_ALL", "LC_CTYPE",
)


class Result:
    """一次檢查的結果。"""

    def __init__(
        self,
        status: str,
        errors: list[str] | None = None,
        output: str = "",
        message: str = "",
    ) -> None:
        self.status: str = status
        self.errors: list[str] = errors or []
        self.output: str = output
        self.message: str = message

    @property
    def passed(self) -> bool:
        return self.status == STATUS_PASSED


def _src_dir() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def parse_stage(exercise: Exercise) -> list[str]:
    """解析階段：回傳診斷清單，空清單代表解析成功。

    除了語法，還會做程式連接（含重名檢查）與資料版面（含 PICTURE 檢查），
    讓這類錯誤也在「建置失敗」階段就報出來，而不是等到執行階段。
    """
    try:
        load_program(exercise.source, exercise.checker)
    except Exception as error:  # noqa: BLE001 - 直譯器本身的缺陷不能讓 CLI 崩潰
        message = describe_error(error)
        return [message] if message else []
    return []


def runner_environment() -> dict[str, str]:
    environment = {
        name: os.environ[name] for name in INHERITED_ENVIRONMENT if name in os.environ
    }
    environment["PYTHONPATH"] = _src_dir()
    environment["PYTHONIOENCODING"] = "utf-8"
    return environment


def run_stage(exercise: Exercise, timeout: float = constants.TEST_TIMEOUT_SECONDS) -> Result:
    """執行階段：在獨立行程跑檢查器，合併擷取 stdout 與 stderr。

    通過的條件：沒有逾時、exit code 為 0、而且子行程寫的 ``result.txt``
    記錄檢查器呼叫了 ``COBLINGS-DONE``。
    """
    artifact = os.path.join(exercise.directory, ARTIFACT_DIRNAME)
    if os.path.isdir(artifact):
        _clean_directory(artifact)
    os.makedirs(artifact, exist_ok=True)

    command = [
        sys.executable,
        "-X",
        "utf8",
        "-m",
        "coblings.cobol.runner",
        "--dir",
        exercise.directory,
        "--student",
        exercise.source,
        "--checker",
        exercise.checker,
        "--out",
        artifact,
        "--timeout",
        str(max(1, int(timeout) - 1)),
    ]

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=exercise.directory,
            env=runner_environment(),
        )
    except OSError as error:
        return Result(STATUS_INTERNAL_ERROR, output=f"無法啟動測試程序：{error}")

    # communicate 會在另一條執行緒讀輸出，所以學生程式陷入無窮迴圈時逾時仍然有效
    try:
        raw, _ = process.communicate(timeout=timeout)
        exit_code = process.returncode
        timed_out = False
    except subprocess.TimeoutExpired:
        process.kill()
        raw, _ = process.communicate()
        exit_code = -1
        timed_out = True

    output = raw.decode("utf-8", errors="replace") if raw else ""

    if timed_out:
        return Result(
            STATUS_INTERNAL_ERROR,
            output=output,
            message=f"測試逾時（超過 {int(timeout)} 秒），可能有無窮迴圈。",
        )

    clean = clean_output(output)
    outcome = RunResult.load(os.path.join(artifact, RESULT_FILENAME))
    if exit_code == 0 and outcome is not None and outcome.passed:
        mismatch = compare_expected_output(exercise, artifact)
        if mismatch:
            return Result(STATUS_TEST_FAILED, output=mismatch, message="程式輸出與預期不符。")
        return Result(STATUS_PASSED, output=clean, message="全部測試通過。")

    return Result(
        STATUS_TEST_FAILED,
        output=clean,
        message="測試沒有輸出結果，可能缺少 COBLINGS-DONE。" if not clean else "測試失敗。",
    )


def verify(exercise: Exercise, timeout: float = constants.TEST_TIMEOUT_SECONDS) -> Result:
    """完整的兩階段檢查。"""
    diagnostics = parse_stage(exercise)
    if diagnostics:
        return Result(STATUS_PARSE_ERROR, errors=diagnostics)
    return run_stage(exercise, timeout)


def clean_output(output: str) -> str:
    """清掉標記行與空白行，只留下學生看得懂的輸出。"""
    kept: list[str] = []
    for line in output.replace("\r\n", "\n").split("\n"):
        trimmed = line.strip()
        if not trimmed:
            continue
        if trimmed == PASS_MARKER:
            continue
        if trimmed.startswith(FAIL_MARKER):
            continue
        kept.append(line)
    return "\n".join(kept).strip()


def compare_expected_output(exercise: Exercise, artifact: str) -> str:
    """把 ``DISPLAY`` 的輸出和 ``expected.txt`` 比對；不同時回傳差異說明。

    每一行右邊的空白會先去掉再比對，因為 ``DISPLAY`` 一個固定長度的欄位時，
    欄位補的空白也會一起印出來。
    """
    expected_path = os.path.join(exercise.directory, EXPECTED_FILENAME)
    if not os.path.isfile(expected_path):
        return ""
    try:
        with open(expected_path, "r", encoding="utf-8-sig") as handle:
            expected = [line.rstrip() for line in handle.read().split("\n") if line.strip()]

        display_path = os.path.join(artifact, DISPLAY_FILENAME)
        actual: list[str] = []
        if os.path.isfile(display_path):
            with open(display_path, "r", encoding="utf-8-sig") as handle:
                actual = [line.rstrip() for line in handle.read().split("\n") if line.strip()]
    except OSError as error:
        return f"讀不到輸出比對檔：{error}"

    if expected == actual:
        return ""

    lines = ["程式輸出與 expected.txt 不符："]
    for index in range(max(len(expected), len(actual))):
        left = expected[index] if index < len(expected) else "（沒有這一行）"
        right = actual[index] if index < len(actual) else "（沒有這一行）"
        if left == right:
            continue
        lines.append(f"  第 {index + 1} 行 期望: {left}")
        lines.append(f"  第 {index + 1} 行 實際: {right}")
    return "\n".join(lines)


def _clean_directory(directory: str) -> None:
    """清空資料夾內容；刪不掉就略過，不中止檢查。"""
    shutil.rmtree(directory, ignore_errors=True)
