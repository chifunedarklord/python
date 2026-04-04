_tuple = ('ab', 'b', 'e', 'c', 'd', 'e', 'ab')

_new = []
for i in _tuple:
    if i not in _new:
        _new.append(i)

_new_tuple = tuple(_new)
print(_new_tuple)