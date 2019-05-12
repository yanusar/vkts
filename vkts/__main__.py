#! /usr/bin/env python3

"""Realisation of access to the functionality of `vkts` via the console"""

import sys, os
from vkts import real
from vkts import admreal as adm
from vkts import vklib as vk
from vkts import usrdata

commands_with_descr = \
[
  [
    'Account commands',

    ['ac_add', '   # enter interactive mode'],
    ['ac_rem', '[email/vk/telegram] <ac_name>'],
    ['ac_activate', '[email/vk/telegram] <ac_name>'],
    ['ac_see', '']
  ],
  [
    'University commands',

    ['un_add', '   # enter interactive mode'],
    ['un_rem', '<un_name>'],
    ['un_activate', '<un_name>'],
    ['un_see', '']
  ],
  [
    'VK API commands',

    ['method', '<method_name> {param0=<v0> param1=...}'],
    ['resolve_group_ids', '<screen_name>'],
    ['resolve_user_ids', '<group_id>']
  ],
  [
    'Commands for working with packs',

    ['grouppack_add', '<pack_name> <group_id>'],
    ['grouppack_rem', '<pack_name> <group_id>'],
    ['exceptpack_add', '<user_id> {comment}'],
    ['exceptpack_rem', '<user_id>'],
    ['search_phystech_groups', '']# TODO:
    # Искать по ключ. словам и/или спискам групп физтехов группы,
    # вычислять их mipt_degree и вывоить в сортированном порядке
    # (добавить опцию с диапазоном degree для включения в заданный
    #  другой опцией groups_pack; а лучше сделать одной опцией для
    #  пополнения одной командой сразу нескольких pack-ов)
  ],
  [
    'Elementary analytical commands',

    ['load_users_pack_by_groups_pack', ''],
    ['load_phystechs_by_search', ''],
    ['drop_groups_data_relevance', ''],
    ['drop_users_data_relevance', '']
  ],
  [
    'Complete analysis',

    ['get_thematic_phystechs_by_their_groups', ''],
    ['get_thematic_phystechs_by_their_wall', ''] # TODO
  ],
  [
    'Administrative commands',

    ['monitor_add', '<group_id>'],
    ['monitor_rem', '<group_id>'],
    ['monitor_see', ''],
    ['broadcast_add', '<email>'],
    ['broadcast_rem', '<email>'],
    ['broadcast_see', ''],
    ['check_updates', '{--no-broadcast}'],
    ['make_birthday_calendar', '<group_id>']
  ]
]

# Make list of command names
commands = [y[0] for x in commands_with_descr for y in x[1:]]

def main():

    # Print Help
    if (len(sys.argv) == 1
        or sys.argv[1] not in commands):
        # then
        for chapter in commands_with_descr:
            print('')
            print(chapter[0])
            for item in chapter[1:]:
                print(' '.join(['vkts'] + item))
        print('')
        sys.exit()
    
    # Execute command
    if sys.argv[1] == 'ac_add':
        real.add_account()
    elif sys.argv[1] == 'ac_rem':
        real.delete_account(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == 'ac_activate':
        real.activate_account(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == 'ac_see':
        real.display_accounts()
    
    elif sys.argv[1] == 'un_add':
        real.add_university()
    elif sys.argv[1] == 'un_rem':
        real.delete_university(sys.argv[2])
    elif sys.argv[1] == 'un_activate':
        real.activate_university(sys.argv[2])
    elif sys.argv[1] == 'un_see':
        real.display_universities()
    
    elif sys.argv[1] == 'method':
        # Apply some method and output result
        print(real.vk_method(sys.argv[2], sys.argv[3:]))
    elif sys.argv[1] == 'resolve_group_ids':
        print(vk.resolve_group_ids(sys.argv[2]))
    elif sys.argv[1] == 'resolve_user_ids':
        print(vk.resolve_user_ids(sys.argv[2]))
    
    # TODO: Не должно быть отдельных опций для исключений
    # TODO: Иена опций неудачные
    # TODO: опций, специфичныхдля конр. ВУЗа, не должно быть
    elif sys.argv[1] == 'grouppack_add':
        # Add group in data/groups_packs/pack by id or scrname
        vk.add_group_to_pack(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == 'grouppack_rem':
        # Remove group from data/groups_packs/pack by id or scrname
        vk.rem_group_from_pack(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == 'exceptpack_add_user':
        # Add group in data/groups_packs/pack by id or scrname
        vk.add_user_to_pack(sys.argv[2], 'exceptions', sys.argv[3])
    elif sys.argv[1] == 'exceptpack_rem_user':
        # Remove group from data/groups_packs/pack by id or scrname
        vk.rem_user_from_pack(sys.argv[2], 'exceptions')
    elif sys.argv[1] == 'search_phystech_groups':
        print('This command is not realised')
    
    # TODO: Этот блок удалить после переделки работы с pack-ми
    elif sys.argv[1] == 'load_users_pack_by_groups_pack':
        # For groups in set data/groups_packs/pack_name load members list
        # and write it to data/users_packs/pack_name
        if (len(sys.argv) > 3):
            vk.load_users_pack_by_groups_pack(sys.argv[2],
                                              sys.argv[3].split(','))
        else:
            vk.load_users_pack_by_groups_pack(sys.argv[2])
    elif sys.argv[1] == 'load_phystechs_by_search':
        # Load list of phystechs using method users.search
        real.load_phystechs_by_search(sys.argv[2])
    elif sys.argv[1] == 'drop_groups_data_relevance':
        # Mark all data stored in data/groups/ irrelevant
        vk.drop_relevance_flag_of_all_groups()
    elif sys.argv[1] == 'drop_groups_data_relevance':
        # Mark all data stored in data/users/ irrelevant
        vk.drop_relevance_flag_of_all_users()
    
    elif sys.argv[1] == 'get_thematic_phystechs_by_their_groups':
        # Analyse by groups
        real.get_thematic_students_by_their_groups()
    
    
    elif sys.argv[1] == 'monitor_add':
        # Add group_id in registry of monitoring groups
        adm.add_group_for_monitoring(sys.argv[2])
    elif sys.argv[1] == 'monitor_rem':
        # Remove monitoring group_id
        adm.remove_monitoring_group(sys.argv[2])
    elif sys.argv[1] == 'monitor_see':
        # Print all monitoring group_id
        adm.display_monitoring_groups()
    elif sys.argv[1] == 'broadcast_add':
        # Add email address for broadcast reports about monitoring groups
        adm.add_email_for_broadcasting(sys.argv[2])
    elif sys.argv[1] == 'broadcast_rem':
        # Remove email from addresses for broadcast reports
        adm.remove_broadcasting_email(sys.argv[2])
    elif sys.argv[1] == 'broadcast_see':
        # Print all addresses for broadcast reports about monitoring groups
        adm.display_broadcasting_email()
    elif sys.argv[1] == 'check_updates':
        # Find changes in monitoring groups
        adm.check_updates('--no-broadcast' not in sys.argv)
    elif sys.argv[1] == 'make_birthday_calendar':
        # Make report with sorted list of birthday of community
        adm.make_birthday_calendar(sys.argv[2])
    
    else:
        print('Command ' + sys.argv[1] + ' is not supported')
        sys.exit()

if __name__ == '__main__':
    main()

