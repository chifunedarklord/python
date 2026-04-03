ten   = input("Tên: ")
tuoi  = input("Tuổi: ")
email = input("Email: ")
skype = input("Skype: ")
dc    = input("Địa chỉ: ")
nlv   = input("Nơi làm việc: ")

with open("setInfo.txt", "w", encoding="utf-8") as f:
    f.write(f"Tên: {ten}\nTuổi: {tuoi}\nEmail: {email}\n")
    f.write(f"Skype: {skype}\nĐịa chỉ: {dc}\nNơi làm việc: {nlv}\n")

with open("setInfo.txt", "r", encoding="utf-8") as f:
    print(f.read())
