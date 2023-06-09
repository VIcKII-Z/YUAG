#!/usr/bin/env python
"""
runserver.py
"""
from sys import exit, stderr
import argparse

from yuag import app

def main():
    """
    Main function
    """
    parser = argparse.ArgumentParser(description='The YUAG search application')
    parser.add_argument('port', type=int, help='the port at which the server should listen')
    args = parser.parse_args()

    try:
        assert args.port > 0 and args.port < 65536, 'port must be in range 1-65535'
        app.run(host='0.0.0.0', port=args.port, debug=True)
    except AssertionError as ex:
        print(ex, file=stderr)
        exit(1)
    except ValueError as ex:
        print(ex, file=stderr)
        exit(1)


if __name__ == '__main__':
    main()
