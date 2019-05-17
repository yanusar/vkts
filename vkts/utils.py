#! /usr/bin/env python3

"""The most common interfaces"""

import sys, traceback, os, __main__
from time import sleep

def is_py_interactive():
    return not hasattr(__main__, '__file__')

def exception_handler(e, msg=None):

    # print stack
    if not isinstance(e, SystemExit):
        traceback.print_exc()

    # print message if need
    if msg:
        print('\n{}\n'.format(msg))

    # exit if not interpreter mode enabled
    if (not isinstance(e, SystemExit)
        and not is_py_interactive()):
        # then
        sys.exit()

