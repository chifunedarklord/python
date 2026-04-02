import math

def la_so_nguyen_to(n):
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

n = int(input("Nhap n: "))

if la_so_nguyen_to(n):
    print("Day la so nguyen to")
else:
    print("Khong phai so nguyen to")
    