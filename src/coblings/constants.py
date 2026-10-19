"""跨模組共用的常數。"""

from __future__ import annotations

import os
import sys

# 工具名稱與版本
NAME = "Coblings"
VERSION = "0.1.0"

# 專案根目錄（此檔位於 <root>/src/coblings/constants.py）
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 狀態目錄與進度檔
STATE_DIR = ".coblings"
PROGRESS_HEADER = "# coblings progress - 請勿手動編輯"

# 題目目錄
EXERCISES_DIRNAME = "exercises"
SOLUTIONS_DIRNAME = "solutions"

# 通過／失敗標記定義在 cobol/builtins.py（只用於顯示與輸出清理，不再是通過的依據）

# 檢查器執行逾時（秒）
TEST_TIMEOUT_SECONDS = 10

# run 監看模式的輪詢間隔（秒）
WATCH_POLL_SECONDS = 1.0

# run 啟動時重新掃描進度，最多同時檢查幾題
SCAN_WORKERS = min(8, os.cpu_count() or 1)

# 產物目錄：runner 子行程把 display.txt／result.txt 寫在題目資料夾的這個子目錄
ARTIFACT_DIRNAME = ".coblings-out"

# 直譯器資源上限定義在 cobol/limits.py；這裡重新匯出，維持舊的 constants.MAX_* 用法
from .cobol.limits import (  # noqa: E402,F401
    MAX_FACTORIAL_ARG,
    MAX_FACTORIAL_RESULT,
    MAX_FILE_RECORDS,
    MAX_INPUT_LINES,
    MAX_OCCURS,
    MAX_PARAGRAPH_JUMPS,
    MAX_PIC_REPEAT,
    MAX_POWER_EXPONENT,
    MAX_RENDERED_ELEMENTS,
    MAX_STORAGE_BYTES,
    MAX_STORAGE_CELLS,
)


def launcher() -> str:
    """提示訊息中顯示的啟動指令。

    系統上沒有名為 coblings 的指令，而且 PowerShell 不會從目前目錄找執行檔，
    所以必須帶上 ``.\\`` 前綴（cmd 也接受）。
    """
    if sys.platform.startswith("win"):
        return ".\\coblings.cmd"
    return "./coblings.sh"


LAUNCHER = launcher()


def is_windows() -> bool:
    return sys.platform.startswith("win")