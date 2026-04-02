import math

def tong_hai_so(a, b):
    return a + b

def la_so_nguyen_to(n):
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

def la_so_hoan_hao(n):
    tong = 0
    for i in range(1, n):
        if n % i == 0:
            tong += i
    return tong == n

while True:
    print("\n MENU ")
    print("1. Tong 2 so")
    print("2. Kiem tra so nguyen to")
    print("3. Kiem tra so hoan hao")
    print("0. Thoat")

    chon = int(input("Chon: "))

    if chon == 1:
        a = int(input("Nhap a: "))
        b = int(input("Nhap b: "))
        print("Tong =", tong_hai_so(a, b))

    elif chon == 2:
        n = int(input("Nhap n: "))
        if la_so_nguyen_to(n):
            print("La so nguyen to")
        else:
            print("Khong phai")

    elif chon == 3:
        n = int(input("Nhap n: "))
        if la_so_hoan_hao(n):
            print("La so hoan hao")
        else:
            print("Khong phai")

    elif chon == 0:
        break

    else:
        print("Lua chon khong hop le")
