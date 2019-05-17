#! /usr/bin/env python3

"""Testing of vkts bash-commands ac_*, un_*, monitor_*, broadcast_*"""

import pytest, json, os
import subprocess as sp

def bash_cmd(args, stdin=None):
    process = sp.Popen(args, stdin=sp.PIPE, stdout=sp.PIPE)
    res, _ = process.communicate(input=(stdin.encode() if stdin else None))
    return res.decode()

def vkts_cmd(s, stdin=None):
    args = ['vkts'] + s.split()
    res = bash_cmd(args, stdin)
    return res

@pytest.mark.run(order=1)
def test_vk_accounts():

    ###   $ vkts ac_add ... ; vkts ac_see
    stdin = '\n'.join(('v', 'ivan', 'f', 'testA@mail.com', 'pswdA', '|'))
    vkts_cmd('ac_add', stdin)
    assert ('vk\n    ivan: \t[testA@mail.com|pswdA]    \t<- activated\n\n'
            == vkts_cmd('ac_see'))

    ###   $ vkts ac_add ... ; vkts ac_see
    stdin = '\n'.join(('v', 'petya', 'p', 'testB@mail.com', '|'))
    vkts_cmd('ac_add', stdin)
    assert ('\n'.join((
            'vk\n    ivan: \t[testA@mail.com|pswdA]    \t<- activated',
            '    petya: \t[testB@mail.com|None]\n\n'))
            == vkts_cmd('ac_see'))

    ###   $ vkts ac_activate vk petya ; vkts ac_see
    vkts_cmd('ac_activate vk petya')
    assert ('\n'.join((
            'vk\n    ivan: \t[testA@mail.com|pswdA]',
            '    petya: \t[testB@mail.com|None]    \t<- activated\n\n'))
            == vkts_cmd('ac_see'))

    ###   $ vkts ac_rem vk pety ; vkts ac_see
    vkts_cmd('ac_rem vk pety')
    assert ('\n'.join((
            'vk\n    ivan: \t[testA@mail.com|pswdA]',
            '    petya: \t[testB@mail.com|None]    \t<- activated\n\n'))
            == vkts_cmd('ac_see'))

    ###   $ vkts ac_rem vk petya ; vkts ac_see
    vkts_cmd('ac_rem vk petya')
    assert ('vk\n    ivan: \t[testA@mail.com|pswdA]    \t<- activated\n\n'
            == vkts_cmd('ac_see'))

    ###   $ vkts ac_rem vk ivan ; vkts ac_see
    vkts_cmd('ac_rem vk ivan')
    assert '' == vkts_cmd('ac_see')

    ###   $ vkts ac_rem vk ivan ; vkts ac_see
    vkts_cmd('ac_rem vk ivan')
    assert '' == vkts_cmd('ac_see')

@pytest.mark.run(order=2)
def test_various_accounts():

    ###   $ vkts ac_add ... 4 times ; vkts ac_see
    stdin = '\n'.join(('v', 'ivan', 'f', 'testA@mail.com', 'pswdA', '|'))
    vkts_cmd('ac_add', stdin)
    stdin = '\n'.join(('e', 'vanka', 'f', 'testA@mail.com', 'pswdA', '|'))
    vkts_cmd('ac_add', stdin)
    stdin = '\n'.join(('e', 'petka', 'p', 'testB@mail.com', '|'))
    vkts_cmd('ac_add', stdin)
    stdin = '\n'.join(('t', 'masha', 'f', 'testC@mail.com', 'pswdC', '|'))
    vkts_cmd('ac_add', stdin)
    assert ('\n'.join((
            'vk\n    ivan: \t[testA@mail.com|pswdA]    \t<- activated\n',
            'email\n    vanka: \t[testA@mail.com|pswdA]    \t<- activated',
            '    petka: \t[testB@mail.com|None]\n',
            'telegram\n    masha: \t[testC@mail.com|pswdC]    \t<- activated\n\n'))
            == vkts_cmd('ac_see'))

    ###   $ vkts ac_rem email vanka ; vkts ac_rem telegram masha ; vkts ac_see
    vkts_cmd('ac_rem email vanka')
    vkts_cmd('ac_rem telegram masha')
    assert ('\n'.join((
            'vk\n    ivan: \t[testA@mail.com|pswdA]    \t<- activated\n',
            'email\n    petka: \t[testB@mail.com|None]    \t<- activated\n\n'))
            == vkts_cmd('ac_see'))

@pytest.mark.run(order=3)
def test_universities():

    ###   $ vkts un_add ...
    with open('.mock_request_responses.json', 'w') as fp:
        responses = \
                [
                    {"response": [{"count": 4, "items": [{"id": 297, "title": "МФТИ (Физтех)"}, {"id": 1160, "title": "МФТИ"}, {"id": 55111, "title": "МФТИ (ГУ) (см. в Москве)"}, {"id": 75468, "title": "МФТИ МФ"}]}, {"count": 1, "items": [{"id": 297, "title": "МФТИ (Физтех)"}]}, {"count": 1, "items": [{"id": 371670, "title": "3-МИПТ"}]}]},
                    {"response": [{"type": "group", "object_id": 932}, {"type": "group", "object_id": 26356004}]},
                    {"response": [[{"id": 79996626, "name": "Клуб Фанатов ЛЛ", "screen_name": "fanclub_letchikleha"}], [{"id": 22685503, "name": "Сообщество фанатов Николы Теслы", "screen_name": "teslaforever"}], {"type": "group", "object_id": 22604105}, {"type": "group", "object_id": 23944985}, {"type": "group", "object_id": 162774745}]},
                    {"response": {"type": "user", "object_id": 23681294}},
                    {"response":
                        [
                            [{"id": 932, "name": "МФТИ — Физтех", "screen_name": "miptru", "is_closed": 0, "description": "Официальная страница бла-бла"}],
                            {"count": 13, "items": [1390, 1422, 3016, 4316, 4320, 4639, 4640, 5178, 5489, 5505, 5518, 5531, 5690]},
                            [{"id": 26356004, "name": "Поток", "screen_name": "miptstream", "description": "Поток» — студенческое СМИ Физтеха"}],
                            {"count": 17, "items": [69810, 71142, 73115, 75566, 77630, 77663, 78393, 79210, 79431, 84364, 86580, 92084, 94718, 99055, 101554, 103946, 142579796]}
                        ]
                    },
                    {"response": 
                        [[
                            {"id": 5505, "first_name": "Сергей", "last_name": "Гижа", "occupation": {"type": "university", "id": 297, "name": "МФТИ (Физтех)"}},
                            {"id": 103946, "first_name": "Артём", "last_name": "Вдовенко"},
                            {"id": 1422, "first_name": "Маша", "last_name": "Егорова", "university": 1, "university_name": "СПбГУ"},
                            {"id": 4639, "first_name": "Александр", "last_name": "Оганезов", "university": 297, "university_name": "МФТИ (Физтех)"},
                            {'id': 142579796, 'first_name': 'Никита', 'last_name': 'Рыков', 'occupation': {'type': 'university', 'id': 55111, 'name': 'МФТИ (ГУ) (см. в Москве)'}},
                            {"university": 297}, {"university": 297}, {"university": 297}, {"university": 297}, {"university": 297}, {"university": 297}, {"university": 297}, {"university": 297}, {"university": 297}, {"university": 297},
                            {"university": 55111}, {"university": 55111}, {"university": 55111}, {"university": 55111}, {"university": 55111}, {"university": 55111}, {"university": 55111}, {"university": 55111}, {"university": 55111}
                        ]]
                    }
                ]

        json.dump(responses, fp)

    stdin = '\n'.join(('mipt', 'МФТИ', 'Физтех', 'MIPT\n', '3', 'miptru', 'miptstream\n', '79996626', '22685503', 'mipt1', 'fupmbd', '12ka_mipt\n', 'id23681294\n', '|'))
    vkts_cmd('un_add', stdin)

    ###   $ vkts ac_see
    assert ('\n'.join((
            'mipt\t\t\t\t<- ACTIVATED',
            'Title:             МФТИ, Физтех, MIPT',
            'Big vk groups:     miptru, miptstream',
            'Crystal vk groups: fanclub_letchikleha, teslaforever, mipt1, fupmbd, 12ka_mipt',
            'Crystal vk users:  id23681294',
            'VK ids:            297, 1160, 55111',
            'Hot VK ids:        297 (54.5 %), 55111 (45.5 %)\n\n'))
            == vkts_cmd('un_see'))

    ###   $ vkts un_add ...
    with open('.mock_request_responses.json', 'w') as fp:
        responses = \
                [
                    {"response": [{"count": 3, "items": [{"id": 1, "title": "СПбГУ"}, {"id": 38, "title": "НГУ им. Лесгафта (бывш. СПбГУФК)"}, {"id": 989, "title": "СПбГУ ГА"}]}]},
                    {"response": [{"type": "group", "object_id": 52298374}, {"type": "group", "object_id": 58219172}]},
                    {"response":
                        [
                            [{"id": 52298374, "name": "СПбГУ", "screen_name": "spb1724"}],
                            {"count": 16, "items": [102, 131, 407, 490, 753, 799, 834, 882, 888, 892, 907, 913, 969, 976, 1092, 1159]},
                            [{"id": 58219172, "name": "Подслушано СПбГУ", "screen_name": "overhearspbsu"}],
                            {"count": 14, "items": [134, 431, 696, 907, 3064, 3768, 4326, 4548, 7224, 7451, 7589, 7859, 8426, 8571]}
                        ]
                    },
                    {"response": 
                        [
                            [{"university": 1}]*15
                        ]
                    }
                ]

        json.dump(responses, fp)

    stdin = '\n'.join(('spbgu', 'СПбГУ\n', '1', 'spb1724', 'overhearspbsu\n\n\n', '|'))
    vkts_cmd('un_add', stdin)

    ###   $ vkts ac_see
    assert ('\n'.join((
            'mipt\t\t\t\t<- ACTIVATED',
            'Title:             МФТИ, Физтех, MIPT',
            'Big vk groups:     miptru, miptstream',
            'Crystal vk groups: fanclub_letchikleha, teslaforever, mipt1, fupmbd, 12ka_mipt',
            'Crystal vk users:  id23681294',
            'VK ids:            297, 1160, 55111',
            'Hot VK ids:        297 (54.5 %), 55111 (45.5 %)\n',
            'spbgu',
            'Title:             СПбГУ',
            'Big vk groups:     spb1724, overhearspbsu',
            'Crystal vk groups: ',
            'Crystal vk users:  ',
            'VK ids:            1',
            'Hot VK ids:        1 (100.0 %)\n\n'))
            == vkts_cmd('un_see'))

    ###   $ vkts un_activate spbgu ; vkts un_see
    vkts_cmd('un_activate spbgu')
    assert ('\n'.join((
            'mipt',
            'Title:             МФТИ, Физтех, MIPT',
            'Big vk groups:     miptru, miptstream',
            'Crystal vk groups: fanclub_letchikleha, teslaforever, mipt1, fupmbd, 12ka_mipt',
            'Crystal vk users:  id23681294',
            'VK ids:            297, 1160, 55111',
            'Hot VK ids:        297 (54.5 %), 55111 (45.5 %)\n',
            'spbgu\t\t\t\t<- ACTIVATED',
            'Title:             СПбГУ',
            'Big vk groups:     spb1724, overhearspbsu',
            'Crystal vk groups: ',
            'Crystal vk users:  ',
            'VK ids:            1',
            'Hot VK ids:        1 (100.0 %)\n\n'))
            == vkts_cmd('un_see'))

    ###   $ vkts un_rem spbgu ; vkts un_see
    vkts_cmd('un_rem spbgu')
    assert ('\n'.join((
            'mipt\t\t\t\t<- ACTIVATED',
            'Title:             МФТИ, Физтех, MIPT',
            'Big vk groups:     miptru, miptstream',
            'Crystal vk groups: fanclub_letchikleha, teslaforever, mipt1, fupmbd, 12ka_mipt',
            'Crystal vk users:  id23681294',
            'VK ids:            297, 1160, 55111',
            'Hot VK ids:        297 (54.5 %), 55111 (45.5 %)\n\n'))
            == vkts_cmd('un_see'))

@pytest.mark.run(order=4)
def test_broadcast():

    #bash_cmd(['rm', os.path.join('.vkts', 'adm_data.json')])

    ###   $ vkts broadcast_add testA@mail.com ; vkts broadcast_see
    vkts_cmd('broadcast_add testA@mail.com')
    assert ('testA@mail.com\n\n'
            == vkts_cmd('broadcast_see'))

    ###   $ vkts broadcast_add testA@mail.com ; vkts broadcast_see
    vkts_cmd('broadcast_add testA@mail.com')
    assert ('testA@mail.com\n\n'
            == vkts_cmd('broadcast_see'))

    ###   $ vkts broadcast_add testB@mail.com ; vkts broadcast_see
    vkts_cmd('broadcast_add testB@mail.com')
    assert ('testA@mail.com\ntestB@mail.com\n\n'
            == vkts_cmd('broadcast_see'))

    ###   $ vkts broadcast_rem testA@mail.com ; vkts broadcast_see
    vkts_cmd('broadcast_rem testA@mail.com')
    assert ('testB@mail.com\n\n'
            == vkts_cmd('broadcast_see'))

    ###   $ vkts broadcast_rem testA@mail.com ; vkts broadcast_see
    vkts_cmd('broadcast_rem testA@mail.com')
    assert ('testB@mail.com\n\n'
            == vkts_cmd('broadcast_see'))

    ###   $ vkts broadcast_rem testB@mail.com ; vkts broadcast_see
    vkts_cmd('broadcast_rem testB@mail.com')
    assert (''
            == vkts_cmd('broadcast_see'))

@pytest.mark.run(order=5)
def test_monitor():

    with open('.mock_request_responses.json', 'w') as fp:
        responses = \
                [
                    {"response": {"type": "group", "object_id": 153105912}},
                    {"response": [{"id": 153105912, "screen_name": "bomanka"}]},
                    {"response": [{"id": 141149614, "screen_name": "memphi_official"}]}
                ]

        json.dump(responses, fp)

    ###   $ vkts monitor_add bomanka ; vkts monitor_see
    vkts_cmd('monitor_add bomanka')
    assert ('153105912 \tbomanka\n\n'
            == vkts_cmd('monitor_see'))

    ###   $ vkts monitor_add 153105912 ; vkts monitor_see
    vkts_cmd('monitor_add 153105912')
    assert ('153105912 \tbomanka\n\n'
            == vkts_cmd('monitor_see'))

    ###   $ vkts monitor_add 141149614 ; vkts monitor_see
    vkts_cmd('monitor_add 141149614')
    assert ('153105912 \tbomanka\n141149614 \tmemphi_official\n\n'
            == vkts_cmd('monitor_see'))

    ###   $ vkts monitor_rem bomanka ; vkts monitor_see
    vkts_cmd('monitor_rem 153105912')
    assert ('141149614 \tmemphi_official\n\n'
            == vkts_cmd('monitor_see'))

    ###   $ vkts monitor_rem bomanka ; vkts monitor_see
    vkts_cmd('monitor_rem bomanka')
    assert ('141149614 \tmemphi_official\n\n'
            == vkts_cmd('monitor_see'))

    ###   $ vkts monitor_rem memphi_official ; vkts monitor_see
    vkts_cmd('monitor_rem memphi_official')
    assert (''
            == vkts_cmd('monitor_see'))

