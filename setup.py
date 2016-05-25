from setuptools import find_packages, setup

setup(
    name="dbx-unittest2pytest",
    version="1.0",
    description='Convert unittest asserts to pytest rewritten asserts',
    keywords='unittest pytest dropbox',
    license='Apache License 2.0',
    author='Nipunn Koorapati, David Euresti',
    author_email='nipunn@dropbox.com, david@dropbox.com',
    packages=find_packages(exclude=['tests']),
    url='https://github.com/dropbox/dbx-unittest2pytest',
    zip_safe=False,

    entry_points={
        'console_scripts': ['dbx-unittest2pytest=dbx_unittest2pytest.main:main'],
    },

    install_requires=[],
)
