n = int(input("Nhập n: "))

if n > 10:
    print("Số nhập vào phải bé hơn 10")
else:
    for i in range(1, n + 1):
        if i % 2 == 0:
            print(i, end=" ")