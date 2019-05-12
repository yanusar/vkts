#! /usr/bin/env python3

"""Realisation of API requests to vk.com. For single request use
`apply_vk_method`. For speedup you can use class `Executor`, wich pack
many requests to packs by 25 requests."""

import urllib.request, json, time, os, getpass
from . import vkauth
from vkts.usrdata import UsrData
import logging
from logging.handlers import RotatingFileHandler

# Adjust logging
handler = RotatingFileHandler(".vklib.vkreq.log", mode='a',
                              maxBytes=1024*1024*10, backupCount=1)
handler.setFormatter(logging.Formatter("%(asctime)s vkreq: %(message)s"))
handler.setLevel(logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

_token = None
mock_responses = '.mock_request_responses.json'

def update_token():
    """Read token from local user data or get new one from vk.com"""

    global _token
    u = UsrData()

    # For first call
    if not _token:
        # Try read token from the previous run
        ac_name, ac_obj = u.get_active_obj('acc', 'vk')
        _token = ac_obj['token']
        if _token:
            logger.debug("Token is read")
            return

    # Get token by request
    _token = None
    attempts = 5
    attempt_pause = 10
    while not _token and attempts > 0:

        # Wait for sparse requests
        if attempts < 5:
            logger.debug("Attempt pause %s", attempt_pause)
            time.sleep(attempt_pause)
            attempt_pause *= 2
        attempts -= 1

        # Request
        logger.debug("Try to get token")
        ac_name, ac_obj = u.get_active_obj('acc', 'vk')
        email = ac_obj['uname']
        pswd = ac_obj['password']
        while not pswd:
            pswd = getpass.getpass('Input password of vk account'
                                   + ' «{}»: '.format(ac_name))
        user_auth = vkauth.VKAuth(permissions = ['friends',
                                                 'groups',
                                                 'wall'],
                                  app_id = '6471192',
                                  api_v = '5.74',
                                  email = email,
                                  pswd = pswd)
        user_auth.auth()
        _token = user_auth._access_token

    # Here token must be
    if _token == None:
        logger.debug("Failed to get token")
        raise

    # Dump token (if account isn't private)
    if ac_obj['password']:
        u.set(_token, 'acc', 'vk', ac_name, 'token')
    logger.debug("Token is updated")

def _make_params_string(**params):
    """Convert list of parameters to string"""

    # Add token & version (if user doesn't give specific this)
    if 'access_token' not in params:
        params['access_token'] = _token
    if 'v' not in params:
        params['v'] = '5.9'

    p_str = '&'.join(['{}={}'.format(f, urllib.parse.quote(str(params[f])))
                      for f in params.keys()])
    return p_str

def _short_print(s):
    # shrink output if it's too long
    if len(s) <= 500:
        print(s)
    else:
        print('{}  ......  {}'.format(s[:245], s[-245:]))

def _vk_api_error_print(obj, url_of_req, p_str):
    print("vk API error code: {}".format(obj['error_code']))
    print(obj['error_msg'])
    _short_print("Broken request: {}{}".format(url_of_req, p_str))

def _vk_api_request(url_of_req, method, p_str):
    """Request (can be mocked by existence of file
    '.mock_request_responses.json' for testing)."""

    if os.path.isfile(mock_responses):

        # "Home-made" mock
        logger.debug("Try Mocked Request (method: %s)", method)
        with open(mock_responses) as fp:
            mocks_list = json.load(fp)
            json_obj = mocks_list.pop(0)
        with open(mock_responses, 'w') as fp:
            json.dump(mocks_list, fp)

    else:

        # Real request
        logger.debug("Try Request (method: %s)", method)
        req = urllib.request.Request(url_of_req + '%s',
                                     data=p_str.encode("ascii"))
        with urllib.request.urlopen(req) as response:
            the_page = response.read().decode("utf-8")
        json_obj = json.loads(the_page)

    return json_obj

def apply_vk_method(method, handle_api_errors=True, **params):
    """Make request to https://api.vk.com/method/. Return JSON-object"""

    global _token

    # Get token if absent
    if not _token and not os.path.isfile('.mock_request_responses.json'):
        update_token()

    # Set token to URL string
    url_of_req = 'https://api.vk.com/method/' + method + '?'
    p_str = _make_params_string(**params)

    # Do request with error processing
    error_pause = 5
    while True:

        try:
            # Request
            json_obj = _vk_api_request(url_of_req, method, p_str)
        except:
            # In case of network problems.
            logger.debug("Request Error")
            _short_print("Broken request: {}{}".format(url_of_req, p_str))
            if error_pause > 35:
                raise
            print('Wait ' + str(error_pause) + ' seconds')
            time.sleep(error_pause)
            error_pause += 5
            continue

        # Process response
        if 'error' in json_obj:
            logger.debug("API Error (%s: %s)", json_obj['error']['error_code'],
                         json_obj['error']['error_msg'])
            if json_obj['error']['error_code'] == 5:
                if 'access_token' in params:
                    del params['access_token']
                update_token()
                p_str = _make_params_string(**params)
                continue
            elif json_obj['error']['error_code'] == 6:
                # It took a long time to create a "clever" mechanism to bypass
                # these errors. However, such a stupid solution was the most
                # effective.
                time.sleep(0.5)
                continue
            elif not handle_api_errors:
                return json_obj
            elif json_obj['error']['error_code'] == 18:
                # Page is deleted or banned
                return {}
            elif (json_obj['error']['error_code'] == 203
                  or json_obj['error']['error_code'] == 7):
                # No have access
                return {}
            elif json_obj['error']['error_code'] == 12:
                # execute compilation error
                _vk_api_error_print(json_obj['error'], url_of_req, p_str)
                return {}
            elif json_obj['error']['error_code'] == 14:
                # Captcha needed
                _vk_api_error_print(json_obj['error'], url_of_req, p_str)
                return json_obj # to study the response format in the future
            elif json_obj['error']['error_code'] in (3, 8, 100, 113):
                # Wrong rquest
                _vk_api_error_print(json_obj['error'], url_of_req, p_str)
                return {}
            else:
                # In case of server problems.
                _vk_api_error_print(json_obj['error'], url_of_req, p_str)
                if error_pause > 35:
                    raise
                print('Wait ' + str(error_pause) + ' seconds')
                time.sleep(error_pause)
                error_pause += 5
                continue

        # No errors -> out loop
        logger.debug("Successful Request")
        break

    return json_obj

class Executor:
    """Class for exploit vk API method `execute` to join
    several requests (up to 25) into single one.
    If > 25 requests are added by `add_request`, then > 1 requests
    of `execute` will be executed by `emit_requests`.

    Example:
    >>> e = Executor()
    >>> e.add_request('utils.resolveScreenName', screen_name='phys_kek')
    >>> e.add_request('utils.resolveScreenName_', screen_name='phys_kek')
    >>> e.add_request('users.getFollowers', **{'user_id': '1'})
    >>> e.emit_requests()
    >>> e.responses[0]['object_id'], e.responses[1], e.responses[2]['count']
    (111557607, [], 5909523)

    More tricky way - use parameter `processor` of `Executor.add_request()`:
    >>> e = Executor()
    >>> f = lambda r: print(r['object_id'] if r else "False")
    >>> for name in ['phys_kek', 'unreal-_-', 'drec_mipt']:
    >>>     e.add_request('utils.resolveScreenName', f, screen_name=name)
    >>> e.emit_requests()
    111557607
    False
    17708"""

    def __init__(self):
        logger.debug("Executor created")
        self.responses = []
        self.errors = []
        self.requests = []
        self.processors = []

    def add_request(self, method, processor=None, **params):
        """Add one request to `Executor.requests`.
        `processor` - function for processing response of this request"""

        logger.debug("Add %sth request %s", len(self.requests) + 1,
                     "with processor" if processor else "without processor")

        # add string request to requests list
        params_s = str(params).replace("'", '"')
        self.requests.append('API.{}({});'.format(method, params_s))
        self.processors.append(processor)

    def emit_requests(self):
        """Pack requests from `Executor.requests` (see `Executor.add_request()`)
        into `execute` requests and emit them to server. Responses will be saved
        in `Executor.responses`."""

        logger.debug("Emit requests (%s pieces)", len(self.requests))
        self.responses = []
        self.errors = []

        requests = self.requests
        cnt = 0
        while requests:

            # start code for execute
            if cnt == 0:
                code = 'var arr = [];\n' + \
                       'var r;\n'

            # collect requests
            req = requests.pop(0)
            code += 'r = {}\n'.format(req) + \
                    'arr = arr + [r];\n'

            # step - recorded regular request
            cnt += 1

            # check for maximum requests to execute
            if cnt == 25:

                # complete code
                code += 'return arr;'
                r = apply_vk_method('execute', **{'code': code})

                # save responses
                self.responses += r['response']
                if 'execute_errors' in r:
                    self.errors += r['execute_errors']

                # process responses
                while cnt:
                    func = self.processors.pop(0)
                    if func:
                        func(r['response'][-cnt])
                    cnt -= 1

        # make last execute if need
        if cnt:

            # complete code
            code += 'return arr;'
            r = apply_vk_method('execute', **{'code': code})

            # save responses
            self.responses += r['response']
            if 'execute_errors' in r:
                self.errors += r['execute_errors']

            # process responses
            while cnt:
                func = self.processors.pop(0)
                if func:
                    func(r['response'][-cnt])
                cnt -= 1

        self.requests = []
        self.processors = []

