
def get_flower_emoji(key):
    d = {
        "U+02600": u"\U00002600",
        "U+02614": u"\U00002614",
        "U+02601": u"\U00002601",
        "U+026C4": u"\U000026C4",
        "U+026A1": u"\U000026A1",
        "U+1F319": u"\U0001F319",
        "U+1F300": u"\U0001F300",
        "U+1F30A": u"\U0001F30A",
        "U+1F431": u"\U0001F431",
        "U+1F436": u"\U0001F436",
        "U+1F42D": u"\U0001F42D",
        "U+1F439": u"\U0001F439",
        "U+1F430": u"\U0001F430",
        "U+1F43A": u"\U0001F43A",
        "U+1F438": u"\U0001F438",
        "U+1F42F": u"\U0001F42F",
        "U+1F428": u"\U0001F428",
        "U+1F43B": u"\U0001F43B",
        "U+1F437": u"\U0001F437",
        "U+1F42E": u"\U0001F42E",
        "U+1F417": u"\U0001F417",
        "U+1F435": u"\U0001F435",
        "U+1F412": u"\U0001F412",
        "U+1F434": u"\U0001F434",
        "U+1F40E": u"\U0001F40E",
        "U+1F42B": u"\U0001F42B",
        "U+1F411": u"\U0001F411",
        "U+1F418": u"\U0001F418",
        "U+1F40D": u"\U0001F40D",
        "U+1F426": u"\U0001F426",
        "U+1F424": u"\U0001F424",
        "U+1F414": u"\U0001F414",
        "U+1F427": u"\U0001F427",
        "U+1F41B": u"\U0001F41B",
        "U+1F419": u"\U0001F419",
        "U+1F420": u"\U0001F420",
        "U+1F41F": u"\U0001F41F",
        "U+1F433": u"\U0001F433",
        "U+1F42C": u"\U0001F42C",
        "U+1F490": u"\U0001F490",
        "U+1F338": u"\U0001F338",
        "U+1F337": u"\U0001F337",
        "U+1F340": u"\U0001F340",
        "U+1F339": u"\U0001F339",
        "U+1F33B": u"\U0001F33B",
        "U+1F33A": u"\U0001F33A",
        "U+1F341": u"\U0001F341",
        "U+1F343": u"\U0001F343",
        "U+1F342": u"\U0001F342",
        "U+1F334": u"\U0001F334",
        "U+1F335": u"\U0001F335",
        "U+1F33E": u"\U0001F33E",
        "U+1F41A": u"\U0001F41A" 
        }
    return d[key]


def gen_flower_emoji():
    import random

    emoji = [
        "U+02600","U+02614", "U+02601","U+026C4","U+1F319","U+026A1",
        "U+1F300","U+1F30A","U+1F431","U+1F436","U+1F42D",
        "U+1F439","U+1F430","U+1F43A","U+1F438","U+1F42F","U+1F428",
        "U+1F43B","U+1F437","U+1F42E","U+1F417","U+1F435",
        "U+1F412","U+1F434","U+1F40E","U+1F42B","U+1F411","U+1F418",
        "U+1F40D","U+1F426","U+1F424","U+1F414","U+1F427",
        "U+1F41B","U+1F419","U+1F420","U+1F41F","U+1F433","U+1F42C",
        "U+1F490","U+1F338","U+1F337","U+1F340","U+1F339",
        "U+1F33B","U+1F33A","U+1F341","U+1F343","U+1F342","U+1F334",
        "U+1F335","U+1F33E","U+1F41A"
        ]
    return random.choice(emoji)


def match_emoji(desc):
    import re
    reg = re.compile('U\+[\w]{5}')
    res_list = reg.findall(desc)

    m = {}
    for key in res_list:
        if not key in m:
            m[key] = get_flower_emoji(key)
    
    for k,v in m.iteritems():
        desc = desc.replace(k,v)

    return desc


