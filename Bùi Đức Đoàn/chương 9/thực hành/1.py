class HocVien:
    def __init__(self, ho_ten, ngay_sinh, email, dien_thoai, dia_chi, lop):
        self.ho_ten = ho_ten
        self.ngay_sinh = ngay_sinh
        self.email = email
        self.dien_thoai = dien_thoai
        self.dia_chi = dia_chi
        self.lop = lop

    def show_info(self):
        print("Họ tên:", self.ho_ten)
        print("Ngày sinh:", self.ngay_sinh)
        print("Email:", self.email)
        print("Điện thoại:", self.dien_thoai)
        print("Địa chỉ:", self.dia_chi)
        print("Lớp:", self.lop)

    def change_info(self, dia_chi="Hà Nội", lop="IT12.x"):
        self.dia_chi = dia_chi
        self.lop = lop


hv1 = HocVien(
    "Bùi Đức Đoàn   ",
    "20/11/2005",
    "chuatebongtoi@gmail.com",
    "123456789",
    "Ha Noi",
    "IT14.1"
)

print("=== Thông tin ban đầu ===")
hv1.show_info()

hv1.change_info()

print("\n=== Sau khi cập nhật ===")
hv1.show_info()