_list = ['abc', 'xyz', 'abc', '12', 'ii', '12', '5a']

_new = []
for i in _list:
    if _list.count(i) == 1:
        _new.append(i)

print(_new)