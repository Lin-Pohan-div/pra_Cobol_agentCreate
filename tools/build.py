"""啟動前的增量建置。

Python 不需要編譯就能執行，但這裡仍然做兩件事：

1. 檢查 Python 版本是否達到最低需求（3.11）
2. 有原始碼變動時用 :mod:`compileall` 產生 .pyc，讓之後的啟動更快

判斷要不要重建的方式與 Java 版一樣：只看修改時間，標記在 ``build/.last-build``
（core-spec CORE-BOOT-02、CORE-BOOT-08）。所有訊息只用 ASCII，
確保在任何主控台字碼頁下都看得懂（CORE-BOOT-05）。
"""

from __future__ import annotations

import compileall
import os
import sys

MIN_PYTHON = (3, 11)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
BUILD = os.path.join(ROOT, "build")
MARKER = os.path.join(BUILD, ".last-build")
TAG = "[coblings]"


def python_sources() -> list[str]:
    """列出 ``src`` 底下所有 Python 原始碼。"""
    found: list[str] = []
    for directory, _sub, files in os.walk(SRC):
        for name in files:
            if name.endswith(".py"):
                found.append(os.path.join(directory, name))
    return found


def newest_source_mtime() -> float:
    newest = 0.0
    for path in python_sources():
        try:
            newest = max(newest, os.path.getmtime(path))
        except OSError:
            pass
    return newest


def main() -> int:
    if sys.version_info < MIN_PYTHON:
        required = ".".join(str(part) for part in MIN_PYTHON)
        print(f"{TAG} Python {required} or newer is required.")
        return 1

    sources = python_sources()
    if not sources:
        print(f"{TAG} No Python sources found under src.")
        return 1

    needs_build = True
    if os.path.isfile(MARKER):
        needs_build = newest_source_mtime() > os.path.getmtime(MARKER)
    if not needs_build:
        return 0

    os.makedirs(BUILD, exist_ok=True)
    print(f"{TAG} Building...")
    if not compileall.compile_dir(SRC, quiet=1, force=True):
        print(f"{TAG} Build failed. Please check the Python sources.")
        return 1
    with open(MARKER, "w", encoding="ascii") as handle:
        handle.write("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
