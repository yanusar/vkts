#! /usr/bin/env python3

import os, shutil

def remove(name):
    if os.path.isfile(name):
        os.remove(name)
    elif os.path.isdir(name):
        shutil.rmtree(name)

# Run testing
os.chdir('tests')
os.system('pytest -vv -s $@')

# Delete a garbage data
for name in ('.vkts', '.vklib.vkreq.log', 'responses_file',
             '.mock_request_responses.json'):
    remove(name)
os.chdir(os.path.pardir)
remove('.pytest_cache')

