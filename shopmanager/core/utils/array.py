
flatten = lambda x: [y for l in x for y in flatten(l)] if type(x) is list else [x]