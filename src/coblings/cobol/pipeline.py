"""從原始檔到可執行程式的共用流程：解析 → 連接 → 資料版面。

``verify``（解析階段）與 ``runner``（子行程）都走這裡，確保兩邊用同一套規則、
報同樣格式的錯誤。
"""

from __future__ import annotations

import os

from .errors import RuntimeError_, SyntaxError_
from .layout import Layout, build_layout
from .nodes import Node, Program
from .parser import parse_source

#: 檢查器專用的斷言內建名稱前綴；學生程式不能呼叫
CHECKER_BUILTIN_PREFIX = "COBLINGS-"

#: 學生程式裡會被換成 CONTINUE 的結束敘述
_STOP_KINDS = ("stop_run", "goback", "exit_program")


def read_source(path: str) -> str:
    with open(path, "r", encoding="utf-8-sig") as handle:
        return handle.read()


def load_program(student_path: str, checker_path: str) -> tuple[Program, Layout]:
    """讀入、解析並連接學生檔與檢查器，回傳 (程式, 資料版面)。

    會丟出 :class:`SyntaxError_`、:class:`RuntimeError_`（連接錯誤）、
    ``OSError`` 或 ``UnicodeDecodeError``。
    """
    student = parse_source(read_source(student_path), os.path.basename(student_path))
    checker = parse_source(read_source(checker_path), os.path.basename(checker_path))
    program = link_programs(student, checker)
    return program, build_layout(program)


def describe_error(error: BaseException) -> str:
    """把解析／連接期的例外轉成給學生看的一行訊息。"""
    if isinstance(error, (SyntaxError_, RuntimeError_)):
        return error.format()
    if isinstance(error, (OSError, UnicodeDecodeError)):
        return f"讀不到題目檔案：{error}"
    return f"直譯器內部錯誤（{type(error).__name__}）：{error}"


# ------------------------------------------------------------------ 連接

def link_programs(student: Program, checker: Program) -> Program:
    """把學生程式接到檢查器後面，成為一支程式。

    * DATA DIVISION：檢查器的區段在前，學生的 WORKING-STORAGE 接在後面
    * PROCEDURE DIVISION：檢查器的段落在前（第一個段落就是進入點），
      學生的段落接在後面；檢查器用 ``PERFORM`` 呼叫學生寫的段落。
    * 學生程式裡的 ``STOP RUN`` / ``GOBACK`` 會被拿掉，因為程式的結束
      應該由檢查器決定。
    * 學生程式不能呼叫 ``CALL "COBLINGS-…"``：斷言與 ``COBLINGS-DONE``
      是檢查器專用的，否則學生可以自己宣告通過。

    兩支輸入程式都不會被修改。
    """
    sections = list(checker.sections)
    seen = {section for section, _ in sections}
    for section, items in student.sections:
        key = section.upper()
        if key == "WORKING-STORAGE":
            merged = list(next((items2 for name, items2 in sections if name.upper() == key), []))
            # 只比「學生 vs 檢查器」：學生檔自己內部重名是歷史行為（版面以先宣告者為準），
            # 這裡不擋，以免既有題目過不了
            checker_names = {name for spec in merged for name in _spec_names(spec)}
            for item in items:
                for name in _spec_names(item):
                    if name in checker_names:
                        raise RuntimeError_(
                            f"學生程式與檢查器都有名為 {name} 的資料項目，請改成不同名稱"
                        )
                merged.append(item)
            for index, (name, _existing) in enumerate(sections):
                if name.upper() == key:
                    sections[index] = (name, merged)
                    break
            else:
                sections.append((key, merged))
            continue
        if key in seen:
            continue
        seen.add(key)
        sections.append((section, items))

    paragraphs = list(checker.paragraphs)
    checker_para_names = {(p.name or "").upper() for p in checker.paragraphs if p.name}
    for paragraph in student.paragraphs:
        para_name = (paragraph.name or "").upper()
        if para_name and para_name in checker_para_names:
            raise RuntimeError_(f"學生程式與檢查器都有段落 {paragraph.name}，請改成不同名稱")
        _reject_checker_builtins(paragraph, student.get("filename") or "")
        statements = [_strip_stop(node) for node in paragraph.statements]
        paragraphs.append(
            type(paragraph)(
                "paragraph", line=paragraph.line, name=paragraph.name,
                statements=statements, section_name=paragraph.section_name
            )
        )

    return Program(
        "program",
        program_id=checker.program_id or student.program_id,
        special_names=list(checker.special_names),
        selects=list(checker.selects) + list(student.selects),
        files={**student.files, **checker.files},
        sections=sections,
        paragraphs=paragraphs,
        declaratives=list(checker.declaratives),
        using_params=list(checker.using_params),
    )


def _reject_checker_builtins(paragraph: Node, filename: str) -> None:
    for node in paragraph.walk():
        if node.kind != "call":
            continue
        name = node.get("name")
        if isinstance(name, str) and name.upper().startswith(CHECKER_BUILTIN_PREFIX):
            raise SyntaxError_(
                f'CALL "{name}" 是檢查器專用的，學生程式不能呼叫',
                line=node.line,
                column=node.column,
                filename=filename,
            )


def _spec_names(spec) -> list[str]:
    """一個資料描述項（含子項、條件名稱）的所有名稱。"""
    names: list[str] = []
    if getattr(spec, "name", None):
        names.append(spec.name)
    for condition in getattr(spec, "conditions", []):
        if getattr(condition, "name", None):
            names.append(condition.name)
    for child in getattr(spec, "children", []):
        names.extend(_spec_names(child))
    return names


def _strip_stop(node: Node) -> Node:
    """拿掉學生程式裡的 STOP RUN／GOBACK／EXIT PROGRAM，包含寫在 IF 裡面的。

    程式什麼時候結束應該由檢查器決定；只清掉最外層會讓巢狀的結束敘述把測試提前結束。
    回傳新的節點樹，原本的 AST 不變。
    """
    if node.kind in _STOP_KINDS:
        # 保留句子編號，NEXT SENTENCE 才能正確跳轉
        return Node("continue", node.line, node.column, sentence=node.get("sentence", 0))
    return node.map_children(_strip_stop)
