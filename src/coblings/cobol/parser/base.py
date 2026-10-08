"""Parser 基礎：詞形操作、共用常數。"""
from __future__ import annotations

from ..errors import SyntaxError_
from ..lexer import EOF, PERIOD, SEMICOLON, WORD, Token

#: 會開頭一個敘述動詞的字
VERBS = frozenset(
    """
    ACCEPT ADD CALL CLOSE COMPUTE CONTINUE DELETE DISPLAY DIVIDE ENTRY EVALUATE
    EXIT GOBACK GO GOTO IF INITIALIZE INSPECT MERGE MOVE MULTIPLY NEXT OPEN PERFORM
    READ RELEASE RETURN REWRITE SEARCH SET SORT START STOP STRING SUBTRACT
    UNSTRING WRITE USE
    """.split()
)

#: PICTURE 子句遇到這些字就要停下來
_PICTURE_STOPPERS = frozenset(
    """
    VALUE USAGE DISPLAY OCCURS REDEFINES JUSTIFIED SIGN BLANK NATIONAL SYNC
    EXTERNAL GLOBAL INITIALIZE BINARY PACKED-DECIMAL COMP COMP-1 COMP-2
    COMP-3 COMP-4 COMP-5 COMPUTATIONAL COMPUTATIONAL-1 COMPUTATIONAL-2
    COMPUTATIONAL-3 COMPUTATIONAL-4 COMPUTATIONAL-5 FLOAT SENTENCE
    PROCEDURE DATA ENVIRONMENT IDENTIFICATION ID DIVISION SECTION
    WORKING-STORAGE LOCAL-STORAGE LINKAGE FILE FD SD
    """.split()
)

_EDITION_ONLY_OPS = frozenset({"(", ")", "-", "+", "*", "/", ",", ".", "$"})

#: 可以直接寫在 PICTURE 後面的 USAGE 字
_USAGE_WORDS = frozenset(
    """
    DISPLAY COMP COMP-1 COMP-2 COMP-3 COMP-4 COMP-5 BINARY PACKED-DECIMAL
    COMPUTATIONAL COMPUTATIONAL-1 COMPUTATIONAL-2 COMPUTATIONAL-3
    COMPUTATIONAL-4 COMPUTATIONAL-5 FLOAT INDEX
    """.split()
)

_RELATIONS = frozenset({"=", ">", "<", ">=", "<=", "==", "!=", "<>"})

#: `IS` 後面可以接的類別條件
_CLASS_KEYWORDS = frozenset(
    {"NUMERIC", "ALPHABETIC", "ALPHABETIC-LOWER", "ALPHABETIC-UPPER"}
)
#: `IS` 後面可以接的符號條件
_SIGN_KEYWORDS = frozenset({"POSITIVE", "NEGATIVE", "ZERO", "NONZERO"})

#: 各種結構的結束關鍵字；出現在敘述清單中就代表目前這個結構結束了
SCOPED_TERMINATORS = frozenset(
    """
    ELSE END-IF END-PERFORM END-EVALUATE END-SEARCH END-READ END-WRITE
    END-ACCEPT END-CALL END-ADD END-SUBTRACT END-MULTIPLY END-DIVIDE
    END-COMPUTE END-DISPLAY END-MOVE END-SET END-INITIALIZE END-INSPECT
    END-STRING END-UNSTRING END-DELETE END-REWRITE END-RETURN END-DECLARATIVES
    WHEN
    """.split()
)


class ParserBase:
    """遞迴下降解析器的基礎（詞形游標與輔助操作）。"""
    def __init__(self, tokens: list[Token], filename: str = "") -> None:
        self.tokens = tokens
        self.filename = filename
        self.pos = 0

    # ---------------------------------------------------------------- 基本操作

    @property
    def tok(self) -> Token:
        return self.tokens[self.pos]

    def peek(self, offset: int = 0) -> Token:
        index = self.pos + offset
        # 防護：負數偏移在 pos=0 時會回傳最後一個 token（EOF），
        # 這不是預期行為，但呼叫端應避免使用負數偏移
        if index < 0:
            index = 0
        index = min(index, len(self.tokens) - 1)
        return self.tokens[index]

    def advance(self) -> Token:
        token = self.tokens[self.pos]
        if token.kind != EOF:
            self.pos += 1
        return token

    def at_eof(self) -> bool:
        return self.tok.kind == EOF

    def at_period(self) -> bool:
        return self.tok.kind == PERIOD or self.tok.kind == SEMICOLON

    def eat_period(self) -> None:
        if self.at_period():
            self.advance()

    def _eat_period_before(self, *words: str) -> None:
        """句點後面緊接著 ``words`` 時才吃掉句點（容忍常見筆誤）；否則句點結束整個句子。"""
        if self.at_period() and self.peek(1).kind == WORD and self.peek(1).upper in words:
            self.advance()

    def expect_period(self) -> None:
        if not self.at_period():
            self.fail(f"這裡需要一個句點（.），但讀到 '{self.tok.value}'")
        self.advance()

    def fail(self, message: str, token: Token | None = None):
        token = token or self.tok
        raise SyntaxError_(message, line=token.line, column=token.column)

    def at_word(self, *words: str) -> bool:
        return self.tok.kind == WORD and self.tok.upper in words

    def at_any_word(self) -> bool:
        return self.tok.kind == WORD

    def eat_word(self, *words: str) -> bool:
        if self.at_word(*words):
            self.advance()
            return True
        return False

    def expect_word(self, *words: str) -> Token:
        if not self.at_word(*words):
            self.fail(f"預期 {' 或 '.join(words)}，但讀到 '{self.tok.value}'")
        return self.advance()

    def skip_to_period(self) -> None:
        """略過整句（遇到句點為止），用於看不懂的子句。"""
        while not self.at_eof() and not self.at_period():
            self.advance()
        self.eat_period()

    def skip_to_section(self) -> None:
        """略過一個 SECTION 的內容，直到下一個 SECTION 或 DIVISION。"""
        while not self.at_eof():
            if self.at_word("SECTION", "DIVISION"):
                return
            self.advance()

    # ---------------------------------------------------------------- 程式
