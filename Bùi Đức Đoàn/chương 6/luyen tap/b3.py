_list = [1, 2, 3, 4, 5, 6, 7, 8, 9]

even = []
odd = []

for i in _list:
    if i % 2 == 0:
        even.append(i)
    else:
        odd.append(i)

print("Chẵn:", even)
print("Lẻ:", odd)