# dbx-unittest2pytest [![Build Status](https://travis-ci.org/dropbox/unittest2pytest.svg?branch=master)](https://travis-ci.org/dropbox/unittest2pytest)

## Warning: this is not the official unittest2pytest!

Dropbox developed this package in parallel with (what became) the official `pytest-dev` package `unittest2pytest`, that
has the same name and does the same thing. It's the one that has the name `unittest2pytest` on PyPI, and it can convert
a few more assertions. Check it out [on Github](https://github.com/pytest-dev/unittest2pytest) or
[on PyPI](https://pypi.python.org/pypi/unittest2pytest). We've since renamed the project dbx-unittest2pytest to avoid confusion

# Description

Convert unittest asserts to pytest rewritten asserts.

py.test supports advanced assertion introspection, allowing it to provide more detailed error messages.
https://pytest.org/latest/assert.html#advanced-assertion-introspection

Check out this blog post detailing how it works.
http://pybites.blogspot.ie/2011/07/behind-scenes-of-pytests-new-assertion.html

tl;dr
If you are using py.test, then "assert a == b" is better than "self.assertEqual(a, b)"

# What's the advantage?

Pytest output before:
```
test/test_login.py:80: in test
    self.assertEquals(login.call_count, 1)
E   AssertionError: 0 != 1
    assert login.call_count == 1
```
Pytest output after:
```
test/test_login.py:80: in test
E   AssertionError: assert 0 == 1
E    +  where 0 = <MagicMock name='mock.desktop_login.login' id='140671857679512'>.call_count
```

# What happens to my test code?

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
```
dbx-unittest2pytest --help
dbx-unittest2pytest --fix=asserts <filename/dirnames>
```
Run 4x parallel.
```
dbx-unittest2pytest --fix=asserts -j4 [filename/dirnames]
```
Write back to original files.
```
dbx-unittest2pytest --fix=asserts -w [filename/dirnames]
```

# Contributing
Contributions are welcome. Tests can be run with [tox][tox]. Lint with [flake8][flake8]
You'll have to agree to Dropbox's [CLA][CLA].

#Issues
If you encounter any problems, please [file an issue][issues] along with a detailed description.

[flake8]: https://flake8.readthedocs.org/en/latest/
[issues]: https://github.com/dropbox/dbx-unittest2pytest/issues
[tox]: https://tox.readthedocs.org/en/latest/
[CLA]: https://opensource.dropbox.com/cla/
