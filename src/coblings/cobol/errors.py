"""COBOL 直譯器的錯誤類型。

分成兩種，對應 CORE-VER-08 的兩種失敗分類：

* :class:`SyntaxError_`：解析期錯誤 → 建置失敗（COMPILE_ERROR）
* :class:`RuntimeError_`：執行期錯誤 → 內部錯誤或測試失敗
"""

from __future__ import annotations


#: 不知道錯誤來自哪個檔案時顯示的名稱
UNKNOWN_FILENAME = "exercise"


class CobolError(Exception):
    """COBOL 錯誤基底類別。

    所有子類別都有 ``filename`` 屬性與相同簽名的 :meth:`format`，
    呼叫端不需要分辨錯誤種類就能產生給學生看的訊息。
    """

    #: 顯示給學生時的錯誤種類前綴
    kind = "錯誤"

    def __init__(self, message: str, filename: str = "") -> None:
        super().__init__(message)
        self.message = message
        #: 錯誤所在的原始檔名（解析器與版面建構會補上）
        self.filename = filename

    def format(self, filename: str = "") -> str:
        return self.message


class SyntaxError_(CobolError):
    """語法錯誤：程式無法被解析。"""

    kind = "error"

    def __init__(
        self, message: str, line: int = 0, column: int = 0, filename: str = ""
    ) -> None:
        super().__init__(message, filename)
        self.line = line
        self.column = column

    def format(self, filename: str = "") -> str:
        """比照 GnuCOBOL 的診斷格式：``檔名:行:欄: error: 訊息``。

        沒有傳入 ``filename`` 時使用錯誤本身記錄的檔名。
        """
        filename = filename or self.filename or UNKNOWN_FILENAME
        if self.line > 0:
            text = f"{filename}:{self.line}"
            if self.column > 0:
                text += f":{self.column}"
            return f"{text}: error: {self.message}"
        return f"{filename}: error: {self.message}"


class RuntimeError_(CobolError):
    """執行期錯誤：由 COBOL 程式在執行中引發。

    對應 COBOL 的「程式檢查錯誤」，例如 SUBSCRIPT OUT OF RANGE、DIVIDE BY ZERO、
    以及斷言內建引發的斷言失敗。
    """

    kind = "runtime"

    def __init__(self, message: str, statement: str = "") -> None:
        super().__init__(message)
        self.statement = statement

    def format(self, filename: str = "") -> str:
        if self.statement:
            return f"{self.statement}: {self.message}"
        return self.message


class AssertionFailure(RuntimeError_):
    """斷言失敗（檢查器的斷言內建丟出）。"""

    def format(self, filename: str = "") -> str:
        return self.message


class StopRun(Exception):
    """STOP RUN：正常結束程式。"""

    def __init__(self, return_code: int = 0) -> None:
        super().__init__("STOP RUN")
        self.return_code = return_code