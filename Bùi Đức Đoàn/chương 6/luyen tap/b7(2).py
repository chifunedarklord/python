_list = ['abc', 'xyz', 'abc', '12', 'ii', '12', '5a']

_new = []
for i in _list:
    if i not in _new:
        _new.append(i)

print(_new)