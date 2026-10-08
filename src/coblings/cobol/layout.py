"""資料版面：把 :class:`DataDescription` 樹轉成可存取的欄位物件。

負責處理層級編號、OCCURS（含 DEPENDING ON）、REDEFINES、66 RENAMES、88 條件名稱，
以及各欄位在群組中的大小與偏移。
"""

from __future__ import annotations

from decimal import Decimal

from . import limits
from .errors import SyntaxError_
from .nodes import DataDescription
from .pic import CAT_ALPHANUMERIC, Pic

#: 儲存初值的容器類型
VALUE_ALNUM = "alnum"
VALUE_NUM = "num"
VALUE_INDEX = "index"


class Field:
    """一個資料項目（可能是群組，可能是基本項目）。"""

    __slots__ = (
        "name", "level", "pic", "usage", "parent", "children", "size",
        "occurs_min", "occurs_max", "depends_on", "redefines", "sign_separate",
        "sign_leading", "justified", "blank_when_zero", "value_spec", "conditions",
        "synonyms", "index", "container", "is_group", "section", "indexed_by",
    )

    def __init__(self, name, level, section=""):
        self.name = name
        self.level = level
        self.section = section
        self.pic: Pic | None = None
        self.usage = "DISPLAY"
        self.parent: Field | None = None
        self.children: list[Field] = []
        self.size = 0
        self.occurs_min = 1
        self.occurs_max: int | None = None
        self.depends_on: str | None = None
        self.redefines: Field | None = None
        self.sign_separate = False
        self.sign_leading = False
        self.justified = False
        self.blank_when_zero = False
        self.value_spec = None
        self.conditions: list = []
        self.synonyms: list = []
        #: 在所屬 SECTION 內的定義順序（用於同層級還原與顯示）
        self.index = 0
        self.container = None
        self.is_group = False
        #: OCCURS … INDEXED BY 宣告的索引名稱
        self.indexed_by: list[str] = []

    # ---------------------------------------------------------------- 查詢

    @property
    def has_occurs(self) -> bool:
        return self.occurs_max is not None

    @property
    def max_occurs(self) -> int:
        return self.occurs_max if self.occurs_max is not None else self.occurs_min

    @property
    def qualified_name(self) -> str:
        names: list[str] = []
        node: Field | None = self
        while node is not None and node.name:
            names.append(node.name)
            node = node.parent
        return ".".join(reversed(names))

    def walk(self):
        """遞迴走訪所有欄位（含群組與基本項目）。"""
        yield self
        for child in self.children:
            yield from child.walk()

    def elementary(self) -> bool:
        return self.pic is not None

    def __repr__(self) -> str:  # pragma: no cover - 除錯用
        return f"Field({self.qualified_name}, size={self.size}, pic={self.pic.text if self.pic else None})"


class Storage:
    """所有欄位初值的儲存區：以 ``(欄位識別碼, 發生次數路徑)`` 為索引。"""

    def __init__(self) -> None:
        self.cells: dict[tuple[int, tuple], object] = {}

    def get(self, field: Field, path: tuple = ()):
        return self.cells.get((id(field), path))

    def set(self, field: Field, path: tuple, value) -> None:
        self.cells[(id(field), path)] = value

    def default_for(self, field: Field) -> object:
        """欄位未賦值時的預設內容。

        COBOL 的資料項目在沒有賦值前，內容是「低值」（本系統以空白表示）。
        """
        if field.usage == "INDEX":
            return 1
        if field.pic is not None and field.pic.category != CAT_ALPHANUMERIC:
            return Decimal(0)
        length = field.pic.char_count if field.pic is not None else 1
        return " " * length


class Layout:
    """整支程式的資料版面。"""

    def __init__(self) -> None:
        self.sections: dict[str, list[Field]] = {}
        self.by_name: dict[str, Field] = {}
        self.records: dict[str, list[Field]] = {}
        #: 66 RENAMES：別名 → 依序要讀寫的欄位清單
        self.aliases: dict[str, list[Field]] = {}
        #: 檔案控制：檔名 → SELECT 敘述
        self.selects: dict[str, dict] = {}
        #: FD 名稱 → 記錄項
        self.fd_of_file: dict[str, str] = {}
        #: REDEFINES：id(共用同一塊位置的項目) → 這一組的所有項目（第一個是原本的項目）
        self.overlays: dict[int, list[Field]] = {}
        self.storage = Storage()

    # ---------------------------------------------------------------- 查詢

    def fields_of(self, section: str) -> list[Field]:
        return self.sections.get(section.upper(), [])

    def lookup(self, name: str) -> Field | None:
        """依名稱（含 ``OF`` 限定）找出欄位。"""
        key = name.upper().strip()
        if key in self.by_name:
            return self.by_name[key]
        if " OF " in key:
            # A OF B：先找 B（B 可能是群組），再在其子項中找 A
            simple, qualifier = key.split(" OF ", 1)
            holder = self.lookup(qualifier)
            if holder is not None:
                for child in holder.walk():
                    if child.name == simple:
                        return child
        # 群組的子項以「群組.子項」註冊，這裡再試一次
        if "." in key:
            head, tail = key.split(".", 1)
            holder = self.lookup(head)
            if holder is not None:
                for child in holder.walk():
                    if child.name == tail:
                        return child
        return None

    def register(self, field: Field) -> None:
        if field.name:
            if field.name not in self.by_name:
                self.by_name[field.name] = field


def _build_field(spec: DataDescription, layout: Layout, section: str) -> Field:
    """把一個資料描述項（含子項）建成 :class:`Field`。"""
    field = Field(spec.name, spec.level, section)
    field.sign_separate = spec.sign_separate
    field.sign_leading = getattr(spec, "sign_leading", False)
    field.justified = spec.justified
    field.blank_when_zero = spec.blank_when_zero
    field.value_spec = spec.value
    field.depends_on = spec.depends_on
    field.conditions = spec.conditions
    field.synonyms = spec.synonyms
    field.indexed_by = list(spec.get("indexed_by") or [])
    # 先記下名稱，等兄弟項目都建好後再換成 Field（見 _build_field 與 build_layout）
    field.redefines = spec.redefines
    if spec.occurs:
        if spec.occurs["max"] > limits.MAX_OCCURS:
            raise _layout_error(
                f"OCCURS {spec.occurs['max']} TIMES 太大（上限 {limits.MAX_OCCURS}）", spec
            )
        field.occurs_min = spec.occurs["min"]
        field.occurs_max = spec.occurs["max"]

    if spec.level == 77:
        field.is_group = False
        _build_elementary(field, spec)
        return field

    if not spec.children:
        _build_elementary(field, spec)
        return field

    field.is_group = True
    for child_spec in spec.children:
        child = _build_field(child_spec, layout, section)
        child.parent = field
        child.index = len(field.children)
        field.children.append(child)
        if child.redefines is not None:
            target = _find_child(field, child.redefines)
            if target is None or target is child:
                raise _layout_error(
                    f"{child.name} REDEFINES {child.redefines}：同一個群組裡找不到 {child.redefines}",
                    child_spec,
                )
            child.redefines = target

    # REDEFINES 的項目和被重新定義的項目共用位置，不另外佔空間
    field.size = sum(_sized(child) for child in field.children if child.redefines is None)
    if field.occurs_max is not None:
        field.size *= field.occurs_max
    return field


def _build_elementary(field: Field, spec: DataDescription) -> None:
    """設定基本欄位的 PICTURE、USAGE 與大小。"""
    usage = (spec.usage or "DISPLAY").upper()
    field.usage = usage
    if usage == "INDEX":
        field.pic = Pic("9(4)")
        field.size = 2
        return
    if spec.picture:
        try:
            field.pic = Pic(spec.picture, usage=usage, sign_separate=spec.sign_separate)
        except SyntaxError_ as exc:
            raise _layout_error(exc.message, spec) from None
        field.size = field.pic.storage_size(usage)
    else:
        # 沒有 PICTURE 的基本項目視為 PIC X(1)，避免版面計算崩潰
        field.pic = Pic("X")
        field.size = 1
    if field.occurs_max is not None:
        field.size *= field.occurs_max


def _layout_error(message: str, spec) -> SyntaxError_:
    """建立帶有檔名與行號的版面錯誤（在解析階段就報給學生）。"""
    return SyntaxError_(
        message,
        line=getattr(spec, "line", 0),
        column=getattr(spec, "column", 0),
        filename=getattr(spec, "filename", ""),
    )


def _find_child(parent: Field, name: str) -> Field | None:
    for child in parent.children:
        if child.name == name.upper():
            return child
        if child.is_group:
            found = _find_child(child, name.upper())
            if found is not None:
                return found
    return None


def _sized(field: Field) -> int:
    return field.size


def build_layout(program) -> Layout:
    """依 PROGRAM 建立資料版面。"""
    layout = Layout()
    for section_name, items in program.sections:
        key = section_name.upper()
        top: list[Field] = []
        for spec in items:
            if spec.name and _top_level_exists(top, spec.name):
                raise _layout_error(
                    f"{spec.name} 重複定義：同一個 {key} SECTION 裡的 01／77 名稱必須唯一", spec
                )
            field = _build_field(spec, layout, key)
            field.container = key
            if isinstance(field.redefines, str):
                # 01 層級的 REDEFINES：對象是前面宣告過的另一個 01
                target = next((item for item in top if item.name == field.redefines.upper()), None)
                if target is None:
                    raise _layout_error(
                        f"{spec.name} REDEFINES {field.redefines}：前面找不到 {field.redefines}", spec
                    )
                field.redefines = target
            top.append(field)
        layout.sections.setdefault(key, []).extend(top)
        for field in top:
            _register_tree(field, layout)
    for fd_name, items in program.files.items():
        record_items: list[Field] = []
        for spec in items:
            field = _build_field(spec, layout, "FILE")
            field.container = "FILE"
            # 同一個 FD 的 01 本來就共用記錄區，REDEFINES 寫不寫都一樣
            field.redefines = None
            record_items.append(field)
            _register_tree(field, layout)
        layout.records[fd_name.upper()] = record_items
        layout.fd_of_file.setdefault(fd_name.upper(), fd_name.upper())
    _check_storage_size(program, layout)
    _register_index_names(layout)
    _register_overlays(layout)
    register_aliases_and_selects(program, layout)
    return layout


def _check_storage_size(program, layout: Layout) -> None:
    """整支程式的資料區不能太大。

    單一 OCCURS 與 PICTURE 已各自有上限，但巢狀 OCCURS 的乘積沒有，
    不擋的話初始化儲存區就可能吃光記憶體。
    """
    tops = [field for fields in layout.sections.values() for field in fields]
    tops += [field for fields in layout.records.values() for field in fields]
    cells = sum(_cell_count(field) for field in tops)
    size = sum(field.size for field in tops)
    if cells > limits.MAX_STORAGE_CELLS or size > limits.MAX_STORAGE_BYTES:
        raise SyntaxError_(
            f"資料區太大：{cells} 個基本項目、{size} 位元組"
            f"（上限 {limits.MAX_STORAGE_CELLS} 個、{limits.MAX_STORAGE_BYTES} 位元組），"
            "請檢查巢狀 OCCURS 的次數",
            filename=program.get("filename") or "",
        )


def _cell_count(field: Field) -> int:
    """這個欄位（含 OCCURS 展開）在儲存區佔幾格。"""
    each = sum(_cell_count(child) for child in field.children) if field.is_group else 1
    return each * (field.max_occurs if field.has_occurs else 1)


def _register_overlays(layout: Layout) -> None:
    """把 REDEFINES 的項目和原本的項目編成同一組，寫入其中一個時要同步其他的。"""
    for fields in layout.sections.values():
        for top in fields:
            for field in top.walk():
                if not isinstance(field.redefines, Field):
                    continue
                root = field.redefines
                while isinstance(root.redefines, Field):
                    root = root.redefines
                group = layout.overlays.setdefault(id(root), [root])
                group.append(field)
                layout.overlays[id(field)] = group


#: INDEXED BY 產生的索引放在這個虛擬 SECTION 裡（初始化時一起設成 1）
INDEX_SECTION = "INDEX-NAMES"


def _register_index_names(layout: Layout) -> None:
    """替 ``OCCURS … INDEXED BY`` 的每個索引名稱建立一個 USAGE INDEX 欄位。"""
    tables = [
        field
        for fields in list(layout.sections.values()) + list(layout.records.values())
        for top in fields
        for field in top.walk()
        if field.indexed_by
    ]
    for table in tables:
        for name in table.indexed_by:
            if name in layout.by_name:
                continue
            index = Field(name, 77, INDEX_SECTION)
            index.usage = "INDEX"
            index.pic = Pic("9(4)")
            index.size = 2
            index.container = INDEX_SECTION
            layout.sections.setdefault(INDEX_SECTION, []).append(index)
            layout.register(index)


def _top_level_exists(top: list[Field], name: str) -> bool:
    return any(f.name == name.upper() for f in top)


def _register_tree(field: Field, layout: Layout) -> None:
    layout.register(field)
    if field.name and field.parent is None and "." not in field.name:
        pass
    for child in field.children:
        qualified = field.name + "." + child.name if field.name else child.name
        if child.name and qualified.upper() not in layout.by_name:
            layout.by_name[qualified.upper()] = child
        _register_tree(child, layout)


def register_aliases_and_selects(program, layout: Layout) -> None:
    """建立 66 RENAMES 別名與 SELECT/FD 的對應表。"""
    for select in getattr(program, "selects", []):
        name = (select.get("name") or "").upper()
        if name:
            layout.selects[name] = select

    # 66 別名：依名稱順序找出要涵蓋的欄位
    sections = layout.sections
    for section_fields in sections.values():
        for field in section_fields:
            _register_aliases(field, layout)


def _register_aliases(field: Field, layout: Layout) -> None:
    for alias in field.synonyms:
        targets: list[Field] = []
        for name in alias.targets:
            found = _find_in(field, name)
            if found is not None:
                targets.append(found)
        if targets:
            layout.aliases[alias.name.upper()] = targets
    for child in field.children:
        _register_aliases(child, layout)


def _find_in(field: Field, name: str) -> Field | None:
    for candidate in field.walk():
        if candidate.name == name.upper():
            return candidate
    return None