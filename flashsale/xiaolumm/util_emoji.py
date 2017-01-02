def get_all_emoji():
    a = {
        # flower
        "U+2600": u"\U00002600", "U+2614": u"\U00002614", "U+2601": u"\U00002601", "U+26C4": u"\U000026C4",
        "U+26A1": u"\U000026A1", "U+1F319": u"\U0001F319", "U+1F300": u"\U0001F300", "U+1F30A": u"\U0001F30A",
        "U+1F431": u"\U0001F431", "U+1F436": u"\U0001F436", "U+1F42D": u"\U0001F42D", "U+1F439": u"\U0001F439",
        "U+1F430": u"\U0001F430", "U+1F43A": u"\U0001F43A", "U+1F438": u"\U0001F438", "U+1F42F": u"\U0001F42F",
        "U+1F428": u"\U0001F428", "U+1F43B": u"\U0001F43B", "U+1F437": u"\U0001F437", "U+1F42E": u"\U0001F42E",
        "U+1F417": u"\U0001F417", "U+1F435": u"\U0001F435", "U+1F412": u"\U0001F412", "U+1F434": u"\U0001F434",
        "U+1F40E": u"\U0001F40E", "U+1F42B": u"\U0001F42B", "U+1F411": u"\U0001F411", "U+1F418": u"\U0001F418",
        "U+1F40D": u"\U0001F40D", "U+1F426": u"\U0001F426", "U+1F424": u"\U0001F424", "U+1F414": u"\U0001F414",
        "U+1F427": u"\U0001F427", "U+1F41B": u"\U0001F41B", "U+1F419": u"\U0001F419", "U+1F420": u"\U0001F420",
        "U+1F41F": u"\U0001F41F", "U+1F433": u"\U0001F433", "U+1F42C": u"\U0001F42C", "U+1F490": u"\U0001F490",
        "U+1F338": u"\U0001F338", "U+1F337": u"\U0001F337", "U+1F340": u"\U0001F340", "U+1F339": u"\U0001F339",
        "U+1F33B": u"\U0001F33B", "U+1F33A": u"\U0001F33A", "U+1F341": u"\U0001F341", "U+1F343": u"\U0001F343",
        "U+1F342": u"\U0001F342", "U+1F334": u"\U0001F334", "U+1F335": u"\U0001F335", "U+1F33E": u"\U0001F33E",
        "U+1F41A": u"\U0001F41A",
        # Vehicle
        "U+1F3E0": u"\U0001F3E0", "U+1F3EB": u"\U0001F3EB", "U+1F3E2": u"\U0001F3E2", "U+1F3E3": u"\U0001F3E3",
        "U+1F3E5": u"\U0001F3E5", "U+1F3E6": u"\U0001F3E6", "U+1F3EA": u"\U0001F3EA", "U+1F3E9": u"\U0001F3E9",
        "U+1F3E8": u"\U0001F3E8", "U+1F492": u"\U0001F492", "U+26EA": u"\U000026EA",
        "U+1F3EC": u"\U0001F3EC", "U+1F307": u"\U0001F307", "U+1F306": u"\U0001F306", "U+1F3E7": u"\U0001F3E7",
        "U+1F3EF": u"\U0001F3EF", "U+1F3F0": u"\U0001F3F0", "U+26FA": u"\U000026FA", "U+1F3ED": u"\U0001F3ED",
        "U+1F5FC": u"\U0001F5FC", "U+1F5FB": u"\U0001F5FB", "U+1F304": u"\U0001F304",
        "U+1F305": u"\U0001F305", "U+1F303": u"\U0001F303", "U+1F5FD": u"\U0001F5FD", "U+1F308": u"\U0001F308",
        "U+1F3A1": u"\U0001F3A1", "U+26F2": u"\U000026F2", "U+1F3A2": u"\U0001F3A2", "U+1F6A2": u"\U0001F6A2",
        "U+1F6A4": u"\U0001F6A4", "U+26F5": u"\U000026F5", "U+2708": u"\U00002708",
        "U+1F680": u"\U0001F680", "U+1F6B2": u"\U0001F6B2", "U+1F699": u"\U0001F699", "U+1F697": u"\U0001F697",
        "U+1F695": u"\U0001F695", "U+1F68C": u"\U0001F68C", "U+1F693": u"\U0001F693", "U+1F692": u"\U0001F692",
        "U+1F691": u"\U0001F691", "U+1F69A": u"\U0001F69A", "U+1F683": u"\U0001F683",
        "U+1F689": u"\U0001F689", "U+1F684": u"\U0001F684", "U+1F685": u"\U0001F685", "U+1F3AB": u"\U0001F3AB",
        "U+26FD": u"\U000026FD", "U+1F6A5": u"\U0001F6A5", "U+26A0": u"\U000026A0", "U+1F6A7": u"\U0001F6A7",
        "U+1F530": u"\U0001F530", "U+1F3B0": u"\U0001F3B0", "U+1F68F": u"\U0001F68F",
        "U+1F488": u"\U0001F488", "U+2668": u"\U00002668", "U+1F3C1": u"\U0001F3C1", "U+1F38C": u"\U0001F38C",
        # Bell
        "U+1F38D": u"\U0001F38D", "U+1F49D": u"\U0001F49D", "U+1F38E": u"\U0001F38E", "U+1F392": u"\U0001F392",
        "U+1F393": u"\U0001F393", "U+1F38F": u"\U0001F38F", "U+1F386": u"\U0001F386", "U+1F387": u"\U0001F387",
        "U+1F390": u"\U0001F390", "U+1F391": u"\U0001F391", "U+1F383": u"\U0001F383",
        "U+1F47B": u"\U0001F47B", "U+1F385": u"\U0001F385", "U+1F384": u"\U0001F384", "U+1F381": u"\U0001F381",
        "U+1F514": u"\U0001F514", "U+1F389": u"\U0001F389", "U+1F388": u"\U0001F388", "U+1F4BF": u"\U0001F4BF",
        "U+1F4C0": u"\U0001F4C0", "U+1F4F7": u"\U0001F4F7", "U+1F3A5": u"\U0001F3A5",
        "U+1F4BB": u"\U0001F4BB", "U+1F4FA": u"\U0001F4FA", "U+1F4F1": u"\U0001F4F1", "U+1F4E0": u"\U0001F4E0",
        "U+260E": u"\U0000260E", "U+1F4BD": u"\U0001F4BD", "U+1F4FC": u"\U0001F4FC", "U+1F50A": u"\U0001F50A",
        "U+1F4E2": u"\U0001F4E2", "U+1F4E3": u"\U0001F4E3", "U+1F4FB": u"\U0001F4FB",
        "U+1F4E1": u"\U0001F4E1", "U+27BF": u"\U000027BF", "U+1F50D": u"\U0001F50D", "U+1F513": u"\U0001F513",
        "U+1F512": u"\U0001F512", "U+1F511": u"\U0001F511", "U+2702": u"\U00002702", "U+1F528": u"\U0001F528",
        "U+1F4A1": u"\U0001F4A1", "U+1F4F2": u"\U0001F4F2", "U+1F4E9": u"\U0001F4E9",
        "U+1F4EB": u"\U0001F4EB", "U+1F4EE": u"\U0001F4EE", "U+1F6C0": u"\U0001F6C0", "U+1F6BD": u"\U0001F6BD",
        "U+1F4BA": u"\U0001F4BA", "U+1F4B0": u"\U0001F4B0", "U+1F531": u"\U0001F531", "U+1F6AC": u"\U0001F6AC",
        "U+1F4A3": u"\U0001F4A3", "U+1F52B": u"\U0001F52B", "U+1F48A": u"\U0001F48A",
        "U+1F489": u"\U0001F489", "U+1F3C8": u"\U0001F3C8", "U+1F3C0": u"\U0001F3C0", "U+26BD": u"\U000026BD",
        "U+26BE": u"\U000026BE", "U+1F3BE": u"\U0001F3BE", "U+26F3": u"\U000026F3", "U+1F3B1": u"\U0001F3B1",
        "U+1F3CA": u"\U0001F3CA", "U+1F3C4": u"\U0001F3C4", "U+1F3BF": u"\U0001F3BF",
        "U+2660": u"\U00002660", "U+2665": u"\U00002665", "U+2663": u"\U00002663", "U+2666": u"\U00002666",
        "U+1F3C6": u"\U0001F3C6", "U+1F47E": u"\U0001F47E", "U+1F3AF": u"\U0001F3AF", "U+1F004": u"\U0001F004",
        "U+1F3AC": u"\U0001F3AC", "U+1F4DD": u"\U0001F4DD", "U+1F4D6": u"\U0001F4D6",
        "U+1F3A8": u"\U0001F3A8", "U+1F3A4": u"\U0001F3A4", "U+1F3A7": u"\U0001F3A7", "U+1F3BA": u"\U0001F3BA",
        "U+1F3B7": u"\U0001F3B7", "U+1F3B8": u"\U0001F3B8", "U+303D": u"\U0000303D", "U+1F45F": u"\U0001F45F",
        "U+1F461": u"\U0001F461", "U+1F460": u"\U0001F460", "U+1F462": u"\U0001F462",
        "U+1F455": u"\U0001F455", "U+1F454": u"\U0001F454", "U+1F457": u"\U0001F457", "U+1F458": u"\U0001F458",
        "U+1F459": u"\U0001F459", "U+1F380": u"\U0001F380", "U+1F3A9": u"\U0001F3A9", "U+1F451": u"\U0001F451",
        "U+1F452": u"\U0001F452", "U+1F302": u"\U0001F302", "U+1F4BC": u"\U0001F4BC",
        "U+1F45C": u"\U0001F45C", "U+1F484": u"\U0001F484", "U+1F48D": u"\U0001F48D", "U+1F48E": u"\U0001F48E",
        "U+2615": u"\U00002615", "U+1F375": u"\U0001F375", "U+1F37A": u"\U0001F37A", "U+1F37B": u"\U0001F37B",
        "U+1F378": u"\U0001F378", "U+1F376": u"\U0001F376", "U+1F374": u"\U0001F374",
        "U+1F354": u"\U0001F354", "U+1F35F": u"\U0001F35F", "U+1F35D": u"\U0001F35D", "U+1F35B": u"\U0001F35B",
        "U+1F371": u"\U0001F371", "U+1F363": u"\U0001F363", "U+1F359": u"\U0001F359", "U+1F358": u"\U0001F358",
        "U+1F35A": u"\U0001F35A", "U+1F35C": u"\U0001F35C", "U+1F372": u"\U0001F372",
        "U+1F35E": u"\U0001F35E", "U+1F373": u"\U0001F373", "U+1F362": u"\U0001F362", "U+1F361": u"\U0001F361",
        "U+1F366": u"\U0001F366", "U+1F367": u"\U0001F367", "U+1F382": u"\U0001F382", "U+1F370": u"\U0001F370",
        "U+1F34E": u"\U0001F34E", "U+1F34A": u"\U0001F34A", "U+1F349": u"\U0001F349",
        "U+1F353": u"\U0001F353", "U+1F346": u"\U0001F346", "U+1F345": u"\U0001F345"
    }
    return a


def get_emoji(key):
    all_emoji = get_all_emoji()
    if key in all_emoji:
        return all_emoji[key]
    return ''


def gen_random_emoji():
    import random
    all_emoji = get_all_emoji()
    keys = all_emoji.keys()
    return random.choice(keys)


def gen_emoji(desc):
    import re
    reg = re.compile('\[\d\]')
    res_list = reg.findall(desc)
    d = {}
    for key in res_list:
        if not key in d:
            d[key] = gen_random_emoji()

    for k, v in d.iteritems():
        desc = desc.replace(k, v)
    return desc


def match_emoji(desc):
    import re
    reg = re.compile('U\+[\w]{4,5}')
    res_list = reg.findall(desc)

    m = {}
    for key in res_list:
        if not key in m:
            m[key] = get_emoji(key)

    for k, v in m.iteritems():
        desc = desc.replace(k, v)

    return desc
