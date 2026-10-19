"""出題者自我驗證工具（core-spec 第 8 章）。

對每一題檢查三件事：

1. ``.original/`` 有原題，而且與練習檔完全一致（reset 還原得回正確的題目）
2. 「未修改」的狀態下會失敗（題目有意義，不是白送）
3. 換上 ``solutions/`` 的解答後會通過（題目可解、檢查器寫對）

用法（在專案根目錄）::

    python tools/selftest.py
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys

# 輸出能是學生程式寫壞時的位元組，編碼錯誤時換成 ? 而不要中斷
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
EXERCISES = os.path.join(ROOT, "exercises")
SOLUTIONS = os.path.join(ROOT, "solutions")
STAGE = os.path.join(ROOT, "build", "selftest")

STUDENT_SUFFIX = ".cbl"
CHECKER_SUFFIX = "Test.cbl"


def run_cli(args: list[str], cwd: str = ROOT) -> tuple[int, str]:
    environment = dict(os.environ)
    existing_path = environment.get("PYTHONPATH", "")
    environment["PYTHONPATH"] = SRC + (os.pathsep + existing_path if existing_path else "")
    process = subprocess.run(
        [sys.executable, "-X", "utf8", "-m", "coblings", "--no-color", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=cwd,
        env=environment,
    )
    return process.returncode, process.stdout.decode("utf-8", errors="replace")


def digest(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def classify(directory: str) -> tuple[list[str], list[str]]:
    sources: list[str] = []
    checkers: list[str] = []
    for name in sorted(os.listdir(directory)):
        path = os.path.join(directory, name)
        if not os.path.isfile(path) or not name.upper().endswith(STUDENT_SUFFIX.upper()):
            continue
        (checkers if name.upper().endswith(CHECKER_SUFFIX.upper()) else sources).append(path)
    return sources, checkers


def check_file_counts(exercise_id: str, directory: str, failures: list[str]) -> bool:
    sources, checkers = classify(directory)
    if len(sources) != 1 or len(checkers) != 1:
        print(
            f"  {exercise_id} : 待修檔 {len(sources)} 個、測試檔 {len(checkers)} 個，兩者都必須剛好一個",
            file=sys.stderr,
        )
        failures.append(f"{exercise_id} (檔案數量不對)")
        return False
    return True


def check_original(exercise_id: str, directory: str, source: str, failures: list[str]) -> None:
    original = os.path.join(directory, ".original", os.path.basename(source) + ".orig")
    if not os.path.isfile(original):
        print(f"  {exercise_id} : 找不到原題 {original}", file=sys.stderr)
        failures.append(f"{exercise_id} (缺原題)")
    elif digest(original) != digest(source):
        print(f"  {exercise_id} : 與 {original} 不一致", file=sys.stderr)
        failures.append(f"{exercise_id} (與原題不一致)")


def stage_exercise(exercise_id: str, stage_exercises: str, source_from: str) -> str | None:
    """把一題的題目檔複製到暫存區，學生檔改用 ``source_from``；回傳暫存資料夾。"""
    directory = os.path.join(EXERCISES, exercise_id)
    sources, checkers = classify(directory)
    if len(sources) != 1 or len(checkers) != 1:
        return None
    destination = os.path.join(stage_exercises, exercise_id)
    os.makedirs(destination, exist_ok=True)
    shutil.copy2(os.path.join(directory, "exercise.json"), destination)
    shutil.copy2(checkers[0], destination)
    # expected.txt 也要一起帶過去，否則 DISPLAY 比對會被跳過，檢查變弱
    expected = os.path.join(directory, "expected.txt")
    if os.path.isfile(expected):
        shutil.copy2(expected, destination)
    shutil.copy2(source_from, os.path.join(destination, os.path.basename(sources[0])))
    return destination


def fresh_stage() -> str:
    """清空並建立暫存的 exercises 目錄。

    所有 verify 都在暫存區用 ``--dir`` 執行，進度寫在 build/selftest/.coblings，
    不會動到出題者自己在專案根目錄的練習進度。
    """
    stage_exercises = os.path.join(STAGE, "exercises")
    shutil.rmtree(STAGE, ignore_errors=True)
    os.makedirs(stage_exercises, exist_ok=True)
    return stage_exercises


def check_must_fail(exercise_ids: list[str], failures: list[str]) -> None:
    print("\n== 檢查 2/3：所有題目原本都應該失敗 ==", file=sys.stderr)
    stage_exercises = fresh_stage()
    for exercise_id in exercise_ids:
        sources, _ = classify(os.path.join(EXERCISES, exercise_id))
        if len(sources) != 1:
            continue
        # 用 .original/ 的原題，而不是可能已被改過的練習檔
        original = os.path.join(
            EXERCISES, exercise_id, ".original", os.path.basename(sources[0]) + ".orig"
        )
        if not os.path.isfile(original):
            continue  # 檢查 1 已經回報缺原題
        if stage_exercise(exercise_id, stage_exercises, original) is None:
            continue
        code, _ = run_cli(["--dir", stage_exercises, "verify", exercise_id])
        if code == 0:
            print(f"  {exercise_id} : 意外已經通過！", file=sys.stderr)
            failures.append(f"{exercise_id} (未修改就通過)")
    shutil.rmtree(STAGE, ignore_errors=True)


def check_solution_passes(exercise_ids: list[str], failures: list[str]) -> None:
    print("\n== 檢查 3/3：換上解答後所有題目都應該通過 ==", file=sys.stderr)
    stage_exercises = fresh_stage()

    for exercise_id in exercise_ids:
        sources, _ = classify(os.path.join(EXERCISES, exercise_id))
        if len(sources) != 1:
            continue
        solution = os.path.join(SOLUTIONS, exercise_id, os.path.basename(sources[0]))
        if not os.path.isfile(solution):
            print(f"  {exercise_id} : 找不到解答檔 {solution}", file=sys.stderr)
            failures.append(f"{exercise_id} (缺解答)")
            continue
        if stage_exercise(exercise_id, stage_exercises, solution) is None:
            continue

        code, output = run_cli(["--dir", stage_exercises, "verify", exercise_id])
        if code == 0:
            print(f"  {exercise_id} : PASS")
        else:
            print(f"  {exercise_id} : FAIL", file=sys.stderr)
            print("    " + " ".join(output.split()), file=sys.stderr)
            failures.append(f"{exercise_id} (解答未通過)")

    shutil.rmtree(STAGE, ignore_errors=True)


def main() -> int:
    print("== 重新建置 Coblings ==", file=sys.stderr)
    build = subprocess.run(
        [sys.executable, os.path.join(ROOT, "tools", "build.py")],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    if build.returncode != 0:
        print("建置失敗", file=sys.stderr)
        return 1

    if not os.path.isdir(EXERCISES):
        print(f"找不到練習目錄：{EXERCISES}", file=sys.stderr)
        return 1

    exercise_ids = sorted(
        name
        for name in os.listdir(EXERCISES)
        if os.path.isdir(os.path.join(EXERCISES, name)) and not name.startswith(".")
    )

    failures: list[str] = []
    print("\n== 檢查 1/3：.original/ 的原題應該和練習檔一致 ==", file=sys.stderr)
    for exercise_id in exercise_ids:
        directory = os.path.join(EXERCISES, exercise_id)
        if not check_file_counts(exercise_id, directory, failures):
            continue
        sources, _ = classify(directory)
        check_original(exercise_id, directory, sources[0], failures)

    check_must_fail(exercise_ids, failures)
    check_solution_passes(exercise_ids, failures)

    print("")
    if not failures:
        print(f"全部通過：{len(exercise_ids)} 題的測試與解答一致。")
        return 0
    print(f"發現 {len(failures)} 個問題：", file=sys.stderr)
    for item in failures:
        print(f"  - {item}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
