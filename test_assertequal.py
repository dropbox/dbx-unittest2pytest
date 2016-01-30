from lib2to3.tests.test_fixers import FixerTestCase

class TestFixAssertEqual(FixerTestCase):
    def setUp(self):
        super(TestFixAssertEqual, self).setUp(
            fix_list=["assertequal"],
            fixer_pkg="unittest2pytest",
        )

    def test_assert_equal_basic(self):
        self.check("self.assertEqual(55, 66)", "assert 55 == 66")
        self.check("self.assertEquals(55, 66)", "assert 55 == 66")
        self.check("self.assertEquals(55, 66,)", "assert 55 == 66")

    def test_assert_notEqual_basic(self):
        self.check("self.assertNotEqual(55, 66)", "assert 55 != 66")
        self.check("self.assertNotEquals(55, 66)", "assert 55 != 66")

    def test_assert_equal_msg(self):
        self.check("self.assertEqual(55, 66, 'Message')", "assert 55 == 66, 'Message'")
        self.check("self.assertEqual(55, 66, 'Message',)", "assert 55 == 66, 'Message'")

    def test_assert_equal_msg_kwd(self):
        self.check("self.assertEqual(55, 66, msg='Message')", "assert 55 == 66, 'Message'")

    def test_assert_true_false(self):
        self.check("self.assert_(obj)", "assert obj")
        self.check("self.assertTrue(obj)", "assert obj")
        self.check("self.assertTrue(obj,)", "assert obj")
        self.check("self.assertFalse(obj)", "assert not obj")
        # This could be better as "assert a not in b", but this is also correct
        self.check("self.assertFalse(a in b)", "assert not a in b")

    def test_assert_equal_true_false(self):
        self.check("self.assertEquals(obj, True)", "assert obj")
        self.check("self.assertEqual(obj, False)", "assert not obj")
        self.check("self.assertEquals(True, obj)", "assert obj")
        self.check("self.assertEqual(False, obj)", "assert not obj")

    def test_assert_equal_none(self):
        self.check("self.assertEqual(None, obj)", "assert None is obj")
        self.check("self.assertEquals(obj, None)", "assert obj is None")

    def test_assert_is_none(self):
        self.check("self.assertIsNone(obj)", "assert obj is None")

    def test_assert_is_not_none(self):
        self.check("self.assertIsNotNone(obj)", "assert obj is not None")

    def test_comparisons(self):
        comp_map = {
            'assertGreater': '>',
            'assertGreaterEqual': '>=',
            'assertLess': '<',
            'assertLessEqual': '<=',
            'assertIn': 'in',
            'assertNotIn': 'not in',
            'assertIs': 'is',
            'assertIsNot': 'is not',
        }

        for method, comp in comp_map.items():
            self.check("self.%s(obj1, obj2)" % method, "assert obj1 %s obj2" % comp)

    def test_assert_equal_multiline(self):
        b = """self.assertEqual(
            True == False,
            False == True,
            "Multiline"
        )
        """
        a = """assert (True == False) == \\
            (False == True), \\
            "Multiline"
        """
        self.check(b, a)

    def test_assert_equal_multiline_trailing_comma(self):
        b = """self.assertEqual(
            True == False,
            False == True,
            "Multiline",
        )
        """
        a = """assert (True == False) == \\
            (False == True), \\
            "Multiline"
        """
        self.check(b, a)

    def test_assert_equal_parenthesize(self):
        b = """self.assertEquals(
            5 in [1, 2, 3],
            6 in [4, 5, 6],
            "Parenthesize",
        )
        """
        a = """assert (5 in [1, 2, 3]) == \\
            (6 in [4, 5, 6]), \\
            "Parenthesize"
        """
        self.check(b, a)

    def test_dont_parenthesize_array(self):
        b = "self.assertEquals('DontParenthesize', [1, 2, 3, 4])"
        a = "assert 'DontParenthesize' == [1, 2, 3, 4]"
        self.check(b, a)
