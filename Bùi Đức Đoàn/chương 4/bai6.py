def la_so_hoan_hao(n):
    tong = 0
    for i in range(1, n):
        if n % i == 0:
            tong += i
    return tong == n

a = int(input("Nhap a: "))
b = int(input("Nhap b: "))

print("Cac so hoan hao trong khoang:")
for i in range(a, b + 1):
    if la_so_hoan_hao(i):
        print(i, end=" ")
