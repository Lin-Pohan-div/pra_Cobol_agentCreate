"""Coblings 的指令列介面（core-spec 第 1 章）。"""

from __future__ import annotations

import os
import shutil
import sys
import time

from dataclasses import dataclass
from typing import Callable

from . import console, constants, verify
from .model import (
    AppState,
    Exercise,
    ExerciseLoadError,
    find_exercise,
    is_unmodified,
    load_exercises,
    next_pending,
)

DIVIDER = "─" * 40


class CommandError(Exception):
    """指令無法執行：訊息直接顯示給使用者，結束碼為 1。"""


@dataclass
class Session:
    """一次 CLI 執行需要的狀態。"""

    root: str
    exercises: list[Exercise]
    state: AppState


@dataclass
class Options:
    """解析後的指令列。"""

    command: str = "welcome"
    args: list[str] | None = None
    directory: str | None = None
    color: bool = True


#: 指令別名 → 正式名稱
ALIASES = {
    "--help": "help", "-h": "help",
    "--version": "version", "-v": "version",
    "ls": "list", "r": "run", "v": "verify", "h": "hint",
}


def parse_options(argv: list[str]) -> Options:
    """拆出全域選項（可以寫在任何位置）與指令。"""
    args = list(argv)
    options = Options()
    if "--no-color" in args:
        args.remove("--no-color")
        options.color = False
    if "--dir" in args:
        index = args.index("--dir")
        if index + 1 >= len(args):
            raise CommandError("--dir 後面要接練習目錄的路徑。")
        options.directory = args[index + 1]
        del args[index : index + 2]
    if args:
        command = args.pop(0).lower()
        options.command = ALIASES.get(command, command)
    options.args = args
    return options


def main(argv: list[str] | None = None) -> int:
    try:
        options = parse_options(sys.argv[1:] if argv is None else argv)
    except CommandError as failure:
        console.error(str(failure))
        return 1
    if not options.color:
        console.enable_color(False)

    # 不需要練習目錄的指令：在專案外面也能執行
    if options.command == "help":
        usage()
        return 0
    if options.command == "version":
        console.print_text(f"{constants.NAME} {constants.VERSION}")
        return 0

    handler = COMMANDS.get(options.command)
    if handler is None:
        console.error(f"未知指令：{options.command}")
        console.println()
        usage()
        return 1

    try:
        session = open_session(options.directory)
        return handler(session, options.args or [])
    except CommandError as failure:
        console.error(str(failure))
        return 1
    except OSError as failure:
        console.error(f"進度檔寫入失敗：{failure}")
        return 1


def open_session(directory: str | None) -> Session:
    """找出練習目錄、載入題目與進度。"""
    if directory is not None:
        exercises_dir = os.path.abspath(directory)
        root = os.path.dirname(exercises_dir)
    else:
        root = locate_root()
        if root is None:
            raise CommandError("找不到練習目錄。請在專案根目錄執行，或用 --dir 指定路徑。")
        exercises_dir = os.path.join(root, constants.EXERCISES_DIRNAME)

    try:
        exercises, warnings = load_exercises(exercises_dir)
    except ExerciseLoadError as failure:
        raise CommandError(str(failure)) from None
    for warning in warnings:
        console.warn(warning)
    if not exercises:
        raise CommandError(f"沒有找到任何練習：{os.path.abspath(exercises_dir)}")

    try:
        state = AppState.load(root, exercises)
    except OSError as failure:
        raise CommandError(f"無法讀取進度檔：{failure}") from None
    return Session(root, exercises, state)


# ================================================================ 指令

def welcome(exercises: list[Exercise], state: AppState) -> int:
    current = find_exercise(exercises, state.current) or exercises[0]
    console.bold(f"{constants.NAME} {constants.VERSION}")
    console.dim("透過修正有問題的 COBOL 程式來學習 COBOL。")
    console.println()
    console.step(f"目前進度: {progress_text(state, exercises)}")
    console.println()
    console.step(f"目前練習: {current.title}")
    console.dim("  檔案: " + os.path.abspath(current.source))
    console.dim("  指令: run 開始監看（存檔自動檢查）/ hint 看提示 / list 看全部")
    console.println()
    console.dim(
        f"第一次玩？執行 {constants.LAUNCHER} guide ／ 全部指令：{constants.LAUNCHER} help"
    )
    return 0


def usage() -> None:
    console.bold(f"用法: {constants.LAUNCHER} [指令] [練習 id]")
    console.println()
    console.step("  run [id]          監看練習檔，存檔就自動檢查，通過後跟到下一題")
    console.step("  verify [id]       只檢查一次並回傳 exit code（適合 CI）")
    console.step("  list              列出所有練習與進度")
    console.step("  hint [id]         顯示提示")
    console.step("  reset [id]        將練習標記為未完成，並把原始碼還原成原題")
    console.step("  reset --all       清除所有進度（不還原原始碼）")
    console.step("  guide             新手教學：怎麼玩、卡住怎麼辦")
    console.step("  help              顯示本說明")
    console.step("  version           顯示版本")
    console.println()
    console.dim("選項: --no-color 關閉色彩、--dir <路徑> 指定練習目錄")


def guide(exercises: list[Exercise], state: AppState) -> int:
    current = find_exercise(exercises, state.current) or exercises[0]
    launcher = constants.LAUNCHER

    console.bold(f"{constants.NAME} 新手教學")
    console.println()
    console.step("怎麼玩")
    console.print_text("  每一題都是一個故意寫壞的 COBOL 程式，把它改到能執行、而且通過測試。")
    console.print_text("  打開檔案修改 → 存檔 → 自動解析並測試 → 通過後跳到下一題。")
    console.println()
    console.step("你現在要改")
    console.print_text("  " + os.path.abspath(current.source))
    console.dim(f"  不要改 {current.checker_file_name}：那是寫好的驗收測試。")
    console.println()
    console.step("用 run 監看")
    console.print_text(f"  {launcher} run 會一直盯著目前這題：")
    console.print_text("  - 每次存檔就清空畫面，顯示最新的檢查結果")
    console.print_text("  - 通過後自動跳到下一題，全部完成時自動結束")
    console.print_text(
        f"  - 測試超過 {constants.TEST_TIMEOUT_SECONDS} 秒沒跑完會判定逾時，通常是無窮迴圈"
    )
    console.print_text("  - 想離開按 Ctrl+C")
    console.print_text(f"  指定題目：{launcher} run 15_recursion（可用 id、名稱或主題關鍵字）")
    console.println()
    console.step("卡住了怎麼辦")
    console.print_text("  1. 仔細看錯誤訊息裡的檔名與行號")
    console.print_text(f"  2. 執行 {launcher} hint 看這題的提示")
    console.print_text("  3. 真的不會，再去看 solutions/ 裡的參考解答")
    console.println()
    console.step("常見問題")
    console.print_text("  沒有顏色？傳統主控台不支援色碼，改用 Windows Terminal 就有。")
    console.print_text(
        f"  進度存在哪？{constants.STATE_DIR}/progress.txt，刪掉就重新開始。"
    )
    console.print_text(
        f"  改壞了想重來？{launcher} reset <id> 會還原成原題，"
        f"舊檔備份在 {constants.STATE_DIR}/backup/。"
    )
    console.print_text("  reset --all 只清除進度，不會還原任何原始碼。")
    console.println()
    console.dim(f"完整指令請執行：{launcher} help")
    return 0


def list_exercises(exercises: list[Exercise], state: AppState) -> int:
    table = console.Table("狀態", "練習", "難度", "主題")
    for exercise in exercises:
        if state.is_done(exercise.id):
            status = console.green("✓ 完成")
        elif exercise.id == state.current:
            status = console.yellow("→ 目前")
        else:
            status = "  待做"
        table.row(status, exercise.title, exercise.difficulty, ", ".join(exercise.topics))
    table.print()
    console.println()
    console.dim(f"共 {len(exercises)} 題，已完成 {len(state.done)} 題。")
    return 0


def watch(exercises: list[Exercise], state: AppState, args: list[str]) -> int:
    """監看學生可編輯檔；存檔就重新檢查，通過後跟到下一題。"""
    if not args:
        scan_progress(exercises, state)
    target = require_exercise(exercises, state, args)
    clear_next = True
    try:
        while True:
            if clear_next:
                console.clear_screen()
            seen = last_modified(target.source)
            if check(exercises, state, target, interactive=True):
                if all(state.is_done(exercise.id) for exercise in exercises):
                    return 0
                target = find_exercise(exercises, state.current)
                if target is None:  # pragma: no cover - 理論上不會發生
                    return 0
                console.println()
                console.dim(DIVIDER)
                clear_next = False
                continue
            console.println()
            console.dim("監看中：存檔後會自動重新檢查（Ctrl+C 離開）")
            wait_for_change(target.source, seen)
            clear_next = True
    except KeyboardInterrupt:
        console.println()
        return 130


def verify_once(exercises: list[Exercise], state: AppState, args: list[str]) -> bool:
    return check(exercises, state, require_exercise(exercises, state, args), interactive=False)


def check(
    exercises: list[Exercise], state: AppState, target: Exercise, interactive: bool
) -> bool:
    """檢查一題；通過就推進到下一題。回傳 True 代表這題通過。"""
    state.current = target.id
    state.save()

    if interactive:
        console.step(f"檢查中: {target.title}")
        console.dim("  " + os.path.abspath(target.source))

    try:
        result = verify.verify(target)
    except OSError as failure:
        console.error(f"✗ 無法準備檢查用的產物目錄：{failure}")
        return False

    if result.status == verify.STATUS_PASSED:
        console.success(f"✓ {target.title} 通過！")
        if result.output:
            print_block("輸出", result.output)
        if state.mark_done(target.id):
            console.success(f"  恭喜完成第 {len(state.done)} 題！")
        upcoming = next_pending(exercises, state, target.id)
        if upcoming is not None:
            state.current = upcoming.id
            console.step("  下一題: " + upcoming.title)
            console.dim("  " + os.path.abspath(upcoming.source))
        else:
            console.success("  全部練習都完成了，去寫自己的 COBOL 吧！")
        state.save()
        return True

    if result.status == verify.STATUS_PARSE_ERROR:
        console.error("✗ 解析失敗，程式還不能執行。")
        print_block("解析錯誤", "\n".join(result.errors))
        console.dim("提示：閱讀錯誤訊息中的檔名與行號。")
        return False

    if result.status == verify.STATUS_TEST_FAILED:
        console.error("✗ 可以解析，但測試沒通過。")
        if not result.output:
            console.dim(result.message)
        else:
            print_block("測試輸出", result.output)
        console.dim(
            f"提示：測試已經寫好了，去調整 {target.source_file_name} 讓輸出符合預期。"
        )
        return False

    console.error(f"✗ {result.message}")
    if result.output:
        print_block("輸出", result.output)
    return False


def hint(exercises: list[Exercise], state: AppState, args: list[str]) -> int:
    target = require_exercise(exercises, state, args)
    console.step("提示 — " + target.title)
    if not target.hint.strip():
        console.dim("（這題沒有額外提示）")
        return 0
    console.println()
    for line in target.hint.splitlines():
        console.print_text("  " + line)
    console.println()
    console.dim(f"卡住了就執行 {constants.LAUNCHER} reset {target.id} 拿回原始碼。")
    return 0


def reset(root: str, exercises: list[Exercise], state: AppState, args: list[str]) -> int:
    if args and args[0] in ("--all", "-a"):
        cleared = len(state.done)
        state.reset_all(exercises)
        state.save()
        console.success(f"已清除 {cleared} 題的進度，回到起點。")
        console.dim(
            f"原始碼沒有被還原；要還原某一題請執行 {constants.LAUNCHER} reset <id>。"
        )
        return 0

    target = require_exercise(exercises, state, args)
    state.unmark_done(target.id)
    state.current = target.id
    state.save()
    console.success(f"已將 {target.title} 標記為未完成。")
    try:
        restore_source(root, target)
    except OSError as failure:
        console.error(f"還原原始碼失敗：{failure}")
        return 1
    return 0


def restore_source(root: str, target: Exercise) -> None:
    """用 ``.original/`` 裡的原題覆蓋學生檔；覆蓋前先備份。"""
    file_name = target.source_file_name
    original = target.original_path
    if not os.path.isfile(original):
        console.warn(f"找不到原題 {original}，原始碼沒有還原。")
        return
    if os.path.isfile(target.source) and _same_file(target.source, original):
        console.dim(f"{file_name} 本來就是原題，不需要還原。")
        return
    if os.path.isfile(target.source):
        backup = os.path.join(root, constants.STATE_DIR, "backup", target.id, file_name)
        os.makedirs(os.path.dirname(backup), exist_ok=True)
        shutil.copy2(target.source, backup)
        console.dim(f"你改過的版本已備份到 {backup}")
    shutil.copy2(original, target.source)
    console.success(f"已將 {file_name} 還原成原題。")


# ================================================================ 進度掃描

def scan_progress(exercises: list[Exercise], state: AppState) -> None:
    """依檔案的實際狀態重建完成集合。"""
    ordered = sorted(exercises, key=lambda item: item.order)
    for index, exercise in enumerate(ordered, start=1):
        console.raw(f"\r掃描進度中… {index}/{len(ordered)} {exercise.id}  ")
        if is_unmodified(exercise):
            state.unmark_done(exercise.id)
            continue
        try:
            result = verify.verify(exercise, timeout=constants.TEST_TIMEOUT_SECONDS)
        except OSError:
            result = None
        if result is not None and result.passed:
            state.mark_done(exercise.id)
        else:
            state.unmark_done(exercise.id)
    console.raw("\r" + " " * 50 + "\r")

    for exercise in ordered:
        if not state.is_done(exercise.id):
            state.current = exercise.id
            break
    state.save()


# ================================================================ 輔助

def locate_root() -> str | None:
    """從目前工作目錄往上找含有 exercises/ 的資料夾。"""
    current = os.path.abspath(os.getcwd())
    path = current
    while True:
        if os.path.isdir(os.path.join(path, constants.EXERCISES_DIRNAME)):
            return path
        parent = os.path.dirname(path)
        if parent == path:
            return None
        path = parent


def resolve(exercises: list[Exercise], state: AppState, args: list[str]) -> Exercise | None:
    if not args:
        return find_exercise(exercises, state.current) or exercises[0]
    return find_exercise(exercises, args[0])


def require_exercise(exercises: list[Exercise], state: AppState, args: list[str]) -> Exercise:
    """同 :func:`resolve`，找不到時丟出 :class:`CommandError`。"""
    target = resolve(exercises, state, args)
    if target is None:
        raise CommandError("找不到練習：" + format_args(args))
    return target


def format_args(args: list[str]) -> str:
    """把參數列顯示成 ``[a, b]`` 的樣子。"""
    return "[" + ", ".join(args) + "]"


def wait_for_change(path: str, seen: float | None) -> None:
    """每秒輪詢一次修改時間，直到檔案真的變了。"""
    while True:
        time.sleep(constants.WATCH_POLL_SECONDS)
        now = last_modified(path)
        # 編輯器存檔時檔案可能短暫消失，等它回來再說
        if now is not None and now != seen:
            return


def last_modified(path: str) -> float | None:
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


def _same_file(left: str, right: str) -> bool:
    try:
        with open(left, "rb") as first, open(right, "rb") as second:
            return first.read() == second.read()
    except OSError:
        return False


def print_block(title: str, body: str) -> None:
    console.println()
    console.bold(title + ":")
    for line in body.replace("\r\n", "\n").split("\n"):
        console.print_text("  " + line)


def progress_text(state: AppState, exercises: list[Exercise]) -> str:
    return f"{len(state.done)}/{len(exercises)} 完成"


# ================================================================ 指令表

#: 需要練習目錄的指令（help／version 在 main() 裡先處理）
COMMANDS: dict[str, Callable[[Session, list[str]], int]] = {
    "welcome": lambda session, args: welcome(session.exercises, session.state),
    "guide": lambda session, args: guide(session.exercises, session.state),
    "list": lambda session, args: list_exercises(session.exercises, session.state),
    "run": lambda session, args: watch(session.exercises, session.state, args),
    "verify": lambda session, args: 0 if verify_once(session.exercises, session.state, args) else 1,
    "hint": lambda session, args: hint(session.exercises, session.state, args),
    "reset": lambda session, args: reset(session.root, session.exercises, session.state, args),
}


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
