def la_so_hoan_hao(n):
    tong = 0
    for i in range(1, n):
        if n % i == 0:
            tong += i
    return tong == n

n = int(input("Nhap n: "))

if la_so_hoan_hao(n):
    print("La so hoan hao")
else:
    print("Khong phai so hoan hao")
