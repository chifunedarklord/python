n = int(input("Nhập một số nguyên dương: "))

if n > 0:
    chia_het_2 = (n % 2 == 0)
    chia_het_3 = (n % 3 == 0)
    
    if chia_het_2 and chia_het_3:
        print(f"{n} chia hết cho cả 2 và 3")
    elif chia_het_2:
        print(f"{n} chia hết cho 2 nhưng không chia hết cho 3")
    elif chia_het_3:
        print(f"{n} chia hết cho 3 nhưng không chia hết cho 2")
    else:
        print(f"{n} không chia hết cho 2 và cũng không chia hết cho 3")
else:
    print("Vui lòng nhập số nguyên dương!")
