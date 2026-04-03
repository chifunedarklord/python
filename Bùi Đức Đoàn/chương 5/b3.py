with open("demo_file1.txt", "w", encoding="utf-8") as f:
    f.write("Thuc \n hanh \n voi \n file\n IO\n")
with open("demo_file1.txt", "r", encoding="utf-8") as f:
    print(f.read())
with open("demo_file1.txt", "r", encoding="utf-8") as f:
    for line in f.readlines():
        print(line, end="")