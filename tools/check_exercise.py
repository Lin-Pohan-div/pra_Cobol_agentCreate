"""單題自我檢查：確認一題的「原題必敗、解答必過」兩個不變量。

用法::

    python tools/check_exercise.py 01_hello [02_variables ...]
"""

from __future__ import annotations

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


def verify(exercise_id: str, directory: str = ROOT) -> tuple[int, str]:
    environment = dict(os.environ)
    existing_path = environment.get("PYTHONPATH", "")
    environment["PYTHONPATH"] = SRC + (os.pathsep + existing_path if existing_path else "")
    process = subprocess.run(
        [sys.executable, "-X", "utf8", "-m", "coblings", "--no-color", "verify", exercise_id],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=directory,
        env=environment,
    )
    return process.returncode, process.stdout.decode("utf-8", errors="replace")


def check(exercise_id: str) -> bool:
    directory = os.path.join(ROOT, "exercises", exercise_id)
    source_name = None
    for name in sorted(os.listdir(directory)):
        if name.upper().endswith(".CBL") and not name.upper().endswith("TEST.CBL"):
            source_name = name
    if source_name is None:
        print(f"{exercise_id}: 找不到學生檔")
        return False

    source = os.path.join(directory, source_name)
    backup = source + ".bak"
    shutil.copy2(source, backup)

    ok = True
    try:
        code, output = verify(exercise_id)
        if code == 0:
            print(f"{exercise_id}: 原題竟然通過了（題目沒有意義）")
            ok = False
        else:
            print(f"{exercise_id}: 原題有失敗，符合預期")

        solution = os.path.join(ROOT, "solutions", exercise_id, source_name)
        if not os.path.isfile(solution):
            print(f"{exercise_id}: 找不到解答 {solution}")
            return False
        shutil.copy2(solution, source)
        code, output = verify(exercise_id)
        if code != 0:
            print(f"{exercise_id}: 解答沒有通過")
            print(output)
            ok = False
        else:
            print(f"{exercise_id}: 解答通過")
    finally:
        shutil.copy2(backup, source)
        os.remove(backup)
    return ok


def main() -> int:
    ids = sys.argv[1:]
    if not ids:
        print(__doc__)
        return 1
    failures = [exercise_id for exercise_id in ids if not check(exercise_id)]
    for exercise_id in failures:
        print(f"FAIL {exercise_id}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
