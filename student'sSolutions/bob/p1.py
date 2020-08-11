def _flatten(L):
    for item in L:
        try:
            yield from flatten(item)
        except TypeError:
            yield item

def flatten(L):
    return list(_flatten(L))