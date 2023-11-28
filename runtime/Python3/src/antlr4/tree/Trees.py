#
# Copyright (c) 2012-2017 The ANTLR Project. All rights reserved.
# Use of this file is governed by the BSD 3-clause license that
# can be found in the LICENSE.txt file in the project root.
#


# A set of utility routines useful for all kinds of ANTLR trees.#
from io import StringIO
from antlr4.Token import Token
from antlr4.Utils import escapeWhitespace
from antlr4.tree.Tree import RuleNode, ErrorNode, TerminalNode, Tree, ParseTree
import typing as t
if t.TYPE_CHECKING:
    from antlr4.Parser import Parser


class Trees(object):

     # Print out a whole tree in LISP form. {@link #getNodeText} is used on the
    #  node payloads to get the text for the nodes.  Detect
    #  parse trees and extract data appropriately.
    @classmethod
    def toStringTree(cls, tree: Tree, ruleNames: t.Optional[t.List[str]] = None, recog: t.Optional['Parser'] = None):
        if recog is not None:
            ruleNames = recog.ruleNames
        s = escapeWhitespace(cls.getNodeText(tree, ruleNames), False)
        if tree.getChildCount() == 0:
            return s
        with StringIO() as buf:
            buf.write("(")
            buf.write(s)
            buf.write(' ')
            for i in range(0, tree.getChildCount()):
                if i > 0:
                    buf.write(' ')
                buf.write(cls.toStringTree(t.cast(Tree, tree.getChild(i)), ruleNames))
            buf.write(")")
            return buf.getvalue()

    @classmethod
    def getNodeText(cls, tree: Tree, ruleNames: t.Optional[t.List[str]] = None, recog: t.Optional['Parser'] = None):
        if recog is not None:
            ruleNames = recog.ruleNames
        if ruleNames is not None:
            if isinstance(tree, RuleNode):
                if tree.getAltNumber() != 0: # should use ATN.INVALID_ALT_NUMBER but won't compile
                    return ruleNames[tree.getRuleIndex()] + ":" + str(tree.getAltNumber())
                return ruleNames[tree.getRuleIndex()]
            elif isinstance(tree, ErrorNode):
                return str(tree)
            elif isinstance(tree, TerminalNode):
                if tree.symbol is not None:
                    return tree.symbol.text or ''
        # no recog for rule names
        payload = tree.getPayload()
        if isinstance(payload, Token):
            return payload.text or ''
        return str(tree.getPayload())


    # Return ordered list of all children of this node
    @classmethod
    def getChildren(cls, tree: Tree):
        return [tree.getChild(i) for i in range(0, tree.getChildCount())]

    # Return a list of all ancestors of this node.  The first node of
    #  list is the root and the last is the parent of this node.
    #
    @classmethod
    def getAncestors(cls, tree: Tree):
        ancestors: t.List[Tree] = []
        curr_tree = tree.getParent()
        while curr_tree is not None:
            ancestors.insert(0, curr_tree) # insert at start
            curr_tree = curr_tree.getParent()
        return ancestors

    @classmethod
    def findAllTokenNodes(cls, tree: ParseTree, ttype: int):
        return cls.findAllNodes(tree, ttype, True)

    @classmethod
    def findAllRuleNodes(cls, tree: ParseTree, ruleIndex: int):
        return cls.findAllNodes(tree, ruleIndex, False)

    @classmethod
    def findAllNodes(cls, tree: ParseTree, index: int, findTokens: bool):
        nodes: t.List[Tree] = []
        cls._findAllNodes(tree, index, findTokens, nodes)
        return nodes

    @classmethod
    def _findAllNodes(cls, tree: ParseTree, index: int, findTokens: bool, nodes: t.List[Tree]):
        from antlr4.ParserRuleContext import ParserRuleContext
        # check this node (the root) first
        if findTokens and isinstance(tree, TerminalNode):
            if tree.symbol and (tree.symbol.type == index):
                nodes.append(tree)
        elif not findTokens and isinstance(tree, ParserRuleContext):
            if tree.ruleIndex == index:
                nodes.append(tree)
        # check children
        for i in range(0, tree.getChildCount()):
            cls._findAllNodes(t.cast(ParseTree, tree.getChild(i)), index, findTokens, nodes)

    @classmethod
    def descendants(cls, tree: ParseTree):
        nodes = [tree]
        for i in range(0, tree.getChildCount()):
            nodes.extend(cls.descendants(t.cast(ParseTree, tree.getChild(i))))
        return nodes
