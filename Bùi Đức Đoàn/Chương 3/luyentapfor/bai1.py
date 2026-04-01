n = int(input("Nhập n: "))

for i in range(1, n):
    if 2 * i < n:
        print(f"{2*i} = 2*{i}")
