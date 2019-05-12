#! /usr/bin/env python3

"""Working with groups and users in vk"""

import sys, json, os, time
from .vkreq import apply_vk_method, Executor
from vkts.utils import exception_handler

def _mkdir_rec(*dir_chain):
    """Recursive mkdir. For example, use `_mkdir_rec('a', 'b', 'c')` to create
    directory 'a/b/c'. Directories 'a' and 'b' will be created too if need"""
    path = ''
    for name in dir_chain:
        path += (name + os.path.sep)
        if not os.path.isdir(path):
            os.mkdir(path)
    return path

class VKObj():
    """Superclass for vk objects"""

    def __repr__(self):
        """Universal verbose view of class instance"""

        # class name
        repr_ = '[{}]\n'.format(self.__class__.__name__)

        # walk through attached fields of class instance
        d = self.__dict__
        keys = sorted(list(d.keys()))
        for key in keys:

            # field name
            repr_ += '{}: '.format(key).ljust(18)

            # empty case
            val = d[key]
            if not val:
                repr_ += '\n'
                continue

            # field value
            if isinstance(val, list) or isinstance(val, tuple):

                # items view
                if len(str(val[0]) + str(val[0])) < 30:
                    val_str = str(val)
                else:
                    val_str = '[{}]'.format(val[0].__class__.__name__)

                # items type, length
                val_str += ' len {}'.format(len(val))

                # if there are repetitions, output unique elements number
                try:
                    uniq_length = len(set(val))
                    if uniq_length != len(val):
                        val_str += ', uniq items {}'.format(uniq_length)
                except:
                    pass

            elif isinstance(val, dict):
                # {int} len N
                random_item = next(iter(val.values()))
                val_str = '{{{}}} len {}'.format(random_item.__class__.__name__,
                                                 len(val))

            else:
                # simple value
                val_str = '{}'.format(val)

            # shrink if need
            if len(val_str) > 52:
                val_str = '{}  ....  {}'.format(val_str[:22], val_str[-22:])

            repr_ += val_str + '\n'

        return repr_

    def dump(self, rewrite=False):
        """Save data about object"""

        # add date to object
        date = time.strftime("%F-%H%M%S")
        self.dump_date = date

        # dump data
        dir_path = _mkdir_rec('data', 'obj', self.__class__.__name__)
        file_path = os.path.join(dir_path, self._get_key())
        if rewrite or not os.path.isfile(file_path):
            with open(file_path, 'w') as fp:
                json.dump(self.__dict__, fp)
        else:
            old_version = json.load(open(file_path))
            old_version.update(self.__dict__)
            with open(file_path, 'w') as fp:
                json.dump(old_version, fp)

    def dump_to_frozen(self):
        """Save data about object"""

        # add date to object
        date = time.strftime("%F-%H%M%S")
        self.dump_date = date

        # dump data
        dir_path = _mkdir_rec('data', 'frozen_obj', self.__class__.__name__)
        date = '_' + date
        with open(os.path.join(dir_path, self._get_key() + date), 'w') as fp:
            json.dump(self.__dict__, fp)

    def open(self):
        """Restore data of object from data/obj/../"""

        # get path to object
        path = os.path.join('data', 'obj', self.__class__.__name__,
                            self._get_key())
        if not os.path.isfile(path):
            return

        # read object
        with open(path) as fp:
            obj = json.load(fp)
        for field in obj:
            setattr(self, field, obj[field])

    def open_last_frozen(self):
        """Restore recent data of object from data/frozen_obj/../"""

        # get path to recent object
        dir_path = os.path.join('data', 'frozen_obj', self.__class__.__name__)
        if not os.path.isdir(dir_path):
            return
        files = next(os.walk(dir_path))[2]
        files = [x for x in files if x.startswith(self._get_key() + '_')]
        if not files:
            return
        obj_path = os.path.join(dir_path, sorted(files)[-1])

        # read object
        with open(obj_path) as fp:
            obj = json.load(fp)
        for field in obj:
            setattr(self, field, obj[field])

# Check user for existance university of univer_ids in list of his universities
def _is_student(user_item, univer_ids):
    """Does the user profile indicate that he studied at a university?"""

    # field universities
    if 'universities' in user_item:
        for i in user_item['universities']:
            if i['id'] in univer_ids:
                return True

    # field occupation
    if 'occupation' in user_item:
        occ = user_item['occupation']
        if occ['type'] == 'university':
            if occ['id'] in univer_ids:
                return True

    return False

class Group(VKObj):
    """A class containing information about the community and a list of
    its members.

    The easiest and fastest way to upload information - use `Group.load()`.
    For fast loading of many small communities use outclass function
    `load_groups`."""

    def __init__(self, group_id):

        if not str(group_id).isdigit():
            print('Wrong group_id {}. It should be digital'.format(group_id))
            return

        # Init
        self.group_id = str(group_id)
        self.count = 0
        self.members = []
        self.cumul_members = [] # cumulative list of former & current members
        self.univers_data = {}

    def _get_key(self):
        """Key for dump"""
        return self.group_id

    def load(self, extra_getById=()):
        """Load from vk.com initial community information
        and full list of community member's ids"""

        # load phase 0
        e = Executor()
        self.load_ph0_fill_requests(e, extra_getById)
        for i in range(1000, 24000, 1000):
            e.add_request('groups.getMembers',
                          self.load_ph1_parse,
                          group_id=self.group_id, offset=i, count=1000)
        e.emit_requests()

        # load phase 1
        if self.count > 24000:
            for i in range(24000, self.count, 1000):
                e.add_request('groups.getMembers',
                              self.load_ph1_parse,
                              group_id=self.group_id, offset=i, count=1000)
            e.emit_requests()

        # update cumulative data
        self.update_cumulative()

    def update_cumulative(self):
        """If we read the data locally (`Group.open()`), and then received
        the current data from the server (`Group.load()` or `load_groups`),
        we combine the new data with the old ones and save in special fields
        of \"cumulative\" data."""
        self.cumul_members = list(set(self.cumul_members + self.members))

    def load_ph0_fill_requests(self, executor, extra_getById=()):
        """Add to executor 1 request groups.getById and 1 request
        groups.getMembers for getting initial vk community information and
        ids of first 1000 members.

        `executor` - object of class `Executor`
        `extra_getById` - additional fields you can specify
                          for vk API method getById"""

        # temporarily save, Group.load_ph0_parse will remove it
        self.extra_getById = extra_getById

        fields_s = ','.join(('description',) + extra_getById)
        executor.add_request('groups.getById',
                             self.load_ph0_parse,
                             group_id=self.group_id, fields=fields_s)
        executor.add_request('groups.getMembers',
                             self.load_ph0_parse,
                             group_id=self.group_id, offset=0, count=1000)

    def load_ph0_parse(self, response):
        """Processor for response of `Group.load_ph0_fill_requests()`"""

        # check and prepare response to read
        if not response:
            return
        if isinstance(response, list):
            response = response[0]

        # remove temporary fields list
        if hasattr(self, 'extra_getById'):
            extra_getById = self.extra_getById
            del self.extra_getById
        else:
            extra_getById = ()

        # save data
        for field in ('screen_name', 'count', 'name', 'description',
                      'photo_200') + extra_getById:
            if field in response:
                setattr(self, field, response[field])
        if 'items' in response:
            self.members = response['items']

    def load_ph1_fill_requests(self, executor):
        """Add to executor requests groups.getMembers for getting
        full list of community member's ids"""

        if not hasattr(self, 'count'):
            return
        for i in range(1000, self.count, 1000):
            executor.add_request('groups.getMembers',
                                 self.load_ph1_parse,
                                 group_id=self.group_id, offset=i, count=1000)

    def load_ph1_parse(self, response):
        """Processor for response of `Group.load_ph1_fill_requests()`"""

        if not response:
            return

        # save data
        if 'items' in response:
            self.members += response['items']

    def load_students(self, university):
        """If you have already executed `Group.load()` you can to get
        a separate list of students in this group.
        Result will be saved in `Group.univers_data`"""

        # make auxiliary class instance add put into it old data if they are
        univer = _UniversityInGroup(university.ids)
        if university.name in self.univers_data:
            for f in univer.__dict__.keys():
                if f != 'students':
                    setattr(univer, f, self.univers_data[university.name][f])

        # load
        e = Executor()
        univer.load_students_fill_requests(e, self)
        e.emit_requests()

        # update cumulative data
        univer.cumul_students = list(set(univer.cumul_students
                                         + univer.students))

        # calc share of students in community
        univer.univer_fraction = len(univer.students)/len(self.members)

        # Save data
        self.univers_data[university.name] = {}
        for f in univer.__dict__.keys():
            self.univers_data[university.name][f] = getattr(univer, f)

    def __repr__(self):

        # main information
        repr_ = VKObj.__repr__(self)

        # universities information
        for uname in self.univers_data:

            # make auxiliary class instance and fill it
            univer = _UniversityInGroup()
            for f in self.univers_data[uname]:
                 setattr(univer, f, self.univers_data[uname][f])
            setattr(univer, 'name', uname)

            # get usual class representation and format it a bit
            lines = VKObj.__repr__(univer)
            lines = lines[:-1].replace('\n', '\n    ')
            lines = lines.replace('[_UniversityInGroup]', '[UniverData]')

            # add to class instance representation
            repr_ += '\n    {}\n'.format(lines)

        return repr_

    def is_empty(self):
        return self.count == 0

class _UniversityInGroup():
    """Auxiliary class for `Group.load_students()` and `Group.__repr__()`"""

    def __init__(self, university_ids=[]):
        self.univer_ids = university_ids
        self.students = []
        self.cumul_students = []
        self.univer_fraction = 0.

    def load_students_fill_requests(self, executor, group):
        """Add to executor request for `Group.load_students()`"""

        # Limiting the server to the length of the request does not allow
        # making a step of 1000 (the maximum allowed by api) requests.
        # But it does not matter: the critical limitation of method users.get
        # is it's runtime on the server.
        step = 500

        for i in range(0, group.count, step):
            user_ids_s = ','.join(map(str, group.members[i:i+step]))
            executor.add_request('users.get',
                                 self.load_students_parse,
                                 user_ids=user_ids_s,
                                 fields='universities,occupation')

    def load_students_parse(self, response):
        """Process to executor request for `Group.load_students()`"""

        if not response:
            return

        # save data
        usr_objs = [x for x in response if _is_student(x, self.univer_ids)]
        self.students += [x['id'] for x in usr_objs]

def load_groups(groups, extra_getById=()):
    """Fast load groups data thanks to vk api method `execute`.
    `groups` - list of objects of `Group` class"""

    e = Executor()

    # load phase 1
    for g in groups:
        g.load_ph0_fill_requests(e, extra_getById)
    e.emit_requests()

    # load phase 2
    for g in groups:
        g.load_ph1_fill_requests(e)
    e.emit_requests()

    # update cumulative data
    for g in groups:
        g.update_cumulative()

class University(VKObj):
    """A class containing information about the university"""

    def __init__(self, name, ids=[]):

        try:
            # check name
            if not name.islower():
                raise
            for ch in name:
                if not ch in 'abcdefghijklmnopqrstuvwxyz_0123456789':
                    raise

            # init data
            self.name = name
            self.ids = list(map(int, ids))

        except:
            exception_handler('Invalid character in university name: '
                              + '"{}"'.format(ch))

    def _get_key(self):
        """Key for dump"""
        return self.name

class User(VKObj):
    """TODO: rewrite like Group"""

    def __init__(self, user_id, univer_ids = []):

        # Assert
        if type(user_id) != int:
            print('Wrong type of user id: ' + str(user_id)
                  + ' (must be \'str\')')
            sys.exit()

        # Init
        self.user_id = user_id
        self.count = 0
        self.friends = []
        # for univer friends:
        self.univer_ids = univer_ids
        self.univer_friends = [] # university membership is listed in account
        self.univer_degree = 0. # len(univer_friends)/len(friends)
        # other data:
        self.is_student = False
        self.photo_max = ''
        self.first_name = ''
        self.last_name = ''
        self.nickname = ''
        self.scrname = ''
        self.byear = 0 # year of birthday
        self.sex = 0 # like in vk API: 0 - unknown, 1 - female, 2 - male
        # flag of relevance
        self.is_relevant = False

    def load_info(self):

        # Getting main info about user
        response = apply_vk_method('users.get',
                                   user_id=str(self.user_id),
                                   fields='universities,occupation,photo_max,'
                                          + 'screen_name,nickname,bdate,sex')
        if response:
            self.is_student = _is_student(response['response'], self.univer_ids)
            if response['response']['photo_max']:
                self.photo_max = response['response']['photo_max']
            else:
                self.photo_max = 'https://vk.com/images/camera_200.png?ava=1'
            self.first_name = response['response']['first_name']
            self.last_name = response['response']['last_name']
            if response['response']['nickname']:
                self.nickname = response['response']['nickname']
            self.scrname = response['response']['scrname']
            if response['response']['bdate']:
                bdate = response['response']['bdate']
                if len(bdate.split('.')) == 3:
                    self.byear = int(bdate.split('.')[2])
            self.sex = int(response['response']['sex'])
        else:
            return

        # Getting count and first 5000 friends
        response = apply_vk_method('friends.get', user_id=str(self.user_id),
                                   offset=0, count=5000,
                                   fields='universities,occupation')
        if response:
            self.count = response['response']['count']
            users = response['response']['items']
        else:
            return

        # Getting the remaining friends
        for i in range(1, int((self.count-1)/5000) + 1):
            response = apply_vk_method('friends.get', user_id=str(self.user_id),
                                       offset=i*5000, count=5000,
                                       fields='universities,occupation')
            if bool(response):
                users += response['response']['items']

        self.friends = [x['id'] for x in users]
        self.univer_friends = \
            [x['id'] for x in users if _is_student(x, self.univer_ids)]
        try:
            self.univer_degree = len(self.univer_friends) / len(self.friends)
        except ZeroDivisionError:
            self.univer_degree = 0
        self.is_relevant = True

        # During the download, the composition of the group could change
        self.count = len(self.friends)

    def get_json_repr(self):
        return {
            'user_id': self.user_id,
            'count': self.count,
            'friends': self.friends,
            'univer_ids': self.univer_ids,
            'univer_friends': self.univer_friends,
            'univer_degree': self.univer_degree,
            'is_student': self.is_student,
            'photo_max': self.photo_max,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'nickname': self.nickname,
            'scrname': self.scrname,
            'byear': self.byear,
            'sex': self.sex,
            'is_relevant': self.is_relevant}

    def save_info(self):
        if not os.path.isdir('data/users'):
            os.mkdir('data/users')
        with open('data/users/' + str(self.user_id), 'w') as f:
            json.dump(self.get_json_repr(), f)

    def is_info(self):
        return os.path.isfile('data/users/' + str(self.user_id))

    def read_info(self):
        if not self.is_info():
            print('Info about user ' + str(self.user_id) + ' is absent')
            raise
        with open('data/users/' + str(self.user_id), 'r') as f:
            json_repr = json.load(f)
        self.user_id = json_repr['user_id']
        self.count = json_repr['count']
        self.friends = json_repr['friends']
        self.univer_ids = json_repr['univer_ids']
        self.univer_friends = json_repr['univer_friends']
        self.univer_degree = json_repr['univer_degree']
        self.is_student = json_repr['is_student']
        self.photo_max = json_repr['photo_max']
        self.first_name = json_repr['first_name']
        self.last_name = json_repr['last_name']
        self.nickname = json_repr['nickname']
        self.scrname = json_repr['scrname']
        self.byear = json_repr['byear']
        self.sex = json_repr['sex']
        self.is_relevant = json_repr['is_relevant']

    def load_and_save_info_if_absent(self):
        if not self.is_info():
            self.load_info()
            self.save_info()
        else:
            self.read_info()
            if not self.is_relevant:
                self.load_info()
                self.save_info()

    def is_empty(self):
        return self.count == 0
