# Copyright (c) 2012-2017 The ANTLR Project. All rights reserved.
# Use of this file is governed by the BSD 3-clause license that
# can be found in the LICENSE.txt file in the project root.
#/


# The basic notion of a tree has a parent, a payload, and a list of children.
#  It is the most abstract interface for all the trees used by ANTLR.
#/
import typing as t
from antlr4.Token import Token
if t.TYPE_CHECKING:
    from antlr4.RuleContext import RuleContext


INVALID_INTERVAL = (-1, -2)

class Tree(object):
    def getChild(self, i: int) -> t.Optional['Tree']: ...
    def getChildCount(self) -> int: ...
    def getChildren(self) -> t.Iterable['Tree']: ...
    def getText(self) -> str: ...
    def getPayload(self) -> t.Any: ...
    def getParent(self) -> t.Optional['Tree']: ...


class SyntaxTree(Tree):
    pass


class ParseTree(SyntaxTree):
    def getChild(self, i: int) -> t.Optional['ParseTree']: ...
    def getChildren(self) -> t.Iterable['ParseTree']: ...
    def accept(self, visitor: 'ParseTreeVisitor') -> t.Any: ...


class RuleNode(ParseTree):
    def getRuleContext(self) -> 'RuleContext': ...
    def getAltNumber(self) -> int: ...
    def getRuleIndex(self) -> int: ...

class TerminalNode(ParseTree):
    symbol: t.Optional[Token]
    parentCtx: t.Optional[RuleNode]


class ErrorNode(TerminalNode):
    pass


class ParseTreeVisitor(object):
    def visit(self, tree: ParseTree):
        return tree.accept(self)

    def visitChildren(self, node: ParseTree):
        result = self.defaultResult()
        n = node.getChildCount()
        for i in range(n):
            if not self.shouldVisitNextChild(node, result):
                return result

            c = node.getChild(i)
            assert c
            childResult = c.accept(self)
            result = self.aggregateResult(result, childResult)

        return result

    def visitTerminal(self, node: ParseTree):
        return self.defaultResult()

    def visitErrorNode(self, node: ParseTree):
        return self.defaultResult()

    def defaultResult(self) -> t.Any:
        return None

    def aggregateResult(self, aggregate: t.Any, nextResult: t.Any):
        return nextResult

    def shouldVisitNextChild(self, node: ParseTree, currentResult: t.Any) -> bool:
        return True


class ParseTreeListener(object):

    def visitTerminal(self, node: TerminalNode):
        pass

    def visitErrorNode(self, node: ErrorNode):
        pass

    def enterEveryRule(self, ctx: RuleNode):
        pass

    def exitEveryRule(self, ctx: RuleNode):
        pass


class TerminalNodeImpl(TerminalNode):
    __slots__ = ('parentCtx', 'symbol')

    def __init__(self, symbol: t.Optional[Token]):
        self.parentCtx = None
        self.symbol = symbol

    def __setattr__(self, key: str, value: t.Any):
        super().__setattr__(key, value)

    def getChild(self, i:int):
        return None

    def getSymbol(self):
        return self.symbol

    def getParent(self):
        return self.parentCtx

    def getPayload(self):
        return self.symbol

    def getSourceInterval(self):
        if self.symbol is None:
            return INVALID_INTERVAL
        tokenIndex = self.symbol.tokenIndex
        return (tokenIndex, tokenIndex)

    def getChildCount(self):
        return 0

    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitTerminal(self)

    def getText(self):
        return self.symbol and self.symbol.text or ''

    def __str__(self):
        if self.symbol and self.symbol.type == Token.EOF:
            return "<EOF>"
        else:
            return self.symbol and self.symbol.text or ''


# Represents a token that was consumed during resynchronization
#  rather than during a valid match operation. For example,
#  we will create this kind of a node during single token insertion
#  and deletion as well as during "consume until error recovery set"
#  upon no viable alternative exceptions.

class ErrorNodeImpl(TerminalNodeImpl, ErrorNode):

    def __init__(self, token: Token):
        super().__init__(token)

    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitErrorNode(self)


class ParseTreeWalker(object):

    DEFAULT: 'ParseTreeWalker'

    def walk(self, listener: ParseTreeListener, tree: ParseTree):
        """
	    Performs a walk on the given parse tree starting at the root and going down recursively
	    with depth-first search. On each node, {@link ParseTreeWalker#enterRule} is called before
	    recursively walking down into child nodes, then
	    {@link ParseTreeWalker#exitRule} is called after the recursive call to wind up.
	    @param listener The listener used by the walker to process grammar rules
	    @param t The parse tree to be walked on
        """
        if isinstance(tree, ErrorNode):
            listener.visitErrorNode(tree)
            return
        elif isinstance(tree, TerminalNode):
            listener.visitTerminal(tree)
            return
        assert isinstance(tree, RuleNode)
        self.enterRule(listener, tree)
        for child in tree.getChildren():
            self.walk(listener, child)
        self.exitRule(listener, tree)

    #
    # The discovery of a rule node, involves sending two events: the generic
    # {@link ParseTreeListener#enterEveryRule} and a
    # {@link RuleContext}-specific event. First we trigger the generic and then
    # the rule specific. We to them in reverse order upon finishing the node.
    #
    def enterRule(self, listener: ParseTreeListener, r: RuleNode):
        """
	    Enters a grammar rule by first triggering the generic event {@link ParseTreeListener#enterEveryRule}
	    then by triggering the event specific to the given parse tree node
	    @param listener The listener responding to the trigger events
	    @param r The grammar rule containing the rule context
        """
        ctx = r.getRuleContext()
        listener.enterEveryRule(ctx)
        ctx.enterRule(listener)

    def exitRule(self, listener: ParseTreeListener, r: RuleNode):
        """
	    Exits a grammar rule by first triggering the event specific to the given parse tree node
	    then by triggering the generic event {@link ParseTreeListener#exitEveryRule}
	    @param listener The listener responding to the trigger events
	    @param r The grammar rule containing the rule context
        """
        ctx = r.getRuleContext()
        ctx.exitRule(listener)
        listener.exitEveryRule(ctx)

ParseTreeWalker.DEFAULT = ParseTreeWalker()
