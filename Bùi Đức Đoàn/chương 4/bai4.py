import math

def la_so_nguyen_to(n):
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

a = int(input("Nhap a: "))
b = int(input("Nhap b: "))

print("Cac so nguyen to trong khoang:")
for i in range(a, b + 1):
    if la_so_nguyen_to(i):
        print(i, end=" ")
