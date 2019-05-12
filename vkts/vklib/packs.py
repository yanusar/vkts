#! /usr/bin/env python3

"""Interfaces for working with packages of groups and users"""

import sys, os
from .vkobjs import *
from .hotreqs import *

# Add group in data/groups_packs/pack_name by group_id or screen_name
def add_group_to_pack(pack_name, some_group_id):

    # Read args
    if some_group_id.isdigit():
        group_id = some_group_id
        scrname = get_group_domain(group_id)
    else:
        scrname = some_group_id
        group_id = str(domain_2_digital_id(scrname))

    # Build dir if absent
    if not os.path.isdir('data/groups_packs'):
        os.mkdir('data/groups_packs')

    # Check existance of group
    ls_res = os.listdir('data/groups_packs/')
    for f_name in ls_res:
        if os.path.isfile('data/groups_packs/' + f_name):
            with open('data/groups_packs/' + f_name, 'r') as f:
                res = f.read()
            if ' # ' + scrname + ' # ' in res:
                print('Set ' + 'data/groups_packs/' + f_name
                      + ' already consist this group')
                sys.exit()

    # Add group in file
    new_line = group_id + ' # ' + scrname + ' # ' \
               + get_group_name(group_id) + '\n'
    with open('data/groups_packs/' + pack_name, 'a') as f:
        f.write(new_line)

# Remove group from data/groups_packs/pack_name by group_id or screen_name
def rem_group_from_pack(pack_name, some_group_id):

    # Check existence of pack
    if not os.path.isfile('data/groups_packs/' + pack_name):
        print('data/groups_packs/' + pack_name + ' is absent')
        sys.exit()

    # Read pack
    with open('data/groups_packs/' + pack_name, 'r') as f:
        lines = f.read().split('\n')[:-1]

    if some_group_id.isdigit():
        # Parse numeric ids
        groups_ids = [x.split(' # ')[0] for x in lines]
    else:
        # Parse domains
        groups_ids = [x.split(' # ')[1] for x in lines]

    # Check existence of group in pack
    if some_group_id not in groups_ids:
        print('Group ' + str(some_group_id) +
              ' is not found in pack ' + pack_name)
        sys.exit()

    # Remove group
    index = groups_ids.index(some_group_id)
    lines.pop(index)

    # Rewrite pack
    with open('data/groups_packs/' + pack_name, 'w') as f:
        f.write('\n'.join(lines) + ('\n' if lines else ''))

# Return list of group_ids of given pack
def read_groups_pack(pack_name):
    if not os.path.isfile('data/groups_packs/' + pack_name):
        print('data/groups_packs/' + pack_name + ' is absent')
        sys.exit()
    with open('data/groups_packs/' + pack_name, 'r') as f:
        lines = f.read().split('\n')[:-1]
    groups = [x.split(' # ')[0] for x in lines]
    return groups

###   Interfaces for working with users packages   ###

# Add user in data/users_packs/pack_name by user_id or screen_name
def add_user_to_pack(some_user_id, pack_name, comment=''):

    # Read args
    if some_user_id.isdigit():
        user_id = some_user_id
    else:
        user_id = str(domain_2_digital_id(scrname))

    # Build dir if absent
    if not os.path.isdir('data/users_packs'):
        os.mkdir('data/users_packs')

    # Add user in pack
    new_line = user_id
    if comment:
        new_line += ' # ' + comment
    with open('data/users_packs/' + pack_name, 'a') as f:
        f.write(new_line)

# Remove user from data/users_packs/pack_name by user_id or screen_name
def rem_user_from_pack(some_user_id, pack_name):

    # Read args
    if some_user_id.isdigit():
        user_id = some_user_id
    else:
        user_id = str(domain_2_digital_id(scrname))

    # Check existence of pack
    if not os.path.isfile('data/users_packs/' + pack_name):
        print('data/users_packs/' + pack_name + ' is absent')
        sys.exit()

    # Read pack
    with open('data/users_packs/' + pack_name, 'r') as f:
        lines = f.read().split('\n')[:-1]

    # Parse numeric ids
    users_ids = [x.split(' # ')[0] for x in lines]

    # Check existence of user in pack
    if user_id not in users_ids:
        print('User ' + user_id + ' is not found in pack ' + pack_name)
        sys.exit()

    # Remove user
    index = users_ids.index(user_id)
    lines.pop(index)

    # Rewrite pack
    with open('data/users_packs/' + pack_name, 'w') as f:
        f.write('\n'.join(lines) + ('\n' if lines else ''))

# Write list of user ids (users_list) to file in data/users_packs/
def write_users_pack(users_list, pack_name):
    if not os.path.isdir('data/users_packs/'):
        os.mkdir('data/users_packs/')
    with open('data/users_packs/' + pack_name, 'w') as f:
        for user in users_list:
            f.write(str(user) + '\n')

# Get members list of users pack
def read_users_pack(pack_name):
    if not os.path.isfile('data/users_packs/' + pack_name):
        print('data/users_packs/' + pack_name + ' is absent')
        sys.exit()
    with open('data/users_packs/' + pack_name, 'r') as f:
        lines = f.read().split('\n')[:-1]
        users_list = [int(x.split(' # ')[0]) for x in lines]
    return users_list

###   Common interfaces for working with packages   ###

# For groups in set data/groups_packs/pack_name load members list
# and write it to data/users_packs/pack_name
def load_users_pack_by_groups_pack(pack_name, univer_ids = []):

    # Get list of groups
    groups = read_groups_pack(pack_name)

    # Getting list of members of groups
    members_list = []
    for g_id in groups:
        g = vk.Group(g_id, univer_ids)
        g.open()
        if g.is_empty():
            g.load()
            g.dump()
        members_list += g.members()

    # Delete repeats and sort
    members_list = list(set(members_list))
    members_list.sort()

    # Write members to data/users_packs/
    write_users_pack(members_list, pack_name)

# Write 'False' to field 'is_relevant' of all stored groups
def drop_relevance_flag_of_all_groups():
    if not os.path.isdir('data/groups/'):
        print('No stored groups data')
        sys.exit()
    ls_res = os.listdir('data/groups/')
    for group_id in ls_res:
        g = Group(group_id)
        g.open()
        g.is_relevant = False

# Write 'False' to field 'is_relevant' of all stored users
def drop_relevance_flag_of_all_users():
    if not os.path.isdir('data/users/'):
        print('No stored users data')
        sys.exit()
    ls_res = os.listdir('data/users/')
    for user_id in ls_res:
        u = User(user_id)
        u.read_info()
        u.is_relevant = False

