import sys

from lib2to3.main import main as lib_main

def main():
    sys.exit(lib_main("unittest2pytest"))

if __name__ == '__main__':
    main()
