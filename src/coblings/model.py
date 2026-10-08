"""練習的資料模型：載入題目、讀寫進度。"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from . import constants, json_lite

STUDENT_SUFFIX = ".cbl"
CHECKER_SUFFIX = "Test.cbl"
ORIGINAL_DIR = ".original"
ORIGINAL_SUFFIX = ".orig"
METADATA_FILE = "exercise.json"


@dataclass
class Exercise:
    """一個練習。"""

    id: str
    name: str
    directory: str
    source: str
    checker: str
    order: int
    difficulty: str = "★"
    topics: list[str] = field(default_factory=list)
    hint: str = ""

    @property
    def title(self) -> str:
        return f"{self.id} — {self.name}"

    @property
    def source_file_name(self) -> str:
        return os.path.basename(self.source)

    @property
    def checker_file_name(self) -> str:
        return os.path.basename(self.checker)

    @property
    def original_path(self) -> str:
        return os.path.join(self.directory, ORIGINAL_DIR, self.source_file_name + ORIGINAL_SUFFIX)


class ExerciseLoadError(Exception):
    """練習資料夾載入失敗（訊息會直接顯示給使用者）。"""


def classify_files(directory: str) -> tuple[list[str], list[str]]:
    """把題目資料夾裡的直接檔案分成學生可編輯檔與檢查器（副檔名不分大小寫）。

    這是辨識學生檔與檢查器的唯一規則；runner 子行程直接收到兩個路徑，不再自行辨識。
    """
    sources: list[str] = []
    checkers: list[str] = []
    for name in sorted(os.listdir(directory)):
        path = os.path.join(directory, name)
        if not os.path.isfile(path):
            continue
        if not name.upper().endswith(STUDENT_SUFFIX.upper()):
            continue
        if name.upper().endswith(CHECKER_SUFFIX.upper()):
            checkers.append(path)
        else:
            sources.append(path)
    return sources, checkers


def load_exercises(root: str) -> tuple[list[Exercise], list[str]]:
    """載入 ``root`` 底下的所有練習；回傳 (練習, 警告)。"""
    if not os.path.isdir(root):
        raise ExerciseLoadError(f"找不到練習資料夾：{os.path.abspath(root)}")

    result: list[Exercise] = []
    warnings: list[str] = []
    for name in sorted(os.listdir(root)):
        directory = os.path.join(root, name)
        if not os.path.isdir(directory) or name.startswith("."):
            continue
        exercise = _read_exercise(directory, name, warnings)
        if exercise is not None:
            result.append(exercise)
    return result, warnings


def _read_exercise(directory: str, exercise_id: str, warnings: list[str]) -> Exercise | None:
    metadata = os.path.join(directory, METADATA_FILE)
    if not os.path.isfile(metadata):
        return None

    sources, checkers = classify_files(directory)
    if not sources or not checkers:
        return None
    if len(sources) > 1 or len(checkers) > 1:
        warnings.append(
            f"略過 {exercise_id}：每題只能有一個待修的 {STUDENT_SUFFIX} 和一個 *{CHECKER_SUFFIX}，"
            f"目前有 {len(sources)} 個待修檔、{len(checkers)} 個測試檔。"
        )
        return None

    try:
        with open(metadata, "r", encoding="utf-8") as handle:
            raw = handle.read()
    except (OSError, UnicodeDecodeError) as error:
        raise ExerciseLoadError(f"{exercise_id}/{METADATA_FILE} 無法讀取：{error}") from None
    try:
        data = json_lite.parse_object(raw)
    except json_lite.JsonError as error:
        raise ExerciseLoadError(f"{exercise_id}/{METADATA_FILE} 格式錯誤：{error}") from None

    raw_topics = data.get("topics", [])
    if isinstance(raw_topics, list):
        topics = [json_lite.to_text(item) for item in raw_topics]
    else:
        topics = [json_lite.to_text(raw_topics)]

    return Exercise(
        id=exercise_id,
        name=json_lite.to_text(data.get("name", exercise_id)),
        directory=directory,
        source=sources[0],
        checker=checkers[0],
        order=_order_of(exercise_id),
        difficulty=json_lite.to_text(data.get("difficulty", "★")),
        topics=topics,
        hint=json_lite.to_text(data.get("hint", "")),
    )


def _order_of(exercise_id: str) -> int:
    """排序值：取練習 id 開頭的連續數字，沒有開頭數字時為 0。"""
    digits = ""
    for char in exercise_id:
        if char.isdigit():
            digits += char
        else:
            break
    return int(digits) if digits else 0


class AppState:
    """學習進度：哪些練習已完成、現在做到哪一題。"""

    def __init__(self, root: str) -> None:
        self.directory = os.path.join(root, constants.STATE_DIR)
        self.file = os.path.join(self.directory, "progress.txt")
        self.done: list[str] = []
        self.current: str = ""

    # ---------------------------------------------------------------- 讀寫

    @classmethod
    def load(cls, root: str, exercises: list[Exercise]) -> "AppState":
        state = cls(root)
        if os.path.isfile(state.file):
            try:
                with open(state.file, "r", encoding="utf-8") as handle:
                    content = handle.read()
            except UnicodeDecodeError as error:
                raise OSError(f"進度檔不是有效的 UTF-8：{error}") from None
            for line in content.splitlines():
                trimmed = line.strip()
                if trimmed.startswith("current:"):
                    state.current = trimmed[len("current:") :].strip()
                elif trimmed.startswith("done:"):
                    item = trimmed[len("done:") :].strip()
                    if item not in state.done:
                        state.done.append(item)

        valid = {exercise.id for exercise in exercises}
        # 題目被刪除或改名後，舊 id 不再計入完成數
        state.done = [item for item in state.done if item in valid]

        if not state.current or state.current not in valid:
            state.current = next(
                (exercise.id for exercise in exercises if exercise.id not in state.done),
                exercises[0].id if exercises else "",
            )
        return state

    def save(self) -> None:
        os.makedirs(self.directory, exist_ok=True)
        lines = [constants.PROGRESS_HEADER, f"current:{self.current}"]
        lines.extend(f"done:{item}" for item in self.done)
        temporary = self.file + ".tmp"
        try:
            with open(temporary, "w", encoding="utf-8", newline="\n") as handle:
                handle.write("\n".join(lines) + "\n")
            os.replace(temporary, self.file)
        except OSError:
            # 清理殘留的臨時檔案，避免下次啟動時混淆
            try:
                os.remove(temporary)
            except OSError:
                pass
            raise

    # ---------------------------------------------------------------- 查詢

    def is_done(self, exercise_id: str) -> bool:
        return exercise_id in self.done

    def mark_done(self, exercise_id: str) -> bool:
        """標記完成；回傳是不是第一次完成。"""
        if exercise_id in self.done:
            return False
        self.done.append(exercise_id)
        return True

    def unmark_done(self, exercise_id: str) -> None:
        if exercise_id in self.done:
            self.done.remove(exercise_id)

    def reset_all(self, exercises: list[Exercise]) -> None:
        self.done.clear()
        for exercise in exercises:
            artifact = os.path.join(exercise.directory, constants.ARTIFACT_DIRNAME)
            if os.path.isdir(artifact):
                shutil.rmtree(artifact, ignore_errors=True)
        self.current = exercises[0].id if exercises else ""


def next_pending(exercises: list[Exercise], state: AppState, done_id: str) -> Exercise | None:
    """從剛通過的那題往後找第一個未完成的練習，找不到再從頭繞回來。"""
    ordered = sorted(exercises, key=lambda item: item.order)
    if not ordered:
        return None
    ids = [item.id for item in ordered]
    if done_id in ids:
        start = ids.index(done_id)
    else:
        return None
    for offset in range(1, len(ordered) + 1):
        candidate = ordered[(start + offset) % len(ordered)]
        if not state.is_done(candidate.id):
            return candidate
    return None


def find_exercise(exercises: list[Exercise], query: str) -> Exercise | None:
    """依 id／前綴／名稱／主題找出練習（CORE-CLI-15）。"""
    if query is None:
        return None
    lowered = query.lower()
    for exercise in exercises:
        if exercise.id.lower() == lowered:
            return exercise
    for exercise in exercises:
        if exercise.id.lower().startswith(lowered):
            return exercise
    for exercise in exercises:
        if lowered in exercise.name.lower():
            return exercise
        if any(lowered in topic.lower() for topic in exercise.topics):
            return exercise
    return None


def is_unmodified(exercise: Exercise) -> bool:
    """學生可編輯檔與原題完全相同（沒有改過）。"""
    original = exercise.original_path
    try:
        if not os.path.isfile(original) or not os.path.isfile(exercise.source):
            return False
        with open(original, "rb") as left, open(exercise.source, "rb") as right:
            return left.read() == right.read()
    except OSError:
        return False
