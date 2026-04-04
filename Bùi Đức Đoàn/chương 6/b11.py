_list = ['apple', 'hi', 'banana', 'cat', 'hello']

n = int(input("Nhập n: "))

result = []
for i in _list:
    if len(i) > n:
        result.append(i)

print(result)