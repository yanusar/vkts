#! /usr/bin/env python3

"""Most frequently used requests to vk.com"""

from .vkreq import apply_vk_method, Executor
from collections.abc import Iterable

def get_group_domain(group_id):
    response = apply_vk_method('groups.getById', group_id=group_id)
    return response['response'][0]['screen_name']

def get_group_name(group_id):
    response = apply_vk_method('groups.getById', group_id=group_id)
    return response['response'][0]['name']

def resolve_group_ids(group_ids):
    """resolve_group_ids(digit id or domain of group) -> digit_id, domain_id.
    You can pass iterable argument for resolve every id in it."""

    if isinstance(group_ids, Iterable) and not isinstance(group_ids, str):

        # load info for resolving
        e = Executor()
        for group_id in group_ids:
            # is `group_id` digit or domain?
            if isinstance(group_id, int) or group_id.isdigit():
                e.add_request('groups.getById', group_ids=group_id)
            else:
                e.add_request('utils.resolveScreenName', screen_name=group_id)
        e.emit_requests()

        # collect result list & return
        res = []
        for group_id, r in zip(group_ids, e.responses):
            # is `group_id` digit or domain?
            if isinstance(group_id, int) or group_id.isdigit():
                digit_id = int(group_id)
                domain_id = r[0]['screen_name']
            else:
                digit_id = r['object_id']
                domain_id = group_id
            res.append((digit_id, domain_id))
        return res

    # `group_ids` is digit or domain?
    if isinstance(group_ids, int) or group_ids.isdigit():
        digit_id = int(group_ids)
        response = apply_vk_method('groups.getById', group_ids=group_ids)
        domain_id = response['response'][0]['screen_name']
    else:
        response = apply_vk_method('utils.resolveScreenName',
                                   screen_name=group_ids)
        digit_id = response['response']['object_id']
        domain_id = group_ids

    return digit_id, domain_id

def get_user_name(user_id):
    response = apply_vk_method('users.get', user_ids=user_id)
    if response:
        return response['response'][0]['first_name'] + ' ' \
               + response['response'][0]['last_name']
    else:
        return 'No name'

def resolve_user_ids(user_id):
    """resolve_user_ids(digit id or domain of user) -> digit_id, domain_id"""

    # `user_id` is digit or domain?
    if isinstance(user_id, int) or user_id.isdigit():
        digit_id = int(user_id)
        response = apply_vk_method('users.get', user_ids=user_id,
                                   fields='screen_name')
        domain_id = response['response'][0]['screen_name']
    else:
        response = apply_vk_method('utils.resolveScreenName',
                                   screen_name=user_id)
        digit_id = response['response']['object_id']
        domain_id = user_id

    return digit_id, domain_id

def domain_2_digital_id(domain):
    response = apply_vk_method('utils.resolveScreenName', screen_name=domain)
    return response['response']['object_id']

