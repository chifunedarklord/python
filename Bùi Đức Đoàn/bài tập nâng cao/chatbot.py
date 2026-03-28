import tkinter as tk
from tkinter import scrolledtext, ttk
import threading
from openai import OpenAI

API_KEY = "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"   # ⚠️ NÊN dùng biến môi trường
MODEL   = "openrouter/free"

client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=API_KEY)

BG       = "#0f0f17"
SURFACE  = "#1a1a28"
CARD     = "#22223a"
BORDER   = "#2e2e4a"
ACCENT   = "#7c6dfa"
ACCENT2  = "#fa6d7c"
GREEN    = "#6dfabc"
TEXT     = "#e8e8f8"
MUTED    = "#6a6a8a"
FONT_UI  = ("Consolas", 11)
FONT_BIG = ("Consolas", 13, "bold")
FONT_OUT = ("Courier New", 11)

def call_ai(prompt: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{
            "role": "user",
            "content": (
                f"Viết code Python cho yêu cầu sau.\n"
                f"Chỉ trả về code Python thuần túy, "
                f"KHÔNG dùng markdown, KHÔNG có ```python, KHÔNG có ```:\n{prompt}"
            )
        }]
    )
    code = response.choices[0].message.content.strip()
    return code.replace("```python", "").replace("```", "").strip()

root = tk.Tk()
root.title("Python AI Code Generator")
root.geometry("860x640")
root.configure(bg=BG)
root.resizable(True, True)

header = tk.Frame(root, bg=SURFACE, pady=14)
header.pack(fill="x")

tk.Label(header, text="PYTHON AI CODE GENERATOR",
         bg=SURFACE, fg=ACCENT, font=("Consolas", 16, "bold")).pack()
tk.Label(header, text="Nhập yêu cầu → AI tạo code Python ngay lập tức",
         bg=SURFACE, fg=MUTED, font=("Consolas", 9)).pack()

sep = tk.Frame(root, height=2, bg=ACCENT)
sep.pack(fill="x")

input_frame = tk.Frame(root, bg=BG, padx=20, pady=14)
input_frame.pack(fill="x")

tk.Label(input_frame, text="YÊU CẦU BÀI LẬP TRÌNH",
         bg=BG, fg=MUTED, font=("Consolas", 8, "bold")).pack(anchor="w")

entry_box = tk.Text(input_frame, height=3, bg=SURFACE, fg=TEXT,
                    font=FONT_UI, relief="flat", bd=0,
                    insertbackground=ACCENT, wrap="word",
                    padx=12, pady=10, highlightthickness=1,
                    highlightbackground=BORDER,
                    highlightcolor=ACCENT)
entry_box.pack(fill="x", pady=(6, 0))

PLACEHOLDER = "VD: Tính tổng từ 1 đến n, kiểm tra số nguyên tố..."

def on_focus_in(e):
    if entry_box.get("1.0", "end-1c") == PLACEHOLDER:
        entry_box.delete("1.0", "end")
        entry_box.configure(fg=TEXT)

def on_focus_out(e):
    if not entry_box.get("1.0", "end-1c").strip():
        entry_box.insert("1.0", PLACEHOLDER)
        entry_box.configure(fg=MUTED)

entry_box.insert("1.0", PLACEHOLDER)
entry_box.configure(fg=MUTED)
entry_box.bind("<FocusIn>", on_focus_in)
entry_box.bind("<FocusOut>", on_focus_out)

btn_row = tk.Frame(root, bg=BG, padx=20)
btn_row.pack(fill="x")

examples = [
    "Tính tổng 1→n",
    "Số nguyên tố",
    "Giai thừa n!",
    "Sắp xếp mảng",
    "Đảo chuỗi",
    "FizzBuzz",
]

chips_frame = tk.Frame(btn_row, bg=BG)
chips_frame.pack(side="left", fill="x", expand=True)

tk.Label(chips_frame, text="Thử nhanh: ", bg=BG, fg=MUTED,
         font=("Consolas", 8)).pack(side="left", pady=6)

def use_example(text):
    entry_box.configure(fg=TEXT)
    entry_box.delete("1.0", "end")
    entry_box.insert("1.0", text)

for ex in examples:
    tk.Button(chips_frame, text=ex, bg=CARD, fg="#a89ef8",
              font=("Consolas", 8), relief="flat", bd=0,
              padx=8, pady=3, cursor="hand2",
              activebackground=BORDER, activeforeground=TEXT,
              command=lambda x=ex: use_example(x)
              ).pack(side="left", padx=3, pady=6)

status_var = tk.StringVar(value="")

def set_btn_state(loading: bool):
    if loading:
        gen_btn.configure(text="Đang tạo code...", state="disabled",
                          bg=BORDER, fg=MUTED)
        status_var.set("AI đang xử lý yêu cầu...")
    else:
        gen_btn.configure(text="⚡  TẠO CODE PYTHON", state="normal",
                          bg=ACCENT, fg="white")
        status_var.set("")

def generate():
    prompt = entry_box.get("1.0", "end-1c").strip()
    if not prompt or prompt == PLACEHOLDER:
        show_result("⚠  Vui lòng nhập yêu cầu bài lập trình!")
        return

    set_btn_state(True)
    show_result("# Đang kết nối AI...\n")

    def worker():
        try:
            code = call_ai(prompt)
            root.after(0, lambda code=code: show_result(code))   # ✅ FIX
        except Exception as e:
            root.after(0, lambda e=e: show_result(f"# Lỗi: {e}"))  # ✅ FIX

    threading.Thread(target=worker, daemon=True).start()

def show_result(code: str):
    output_box.configure(state="normal")
    output_box.delete("1.0", "end")
    output_box.insert("1.0", code)
    output_box.configure(state="disabled")
    set_btn_state(False)
    status_var.set(f" Tạo thành công!  ({len(code.splitlines())} dòng code)")

gen_btn = tk.Button(root, text="⚡  TẠO CODE PYTHON",
                    bg=ACCENT, fg="white", font=("Consolas", 12, "bold"),
                    relief="flat", bd=0, pady=12,
                    cursor="hand2", activebackground="#5a4edb",
                    command=generate)
gen_btn.pack(fill="x", padx=20, pady=(4, 0))

root.bind("<Control-Return>", lambda e: generate())

out_label_row = tk.Frame(root, bg=BG, padx=20)
out_label_row.pack(fill="x", pady=(12, 0))

tk.Label(out_label_row, text=" CODE PYTHON", bg=BG, fg=MUTED,
         font=("Consolas", 8, "bold")).pack(side="left")

def copy_code():
    code = output_box.get("1.0", "end-1c").strip()
    if code and not code.startswith("⚠") and not code.startswith("# Đang"):
        root.clipboard_clear()
        root.clipboard_append(code)
        copy_btn.configure(text="✓ Đã copy!", fg=GREEN)
        root.after(2000, lambda: copy_btn.configure(text="Copy Code", fg=ACCENT))

copy_btn = tk.Button(out_label_row, text="Copy Code",
                     bg=BG, fg=ACCENT, font=("Consolas", 8),
                     relief="flat", bd=0, cursor="hand2",
                     command=copy_code)
copy_btn.pack(side="right")

output_box = scrolledtext.ScrolledText(
    root, bg="#0d0d18", fg="#c8d3f0",
    font=FONT_OUT, relief="flat", bd=0,
    padx=18, pady=14, wrap="none",
    insertbackground=ACCENT,
    state="disabled"
)
output_box.pack(fill="both", expand=True, padx=20, pady=(0, 0))

status_bar = tk.Frame(root, bg=SURFACE, pady=5)
status_bar.pack(fill="x")

tk.Label(status_bar, textvariable=status_var,
         bg=SURFACE, fg=GREEN, font=("Consolas", 8)).pack(side="left", padx=14)

tk.Label(status_bar, text="Ctrl+Enter = Tạo code  |  OpenRouter API",
         bg=SURFACE, fg=MUTED, font=("Consolas", 8)).pack(side="right", padx=14)

root.mainloop()
