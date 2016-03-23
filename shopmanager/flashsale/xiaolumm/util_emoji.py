
def get_flower_emoji(key):
    d = {
        "U02600": u"\U00002600",
        "U02614": u"\U00002614",
        "U02601": u"\U00002601",
        "U026C4": u"\U000026C4",
        "U026A1": u"\U000026A1",
        "U1F319": u"\U0001F319",
        "U1F300": u"\U0001F300",
        "U1F30A": u"\U0001F30A",
        "U1F431": u"\U0001F431",
        "U1F436": u"\U0001F436",
        "U1F42D": u"\U0001F42D",
        "U1F439": u"\U0001F439",
        "U1F430": u"\U0001F430",
        "U1F43A": u"\U0001F43A",
        "U1F438": u"\U0001F438",
        "U1F42F": u"\U0001F42F",
        "U1F428": u"\U0001F428",
        "U1F43B": u"\U0001F43B",
        "U1F437": u"\U0001F437",
        "U1F42E": u"\U0001F42E",
        "U1F417": u"\U0001F417",
        "U1F435": u"\U0001F435",
        "U1F412": u"\U0001F412",
        "U1F434": u"\U0001F434",
        "U1F40E": u"\U0001F40E",
        "U1F42B": u"\U0001F42B",
        "U1F411": u"\U0001F411",
        "U1F418": u"\U0001F418",
        "U1F40D": u"\U0001F40D",
        "U1F426": u"\U0001F426",
        "U1F424": u"\U0001F424",
        "U1F414": u"\U0001F414",
        "U1F427": u"\U0001F427",
        "U1F41B": u"\U0001F41B",
        "U1F419": u"\U0001F419",
        "U1F420": u"\U0001F420",
        "U1F41F": u"\U0001F41F",
        "U1F433": u"\U0001F433",
        "U1F42C": u"\U0001F42C",
        "U1F490": u"\U0001F490",
        "U1F338": u"\U0001F338",
        "U1F337": u"\U0001F337",
        "U1F340": u"\U0001F340",
        "U1F339": u"\U0001F339",
        "U1F33B": u"\U0001F33B",
        "U1F33A": u"\U0001F33A",
        "U1F341": u"\U0001F341",
        "U1F343": u"\U0001F343",
        "U1F342": u"\U0001F342",
        "U1F334": u"\U0001F334",
        "U1F335": u"\U0001F335",
        "U1F33E": u"\U0001F33E",
        "U1F41A": u"\U0001F41A" 
        }
    return d[key]


def gen_flower_emoji():
    import random

    emoji = [
        "U02600","U02614", "U02601","U026C4","U1F319","U026A1",
        "U1F300","U1F30A","U1F431","U1F436","U1F42D",
        "U1F439","U1F430","U1F43A","U1F438","U1F42F","U1F428",
        "U1F43B","U1F437","U1F42E","U1F417","U1F435",
        "U1F412","U1F434","U1F40E","U1F42B","U1F411","U1F418",
        "U1F40D","U1F426","U1F424","U1F414","U1F427",
        "U1F41B","U1F419","U1F420","U1F41F","U1F433","U1F42C",
        "U1F490","U1F338","U1F337","U1F340","U1F339",
        "U1F33B","U1F33A","U1F341","U1F343","U1F342","U1F334",
        "U1F335","U1F33E","U1F41A"
        ]
    return random.choice(emoji)


def gen_emoji(desc):
    import re
    reg = re.compile('\[\d\]')
    res_list = reg.findall(desc)
    d = {}
    for key in res_list:
        if not key in d:
            d[key] = gen_flower_emoji()
    
    for k,v in d.iteritems():
        desc = desc.replace(k,v)
    return desc


def match_emoji(desc):
    import re
    reg = re.compile('U[\w]{5}')
    res_list = reg.findall(desc)

    m = {}
    for key in res_list:
        if not key in m:
            m[key] = get_flower_emoji(key)
    
    for k,v in m.iteritems():
        desc = desc.replace(k,v)

    return desc


