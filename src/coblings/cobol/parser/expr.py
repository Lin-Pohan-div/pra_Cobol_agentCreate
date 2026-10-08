"""Parser 運算式：運算元、算式、條件、識別字、常數。"""
from __future__ import annotations

from decimal import Decimal

from .. import nodes
from ..lexer import COLON, COMMA, NUMBER, OP, STRING, WORD
from .base import (
    ParserBase,
    SCOPED_TERMINATORS,
    VERBS,
    _CLASS_KEYWORDS,
    _RELATIONS,
    _SIGN_KEYWORDS,
)


#: 條件後面可能出現、但絕對不是條件名稱的關鍵字
_CONDITION_FOLLOWERS = frozenset(
    """
    OR AND NOT THEN NEXT SENTENCE ALSO THRU THROUGH IS ARE OTHER UNTIL VARYING
    AFTER BEFORE TIMES AT ON INVALID WITH FROM BY TO GIVING INTO TRUE FALSE ANY
    """.split()
)


def _is_condition_keyword(word: str) -> bool:
    return (
        word in VERBS
        or word in SCOPED_TERMINATORS
        or word in _CONDITION_FOLLOWERS
        or word.startswith("END-")
    )


class ExprParser(ParserBase):
    """解析運算式與條件。"""
    def parse_operand(self):
        """解析一個運算元（可能是運算式）。"""
        if self.tok.kind == OP and self.tok.value in "+-" and self.peek(1).kind in (NUMBER, OP, WORD):
            token = self.advance()
            operand = self.parse_operand()
            return nodes.Node("unary", token.line, token.column, op=token.value, operand=operand)
        return self.parse_primary()

    def parse_arithmetic(self):
        left = self.parse_term()
        while self.tok.kind == OP and self.tok.value in "+-":
            token = self.advance()
            right = self.parse_term()
            left = nodes.Node("binary", token.line, token.column, op=token.value, left=left, right=right)
        return left

    def parse_term(self):
        left = self.parse_factor()
        while self.tok.kind == OP and self.tok.value in "*/":
            token = self.advance()
            right = self.parse_factor()
            left = nodes.Node("binary", token.line, token.column, op=token.value, left=left, right=right)
        return left

    def parse_factor(self):
        if self.tok.kind == OP and self.tok.value in "+-":
            token = self.advance()
            operand = self.parse_factor()
            return nodes.Node("unary", token.line, token.column, op=token.value, operand=operand)
        return self.parse_power()

    def parse_power(self):
        base = self.parse_primary()
        if self.tok.kind == OP and self.tok.value == "**":
            token = self.advance()
            exponent = self.parse_factor()
            return nodes.Node("binary", token.line, token.column, op="**", left=base, right=exponent)
        return base

    def parse_primary(self):
        token = self.tok
        if token.kind == NUMBER:
            self.advance()
            return nodes.Node("literal", token.line, token.column, value=Decimal(token.value))
        if token.kind == STRING:
            self.advance()
            return nodes.Node("literal", token.line, token.column, value=token.value)
        if token.kind == OP and token.value == "(":
            self.advance()
            inner = self.parse_condition()
            if not (self.tok.kind == OP and self.tok.value == ")"):
                self.fail("括號沒有關閉")
            self.advance()
            # parse_condition 會把單純的運算式包成「條件」節點，
            # 在算式裡要拿回原本的運算式，否則 (3 + 4) 會變成真／假
            if inner.kind == "relation" and inner.get("op") == "IS_TRUE" and inner.get("right") is None:
                return inner.left
            return inner
        if token.kind == OP and token.value == "$":
            self.advance()
            return self.parse_primary()
        if token.kind == WORD:
            upper = token.upper
            if upper in ("ZERO", "ZEROS", "ZEROES", "SPACES", "SPACE", "HIGH-VALUES", "LOW-VALUES",
                         "QUOTES", "NULL", "NULLS", "TRUE", "FALSE", "ALL"):
                self.advance()
                if upper == "ALL":
                    pattern = self.parse_literal()
                    return nodes.Node("figurative", token.line, token.column, name="ALL", pattern=pattern.value)
                return nodes.Node("figurative", token.line, token.column, name=upper)
            if upper == "FUNCTION":
                return self.parse_function()
            return self.parse_identifier()
        self.fail(f"預期一個運算元，但讀到 '{token.value}'")

    def parse_function(self):
        token = self.expect_word("FUNCTION")
        if self.tok.kind != WORD:
            self.fail("FUNCTION 之後必須是函式名稱")
        name = self.advance().upper
        self.eat_word("OF")
        args: list = []
        if self.tok.kind == OP and self.tok.value == "(":
            self.advance()
            if not (self.tok.kind == OP and self.tok.value == ")"):
                args.append(self.parse_arithmetic())
                while self.tok.kind == COMMA:
                    self.advance()
                    args.append(self.parse_arithmetic())
            self.advance()
        else:
            args.append(self.parse_arithmetic())
        return nodes.Node("function", token.line, token.column, name=name, args=args)

    # ---- 條件

    def parse_condition(self):
        left = self.parse_and()
        while self.at_word("OR"):
            token = self.advance()
            right = self.parse_and()
            left = nodes.Node("logical", token.line, token.column, op="OR", left=left, right=right)
        return left

    def parse_and(self):
        left = self.parse_not()
        while self.at_word("AND"):
            token = self.advance()
            right = self.parse_not()
            left = nodes.Node("logical", token.line, token.column, op="AND", left=left, right=right)
        return left

    def parse_not(self):
        if self.at_word("NOT"):
            token = self.advance()
            inner = self.parse_not()
            return nodes.Node("logical", token.line, token.column, op="NOT", left=inner)
        return self.parse_relation()

    def parse_relation(self):
        left = self.parse_arithmetic()
        token = self.tok
        if token.kind == OP and token.value in _RELATIONS:
            self.advance()
            right = self.parse_arithmetic()
            return nodes.Node("relation", token.line, token.column, op=token.value, left=left, right=right)
        if token.kind == WORD:
            upper = token.upper
            if upper in ("NUMERIC", "ALPHABETIC", "ALPHABETIC-LOWER", "ALPHABETIC-UPPER"):
                self.advance()
                return nodes.Node("class_condition", token.line, token.column, class_name=upper, target=left)
            if upper in ("POSITIVE", "NEGATIVE", "ZERO", "NONZERO"):
                self.advance()
                return nodes.Node("sign_condition", token.line, token.column, class_name=upper, target=left)
        if self.at_word("IS", "ARE"):
            # `IF X IS NUMERIC` / `IF X IS NOT ZERO`：IS 後面接類別或符號條件
            self.advance()
            negated = self.eat_word("NOT")
            keyword = self.tok
            if keyword.kind == WORD and keyword.upper in _CLASS_KEYWORDS:
                self.advance()
                node = nodes.Node(
                    "class_condition",
                    keyword.line,
                    keyword.column,
                    class_name=keyword.upper,
                    target=left,
                    negated=negated,
                )
                return node
            if keyword.kind == WORD and keyword.upper in _SIGN_KEYWORDS:
                self.advance()
                return nodes.Node(
                    "sign_condition",
                    keyword.line,
                    keyword.column,
                    class_name=keyword.upper,
                    target=left,
                    negated=negated,
                )
        if left.kind == "identifier":
            # `IF WS-FLAG IS-YES` 這種（非標準）寫法：後面接的是條件名稱。
            # 後面是 OR／AND／THEN 這類關鍵字時不能吃掉，否則 `IF A-ON OR B-ON` 會壞掉
            if self.tok.kind == WORD and not _is_condition_keyword(self.tok.upper):
                following = self.advance()
                return nodes.Node(
                    "relation", following.line, following.column,
                    op="IS_TRUE", left=nodes.Node("identifier", following.line, following.column,
                                                  name=following.value.upper(), subscripts=[]),
                    right=None,
                )
            return nodes.Node("relation", left.line, left.column, op="IS_TRUE", left=left, right=None)
        return nodes.Node("relation", left.line, left.column, op="IS_TRUE", left=left, right=None)

    # ---- 識別字

    def parse_identifier(self):
        """解析識別字：名稱（OF 限定）（下標）."""
        token = self.tok
        if token.kind != WORD:
            return None
        name = self.advance().value.upper()
        line, column = token.line, token.column
        while self.at_word("OF"):
            self.advance()
            if self.tok.kind == WORD:
                name = name + " OF " + self.advance().value.upper()
            else:
                break
        subscripts: list = []
        if self.tok.kind == OP and self.tok.value == "(":
            self.advance()
            while True:
                subscripts.append(self.parse_arithmetic())
                # 參考修改的分隔符 `:` 會被 lexer 發成 COLON token
                if (self.tok.kind == OP and self.tok.value == ":") or self.tok.kind == COLON:
                    self.advance()
                    length = self.parse_arithmetic()
                    # 參考修改 X (a : b)：起點 a 已經在 plain 的最後一個
                    subscripts.append(("refmod", length))
                    break
                if self.tok.kind == COMMA:
                    self.advance()
                    continue
                break
            if not (self.tok.kind == OP and self.tok.value == ")"):
                self.fail("下標的括號沒有關閉")
            self.advance()
        return nodes.Node("identifier", line, column, name=name, subscripts=subscripts)

    def parse_identifier_list(self, terminator_words: tuple[str, ...] = ()) -> list:
        result = []
        while not self.at_eof():
            if terminator_words and self.at_word(*terminator_words):
                break
            if self.at_period():
                break
            identifier = self.parse_identifier()
            if identifier is None:
                break
            result.append(identifier)
            if self.tok.kind == COMMA:
                self.advance()
                continue
            break
        return result

    def parse_literal_or_expression(self):
        return self.parse_arithmetic()

    def parse_literal(self):
        token = self.tok
        if token.kind == STRING:
            self.advance()
            return nodes.Node("literal", token.line, token.column, value=token.value)
        if token.kind == NUMBER:
            self.advance()
            return nodes.Node("literal", token.line, token.column, value=Decimal(token.value))
        if token.kind == OP and token.value in "+-":
            self.advance()
            inner = self.parse_literal()
            return nodes.Node("literal", token.line, token.column, value=inner.value)
        self.fail(f"預期一個常數，但讀到 '{token.value}'")
        return None
