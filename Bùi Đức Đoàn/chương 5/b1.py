n = int(input("Nhập số dòng cần đọc: "))

with open("demo_file1.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i in range(min(n, len(lines))):
    print(lines[i], end="")
