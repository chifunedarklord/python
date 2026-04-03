text = input("Nhập đoạn văn bản: ")

with open("output.txt", "w", encoding="utf-8") as f:
    f.write(text)

with open("output.txt", "r", encoding="utf-8") as f:
    print("Nội dung file:", f.read())