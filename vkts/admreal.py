#! /usr/bin/env python3

"""Module for administering and monitoring vk.com communities"""

import os, sys, time
from vkts.report import Report
import vkts.vklib as vk
from vkts.vklib import apply_vk_method
from vkts.usrdata import UsrData

def add_group_for_monitoring(group_id):
    """Add group_id in registry of monitoring groups"""

    u = UsrData()

    # make group object fo saving
    digit_id, domain = vk.resolve_group_ids(group_id)
    obj = {'id': digit_id, 'domain': domain}

    # avoid repetition
    obj_list = u.get('adm', 'mon_groups')
    for o in obj_list:
        if o['id'] == digit_id:
            return

    # dump administrative data
    u.set(obj, 'adm', 'mon_groups')

def remove_monitoring_group(group_id):
    """Remove monitoring group_id"""

    # get list of objects
    u = UsrData()
    objs_list = u.get('adm', 'mon_groups')
    assert isinstance(objs_list, list), 'Monitoring groups data is incorrect'

    # look for object with specific id
    is_digit = (isinstance(group_id, int) or group_id.isdigit())
    for i, obj in enumerate(objs_list):
        assert isinstance(obj, dict), \
                'Monitoring groups data is incorrect: {}'.format(obj)
        # delete it from list
        if ((is_digit and obj['id'] == int(group_id))
            or obj['domain'] == group_id):
            #then
            u.del_('adm', 'mon_groups', i)
            break

def display_monitoring_groups():
    """Print all monitoring group_id"""

    objs_list = UsrData().get('adm', 'mon_groups')
    if objs_list:
        for obj in objs_list:
            print('{} \t{}'.format(obj['id'], obj['domain']))
        print('')

def add_email_for_broadcasting(email):
    """Add email address for broadcast reports about monitoring groups"""

    u = UsrData()

    # avoid repetition
    emails_list = u.get('adm', 'bc_emails')
    if emails_list and email in emails_list:
        return

    # add email
    u.set(email, 'adm', 'bc_emails')

def remove_broadcasting_email(email):
    """Remove email from addresses for broadcast reports
    about monitoring groups"""

    UsrData().del_('adm', 'bc_emails', email)

def display_broadcasting_email():
    """Print all addresses for broadcast reports about monitoring groups"""

    adm_data = UsrData().get('adm')
    if 'bc_emails' in adm_data and adm_data['bc_emails']:
        print('{}\n'.format('\n'.join(adm_data['bc_emails'])))

def check_updates(broadcast):
    """Check for changes in target groups, make report, send it to email"""

    # TODO: _mkdir_rec
    # TODO: Уменьшить число запросов
    tg_dir = os.sep.join(['data', 'adm_groups']) + os.sep

    # Read list of groups ids
    gr_list = UsrData().get('adm', 'mon_groups')
    if not gr_list:
        print('No monitoring groups (try command monitor_add)')
        sys.exit()
    gr_list = [[x['id'], x['domain']] for x in gr_list]

    # Make report
    r = Report('adm_groups_updates', html_only=False)
    new_files = []
    for g_info in gr_list:

        # Check accessibility of group data
        res = apply_vk_method('groups.getMembers', group_id=g_info[0])
        if 'error' in res and res['error']['error_code']== 203:
            continue

        # Get data about group
        g = vk.Group(g_info[0])
        try:
            g.load()
        except Exception as e:
            # In case of network problems we must delete collected data.
            # Otherwise, this data will spoil the next attempt
            # to generate a report
            print('Could not load information about the group of ' + g_info[1]
                    + ' (' + str(e) + ')')
            for f in new_files:
                os.remove(f)
            sys.exit()
        if g.is_empty():
            continue

        # Dump data
        if not os.path.isdir(tg_dir + g_info[1] + '/'):
            os.mkdir(tg_dir + g_info[1] + '/')
        if not os.path.isdir(tg_dir + g_info[1] + '/members/'):
            os.mkdir(tg_dir + g_info[1] + '/members/')
        out_file_name = tg_dir + g_info[1] + '/members/' \
                        + time.strftime("%F-%H%M%S") + '.txt'
        with open(out_file_name, 'w') as f:
            for user in g.members:
                f.write(str(user) + '\n')

        # Diff 2 last files
        ls_res = os.listdir(tg_dir + g_info[1] + '/members/')
        if len(ls_res) < 2:
            continue
        ls_res.sort()
        old_file = tg_dir + g_info[1] + '/members/' + ls_res[-2]
        new_file = tg_dir + g_info[1] + '/members/' + ls_res[-1]
        with open(old_file, 'r') as f:
            old_list = f.read().split('\n')[:-1]
        with open(new_file, 'r') as f:
            new_list = f.read().split('\n')[:-1]
        just_in_old = list(set(old_list) - set(new_list))
        just_in_new = list(set(new_list) - set(old_list))

        # If last 2 filaes are the same, then delete last one
        if len(just_in_old) == 0 and len(just_in_new) == 0:
            os.remove(new_file)
            continue
        else:
            new_files.append(out_file_name)
            if just_in_old:
                r.add_line('Покинули группу ' + g_info[1] + ':')
                for user_id in just_in_old:
                    r.add_str('[' + user_id + '] ')
                    r.add_vk_link('id' + user_id,
                                  vk.get_user_name(user_id))
                r.add_line('')
            if just_in_new:
                r.add_line('Вошли в группу ' + g_info[1] + ':')
                for user_id in just_in_new:
                    r.add_str('[' + user_id + '] ')
                    r.add_vk_link('id' + user_id,
                                  vk.get_user_name(user_id))
                r.add_line('')
            if just_in_old or just_in_new:
                r.add_line('В группе ' + str(g.count) + ' человек')
                r.add_line('')

    # Close report and broadcast it
    if not r.is_empty():
        r.conclude()
        r.dump()
        if broadcast:
            r.broadcast()

# Make report about birthday of all members of groups
def make_birthday_calendar(group_id):

    # Read arg
    group_id, scrname = vk.resolve_group_ids(group_id)

    # Load info about members
    g = vk.Group(group_id)
    g.load()
    members = g.members
    btd_list = []
    step = 200 # instead of 1000 to avoid error 414 (URI Too Long)
    last_index = int((len(members)-1)/step)
    for i in range(0, last_index + 1):
        if i == last_index:
            count = len(members) % step
        else:
            count = step
        members_str = ','.join([str(user)
                                for user in members[i*step:i*step+step]])
        btd_list += apply_vk_method('users.get', user_ids=members_str,
                                    fields='bdate,photo_max')['response']

    # Empty list -> out
    if not btd_list:
        print('No members with known date of birthday')
        sys.exit()

    # Delete users without birthday date
    tmp = [user for user in btd_list if 'bdate' in user]
    btd_list = tmp

    # Set default ava if it's absent
    for user in btd_list:
        if not user['photo_max']:
            user['photo_max'] = 'https://vk.com/images/camera_200.png?ava=1'

    # Add fields 'bmonth' and 'bday'
    for user in btd_list:
        user.update({'bmonth': int(user['bdate'].split('.')[1]),
                     'bday': int(user['bdate'].split('.')[0])})

    # Add field 'bval_for_sort' = 'bmonth' * 100 + 'bdate'
    for user in btd_list:
        user.update({'bval_for_sort': user['bmonth'] * 100 + user['bday']})

    # Sort by birthday date
    btd_list.sort(key = lambda user: user['bval_for_sort'])

    # Create calendar report
    r = Report('birthday_calendar')
    i = 0
    r.add_str('<table>\n')
    for user in btd_list:
        i += 1
        r.add_str('<tr>\n')
        r.add_str(' <td valign="top">' + str(i) + '.</td>\n')
        r.add_str(' <td><a href="https://vk.com/id' + str(user['id']) + '" target="_blank"><img height=50 src="' + user['photo_max'] + '"></a></td>\n')
        r.add_str(' <td valign="top">\n')
        r.add_line('  ' + user['first_name'] + ' ' + user['last_name'])
        months = ['января', 'февраля', 'марта', 'апреля',
                  'мая', 'июня', 'июля', 'августа',
                  'сентября', 'октября', 'ноября', 'декабря']
        r.add_line('  ' + str(user['bday']) + ' ' + months[user['bmonth']-1])
        r.add_str('</td>\n')
        r.add_str('</tr>\n')
    r.add_str('</table>\n')

    # Conclude report
    if not r.is_empty():
        r.conclude()
        r.dump()

