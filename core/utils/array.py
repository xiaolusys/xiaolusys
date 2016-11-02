from collections import defaultdict

def iterable(obj):
    try: iter(obj)
    except: return False
    return True

flatten = lambda x: [y for l in x for y in flatten(l)] if type(x) is list else [x]

def group_count(list):
    d = defaultdict(int)
    for key in list:
        d[key] += 1
    return d