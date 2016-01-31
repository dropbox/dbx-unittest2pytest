"""Fixer that tranlslates unittest assertions to python assertions.

E.g.
   self.assert_(x)  -> assert x
   self.assertEquals(x, y) -> assert x == y

"""
from __future__ import absolute_import

from lib2to3.fixer_base import BaseFix
from lib2to3.fixer_util import Name, Comma, LParen, RParen
from lib2to3.patcomp import PatternCompiler
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

class FixAsserts(BaseFix):
    """A Fixer in the lib2to3 framework for converting self.assertEqual or self.assertEquals
    to a regular assert statement. We do this because py.test can inspect types of statements
    if they use regular assert statements (better than the unit test framework can figure out)

    This now also converts a whole bunch of other TestCase assertions!
    """
    METHODS = """
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
    ONE_ARG = "(one=any)"
    ONE_ARG_COMMA = "arglist< one=any ',' >"
    TWO_ARG = "arglist< one=any ',' two=any [','] >"
    THREE_ARG = "arglist< one=any ',' two=any ',' three=any [','] >"
    PATTERN = """
    power<
        'self'
        trailer< '.' %(methods)s >
        trailer< '(' (
            %(three_arg)s |
            %(two_arg)s |
            %(one_arg_comma)s |
            %(one_arg)s
         ) ')' >
    >
    """ % dict(
        methods=METHODS,
        one_arg=ONE_ARG,
        one_arg_comma=ONE_ARG_COMMA,
        two_arg=TWO_ARG,
        three_arg=THREE_ARG,
    )
    IN_PATTERN = "comparison< a=any 'in' b=any >"
    NOTIN_PATTERN = "comparison< a=any comp_op<'not' 'in'> b=any >"

    def __init__(self, options, log):
        super(FixAsserts, self).__init__(options, log)
        PC = PatternCompiler()
        self.in_pattern = PC.compile_pattern(self.IN_PATTERN)
        self.notin_pattern = PC.compile_pattern(self.NOTIN_PATTERN)

    def transform(self, node, results):
        """Returns what the above should be replaced with.

        This is called by the fixer.  Whatever this returns will be replaced
        into the node.

        """
        method = results['method'][0].value

        if "\n" in str(node) and "#" in str(node):
            # Bail on inline comments. We don't know what to do.
            return None

        if method in ('assertTrue', 'assert_'):
            # Replace with a simple assert.
            return assertion(results['one'], results.get('two'), prefix=node.prefix)
        if method == 'assertFalse':
            in_results = {}
            # Handle "self.assertFalse(a in b)" -> "assert a not in b"
            if self.in_pattern.match(results['one'], in_results):
                return assert_comparison(in_results['a'], NOT_IN, in_results['b'],
                                         results.get('two'), prefix=node.prefix)
            # Handle "self.assertFalse(a not in b)" -> "assert a in b"
            if self.notin_pattern.match(results['one'], in_results):
                return assert_comparison(in_results['a'], IN, in_results['b'],
                                         results.get('two'), prefix=node.prefix)

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