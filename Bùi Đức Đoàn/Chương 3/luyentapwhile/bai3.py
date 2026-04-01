n = int(input("Nhập n: "))

if n < 2:
    print("Không phải số nguyên tố")
else:
    i = 2
    la_so_nguyen_to = True

    while i <= n // 2:
        if n % i == 0:
            la_so_nguyen_to = False
            break
        i += 1

    if la_so_nguyen_to:
        print("Đây là số nguyên tố")
    else:
        print("Không phải số nguyên tố")