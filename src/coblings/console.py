"""終端機輸出：色彩、編碼、替代字、清畫面與表格。

對應 core-spec 第 6 章（CORE-OUT-01 ～ CORE-OUT-10）。

編碼策略（CORE-OUT-04、CORE-OUT-05）：輸出前先試著用終端機實際使用的編碼編碼整段文字；
編不進去的字元再逐字查替代表（✓→v、✗→x、→→->、—／─→-、其他→?）。
"""

from __future__ import annotations

import codecs
import ctypes
import os
import sys
import unicodedata

RESET = "\x1b[0m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"
RED = "\x1b[31m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"
BLUE = "\x1b[34m"
CYAN = "\x1b[36m"

#: 目前編碼表示不了的符號改用這些 ASCII 替代字
#: （接上終端機時不會用到這張表，因為終端機是 Unicode 的）
FALLBACKS = {
    "✓": "v",
    "✗": "x",
    "→": "->",
    "—": "-",
    "─": "-",
    "★": "*",
    "☆": "*",
    "…": "...",
    "•": "*",
    "×": "x",
}

_IS_WINDOWS = os.name == "nt"


def terminal_encoding() -> str:
    """取得輸出被導向檔案或管線時要使用的編碼（CORE-OUT-04）。

    接上終端機時不會用到這個值：此時交給 Python 直接寫入終端機
    （Windows 走 UTF-16，主控台字碼頁不會擋掉任何字元）。

    ``COBLINGS_ENCODING`` 或 ``PYTHONIOENCODING`` 可以強制指定；Windows 上預設
    會再問一次主控台的字碼頁，因為舊版 Python 的 ``sys.stdout.encoding`` 在被導向時
    只反映系統的 ANSI 字碼頁。
    """
    for name in ("COBLINGS_ENCODING", "PYTHONIOENCODING"):
        override = os.environ.get(name)
        if override:
            resolved = _resolve_codec(override)
            if resolved:
                return resolved

    if _IS_WINDOWS:
        code_page = _windows_code_page()
        if code_page:
            resolved = _resolve_codec(f"cp{code_page}")
            if resolved:
                return resolved

    return _resolve_codec(getattr(sys.stdout, "encoding", "") or "") or "utf-8"


def _resolve_codec(name: str) -> str | None:
    """把編碼名稱正規化；不支援就回傳 None。"""
    cleaned = (name or "").strip().lower()
    if not cleaned:
        return None
    if cleaned in ("ascii", "ansi_x3.4-1968", "us-ascii"):
        return None
    try:
        codecs.lookup(cleaned)
    except LookupError:
        return None
    return cleaned


def _windows_code_page() -> int | None:
    """Windows 上的 ANSI 字碼頁（與 shell 解讀原生程式輸出的方式一致）。"""
    try:
        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        return int(kernel32.GetACP())
    except Exception:  # pragma: no cover - 非預期環境
        return None


ENCODING = terminal_encoding()


def _supports_ansi() -> bool:
    """判斷終端機是否支援 ANSI 色碼與控制序列。"""
    if not _IS_WINDOWS:
        return True
    if os.environ.get("WT_SESSION") or os.environ.get("ConEmuANSI") or os.environ.get("TERM_PROGRAM") == "vscode":
        return True
    try:
        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_uint32()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        return bool(mode.value & 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
    except Exception:  # pragma: no cover - 非預期環境一律當成不支援
        return False


_color = sys.stdout.isatty() and _supports_ansi()


def enable_color(enabled: bool) -> None:
    """讓 ``--no-color`` 可以覆寫自動判斷的結果。"""
    global _color
    _color = enabled


def color_enabled() -> bool:
    return _color


def _fit(text: str) -> bytes:
    """把文字編成終端機編碼；無法表示的字元換成替代字。"""
    try:
        return text.encode(ENCODING)
    except UnicodeEncodeError:
        out: list[str] = []
        for char in text:
            try:
                char.encode(ENCODING)
                out.append(char)
            except UnicodeEncodeError:
                out.append(FALLBACKS.get(char, "?"))
        return "".join(out).encode(ENCODING, errors="replace")


def _paint(code: str, text: str) -> str:
    return f"{code}{text}{RESET}" if _color else text


def _write(text: str, newline: bool = True) -> None:
    payload = text + ("\n" if newline else "")
    stream = sys.stdout
    if stream is None:  # pragma: no cover - 測試環境取代 stdout 時
        return
    if stream.isatty():
        # 接上終端機時交給 Python 自己去寫：Windows 會用 UTF-16 寫入主控台，
        # 所以 ✓、★ 這些符號不會被主控台字碼頁擋掉（core-spec CORE-OUT-04）。
        try:
            stream.write(payload)
            stream.flush()
            return
        except UnicodeEncodeError:  # pragma: no cover - 少數非 UTF-8 的終端機
            pass
    buffer = getattr(stream, "buffer", None)
    if buffer is None:
        # stdout 被換成沒有 buffer 的物件（例如測試用的 StringIO）時直接寫文字
        try:
            stream.write(payload)
            stream.flush()
        except (OSError, UnicodeError):
            pass
        return
    try:
        buffer.write(_fit(payload))
        buffer.flush()
    except (OSError, UnicodeError):
        # 寫入失敗（例如管道破裂）時不應讓程式崩潰
        pass


# ---------------------------------------------------------------- 對外 API

def print_text(text: str = "") -> None:
    _write(text)


def println() -> None:
    _write("")


def bold(text: str) -> None:
    _write(_paint(BOLD, text))


def dim(text: str) -> None:
    _write(_paint(DIM, text))


def info(text: str) -> None:
    _write(_paint(CYAN, text))


def step(text: str) -> None:
    _write(_paint(BLUE, text))


def success(text: str) -> None:
    _write(_paint(GREEN, text))


def warn(text: str) -> None:
    _write(_paint(YELLOW, text))


def error(text: str) -> None:
    _write(_paint(RED, text))


def green(text: str) -> str:
    """回傳帶綠色的字串（給表格這類需要字串的情境用）。"""
    return _paint(GREEN, text)


def yellow(text: str) -> str:
    return _paint(YELLOW, text)


def raw(text: str) -> None:
    """輸出但不換行、不套用替代字之外的處理（進度列等）。"""
    _write(text, newline=False)


def clear_screen() -> None:
    """清畫面；只在使用互動式終端機時執行，而且失敗不中斷流程。"""
    if not sys.stdout.isatty():
        return
    if _IS_WINDOWS:
        try:
            import subprocess

            subprocess.run(["cmd", "/c", "cls"], check=False)
        except Exception:  # pragma: no cover - 清不掉就算了
            pass
        return
    _write("\x1b[H\x1b[2J\x1b[3J", newline=False)


# ---------------------------------------------------------------- 顯示寬度

def display_width(text: str) -> int:
    """計算顯示寬度：略過 ANSI 色碼，東亞全形字元算兩格。"""
    width = 0
    in_escape = False
    for char in text:
        if in_escape:
            if char == "m":
                in_escape = False
            continue
        if char == "\x1b":
            in_escape = True
            continue
        width += 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
    return width


class Table:
    """極簡等寬表格，用於 ``list`` 指令。"""

    def __init__(self, *headers: str) -> None:
        self.headers = list(headers)
        self.rows: list[list[str]] = []

    def row(self, *cells: str) -> None:
        if len(cells) != len(self.headers):
            raise ValueError(
                f"欄位數不符：需要 {len(self.headers)} 個，收到 {len(cells)} 個"
            )
        self.rows.append(list(cells))

    def render(self) -> list[str]:
        widths = [display_width(header) for header in self.headers]
        for row in self.rows:
            for index, cell in enumerate(row):
                widths[index] = max(widths[index], display_width(cell))

        divider = "+" + "+".join("─" * (width + 2) for width in widths) + "+"
        lines = [divider, self._line(self.headers, widths), divider]
        for row in self.rows:
            lines.append(self._line(row, widths))
        lines.append(divider)
        return lines

    def print(self) -> None:
        for line in self.render():
            print_text(line)

    @staticmethod
    def _line(cells: list[str], widths: list[int]) -> str:
        parts = []
        for cell, width in zip(cells, widths):
            parts.append("| " + cell + " " * max(0, width - display_width(cell)) + " ")
        return "".join(parts) + "|"
