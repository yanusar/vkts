#! /usr/bin/env python3

import os
import shutil
import sys


def remove(name):
    if os.path.isfile(name):
        os.remove(name)
    elif os.path.isdir(name):
        shutil.rmtree(name)


# Output: is envirement usual (host) or virtual (created by virtualenv for e.g)
try:
    from colorama import init, Fore, Style
    init()
    if hasattr(sys, 'real_prefix'):
        print(Fore.GREEN + 'VIRTUAL ENVIRONMENT IS ENABLED' + Style.RESET_ALL)
    else:
        print(Fore.RED + 'HOME ENVIRONMENT IS ENABLED' + Style.RESET_ALL)
except Exception:
    if hasattr(sys, 'real_prefix'):
        print('VIRTUAL ENVIRONMENT IS ENABLED')
    else:
        print('HOME ENVIRONMENT IS ENABLED')

# Run testing
os.chdir('tests')
os.system('pytest -vv -s $@')

# Delete a garbage data
for name in ('.vkts', '.vklib.vkreq.log', 'responses_file',
             '.mock_request_responses.json'):
    remove(name)
os.chdir(os.path.pardir)
remove('.pytest_cache')
