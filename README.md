# unittest2pytest

Convert unittest asserts to pytest rewritten asserts.

py.test supports advanced assertion introspection, allowing it to provide more detailed error messages.
https://pytest.org/latest/assert.html#advanced-assertion-introspection

Check out this blog post detailing how it works.
http://pybites.blogspot.ie/2011/07/behind-scenes-of-pytests-new-assertion.html

# What's the advantage?

Before:
```python
test/test_login.py:80: in test
    self.assertEquals(login.call_count, 1)
E   AssertionError: 0 != 1
    assert login.call_count == 1
```
After:
```python
test/test_login.py:80: in test
E   AssertionError: assert 0 == 1
E    +  where 0 = <MagicMock name='mock.desktop_login.login' id='140671857679512'>.call_count
```

# What happens to my code?

Before:
```python
self.assertEqual(a, b)
self.assertEqual(a, None)
self.assertFalse(a)
```
After:
```python
assert a == b
assert a is None
assert not a
```

See unit tests for many more examples.

# Usage
Coming soon

# Contributing
Contributions are welcome. Tests can be run with [tox][tox]. Lint with [flake8][flake8]

#Issues
If you encounter any problems, please [file an issue][issues] along with a detailed description.

[flake8]: https://flake8.readthedocs.org/en/latest/
[issues]: https://github.com/dropbox/unittest2pytest/issues
[tox]: https://tox.readthedocs.org/en/latest/
