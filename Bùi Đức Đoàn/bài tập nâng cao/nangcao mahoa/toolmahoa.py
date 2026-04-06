import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import os


# ─────────────────────────────────────────────
#  Core logic
# ─────────────────────────────────────────────

def load_cipher(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def encrypt_text(text: str, cipher: dict) -> str:
    result = []
    for ch in text:
        result.append(cipher.get(ch, ch))
    return "".join(result)


def decrypt_text(text: str, cipher: dict) -> str:
    reverse = {v: k for k, v in cipher.items()}
    result = []
    i = 0
    # Build a set of all cipher values sorted by length (longest first)
    # so multi-char tokens are matched greedily
    tokens = sorted(reverse.keys(), key=len, reverse=True)
    while i < len(text):
        matched = False
        for tok in tokens:
            if text[i:i+len(tok)] == tok:
                result.append(reverse[tok])
                i += len(tok)
                matched = True
                break
        if not matched:
            result.append(text[i])
            i += 1
    return "".join(result)


# ─────────────────────────────────────────────
#  GUI
# ─────────────────────────────────────────────

DARK_BG   = "#0f0e17"
CARD_BG   = "#1a1928"
ACCENT    = "#e94560"
ACCENT2   = "#0f3460"
TEXT_PRI  = "#fffffe"
TEXT_SEC  = "#a7a9be"
INPUT_BG  = "#16213e"
BORDER    = "#2a2a4a"
SUCCESS   = "#06d6a0"
WARNING   = "#ffd166"


class CipherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🔐  Cipher Tool")
        self.geometry("900x680")
        self.minsize(760, 580)
        self.configure(bg=DARK_BG)

        self.cipher_path = tk.StringVar()
        self.input_path  = tk.StringVar()
        self.output_path = tk.StringVar()

        self._build_ui()

    # ── layout ──────────────────────────────

    def _build_ui(self):
        # title bar
        hdr = tk.Frame(self, bg=DARK_BG, pady=18)
        hdr.pack(fill="x", padx=30)
        tk.Label(hdr, text="CIPHER", font=("Courier New", 28, "bold"),
                 fg=ACCENT, bg=DARK_BG).pack(side="left")
        tk.Label(hdr, text=" TOOL", font=("Courier New", 28, "bold"),
                 fg=TEXT_PRI, bg=DARK_BG).pack(side="left")
        tk.Label(hdr, text="  v1.0  —  Mã hóa & Giải mã văn bản",
                 font=("Courier New", 10), fg=TEXT_SEC, bg=DARK_BG).pack(
                 side="left", padx=12, pady=6)

        sep = tk.Frame(self, height=2, bg=ACCENT)
        sep.pack(fill="x", padx=30)

        # notebook
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook",           background=DARK_BG, borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=CARD_BG, foreground=TEXT_SEC,
                        font=("Courier New", 11, "bold"),
                        padding=[20, 8])
        style.map("TNotebook.Tab",
                  background=[("selected", ACCENT2)],
                  foreground=[("selected", TEXT_PRI)])

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=30, pady=20)

        tab_enc = tk.Frame(nb, bg=DARK_BG)
        tab_dec = tk.Frame(nb, bg=DARK_BG)
        tab_mgr = tk.Frame(nb, bg=DARK_BG)

        nb.add(tab_enc, text="  🔒  Mã hóa  ")
        nb.add(tab_dec, text="  🔓  Giải mã  ")
        nb.add(tab_mgr, text="  📋  Quản lý bộ mã  ")

        self._build_encrypt_tab(tab_enc)
        self._build_decrypt_tab(tab_dec)
        self._build_manager_tab(tab_mgr)

        # status bar
        self.status_var = tk.StringVar(value="Sẵn sàng.")
        sb = tk.Label(self, textvariable=self.status_var,
                      font=("Courier New", 9), fg=TEXT_SEC,
                      bg=DARK_BG, anchor="w", padx=32)
        sb.pack(fill="x", side="bottom", pady=(0, 6))

    # ── shared widgets ───────────────────────

    def _card(self, parent, title=""):
        frame = tk.Frame(parent, bg=CARD_BG, bd=0,
                         highlightbackground=BORDER, highlightthickness=1)
        frame.pack(fill="x", padx=6, pady=6)
        if title:
            tk.Label(frame, text=title, font=("Courier New", 10, "bold"),
                     fg=ACCENT, bg=CARD_BG, anchor="w").pack(
                     fill="x", padx=14, pady=(10, 4))
        return frame

    def _file_row(self, parent, label, var, save=False, filetypes=None):
        row = tk.Frame(parent, bg=CARD_BG)
        row.pack(fill="x", padx=14, pady=4)
        tk.Label(row, text=label, width=18, anchor="w",
                 font=("Courier New", 10), fg=TEXT_SEC, bg=CARD_BG).pack(side="left")
        entry = tk.Entry(row, textvariable=var, font=("Courier New", 10),
                         bg=INPUT_BG, fg=TEXT_PRI, insertbackground=TEXT_PRI,
                         relief="flat", bd=4)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        cmd = (lambda v=var, ft=filetypes: self._save_file(v, ft)) if save \
              else (lambda v=var, ft=filetypes: self._open_file(v, ft))
        btn = tk.Button(row, text="Chọn", font=("Courier New", 9, "bold"),
                        fg=TEXT_PRI, bg=ACCENT2, activebackground=ACCENT,
                        relief="flat", bd=0, padx=10, cursor="hand2",
                        command=cmd)
        btn.pack(side="left")

    def _open_file(self, var, filetypes):
        ft = filetypes or [("All files", "*.*")]
        p = filedialog.askopenfilename(filetypes=ft)
        if p:
            var.set(p)

    def _save_file(self, var, filetypes):
        ft = filetypes or [("All files", "*.*")]
        p = filedialog.asksaveasfilename(filetypes=ft, defaultextension=ft[0][1])
        if p:
            var.set(p)

    def _btn(self, parent, text, cmd, color=ACCENT):
        return tk.Button(parent, text=text,
                         font=("Courier New", 11, "bold"),
                         fg=TEXT_PRI, bg=color,
                         activebackground=TEXT_PRI, activeforeground=DARK_BG,
                         relief="flat", bd=0, padx=22, pady=8,
                         cursor="hand2", command=cmd)

    def _log_area(self, parent):
        box = scrolledtext.ScrolledText(
            parent, height=8, font=("Courier New", 9),
            bg=INPUT_BG, fg=SUCCESS, insertbackground=TEXT_PRI,
            relief="flat", bd=6, wrap="word", state="disabled")
        box.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        return box

    def _log(self, box, msg, color=SUCCESS):
        box.configure(state="normal")
        box.insert("end", msg + "\n")
        box.see("end")
        box.configure(state="disabled")
        self.status_var.set(msg)

    # ── encrypt tab ──────────────────────────

    def _build_encrypt_tab(self, tab):
        pad = tk.Frame(tab, bg=DARK_BG)
        pad.pack(fill="both", expand=True, padx=8, pady=8)

        c1 = self._card(pad, "📂  Tệp đầu vào")
        self._file_row(c1, "File mật mã (JSON):", self.cipher_path,
                       filetypes=[("JSON", "*.json"), ("All", "*.*")])
        self._file_row(c1, "File văn bản gốc:", self.input_path,
                       filetypes=[("Text", "*.txt"), ("All", "*.*")])
        self._file_row(c1, "File kết quả:", self.output_path,
                       save=True, filetypes=[("Text", "*.txt"), ("All", "*.*")])
        tk.Frame(c1, height=8, bg=CARD_BG).pack()

        c2 = self._card(pad, "⚡  Thực thi")
        btnrow = tk.Frame(c2, bg=CARD_BG)
        btnrow.pack(padx=14, pady=8, anchor="w")
        self._btn(btnrow, "🔒  MÃ HÓA NGAY", self._do_encrypt).pack(side="left", padx=(0, 10))
        self._btn(btnrow, "Xem trước văn bản gốc",
                  self._preview_input, color=ACCENT2).pack(side="left")

        c3 = self._card(pad, "📋  Nhật ký")
        self.enc_log = self._log_area(c3)

    # ── decrypt tab ──────────────────────────

    def _build_decrypt_tab(self, tab):
        pad = tk.Frame(tab, bg=DARK_BG)
        pad.pack(fill="both", expand=True, padx=8, pady=8)

        self.dec_cipher_path = tk.StringVar()
        self.dec_input_path  = tk.StringVar()
        self.dec_output_path = tk.StringVar()

        c1 = self._card(pad, "📂  Tệp đầu vào")
        self._file_row(c1, "File mật mã (JSON):", self.dec_cipher_path,
                       filetypes=[("JSON", "*.json"), ("All", "*.*")])
        self._file_row(c1, "File đã mã hóa:", self.dec_input_path,
                       filetypes=[("Text", "*.txt"), ("All", "*.*")])
        self._file_row(c1, "File kết quả:", self.dec_output_path,
                       save=True, filetypes=[("Text", "*.txt"), ("All", "*.*")])
        tk.Frame(c1, height=8, bg=CARD_BG).pack()

        c2 = self._card(pad, "⚡  Thực thi")
        btnrow = tk.Frame(c2, bg=CARD_BG)
        btnrow.pack(padx=14, pady=8, anchor="w")
        self._btn(btnrow, "🔓  GIẢI MÃ NGAY", self._do_decrypt).pack(side="left", padx=(0, 10))
        self._btn(btnrow, "Xem trước file mã hóa",
                  self._preview_encrypted, color=ACCENT2).pack(side="left")

        c3 = self._card(pad, "📋  Nhật ký")
        self.dec_log = self._log_area(c3)

    # ── manager tab ──────────────────────────

    def _build_manager_tab(self, tab):
        pad = tk.Frame(tab, bg=DARK_BG)
        pad.pack(fill="both", expand=True, padx=8, pady=8)

        top = tk.Frame(pad, bg=DARK_BG)
        top.pack(fill="x")

        left = self._card(top, "✏️  Soạn bộ mã mới (JSON)")
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self.cipher_editor = scrolledtext.ScrolledText(
            left, height=14, font=("Courier New", 10),
            bg=INPUT_BG, fg=WARNING, insertbackground=TEXT_PRI,
            relief="flat", bd=6, wrap="word")
        self.cipher_editor.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        sample = '{\n  "a": "!",\n  "b": "@",\n  "c": "#",\n  " ": "_"\n}'
        self.cipher_editor.insert("1.0", sample)

        right = self._card(top, "💾  Lưu / Tải")
        right.pack(side="left", fill="y", padx=(0, 0))

        self.mgr_path = tk.StringVar()
        self._file_row(right, "Đường dẫn:", self.mgr_path,
                       filetypes=[("JSON", "*.json"), ("All", "*.*")])

        bpad = tk.Frame(right, bg=CARD_BG)
        bpad.pack(padx=14, pady=6, fill="x")
        self._btn(bpad, "💾  Lưu", self._save_cipher, color=SUCCESS).pack(fill="x", pady=3)
        self._btn(bpad, "📂  Tải", self._load_cipher_editor, color=ACCENT2).pack(fill="x", pady=3)
        self._btn(bpad, "✅  Kiểm tra JSON", self._validate_json, color=WARNING).pack(fill="x", pady=3)

        c2 = self._card(pad, "📋  Nhật ký")
        self.mgr_log = self._log_area(c2)

    # ── actions ──────────────────────────────

    def _do_encrypt(self):
        cp = self.cipher_path.get().strip()
        ip = self.input_path.get().strip()
        op = self.output_path.get().strip()
        if not cp or not ip or not op:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn đầy đủ các file.")
            return
        try:
            cipher = load_cipher(cp)
            with open(ip, "r", encoding="utf-8") as f:
                plain = f.read()
            enc = encrypt_text(plain, cipher)
            with open(op, "w", encoding="utf-8") as f:
                f.write(enc)
            self._log(self.enc_log,
                      f"✅  Mã hóa thành công! {len(plain)} ký tự → {op}")
            self._log(self.enc_log,
                      f"   Dùng {len(cipher)} ký tự trong bộ mã, {sum(ch in cipher for ch in plain)} ký tự được thay thế.")
        except Exception as e:
            self._log(self.enc_log, f"❌  Lỗi: {e}", color=ACCENT)
            messagebox.showerror("Lỗi", str(e))

    def _do_decrypt(self):
        cp = self.dec_cipher_path.get().strip()
        ip = self.dec_input_path.get().strip()
        op = self.dec_output_path.get().strip()
        if not cp or not ip or not op:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn đầy đủ các file.")
            return
        try:
            cipher = load_cipher(cp)
            with open(ip, "r", encoding="utf-8") as f:
                enc = f.read()
            plain = decrypt_text(enc, cipher)
            with open(op, "w", encoding="utf-8") as f:
                f.write(plain)
            self._log(self.dec_log,
                      f"✅  Giải mã thành công! → {op}")
            self._log(self.dec_log,
                      f"   Kết quả: {len(plain)} ký tự.")
        except Exception as e:
            self._log(self.dec_log, f"❌  Lỗi: {e}", color=ACCENT)
            messagebox.showerror("Lỗi", str(e))

    def _preview_input(self):
        ip = self.input_path.get().strip()
        if not ip:
            messagebox.showinfo("Thông tin", "Chưa chọn file văn bản gốc.")
            return
        self._show_preview("Văn bản gốc", ip)

    def _preview_encrypted(self):
        ip = self.dec_input_path.get().strip()
        if not ip:
            messagebox.showinfo("Thông tin", "Chưa chọn file mã hóa.")
            return
        self._show_preview("File đã mã hóa", ip)

    def _show_preview(self, title, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read(2000)
            win = tk.Toplevel(self)
            win.title(f"Xem trước — {title}")
            win.geometry("600x400")
            win.configure(bg=DARK_BG)
            tk.Label(win, text=os.path.basename(path),
                     font=("Courier New", 11, "bold"),
                     fg=ACCENT, bg=DARK_BG).pack(anchor="w", padx=14, pady=8)
            box = scrolledtext.ScrolledText(win, font=("Courier New", 10),
                                            bg=INPUT_BG, fg=TEXT_PRI,
                                            relief="flat", bd=6)
            box.pack(fill="both", expand=True, padx=14, pady=(0, 14))
            box.insert("1.0", content + ("\n…(cắt bớt)" if len(content) == 2000 else ""))
            box.configure(state="disabled")
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def _save_cipher(self):
        path = self.mgr_path.get().strip()
        if not path:
            path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON", "*.json"), ("All", "*.*")])
            if not path:
                return
            self.mgr_path.set(path)
        raw = self.cipher_editor.get("1.0", "end").strip()
        try:
            data = json.loads(raw)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._log(self.mgr_log, f"✅  Đã lưu bộ mã → {path}")
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON không hợp lệ", str(e))

    def _load_cipher_editor(self):
        path = self.mgr_path.get().strip()
        if not path:
            path = filedialog.askopenfilename(
                filetypes=[("JSON", "*.json"), ("All", "*.*")])
            if not path:
                return
            self.mgr_path.set(path)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.cipher_editor.delete("1.0", "end")
            self.cipher_editor.insert("1.0", json.dumps(data, ensure_ascii=False, indent=2))
            self._log(self.mgr_log, f"✅  Đã tải bộ mã từ {path}")
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def _validate_json(self):
        raw = self.cipher_editor.get("1.0", "end").strip()
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("Bộ mã phải là một JSON object (dict).")
            self._log(self.mgr_log,
                      f"✅  JSON hợp lệ — {len(data)} cặp mã.")
        except Exception as e:
            self._log(self.mgr_log, f"❌  {e}", color=ACCENT)
            messagebox.showerror("Lỗi JSON", str(e))


# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = CipherApp()
    app.mainloop()