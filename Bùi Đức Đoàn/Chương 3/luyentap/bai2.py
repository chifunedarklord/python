def tong_nhieu_so(ds):
    tong = 0
    for x in ds:
        tong += x
    return tong

n = int(input("Nhap so luong phan tu: "))
ds = []

for i in range(n):
    x = int(input("Nhap so: "))
    ds.append(x)

print("Tong =", tong_nhieu_so(ds))
