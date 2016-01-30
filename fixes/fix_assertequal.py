"""Fixer that tranlslates unittest assertions to python assertions.

E.g.
   self.assert_(x)  -> assert x
   self.assertEquals(x, y) -> assert x == y

"""
from __future__ import absolute_import

from lib2to3.fixer_base import BaseFix
from lib2to3.fixer_util import Name, Comma, LParen, RParen
from lib2to3.pgen2 import token
from lib2to3.pytree import Leaf, Node
from lib2to3.pygram import python_symbols as syms

import copy

NOT = [Leaf(token.NAME, "not", prefix=" ")]
EQUALS = [Leaf(token.EQEQUAL, "==", prefix=" ")]
NOTEQUALS = [Leaf(token.NOTEQUAL, "!=", prefix=" ")]
IN = [Leaf(token.NAME, "in", prefix=" ")]
NOT_IN = NOT + IN
IS = [Leaf(token.NAME, "is", prefix=" ")]
IS_NOT = IS + NOT
NONE = Leaf(token.NAME, "None", prefix=" ")

GREATER = [Leaf(token.GREATER, ">", prefix=" ")]
GREATER_EQUAL = [Leaf(token.GREATEREQUAL, ">=", prefix=" ")]
LESS = [Leaf(token.LESS, "<", prefix=" ")]
LESS_EQUAL = [Leaf(token.LESSEQUAL, "<=", prefix=" ")]

TRUE = Name("True")
FALSE = Name("False")

def make_operand(node):
    """Convert a node into something we can put in a statement.

    Adds parentheses if needed.
    """
    if (isinstance(node, Leaf) or
            node.type == syms.power or
            node.type == syms.atom and node.children[0].type != token.STRING):
        result = [node.clone()]  # No parentheses required in simple stuff
    else:
        # Parentheses required in complex statements (eg. assertEqual(x + y, 17))
        result = [LParen(), node.clone(), RParen()]
        result[0].prefix = node.prefix
        result[1].prefix = ""
    return result

def make_assert_msg(msg):
    """Returns the assert message that should be added to the assertion.

    Args:
      msg: The Node holding the msg.  (Could be a bare string or a keyword arg)
    """
    if msg is None:
        return []

    if msg.type == syms.argument:
        # If we have a `msg="blah"`, just return the "blah" portion but keep
        # the prefix of the `msg=` part.
        p_prefix = msg.prefix
        msg = msg.children[2]
        msg.prefix = p_prefix

    if not msg.prefix:
        msg.prefix = u" "
    if "\n" in msg.prefix:
        msg.prefix = " \\" + msg.prefix
    return [Comma()] + make_operand(msg)

def assert_comparison(lhs, comparator, rhs, msg, prefix):
    """Build an assert statement in the AST"""
    children = [Name("assert")]

    # Single space after assert. Maintain the indentation/newline of the rhs, but
    # have to prepend a backslash for the assert to work.
    lhs.prefix = " "

    if "\n" in rhs.prefix:
        rhs.prefix = " \\" + rhs.prefix

    children.extend(make_operand(lhs))
    children.extend(copy.deepcopy(comparator))
    children.extend(make_operand(rhs))
    children.extend(make_assert_msg(msg))

    return Node(syms.assert_stmt, children, prefix=prefix)

def assertion(expr, msg, prefix, is_not=False):
    """Build an assert statement in the AST"""
    children = [Name("assert")]
    if is_not:
        children.append(Leaf(token.NAME, "not", prefix=" "))

    # Single space after assert. Maintain the indentation/newline of the expr.
    expr.prefix = " "
    children.append(expr.clone())
    children.extend(make_assert_msg(msg))

    return Node(syms.assert_stmt, children, prefix=prefix)

class FixAssertequal(BaseFix):
    """A Fixer in the lib2to3 framework for converting self.assertEqual or self.assertEquals
    to a regular assert statement. We do this because py.test can inspect types of statements
    if they use regular assert statements (better than the unit test framework can figure out)

    This now also converts a whole bunch of other TestCase assertions!
    """
    methods = """
              method=('assertEqual'|'assertEquals'
                     |'assertNotEqual'|'assertNotEquals'
                     |'assertTrue'|'assert_'
                     |'assertFalse'
                     |'assertIn'|'assertNotIn'
                     |'assertIs'|'assertIsNot'
                     |'assertIsNone'|'assertIsNotNone'
                     |'assertGreater'|'assertGreaterEqual'
                     |'assertLess'|'assertLessEqual'
                     )
              """
    PATTERN = """
    power<
        'self'
        trailer< '.' %(methods)s >
        ( trailer<
            '(' arglist<
                one=any ','
                two=any
                [',' three=any ]
                [',']
                > ')'
          > |
          trailer< '(' one=any ')' >
        )
    >
    """ % dict(methods=methods)

    def transform(self, node, results):
        """Returns what the above should be replaced with.

        This is called by the fixer.  Whatever this returns will be replaced
        into the node.

        """
        method = results['method'][0].value

        if method in ('assertTrue', 'assert_'):
            # Replace with a simple assert.
            return assertion(results['one'], results.get('two'), prefix=node.prefix)
        if method == 'assertFalse':
            # Replace with an assert but adding a 'not' in the front.
            return assertion(results['one'], results.get('two'), prefix=node.prefix,
                             is_not=True)

        if method in ('assertEqual', 'assertEquals'):
            # There are a couple of cases here.
            #   If either side is a True or False we replace it with a simple assert.
            #      i.e. "assert lhs" or "assert not lhs"
            #   If either side is None we use "assert lhs|rhs is None"
            #   Otherwise we do "assert lhs == rhs"
            comp = EQUALS
            lhs = results['one']
            rhs = results['two']

            if lhs in (TRUE, FALSE):
                rhs.prefix = lhs.prefix
                return assertion(rhs, results.get('three'),
                                 prefix=node.prefix, is_not=(lhs == FALSE))

            if rhs in (TRUE, FALSE):
                return assertion(lhs, results.get('three'),
                                 prefix=node.prefix, is_not=(rhs == FALSE))

            if NONE in (lhs, rhs):
                comp = IS

            return assert_comparison(lhs, comp, rhs,
                                     results.get('three'), prefix=node.prefix)

        if method == 'assertIsNone':
            return assert_comparison(results['one'], IS, NONE,
                                     results.get('two'), prefix=node.prefix)
        if method == 'assertIsNotNone':
            return assert_comparison(results['one'], IS_NOT, NONE,
                                     results.get('two'), prefix=node.prefix)

        comp_map = {
            'assertNotEqual': NOTEQUALS,
            'assertNotEquals': NOTEQUALS,
            'assertGreater': GREATER,
            'assertGreaterEqual': GREATER_EQUAL,
            'assertLess': LESS,
            'assertLessEqual': LESS_EQUAL,
            'assertIn': IN,
            'assertNotIn': NOT_IN,
            'assertIs': IS,
            'assertIsNot': IS_NOT,
        }

        assert method in comp_map

        return assert_comparison(results['one'], comp_map[method], results['two'],
                                 results.get('three'), prefix=node.prefix)
