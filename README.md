**Disclaimer:** the package is in the process of deep recast. Many features are not yet implemented at all. Now the most useful thing in it is a library **vkts.vklib** with the possibility of accelerated work with vk API and convenient work with social network objects.

**vkts** &mdash; application for thematic students search in social network vk.com. It contains a library **vkts.vklib** of accelerated work with vk API. Also, there are several community monitoring features.

### Install

    $ git clone https://github.com/smurphik/vkts
    $ cd vkts
    $ sudo python3 setup.py install clean

Alternative way:

    $ sudo pip3 install vkts

### Setting

First of all, you must enter data about at least one vk account. If you do not want to enter a password every vkts session, add a *fake* account. So password will be stored in your computer. Otherwise, add a *private* account.

    $ mkdir vkts_work_dir
    $ cd vkts_work_dir/
    $ vkts ac_add
    What type of account do you want to create?
    Input please one letter - [e]mail, [v]k.ru
    or [t]elegram: v

    Input name of new account: vanya

    Are your account fake (password will be stored
    unencrypted on your computer) or private (you
    will be forced to enter the password every run)?
    Input please [f]ake or [p]rivate: f

    Input email address: vanya@masha.ru        

    Input password: gagarin256

Now we can see result:

    $ vkts ac_see
    vk
        vanya: 	[vanya@masha.ru|gagarin256]    	<- activated

Further customization should be done by commands *monitor_add*, *broadcast_add*, *un_add* (see *vkts --help*). But functionality associated with this data is currently unstable.

### Using as application

Realisation of many commands is now in unstable state. But there is something useful.

    $ vkts method database.getCountries code=GA
    {'response': {'count': 1, 'items': [{'id': 56, 'title': 'Габон'}]}}
    $ vkts method database.getCities country_id=56
    {'response': {'count': 3, 'items': [{'id': 4134854, 'title': 'Franceville'}, {'id': 2722567, 'title': 'Libreville'}, {'id': 4132567, 'title': 'Port-Gentil'}]}}
    $ vkts method groups.getMembers group_id=phys_kek count=5
    {'response': {'count': 19373, 'items': [510, 3016, 6477, 9190, 12632]}}

Name resolution is more simple to use (it's useful with active manual work with pages).

    $ vkts resolve_group_ids 3113588
    (3113588, 'oxxxymiron')
    $ vkts resolve_user_ids 1
    (1, 'durov')
    $ vkts resolve_user_ids durov
    (1, 'durov')

### Using as a library

So you can import `vkts` and it's submodules:

    >>> from vkts.vklib import apply_vk_method, Executor, Group
    >>> g_frtk = Group(17708)
    >>> g_frtk.load(extra_getById=('links',))
    >>> print(g_frtk)
    [Group]
    count:            2756
    cumul_members:    [34603008, 7036929, 14  ....  1, 104300542] len 2756
    description:      Неофициальная группа Ф  ....   https://frtk.mipt.ru/
    group_id:         17708
    links:            [dict] len 12
    members:          [5489, 5518, 5531, 559  ....  3, 540738585] len 2756
    name:             ФРТК МФТИ
    photo_200:        https://sun1-22.userap  ....  /zG4LuCbiUlE.jpg?ava=1
    screen_name:      drec_mipt
    univers_data:     

    >>> print(g_frtk.description)
    Неофициальная группа ФРТК.

    Факультет радиотехники и кибернетики. Всегда первый.

    Группа поддерживается Советом студентов ФРТК.

    Сайт студсовета: https://frtk.mipt.ru/
