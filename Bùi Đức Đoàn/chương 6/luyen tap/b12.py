_list = ['abc', 'xyz', 'aba', '1221', 'ii', 'ii2', '5yhy5']

n = int(input("Nhập n: "))

count = 0
for i in _list:
    if len(i) >= n and i[0] == i[-1]:
        count += 1

print("Kết quả:", count)