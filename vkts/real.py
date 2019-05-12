#! /usr/bin/env python3

"""Implementation of the main functions of the application: editing user data,
thematic search, other console commands"""

import sys, re
from collections import Counter
from vkts.report import Report
import vkts.vklib as vk
from vkts.vklib import apply_vk_method
from vkts.usrdata import UsrData
from vkts.utils import exception_handler

####################################################################
##                        Account commands                        ##
####################################################################

def add_account():
    """Interactive function of account adding"""

    try:
        # Read data about account

        # Account type
        in_str = input('What type of account do you want to create?\n'
                       + 'Input please one letter - [e]mail, [v]k.ru\n'
                       + 'or [t]elegram: ').lower()
        ac_type = {'e':'email', 'v':'vk', 't':'telegram'}[in_str]

        # Account name
        ac_name = input('\nInput name of new account: ').lower()

        # Privacy
        print('\nAre your account fake (password will be stored\n'
              + 'unencrypted on your computer) or private (you\n'
              + 'will be forced to enter the password every run)?')
        in_str = input('Input please [f]ake or [p]rivate: ').lower()
        ac_privacy = {'f':'fake', 'p':'private'}[in_str]

        # User name
        if ac_type == 'email' or ac_type == 'vk':
            ac_user_name = input('\nInput email address: ')
        elif ac_type == 'telegram':
            ac_user_name = input('\nInput nickname: ').lstrip('@')
        else:
            raise

        # Password (it's fake account, so we don't use smth. like getpass)
        if ac_privacy == 'fake':
            ac_password = input('\nInput password: ')
        else:
            ac_password = None

        # Save account data
        acc_obj = {'uname': ac_user_name,
                   'password': ac_password,
                   'token': None,
                   'is_activated': False}
        UsrData().set(acc_obj, 'acc', ac_type, ac_name, correct_is_act=True)

    except Exception as e:
        exception_handler('Failed to enter account data')

def delete_account(ac_type, ac_name):
    """Deletion account ac_name of type ac_type from registry"""

    UsrData().del_('acc', ac_type, ac_name, correct_is_act=True)

def activate_account(ac_type, ac_name):
    """Choose active account"""

    u = UsrData()
    if ac_name in u.get('acc', ac_type):
        u.drop_activations('acc', ac_type)
        u.set(True, 'acc', ac_type, ac_name, 'is_activated')

def display_accounts():
    """Display all accounts and active marks"""

    accs = UsrData().get('acc')
    for ac_type in accs:

        # check existance
        if not accs[ac_type]:
            continue

        # print accounts of type ac_type
        print(ac_type)
        for ac_name in accs[ac_type]:
            acc_obj = accs[ac_type][ac_name]
            print('    {}: \t[{}|{}]{}'.format(ac_name,
                                               acc_obj['uname'],
                                               acc_obj['password'],
                                               ('    \t<- activated'
                                                if acc_obj['is_activated']
                                                else '')))
        print('')

####################################################################
##                      University commands                       ##
####################################################################

# Search hot university ids by un_groups
def search_hot_university_ids(un_groups, un_ids):

    # load members of groups
    groups = [vk.Group(group_id['id']) for group_id in un_groups]
    vk.load_groups(groups)

    # unite groups members in a single users list
    users = []
    for group in groups:
        users += group.members
    users = list(set(users))

    # load education info about users
    e = vk.Executor()
    users_education = []
    for i in range(0, len(users), 500):
        ids_str = ','.join(list(map(str, users[i:i+500])))
        e.add_request('users.get', user_ids=ids_str,
                      fields='occupation,education,universities',
                      processor=users_education.extend)
    e.emit_requests()

    # Count university appearances
    un_ids_cnt = {un_id:0 for un_id in un_ids}
    for item in users_education:
        if 'university' in item:
            un_id = str(item['university'])
            if un_id in un_ids_cnt:
                un_ids_cnt[un_id] += 1
                continue
        if ('occupation' in item
            and item['occupation']['type'] == 'university'):
            # then
            un_id = str(item['occupation']['id'])
            if un_id in un_ids_cnt:
                un_ids_cnt[un_id] += 1
                continue

    # Filter out unused ids
    hot_ids = list(un_ids_cnt.items())
    hot_ids = [x for x in hot_ids if x[1] >= 10]
    hot_ids.sort(key=(lambda x: x[1]), reverse=True)
    hot_ids = [{'id': x[0], 'temp': x[1]} for x in hot_ids]

    return hot_ids

def add_university():
    """Interactive function of adding data abaot university"""

    # Read data about university
    try:

        # Name of university
        un_name = input(
              'Input please simple name of university (better in short latin;\n'
              + 'for example: mipt, msu, mgimo): \n> ')

        # Titles of university
        print('Input please all titles of university (for example:\n'
              + 'МФТИ, Физтех, MIPT). After every title press [ENTER].\n'
              + 'Finish input by [ENTER].')
        un_titles = []
        while True:
            title = input('> ')
            if not title:
                break
            un_titles.append(title)
        assert un_titles

        # Looking for a university in the vk database
        e = vk.Executor()
        for title in un_titles:
            e.add_request('database.getUniversities', q=title)
        e.emit_requests()
        un_items = []
        for r in e.responses:
            un_items.extend(r['items'])

        # Clarify the results by checking exact words match
        tmp = un_items
        un_items = []
        unique_ids = set()
        for item in tmp:

            # ensuring uniqueness of search results
            if item['id'] in unique_ids:
                continue
            unique_ids.add(item['id'])

            # check title existence
            for title in un_titles:
                for word in title.split():
                    if not re.search(r'\b' + word.lower() + r'\b',
                                     item['title'].lower()):
                        break
                else:
                    un_items.append(item)
                    break

        del tmp, unique_ids
        assert un_items

        # Ask the user to clarify the results
        print('Database search results may contain extra items.\n'
              + 'Check it please. You will see chanks of 10 items in turn.\n'
              + 'For every chank enter the numbers corresponding to the wrong\n'
              + 'elements (for example, 239 if corr. three items are wrong).\n'
              + 'Then press [ENTER].')
        tmp = un_items
        un_items = []
        for i in range(0, len(tmp), 10):
            chunk = tmp[i:i+10]
            for j, item in enumerate(chunk):
                print('{}> {}'.format(j, item['title']))
            in_str = input('Wrong numbers: ')
            extra_indexes_list = [int(c) for c in in_str if c.isdigit()]
            extra_indexes_list.sort(reverse=True)
            for j in extra_indexes_list:
                del chunk[j]
            un_items.extend(chunk)
        del tmp
        assert un_items

        # Read very big groups which consists many students
        print('Input please id or domains of very very big groups\n'
              + 'which consists many students of added university.\n'
              + 'After every id press [ENTER]. Finish input by [ENTER].')
        un_big_groups = []
        while True:
            gr_id = input('> ')
            if not gr_id:
                break
            un_big_groups.append(gr_id)
        un_big_groups = vk.resolve_group_ids(un_big_groups)
        un_big_groups = [{'id': x[0], 'domain': x[1]} for x in un_big_groups]
        assert un_big_groups

        # Read groups which consists almost exclusively of students
        print('Input please id or domains of groups which consists\n'
              + 'almost exclusively of students of added university.\n'
              + 'After every id press [ENTER]. Finish input by [ENTER].')
        un_groups = []
        while True:
            gr_id = input('> ')
            if not gr_id:
                break
            un_groups.append(gr_id)
        un_groups = vk.resolve_group_ids(un_groups)
        un_groups = [{'id': x[0], 'domain': x[1]} for x in un_groups]

        # Read users whose almost all friends are students
        print('Input please id or domains of users whose almost all\n'
              + 'friends are students of added university.\n'
              + 'After every id press [ENTER]. Finish input by [ENTER].')
        un_users = []
        while True:
            us_id = input('> ')
            if not us_id:
                break
            us_id, us_scr = vk.resolve_user_ids(us_id)
            un_users.append({'id': us_id, 'domain': us_scr})

        # Search hot university ids by un_big_groups (unfortunately,
        # vk search method is not stable, so we use this approach)
        print('Start analysis of the prevalence of university identifiers.\n'
              + '(It could take several minutes)')
        un_ids = list(map(str, [x['id'] for x in un_items]))
        hot_ids = search_hot_university_ids(un_big_groups, un_ids)

        # Save university data
        univ_obj = {'titles': un_titles,
                    'big_groups': un_big_groups,
                    'crystal_groups': un_groups,
                    'crystal_users': un_users,
                    'all_ids': [x['id'] for x in un_items],
                    'hot_ids': hot_ids,
                    'is_activated': False}
        UsrData().set(univ_obj, 'univ', un_name, correct_is_act=True)

    except Exception as e:
        exception_handler('Failed to enter or add university data')

def delete_university(un_name):
    """Deletion un_name from registry"""

    UsrData().del_('univ', un_name, correct_is_act=True)

def activate_university(un_name):
    """Choose active university for analysis"""

    u = UsrData()
    if un_name in u.get('univ'):
        u.drop_activations('univ')
        u.set(True, 'univ', un_name, 'is_activated')

def display_universities():
    """Display data for all universities"""

    # Read universities registry
    univs = UsrData().get('univ')

    # Print
    for un_name in univs:
        univ_obj = univs[un_name]
        print(un_name + '{}'.format('\t\t\t\t<- ACTIVATED'
                                     if univ_obj['is_activated']
                                     else ''))
        print('Title:             {}'.format(', '.join(univ_obj['titles'])))
        s = ', '.join([x['domain'] for x in univ_obj['big_groups']])
        print('Big vk groups:     {}'.format(s))
        s = ', '.join([x['domain'] for x in univ_obj['crystal_groups']])
        print('Crystal vk groups: {}'.format(s))
        s = ', '.join([x['domain'] for x in univ_obj['crystal_users']])
        print('Crystal vk users:  {}'.format(s))

        # Identifier list with carry and indents
        print('VK ids:            ', end='')
        ids = [str(x) for x in univ_obj['all_ids']]
        ids2 = []
        for i in range(0, len(ids), 5):
            ids2.append(', '.join(ids[i:i+5]))
        s = ',\n                   '.join(x for x in ids2)
        print(s)

        # Hot identifiers with temperature in parentheses
        sum_cnt = sum([x['temp'] for x in univ_obj['hot_ids']])
        s =', '.join(['{} ({:.1f} %)'.format(x['id'], 100*x['temp']/sum_cnt)
                       for x in univ_obj['hot_ids']])
        print('Hot VK ids:        {}'.format(s))

        print('')

####################################################################
##                        VK API commands                         ##
####################################################################

# Any user-defined vk API method
def vk_method(method_name, args):
    args_list = [x.split('=', 1) for x in args]
    args_dict = {x[0]: x[1] for x in args_list}
    return apply_vk_method(method_name, handle_api_errors=False, **args_dict)

####################################################################
##                         Other commands                         ##
####################################################################

# Search new crystal students among friends of given set of crystal students
def load_crystal_students_from_friends(given_crystal,
                                       exceptions_list, # users not to be searched for
                                   univer_ids):
    new_crystal = []
    for user_id in given_crystal:
        u = vk.User(user_id, univer_ids)
        u.load_and_save_info_if_absent()
        u.read_info()
        new_crystal += u.univer_friends

    print('new_crystal: ' + str(len(new_crystal)))
    new_crystal = list(set(new_crystal))
    print('unique new_crystal: ' + str(len(new_crystal)))
    new_crystal = list(set(new_crystal) - set(exceptions_list))
    print('with except new_crystal: ' + str(len(new_crystal)))
    return new_crystal

# Load friends of given users list with counters of repetitions
# Return: generate dict {id0:num_of_repeat(id0), id1:..., ...}
def load_friends_of_users_with_cnt(users_list):

    friends_list = []
    for user_id in users_list:
        u = vk.User(user_id)
        u.read_info()
        friends_list += u.friends

    # Count repeating elements in list
    # (generate dict {id0:num_of_repeat(id0), id1:..., ...})
    friends_cnt = dict(Counter(friends_list))

    # Exclude original users
    users_set = set(users_list)
    friends_cnt_filtered = \
        {x:friends_cnt[x] for x in friends_cnt if x not in users_set}

    return friends_cnt_filtered

# Load ids of friends of users and write them to data/users_packs/pack_name
def load_users_friends_to_users_pack(user_ids, pack_name, univer_ids):

    friends_list = []
    for user_id in user_ids:
        u = vk.User(user_id, univer_ids)
        u.load_and_save_info_if_absent()
        u.read_info()
        friends_list += u.friends

    # Delete repeats and sort
    friends_list = list(set(friends_list))
    friends_list.sort()

    # Write
    vk.write_users_pack(friends_list, pack_name)

# Wrapper for method users.search
def users_search_wrapper(university_id, **p):
    response = apply_vk_method('users.search', university=university_id,
                               offset=0, count=1000, **p)
    if bool(response):
        return [x['id'] for x in response['response']['items']]
    else:
        return []

# Load list of phystechs using method users.search
# WARNING: Don't use it too often. Otherwise account will be banned.
# TODO: Обобщить на другие вузы (МГИМО, СПбГУ, Бауманка, МГЮА, универсальный),
#       хранить в спец. файле в data список вузов с id и ключевыми словами
def load_phystechs_by_search(pack_name):

    # Getting list of phystechs
    phystechs_list = users_search_wrapper(55111, {'sort': 0})
#TODO: После отладки новой версии раскоментить и удалить след. строку
    phystechs_list = phystechs_list[10]
#    phystechs_list += users_search_wrapper(55111, **{'sort': 1})
#    phystechs_list += users_search_wrapper(55111, **{'age_to': 25})
#    phystechs_list += users_search_wrapper(55111, **{'age_from': 26})
#    phystechs_list += users_search_wrapper(55111, **{'city': 1}) # Москва
#    #print('55111: ' + str(len(list(set(phystechs_list)))))
#    phystechs_list += users_search_wrapper(297, **{'sort': 0, 'sex': 1})
#    phystechs_list += users_search_wrapper(297, **{'sort': 1, 'sex': 1})
#    #print('sex 1: ' + str(len(list(set(phystechs_list)))))
#    phystechs_list += users_search_wrapper(297, **{'sort': 0, 'sex': 2})
#    phystechs_list += users_search_wrapper(297, **{'sort': 1, 'sex': 2})
#    #print('sex 2: ' + str(len(list(set(phystechs_list)))))
#    phystechs_list += users_search_wrapper(297, **{'age_to': 18})
#    for i in range(19, 36):
#        phystechs_list += users_search_wrapper(297, **{'age_from': i, 'age_to': i})
#    phystechs_list += users_search_wrapper(297, **{'age_from': 36, 'age_to': 37})
#    phystechs_list += users_search_wrapper(297, **{'age_from': 38, 'age_to': 40})
#    phystechs_list += users_search_wrapper(297, **{'age_from': 41, 'age_to': 45})
#    phystechs_list += users_search_wrapper(297, **{'age_from': 46, 'age_to': 50})
#    phystechs_list += users_search_wrapper(297, **{'age_from': 51, 'age_to': 55})
#    phystechs_list += users_search_wrapper(297, **{'age_from': 56, 'age_to': 60})
#    phystechs_list += users_search_wrapper(297, **{'age_from': 61, 'age_to': 70})
#    phystechs_list += users_search_wrapper(297, **{'age_from': 71})
#    #print('ages: ' + str(len(list(set(phystechs_list)))))
#    phystechs_list += users_search_wrapper(297, **{'city': 1}) # Москва
#    #print('Moscow: ' + str(len(list(set(phystechs_list)))))
#    phystechs_list += users_search_wrapper(297, **{'city': 857}) # Долгопрудный
#    #print('Dolgoprudny: ' + str(len(list(set(phystechs_list)))))
#    for n in ['Александр', 'Сергей', 'Дмитрий', 'Андрей', 'Алексей', 'Владимир', 'Михаил',
#              'Игорь', 'Евгений', 'Юрий', 'Никита', 'Олег', 'Николай', 'Иван', 'Павел']:
#        phystechs_list += users_search_wrapper(297, **{'q': urllib.parse.quote(n)})
#    #print('Names: ' + str(len(list(set(phystechs_list)))))

    # Sort result & delete repeats
    phystechs_list = list(set(phystechs_list))
    phystechs_list.sort()

    # Write & return
    vk.write_users_pack(phystechs_list, pack_name)
    return

# Read from groups of set members of university (field 'univer_members')
def read_crystal_students_of_groups_pack(pack_name):

    groups = vk.read_groups_pack(pack_name)

    crystal_students = []
    for group_id in groups:
        g = vk.Group(group_id)
        g.open()
        crystal_students += g.univer_members

    return crystal_students

#
def make_users_list_with_add_info(users_list,
                                  univer_groups_packs_list,
                                  thematic_groups_packs_list):
    ext_users_list = [{'id':x,
                       'univer_groups':[],
                       'thematic_groups':[]} for x in users_list]

    for groups_pack in univer_groups_packs_list:
        groups_list = vk.read_groups_pack(groups_pack)
        for group_id in groups_list:
            g = vk.Group(group_id)
            g.open()
            members_list = g.members
            for ext_user in ext_users_list:
                if ext_user['id'] in members_list:
                    ext_user['univer_groups'].append([group_id, g.name])

    for groups_pack in thematic_groups_packs_list:
        groups_list = vk.read_groups_pack(groups_pack)
        for group_id in groups_list:
            g = vk.Group(group_id)
            g.open()
            members_list = g.members
            for ext_user in ext_users_list:
                if ext_user['id'] in members_list:
                    ext_user['thematic_groups'].append([group_id, g.name])

    return ext_users_list

# Create report about thematic student by list with
# information (id, their groups packs) about them
def make_thematic_report(ext_users_list, univer_ids):

    # Begin report
    r = Report('thematic_students_list')
    i = 0
    r.add_str('<table>\n')

    for ext_user in ext_users_list:

        # Read user info
        u = vk.User(ext_user['id'], univer_ids)
        u.load_and_save_info_if_absent()
        u.read_info()

        # Write user description to report
        i += 1
        r.add_str('<tr>\n')
        r.add_str(' <td valign="top">' + str(i) + '.</td>\n')
        r.add_str(' <td><a href="https://vk.com/id' + str(ext_user['id']) + '" target="_blank"><img height=50 src="' + u.photo_max + '"></a></td>\n')
        r.add_str(' <td valign="top">\n')
        r.add_line('  ' + u.first_name + ' ' + u.last_name)
        r.add_str(' <td valign="top">\n')
        r.add_str('  MIPT: ')
        if u.is_student:
            r.add_str('PROFILE, ')
        for group in ext_user['univer_groups']:
            r.add_str('<a = href="https://vk.com/club' + group[0] + '" target="_blank">' + group[1] + '</a>, ')
        r.add_str('<br>')
        r.add_str('  Thematic: ')
        for group in ext_user['thematic_groups']:
            r.add_str('<a = href="https://vk.com/club' + group[0] + '" target="_blank">' + group[1] + '</a>, ')
        r.add_str(' </td>\n')
        r.add_str('</tr>\n')

    # Conclude report
    r.add_str('</table>\n')
    if not r.is_empty():
        r.conclude()
        r.dump()

def get_thematic_students_by_their_groups():

    univer_ids = [297, 55111]

    # Load members of mipt groups
    #vk.load_users_pack_by_groups_pack('mipt_crystal_gr', univer_ids)
    #vk.load_users_pack_by_groups_pack('mipt_very', univer_ids)
    #vk.load_users_pack_by_groups_pack('mipt_roughly', univer_ids)

    # Load friends of user 23681294 (Концертный Физтеха)
    # to data/users_packs/mipt_crystal_us
    #load_users_friends_to_users_pack(['23681294'], 'mipt_crystal_us', univer_ids)
    ## TODO: Фильтрации здесь или в конце
    ## TODO: убрать всё crystal в одну ф-ию
    ## TODO: раскоментить search
    ## TODO: clear в users и groups если нет в pack-ах

    # Search phystechs by and dump to data/users_packs/mipt_crystal_search
    # WARNING: too frequent calls to this function result in
    #          the method users.search being blocked
    #load_phystechs_by_search('mipt_crystal_search')
    ## TODO: Всем, кто найден поиском нужно проставлять is_student

    # Read phystechs from crystal sources
    #mipt_crystal_1_gusm = vk.read_users_pack('mipt_crystal_gr')
    #print('+ mipt_crystal_gr: ' + str(len(list(set(mipt_crystal_1_gusm)))))
    #mipt_crystal_1_gusm += vk.read_users_pack('mipt_crystal_us')
    #print('+ mipt_crystal_us: ' + str(len(list(set(mipt_crystal_1_gusm)))))
    #mipt_crystal_1_gusm += vk.read_users_pack('mipt_crystal_search')
    #print('+ mipt_crystal_search: ' + str(len(list(set(mipt_crystal_1_gusm)))))
    #mipt_crystal_1_gusm = list(set(mipt_crystal_1_gusm))

    # Search crystal phystechs in mipt-groups
    #mipt_crystal_1_gusm += \
    #    read_crystal_students_of_groups_pack('mipt_very')
    #print('+ mipt_very: ' + str(len(list(set(mipt_crystal_1_gusm)))))
    #mipt_crystal_1_gusm += \
    #    read_crystal_students_of_groups_pack('mipt_roughly')
    #print('+ mipt_roughly: ' + str(len(list(set(mipt_crystal_1_gusm)))))
    #mipt_crystal_1_gusm = list(set(mipt_crystal_1_gusm))

    # Search crystal phystechs among friends of crystal
    # WARNING: execution of this code block lasts > 2 hour
    #new_crystal = load_crystal_students_from_friends(mipt_crystal_1_gusm,
    #                                             mipt_crystal_1_gusm,
    #                                             univer_ids)
    #mipt_crystal_1_gusm += new_crystal
    #print('+ mipt_friends: ' + str(len(list(set(mipt_crystal_1_gusm)))))
    #while len(new_crystal) > 0:
    #    new_crystal = \
    #        load_crystal_students_from_friends(new_crystal,
    #                                       mipt_crystal_1_gusm,
    #                                       univer_ids)
    #    mipt_crystal_1_gusm += new_crystal
    #    print('+ mipt_friends: ' + str(len(list(set(mipt_crystal_1_gusm)))))

    # Write students to data/users_packs/
    #vk.write_users_pack(mipt_crystal_1_gusm, 'mipt_crystal_1_gusm')

    # Search students among friends of crystal on the basis of
    # the number of crystals in friends
    #mipt_crystal_1_gusm = vk.read_users_pack('mipt_crystal_1_gusm')
    #cryst_friends_cnt = load_friends_of_users_with_cnt(mipt_crystal_1_gusm)
    #print('cryst_friends_cnt: ' + str(len(cryst_friends_cnt)))
    #cryst_friends_2 = \
    #    [x for x in cryst_friends_cnt if cryst_friends_cnt[x] >= 2]
    #vk.write_users_pack(cryst_friends_2, 'cryst_friends_2')
    #print('cryst_friends_2: ' + str(len(cryst_friends_2)))
    #cryst_friends_3 = \
    #    [x for x in cryst_friends_cnt if cryst_friends_cnt[x] >= 3]
    #vk.write_users_pack(cryst_friends_3, 'cryst_friends_3')
    #print('cryst_friends_3: ' + str(len(cryst_friends_3)))
    #cryst_friends_5 = \
    #    [x for x in cryst_friends_cnt if cryst_friends_cnt[x] >= 5]
    #vk.write_users_pack(cryst_friends_5, 'cryst_friends_5')
    #print('cryst_friends_5: ' + str(len(cryst_friends_5)))
    #cryst_friends_10 = \
    #    [x for x in cryst_friends_cnt if cryst_friends_cnt[x] >= 10]
    #vk.write_users_pack(cryst_friends_10, 'cryst_friends_10')
    #print('cryst_friends_10: ' + str(len(cryst_friends_10)))

    #vk.load_users_pack_by_groups_pack('thematic_very')
    #vk.load_users_pack_by_groups_pack('thematic_roughly')
    #vk.load_users_pack_by_groups_pack('thematic_side') # TODO Докачать

    # Read phystechs and thematic from dump
    mipt_crystal = set(vk.read_users_pack('mipt_crystal_1_gusm'))
    cryst_friends_10 = set(vk.read_users_pack('cryst_friends_10'))
    cryst_friends_5 = set(vk.read_users_pack('cryst_friends_5'))
    thematic_very = set(vk.read_users_pack('thematic_very'))
    exceptions = set(vk.read_users_pack('exceptions'))

    intersection = list((mipt_crystal & thematic_very) - exceptions)
    intersection.sort()
    extended_intersection = \
        make_users_list_with_add_info(intersection,
                                 ['mipt_crystal_gr', 'mipt_very'],
                                 ['thematic_very', 'thematic_roughly'])
    make_thematic_report(extended_intersection, univer_ids)

    #intersection = list((cryst_friends_10 & thematic_very) - exceptions)
    #intersection.sort()
    #extended_intersection = \
    #    make_users_list_with_add_info(intersection,
    #                             ['mipt_crystal_gr', 'mipt_very'],
    #                             ['thematic_very', 'thematic_roughly'])
    #make_thematic_report(extended_intersection, univer_ids)
    #sys.exit()

    #intersection = list(set(cryst_friends_5) & set(thematic_very))
    #intersection.sort()
    #print(len(intersection))
    #print(intersection)

