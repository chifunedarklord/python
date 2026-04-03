with open("demo_file2.txt", "w") as f:
    f.write("Dem so luong tu xuat hien abc abc abc 12 12 it it eaut")

word_count = {}
with open("demo_file2.txt", "r") as f:
    words = f.read().split()
    for word in words:
        word_count[word] = word_count.get(word, 0) + 1

print(word_count)