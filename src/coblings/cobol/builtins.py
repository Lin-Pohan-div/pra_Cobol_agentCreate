"""斷言函式庫：COBOL 版的 TestKit。

學生寫的程式**不應該**修改檢查器；檢查器用這些內建來斷言學生程式的行為。
對應 core-spec 第 5 章（CORE-KIT-01 ～ CORE-KIT-08）：

* 全部斷言通過後必須呼叫 ``COBLINGS-DONE``，才會輸出通過標記（CORE-KIT-01）
* 任何一個斷言失敗就立刻中止後續敘述，並以非 0 的 exit code 結束（CORE-KIT-02）
* 通過標記是一行固定字串，輸出後立刻 flush（CORE-KIT-03）

用法（寫在檢查器的 PROCEDURE DIVISION 開頭段落）：

.. code-block:: cobol

    COBLINGS-TEST-MAIN.
        PERFORM GET-GREET
        CALL "COBLINGS-EXPECT-EQUALS"
            USING BY CONTENT "greet(\"World\")"
                  BY CONTENT "Hello, World!"
                  BY CONTENT WS-RESULT
        CALL "COBLINGS-DONE"
        GOBACK.
"""

from __future__ import annotations

from decimal import Decimal

from .limits import MAX_RENDERED_ELEMENTS
from .pic import CAT_NUMERIC_EDITED
from .errors import AssertionFailure, RuntimeError_, StopRun

#: COBLINGS-DONE 印出的通過標記。只給人看：通過與否由直譯器狀態（``interp.passed``）決定
PASS_MARKER = "COBLINGS_TESTS_PASSED"

#: COBLINGS-FAIL 印出的失敗標記前綴（顯示時會被清掉）
FAIL_MARKER = "COBLINGS_TESTS_FAILED"

#: 浮點斷言的預設容許誤差
DEFAULT_EPSILON = Decimal("1e-9")


def _render(interp, value, field=None) -> str:
    """把值渲染成好讀的字串；表格項目會展開成 ``[a, b, c]``。"""
    if field is not None and getattr(field, "has_occurs", False):
        # 延遲匯入：interp → datastmt → builtins → interp 會形成循環
        from .interp import Reference

        values = []
        total = field.max_occurs
        for index in range(1, min(total, MAX_RENDERED_ELEMENTS) + 1):
            try:
                values.append(_render_scalar(interp, interp.get_reference(Reference(field, (index,))), field))
            except RuntimeError_:
                break
        if total > MAX_RENDERED_ELEMENTS:
            values.append(f"…（共 {total} 個）")
        return "[" + ", ".join(values) + "]"
    return _render_scalar(interp, value, field)


def _render_scalar(interp, value, field=None) -> str:
    """把值渲染成好讀的字串；表格項目會展開成 ``[a, b, c]``。"""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, Decimal):
        text = format(value, "f")
        if text.endswith(".0"):
            text = text[:-2]
        return text
    if isinstance(value, int):
        return str(value)
    text = str(value)
    if field is not None and field.pic is not None and field.pic.category == CAT_NUMERIC_EDITED:
        return field.pic.to_text(interp.to_decimal(value))
    return text


def _fail(label: str, expected: str, actual: str) -> None:
    raise AssertionFailure(f"{label}\n  期望: {expected}\n  實際: {actual}")


def call_builtin(interp, name: str, args: list[tuple]):
    """處理檢查器裡的 ``CALL "COBLINGS-…"``。"""
    handler = _BUILTINS.get(name)
    if handler is None:
        raise RuntimeError_(f"未知的內建程式：{name}")
    return handler(interp, args)


def _value(args: list[tuple], index: int, default=None):
    if index < len(args):
        return args[index][0]
    return default


def _field(args: list[tuple], index: int):
    if index < len(args):
        return args[index][1]
    return None


# ------------------------------------------------------------------ 完成宣告

def _done(interp, args):
    interp.passed = True
    interp.emit(PASS_MARKER)
    return None


def _fail_builtin(interp, args):
    message = _value(args, 0, "檢查失敗")
    interp.emit(FAIL_MARKER)
    raise AssertionFailure(str(message))


# ------------------------------------------------------------------ 斷言

def _expect_equals(interp, args):
    label = str(_value(args, 0, "結果"))
    expected = _value(args, 1)
    actual = _value(args, 2)
    interp.checks += 1
    # 用 COBOL 自己的比較規則：文字欄位會先補空白到一樣長再比
    if not interp.compare(expected, actual, "="):
        _fail(label, _render(interp, expected, _field(args, 1)), _render(interp, actual, _field(args, 2)))
    return None


def _expect_true(interp, args):
    label = str(_value(args, 0, "結果"))
    value = _value(args, 1)
    interp.checks += 1
    if not interp.to_bool(value):
        _fail(label, "true", _render(interp, value, _field(args, 1)))
    return None


def _expect_false(interp, args):
    label = str(_value(args, 0, "結果"))
    value = _value(args, 1)
    interp.checks += 1
    if interp.to_bool(value):
        _fail(label, "false", _render(interp, value, _field(args, 1)))
    return None


def _expect_close(interp, args):
    label = str(_value(args, 0, "結果"))
    expected = interp.to_decimal(_value(args, 1, 0))
    actual = interp.to_decimal(_value(args, 2, 0))
    epsilon = interp.to_decimal(_value(args, 3, DEFAULT_EPSILON))
    interp.checks += 1
    if abs(expected - actual) > epsilon:
        _fail(label, _render(interp, expected), _render(interp, actual))
    return None


def _expect_present(interp, args):
    """斷言值不是全空白（COBOL 版的「非 null」）。"""
    label = str(_value(args, 0, "結果"))
    value = _value(args, 1, "")
    interp.checks += 1
    text = interp._raw_text(value).strip()
    if text == "":
        _fail(label, "非空白內容", "（全空白）")
    return None


def _expect_error(interp, args):
    """斷言執行某個段落會引發執行期錯誤。

    用法：``CALL "COBLINGS-EXPECT-ERROR" USING BY CONTENT 標籤 BY CONTENT 段落名稱``
    第三個引數可省略；給的話會再檢查錯誤訊息是否包含該文字：

    ``CALL "COBLINGS-EXPECT-ERROR" USING BY CONTENT 標籤 BY CONTENT 段落名稱
        BY CONTENT "SUBSCRIPT"``
    """
    label = str(_value(args, 0, "結果"))
    paragraph = str(_value(args, 1, "")).strip().upper()
    expected_text = _value(args, 2)
    interp.checks += 1
    if not paragraph:
        _fail(label, "有效的段落名稱", "（空白）")
    if paragraph not in interp.para_index:
        _fail(label, f"段落 {paragraph}", "（找不到這個段落）")
    error: RuntimeError_ | None = None
    try:
        interp.perform_paragraph(paragraph)
    except RuntimeError_ as failure:
        error = failure
    except StopRun:
        # 段落正常結束（例如裡面有 EXIT PROGRAM）：代表沒有發生錯誤
        pass
    if error is None:
        _fail(label, f"{paragraph} 引發執行期錯誤", "（沒有發生錯誤）")
    if expected_text is not None:
        wanted = str(expected_text).strip()
        if wanted and wanted not in error.format():
            _fail(label, f"錯誤訊息包含 \"{wanted}\"", error.format())
    return None


def _expect_no_error(interp, args):
    label = str(_value(args, 0, "結果"))
    paragraph = str(_value(args, 1, "")).strip().upper()
    interp.checks += 1
    if paragraph not in interp.para_index:
        _fail(label, f"段落 {paragraph}", "（找不到這個段落）")
    try:
        interp.perform_paragraph(paragraph)
    except RuntimeError_ as error:
        _fail(label, "沒有執行期錯誤", error.format())
    except StopRun:
        pass
    return None


def _expect_length(interp, args):
    label = str(_value(args, 0, "結果"))
    expected = interp.to_int(_value(args, 1, 0))
    actual = interp.to_int(_value(args, 2, 0))
    interp.checks += 1
    if expected != actual:
        _fail(label, str(expected), str(actual))
    return None


_BUILTINS = {
    "COBLINGS-DONE": _done,
    "COBLINGS-FAIL": _fail_builtin,
    "COBLINGS-ASSERT": lambda interp, args: (
        None
        if interp.to_bool(_value(args, 0))
        else _fail(str(_value(args, 1, "斷言")), "true", "false")
    ),
    "COBLINGS-EXPECT-EQUALS": _expect_equals,
    "COBLINGS-EXPECT-TRUE": _expect_true,
    "COBLINGS-EXPECT-FALSE": _expect_false,
    "COBLINGS-EXPECT-CLOSE": _expect_close,
    "COBLINGS-EXPECT-PRESENT": _expect_present,
    "COBLINGS-EXPECT-ERROR": _expect_error,
    "COBLINGS-EXPECT-NO-ERROR": _expect_no_error,
    "COBLINGS-EXPECT-LENGTH": _expect_length,
}