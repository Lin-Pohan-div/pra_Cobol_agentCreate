"""直譯器數值層：Fill、Reference、欄位存取與型別轉換。"""
from __future__ import annotations

import re
from decimal import ROUND_DOWN, Decimal, InvalidOperation

from ..errors import RuntimeError_
from ..layout import Field
from ..pic import CAT_ALPHANUMERIC, CAT_NUMERIC, CAT_NUMERIC_EDITED


class Fill:
    """以單一字元填滿欄位的特殊值（ZERO／SPACES／HIGH-VALUES…）。"""

    __slots__ = ("char",)

    def __init__(self, char: str) -> None:
        self.char = char


ZERO_FILL = Fill("0")
SPACE_FILL = Fill(" ")
HIGH_FILL = Fill("\uffff")
LOW_FILL = Fill("\x00")


class GoToSignal(Exception):
    """GO TO 造成的非區域跳轉。"""

    def __init__(self, target: str) -> None:
        super().__init__(target)
        self.target = target


class ExitPerformSignal(Exception):
    """EXIT PERFORM [CYCLE]：結束（或跳到下一輪）目前的內嵌 PERFORM。"""

    def __init__(self, cycle: bool = False) -> None:
        super().__init__("EXIT PERFORM")
        self.cycle = cycle


class ExitParagraphSignal(Exception):
    """EXIT PARAGRAPH：跳到目前段落的結尾。"""


class ExitSectionSignal(Exception):
    """EXIT SECTION：跳到目前 SECTION 的結尾。"""


class NextSentenceSignal(Exception):
    """NEXT SENTENCE：跳到下一個句點之後的敘述。"""


class Reference:
    """一個已解析的資料項目參考。"""

    __slots__ = ("field", "path", "refmod", "span", "name")

    def __init__(self, field: Field, path: tuple, refmod=None, span=None, name: str = "") -> None:
        self.field = field
        self.path = path
        self.refmod = refmod
        self.span = span
        self.name = name

    def __repr__(self) -> str:  # pragma: no cover - 除錯用
        return f"Reference({self.field.qualified_name}{self.path})"


#: 文字轉數值時接受的寫法：正負號、貨幣符號、千分位、小數點、尾端 +／-／CR／DB
_NUMBER_TEXT = re.compile(
    r"([+-])?\s*\$?\s*([0-9]+(?:\.[0-9]*)?|\.[0-9]+)\s*([+-]|CR|DB)?",
    re.IGNORECASE,
)


class ValuesMixin:
    """欄位存取、型別轉換（需要直譯器本體的 mixin）。"""
    def _value_from_spec(self, field: Field, spec):
        if spec.kind == "all_literal":
            pattern = str(spec.pattern)
            length = field.pic.char_count if field.pic else 1
            if field.pic is not None and field.pic.category != CAT_ALPHANUMERIC:
                return field.pic.from_string(pattern * max(1, length))
            return (pattern * length)[:length]
        if spec.kind == "figurative":
            return self._figurative_value(field, spec.value)
        return self.coerce(field, self.eval(spec))

    def _figurative_value(self, field: Field | None, name: str):
        if name in ("ZERO", "ZEROS", "ZEROES"):
            if field is not None and field.pic is not None and field.pic.category == CAT_ALPHANUMERIC:
                return Fill("0")
            return Decimal(0)
        if name in ("SPACE", "SPACES"):
            return SPACE_FILL
        if name == "HIGH-VALUES":
            return HIGH_FILL
        if name == "LOW-VALUES":
            return LOW_FILL
        if name == "QUOTES":
            return Fill('"')
        if name in ("NULL", "NULLS"):
            return SPACE_FILL if field is None else self.coerce(field, "")
        if name == "TRUE":
            return True
        if name == "FALSE":
            return False
        return SPACE_FILL

    def resolve(self, node) -> Reference:
        """把識別字節點解析成 :class:`Reference`。"""
        if node is None or node.kind != "identifier":
            raise RuntimeError_("這裡需要一個資料項目名稱")
        name = node.name.upper()
        field = self.layout.lookup(name)
        if field is None:
            alias = self.layout.aliases.get(name)
            if alias is not None:
                return Reference(alias[0], (), span=alias, name=name)
            raise RuntimeError_(f"找不到資料項目 {node.name}")
        return self.resolve_field(field, node.subscripts, name)

    def resolve_field(self, field: Field, subscripts, name: str = "") -> Reference:
        """依下標（與參考修改）把欄位解析成 :class:`Reference`。"""
        subscripts = list(subscripts or [])
        refmod = None
        plain = []
        for sub in subscripts:
            if isinstance(sub, tuple) and sub and sub[0] == "refmod":
                # 參考修改：X (a : b)，a 已經在 plain 的最後一個
                refmod = (plain.pop() if plain else None, sub[1])
            else:
                plain.append(sub)

        path: tuple = ()
        current = field
        include_self = True
        for sub in plain:
            occ = current if (include_self and current.has_occurs) else None
            if occ is None:
                occ = self._first_occurs(current)
            if occ is None:
                occ = self._ancestor_occurs(current)
            if occ is None:
                raise RuntimeError_(f"{current.qualified_name} 沒有可以使用下標的 OCCURS 項目")
            index = self.to_int(self.eval(sub), "下標")
            limit = self._occurs_max(occ)
            if index < 1 or index > limit:
                raise RuntimeError_(
                    f"SUBSCRIPT OUT OF RANGE：{occ.qualified_name} 的下標 {index} 超出 1 到 {limit}"
                )
            path = path + (index,)
            current = occ
            include_self = False
        if refmod is not None:
            start_node, length_node = refmod
            if start_node is None or length_node is None:
                raise RuntimeError_("參考修改的寫法是 欄位 (起點 : 長度)，兩邊都要寫")
            start = self.to_int(self.eval(start_node), "參考修改起點")
            length = self.to_int(self.eval(length_node), "參考修改長度")
            if start < 1:
                raise RuntimeError_("參考修改的起點必須大於或等於 1")
            if length < 1:
                raise RuntimeError_("參考修改的長度必須大於或等於 1")
            refmod = (start_node, length_node)
        return Reference(field, path, refmod=refmod, name=name)

    def _first_occurs(self, field: Field) -> Field | None:
        for child in field.walk():
            if child.has_occurs:
                return child
        return None

    def _ancestor_occurs(self, field: Field) -> Field | None:
        """往上找帶有 OCCURS 的群組。

        `WS-G-ID (2)` 這種寫法在 COBOL 裡很常見：下標其實是給上層的表格群組用的。
        """
        node = field.parent
        while node is not None:
            if node.has_occurs:
                return node
            node = node.parent
        return None

    def _occurs_max(self, field: Field) -> int:
        if field.depends_on:
            dependency = self.layout.lookup(field.depends_on)
            if dependency is not None:
                try:
                    value = self.get_reference(self.resolve_name_only(dependency))
                    count = self.to_int(value, "OCCURS DEPENDING ON")
                    if count < field.occurs_min:
                        count = field.occurs_min
                    return max(count, 1)
                except RuntimeError_:
                    pass
        return field.max_occurs

    def resolve_name_only(self, field: Field) -> Reference:
        return Reference(field, ())

    def get_reference(self, reference: Reference):
        """讀取參考的值。"""
        if reference.span:
            parts = []
            for field in reference.span:
                parts.append(self._raw_text(self.get_reference(Reference(field, ()))))
            return "".join(parts)
        field = reference.field
        if field.is_group and reference.refmod is None:
            return self.group_text(reference)
        if reference.refmod is not None:
            if field.is_group:
                text = self.group_text(reference)
            else:
                text = self._raw_text(self._raw_get(field, reference.path))
            start = self.to_int(self.eval(reference.refmod[0]), "參考修改起點") - 1
            length = self.to_int(self.eval(reference.refmod[1]), "參考修改長度")
            if start < 0:
                raise RuntimeError_("參考修改的起點小於 1")
            if length < 1:
                raise RuntimeError_("參考修改的長度必須大於或等於 1")
            if start + length > len(text):
                raise RuntimeError_(
                    f"參考修改超出欄位長度：{field.qualified_name} 只有 {len(text)} 個字"
                )
            return text[start : start + length]
        return self._raw_get(field, reference.path)

    def _raw_get(self, field: Field, path: tuple):
        value = self.storage.get(field, path)
        if value is None:
            value = self.storage.default_for(field)
            self.storage.set(field, path, value)
        return value

    def set_reference(self, reference: Reference, value, rounding: bool = False) -> None:
        """把值寫入參考（自動依 PICTURE 做截斷或捨入）。"""
        if reference.span:
            self._write_span(reference.span, value)
            return
        field = reference.field
        if field.is_group and reference.refmod is None:
            self.set_group_text(reference, value)
            return
        if reference.refmod is not None:
            if field.is_group:
                text = list(self.group_text(reference))
            else:
                text = list(self._raw_text(self._raw_get(field, reference.path)))
            start = self.to_int(self.eval(reference.refmod[0]), "參考修改起點") - 1
            length = self.to_int(self.eval(reference.refmod[1]), "參考修改長度")
            if start < 0:
                raise RuntimeError_("參考修改的起點小於 1")
            if length < 1:
                raise RuntimeError_("參考修改的長度必須大於或等於 1")
            if start + length > len(text):
                raise RuntimeError_(
                    f"參考修改超出欄位長度：{field.qualified_name} 只有 {len(text)} 個字"
                )
            replacement = self._raw_text(value)[:length]
            replacement = replacement.ljust(length)
            for offset, char in enumerate(replacement):
                text[start + offset] = char
            if field.is_group:
                self.set_group_text(Reference(field, reference.path), "".join(text))
                return
            self.storage.set(field, reference.path, self.coerce(field, "".join(text)))
            self.sync_overlay(field, reference.path)
            return
        self.storage.set(field, reference.path, self.coerce(field, value, rounding))
        self.sync_overlay(field, reference.path)

    # ---------------------------------------------------------------- 群組 ↔ 文字

    @staticmethod
    def element_length(field: Field) -> int:
        """基本項目在群組（與檔案記錄）裡佔的字元數。"""
        pic = field.pic
        if pic is None:
            return 1
        if pic.category == CAT_NUMERIC:
            return pic.total_digits + (1 if pic.has_sign else 0)
        return pic.char_count

    def group_elements(self, field: Field, path: tuple):
        """群組底下所有基本項目 ``(欄位, 路徑)``，依記憶體順序展開 OCCURS。

        REDEFINES 的項目和被重新定義的項目共用位置，這裡只走原本的那一個。
        """
        depth = 0
        node: Field | None = field
        while node is not None:
            if node.has_occurs:
                depth += 1
            node = node.parent
        # 參考本身已經帶了這一層的下標（例如 WS-ITEM (2)）就不再展開
        expand_self = field.has_occurs and len(path) < depth
        yield from self._walk_elements(field, path, expand_self)

    def _walk_elements(self, field: Field, path: tuple, expand_self: bool):
        if expand_self and field.has_occurs:
            for index in range(1, field.max_occurs + 1):
                yield from self._walk_elements(field, path + (index,), False)
            return
        if not field.is_group:
            yield field, path
            return
        for child in field.children:
            if child.redefines is not None:
                continue
            yield from self._walk_elements(child, path, True)

    def element_text(self, field: Field, value) -> str:
        """基本項目在記錄裡的固定長度文字（數字補零、隱含小數點不印出）。"""
        length = self.element_length(field)
        pic = field.pic
        if pic is None or pic.category == CAT_ALPHANUMERIC:
            text = value.char * length if isinstance(value, Fill) else self._raw_text(value)
            return text[:length].ljust(length)
        number = self.to_decimal(value)
        if pic.category == CAT_NUMERIC_EDITED:
            return pic.to_text(number)[:length].rjust(length)
        digits = int(abs(number).scaleb(pic.dec_digits).to_integral_value(rounding=ROUND_DOWN))
        text = str(digits).zfill(pic.total_digits)[-pic.total_digits :] if pic.total_digits else ""
        if pic.has_sign:
            sign = "-" if number < 0 else "+"
            return sign + text if field.sign_leading else text + sign
        return text

    def element_from_text(self, field: Field, text: str):
        """把記錄裡切出來的一段文字轉回基本項目的值。"""
        pic = field.pic
        if pic is None or pic.category == CAT_ALPHANUMERIC:
            return text
        stripped = text.strip(" \x00\uffff")
        if not stripped:
            return Decimal(0)
        if pic.category == CAT_NUMERIC_EDITED or "." in stripped or "," in stripped:
            # 數字編輯欄位，或是人手寫、帶小數點的資料
            return self.to_decimal(stripped)
        negative = stripped.startswith("-") or stripped.endswith("-")
        digits = stripped.strip("+-").strip()
        if not digits or any(ch not in "0123456789" for ch in digits):
            raise RuntimeError_(
                f"{field.qualified_name} 收到的內容 '{text}' 不是數字（請檢查記錄版面或資料內容）"
            )
        number = Decimal(int(digits)).scaleb(-pic.dec_digits)
        return -number if negative else number

    def group_text(self, reference: Reference) -> str:
        """群組項目的值：底下每個基本項目的記錄文字依序串起來。"""
        return "".join(
            self.element_text(field, self._raw_get(field, path))
            for field, path in self.group_elements(reference.field, reference.path)
        )

    def set_group_text(self, reference: Reference, value) -> None:
        """把一段文字（或象徵常數）依版面拆開，寫進群組底下的每個基本項目。"""
        self._distribute(reference.field, reference.path, value, lenient=False)
        self.sync_overlay(reference.field, reference.path)

    def _distribute(self, field: Field, path: tuple, value, lenient: bool) -> None:
        """把文字依版面寫進 ``field`` 底下的基本項目。

        ``lenient`` 用於 REDEFINES 的同步：數字欄位收到非數字內容時照樣存起來
        （真正拿來計算時才會報「不是有效的數值」），而不是在搬移時就報錯。
        """
        elements = list(self.group_elements(field, path))
        total = sum(self.element_length(item) for item, _ in elements)
        if isinstance(value, Fill):
            text = (value.char * total)[:total]
        else:
            text = self._raw_text(value)[:total].ljust(total)
        position = 0
        for item, item_path in elements:
            length = self.element_length(item)
            piece = text[position : position + length]
            position += length
            if item.usage == "INDEX":
                continue
            try:
                stored = self.coerce(item, self.element_from_text(item, piece))
            except RuntimeError_:
                if not lenient:
                    raise
                stored = piece
            self.storage.set(item, item_path, stored)

    def area_text(self, field: Field, path: tuple) -> str:
        """一個項目（含 OCCURS 的所有元素）佔用的那段記錄文字。"""
        return "".join(
            self.element_text(item, self._raw_get(item, item_path))
            for item, item_path in self.group_elements(field, path)
        )

    def sync_overlay(self, field: Field, path: tuple) -> None:
        """REDEFINES：寫入某個項目後，把同一塊位置的其他項目一起更新。"""
        overlays = self.layout.overlays
        if not overlays:
            return
        member = field
        while member is not None and id(member) not in overlays:
            member = member.parent
        if member is None:
            return
        # 這一組項目的位置只由上層 OCCURS 的下標決定（項目自己的 OCCURS 要整個展開）
        depth = 0
        node = member.parent
        while node is not None:
            if node.has_occurs:
                depth += 1
            node = node.parent
        base = tuple(path[:depth])
        text = self.area_text(member, base)
        for other in overlays[id(member)]:
            if other is not member:
                self._distribute(other, base, text, lenient=True)

    def _write_span(self, span: list[Field], value) -> None:
        text = self._raw_text(value)
        for field in span:
            length = field.size if field.pic is None or field.pic.category == CAT_ALPHANUMERIC else field.pic.char_count
            piece = text[:length]
            text = text[length:]
            self.storage.set(field, (), self.coerce(field, piece))

    def _initialize_group(self, field: Field, path: tuple) -> None:
        """INITIALIZE 群組：所有基本項目回到預設值。"""
        if field.occurs_max is not None:
            for index in range(1, field.max_occurs + 1):
                self._initialize_group_children(field, path + (index,))
        else:
            self._initialize_group_children(field, path)
        self.sync_overlay(field, path)

    def _initialize_group_children(self, field: Field, path: tuple) -> None:
        if field.pic is not None and not field.is_group:
            self.storage.set(field, path, self.storage.default_for(field))
            return
        for child in field.children:
            if child.redefines is not None:
                continue
            self._initialize_group(child, path)

    # ---------------------------------------------------------------- 型別轉換

    def coerce(self, field: Field, value, rounding: bool = False):
        """把任意值轉成欄位能接受的型別，並套用截斷／捨入規則。"""
        pic = field.pic
        if field.usage == "INDEX":
            return self.to_int(value, "索引")
        if pic is None:  # pragma: no cover - 理論上不會發生
            return value
        if pic.category == CAT_ALPHANUMERIC:
            length = pic.char_count
            if isinstance(value, Fill):
                text = value.char * length
            else:
                text = self._raw_text(value)
            if field.justified:
                # JUSTIFIED RIGHT：靠右對齊，多的字丟右邊、少的字補左邊
                return text[-length:] if len(text) > length else text.rjust(length)
            # 一般文數字欄位靠左對齊：多的字丟右邊、少的字補右邊
            return text[:length] if len(text) > length else text.ljust(length)
        # 數字（含數字編輯）
        if isinstance(value, Fill):
            if value.char in ("0", " "):
                number = Decimal(0)
            elif value.char and all(ch in "0123456789" for ch in value.char):
                # ALL "1" 搬進 PIC 9(3)V9 → 111.1
                digits = pic.total_digits or 1
                number = Decimal(int((value.char * digits)[:digits])).scaleb(-pic.dec_digits)
            else:
                raise RuntimeError_(
                    "HIGH-VALUES、LOW-VALUES 或非數字的 ALL 常數不能直接搬進數字欄位"
                )
        else:
            number = self.to_decimal(value)
        return pic.quantize(number, rounding)

    def _raw_text(self, value) -> str:
        """把值轉成它的字串表示（供文字欄位使用）。"""
        if isinstance(value, Fill):
            # 象徵常數（SPACES、QUOTES…）單獨求值時就是一個字元
            return value.char
        if isinstance(value, bool):
            return "1" if value else "0"
        if isinstance(value, str):
            return value
        if isinstance(value, Decimal):
            if value == value.to_integral_value():
                return str(int(value))
            return format(value.normalize(), "f")
        if value is None:
            return ""
        return str(value)

    def to_decimal(self, value) -> Decimal:
        if isinstance(value, Fill):
            raise RuntimeError_("象徵常數（例如 SPACES）不能當成數值使用")
        if isinstance(value, bool):
            return Decimal(1 if value else 0)
        if isinstance(value, Decimal):
            return value
        if isinstance(value, int):
            return Decimal(value)
        if isinstance(value, str):
            text = value.strip()
            if text == "":
                return Decimal(0)
            if text.upper() in ("TRUE",):
                return Decimal(1)
            if text.upper() in ("FALSE",):
                return Decimal(0)
            # 只接受看得懂的數字寫法；"12A34" 不能悄悄變成 1234
            match = _NUMBER_TEXT.fullmatch(text.replace(",", ""))
            if match is None:
                raise RuntimeError_(f"'{value}' 不是有效的數值")
            number = Decimal(match.group(2))
            trailing = (match.group(3) or "").upper()
            if match.group(1) == "-" or trailing in ("-", "CR", "DB"):
                number = -number
            return number
        raise RuntimeError_(f"無法把 {value!r} 當成數值使用")

    def to_int(self, value, what: str = "數值") -> int:
        """轉成整數（下標、TIMES、索引等），小數部分一律向零截斷。

        COBOL 把非整數放進整數用途時是截斷而不是捨入：``2.7`` → 2、``-2.7`` → -2。
        不要改回預設的 ROUND_HALF_EVEN，否則 ``T (2.5)`` 這類下標會變成 2 或 3 不定。
        """
        try:
            return int(self.to_decimal(value).to_integral_value(rounding=ROUND_DOWN))
        except (InvalidOperation, ValueError):
            raise RuntimeError_(f"{what} 必須是整數，但讀到 {value!r}") from None

    def to_bool(self, value) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, Decimal):
            return value != 0
        text = self._raw_text(value).strip()
        if text.upper() == "TRUE":
            return True
        if text.upper() == "FALSE":
            return False
        return self.to_decimal(value) != 0

    # ================================================================ 求值
