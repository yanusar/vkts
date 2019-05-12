#! /usr/bin/env python3

"""The most common interfaces"""

import sys, traceback

def exception_handler(msg=None):

    # print stack
    traceback.print_exc()

    # print message if need
    if msg:
        print()
        print(msg)

    # exit if not interpreter mode enabled
    try:
        sys.exit()
    except:
        pass

