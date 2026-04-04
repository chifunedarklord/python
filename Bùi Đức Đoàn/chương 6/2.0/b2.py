_tuple = ('ab', 'b', 'e', 'c', 'd', 'e', 'ab')

_new = []
for i in _tuple:
    if _tuple.count(i) == 1:
        _new.append(i)

_new_tuple = tuple(_new)
print(_new_tuple)