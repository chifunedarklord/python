# Từ điển mã hóa
code_map = {'a': '!', 'b': '@', 'c': '#', 'd': '$'}

# Tạo từ điển giải mã (đảo key-value)
decode_map = {v: k for k, v in code_map.items()}

# Hàm mã hóa
def encode(text):
    result = ""
    for ch in text:
        if ch in code_map:
            result += code_map[ch]
        else:
            result += ch
    return result

# Hàm giải mã
def decode(text):
    result = ""
    for ch in text:
        if ch in decode_map:
            result += decode_map[ch]
        else:
            result += ch
    return result

# Test
text = input("Nhập văn bản: ")

encoded = encode(text)
print("Mã hóa:", encoded)

decoded = decode(encoded)
print("Giải mã:", decoded)