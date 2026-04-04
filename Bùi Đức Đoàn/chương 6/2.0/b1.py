_tuple = ('a', 'b', 'd', 'e')

temp = list(_tuple)
temp.insert(2, 'c')

_new_tuple = tuple(temp)
print(_new_tuple)