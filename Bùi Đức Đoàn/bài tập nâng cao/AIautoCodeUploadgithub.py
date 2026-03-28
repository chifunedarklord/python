
import os, re, sys, time, base64, json, threading
from pathlib import Path

# ── Kiểm tra thư viện ───────────────────────────────────────
missing = []
try:    from openai import OpenAI
except: missing.append("openai")
try:    import requests
except: missing.append("requests")

if missing:
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk(); root.withdraw()
    messagebox.showerror(
        "Thiếu thư viện",
        f"Chưa cài: {', '.join(missing)}\n\nMở CMD và chạy:\n  pip install {' '.join(missing)}"
    )
    sys.exit(1)

try:
    from dotenv import load_dotenv; load_dotenv()
except: pass

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox

# ── Màu sắc & font ──────────────────────────────────────────
BG         = "#0f0f17"
SURFACE    = "#1a1a28"
CARD       = "#22223a"
BORDER     = "#2e2e4a"
ACCENT     = "#7c6dfa"
GREEN      = "#6dfabc"
YELLOW     = "#f1fa8c"
RED        = "#ff5555"
CYAN       = "#8be9fd"
TEXT       = "#e8e8f8"
MUTED      = "#6a6a8a"
FONT_UI    = ("Consolas", 10)
FONT_BOLD  = ("Consolas", 10, "bold")
FONT_MONO  = ("Consolas", 9)
FONT_TITLE = ("Consolas", 14, "bold")
FONT_H2    = ("Consolas", 11, "bold")

CONFIG_FILE = Path(__file__).parent / ".gui_config.json"
OR_BASE_URL = "https://openrouter.ai/api/v1"


# ════════════════════════════════════════════════════════════
#  LOGIC CORE
# ════════════════════════════════════════════════════════════

def parse_problems(text: str) -> list:
    pattern = r"[Bb][àa][Ii]\s*(\d+)\s*[:\.]([\s\S]*?)(?=[Bb][àa][Ii]\s*\d+\s*[:\.]|$)"
    problems = []
    for num, content in re.findall(pattern, text):
        content = content.strip()
        if len(content) > 10:
            problems.append({
                "num":      num.strip(),
                "content":  content,
                "filename": f"Bai{num.strip()}.py",
            })
    return problems

def generate_code(client, model: str, problem: dict) -> str:
    prompt = (
        f"Bạn là giáo viên lập trình Python cho sinh viên năm nhất.\n"
        f"Hãy viết code Python hoàn chỉnh để giải bài tập sau:\n\n"
        f"\"{problem['content']}\"\n\n"
        f"Yêu cầu bắt buộc:\n"
        f"- Chỉ trả về code Python thuần túy, KHÔNG markdown, KHÔNG backtick\n"
        f"- Dòng đầu là comment: # Bài {problem['num']}: <tóm tắt tên bài>\n"
        f"- Có comment tiếng Việt giải thích logic\n"
        f"- Dùng input() để nhập, print() để xuất\n"
        f"- Code chạy được ngay, xử lý trường hợp đặc biệt nếu cần"
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    code = resp.choices[0].message.content.strip()
    code = re.sub(r"^```(?:python)?\n?", "", code)
    code = re.sub(r"\n?```$", "", code)
    return code.strip()

def push_to_github(token, repo, branch, folder, filename, code, commit_msg) -> dict:
    folder = folder.strip("/")
    path_in_repo = f"{folder}/{filename}" if folder else filename
    api_url = f"https://api.github.com/repos/{repo}/contents/{path_in_repo}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    sha = None
    r = requests.get(f"{api_url}?ref={branch}", headers=headers, timeout=15)
    if r.status_code == 200:
        sha = r.json().get("sha")
    content_b64 = base64.b64encode(code.encode("utf-8")).decode("ascii")
    body = {"message": commit_msg, "content": content_b64, "branch": branch}
    if sha: body["sha"] = sha
    r2 = requests.put(api_url, headers=headers, json=body, timeout=15)
    if r2.status_code in (200, 201):
        return {"success": True, "url": r2.json().get("content", {}).get("html_url", "")}
    return {"success": False, "url": "", "error": r2.json().get("message", r2.text)}

def save_local(problem, code, out_dir) -> Path:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    fp = Path(out_dir) / problem["filename"]
    fp.write_text(code, encoding="utf-8")
    return fp


# ════════════════════════════════════════════════════════════
#  WIDGET HELPERS
# ════════════════════════════════════════════════════════════

def lbl(parent, text, font=FONT_UI, fg=TEXT, bg=BG, **kw):
    return tk.Label(parent, text=text, font=font, fg=fg, bg=bg, **kw)

def ent(parent, var=None, show=None, w=38):
    return tk.Entry(
        parent, textvariable=var, show=show, width=w, font=FONT_UI,
        bg=CARD, fg=TEXT, insertbackground=TEXT, relief="flat", bd=0,
        highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT,
    )

def btn(parent, text, cmd, bg=ACCENT, fg="white", w=None):
    cfg = dict(text=text, command=cmd, font=FONT_BOLD, bg=bg, fg=fg,
               activebackground=BORDER, activeforeground=TEXT,
               relief="flat", bd=0, cursor="hand2", padx=12, pady=7)
    if w: cfg["width"] = w
    return tk.Button(parent, **cfg)

def frm(parent, bg=BG, px=0, py=0):
    return tk.Frame(parent, bg=bg, padx=px, pady=py)

def sec(parent, icon, text):
    f = frm(parent)
    f.pack(fill="x", pady=(14, 4))
    tk.Frame(f, bg=ACCENT, width=3).pack(side="left", fill="y", padx=(0, 8))
    lbl(f, f"{icon}  {text}", font=FONT_H2, fg=ACCENT).pack(side="left")


# ════════════════════════════════════════════════════════════
#  APP
# ════════════════════════════════════════════════════════════

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Auto Code + GitHub Pusher  —  OpenRouter AI (Miễn phí)")
        self.configure(bg=BG)
        w, h = 980, 800
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.minsize(820, 620)

        # ── Biến ──
        self.v_or_key    = tk.StringVar(value=os.getenv("OPENROUTER_API_KEY", ""))
        self.v_or_model  = tk.StringVar(value="openrouter/auto")
        self.v_gh_token  = tk.StringVar(value=os.getenv("GITHUB_TOKEN", ""))
        self.v_gh_repo   = tk.StringVar(value=os.getenv("GITHUB_REPO", ""))
        self.v_gh_branch = tk.StringVar(value="main")
        self.v_gh_folder = tk.StringVar(value="")
        self.v_out_dir   = tk.StringVar(value="output")
        self.v_show_key  = tk.BooleanVar(value=False)
        self.v_show_gh   = tk.BooleanVar(value=False)
        self.v_auto_push = tk.BooleanVar(value=True)

        self.generated   = []
        self.running     = False
        self._load_cfg()
        self._build()

    # ── Config ──────────────────────────────────────────────

    def _load_cfg(self):
        if CONFIG_FILE.exists():
            try:
                cfg = json.loads(CONFIG_FILE.read_text())
                for k, v in cfg.items():
                    var = getattr(self, f"v_{k}", None)
                    if var: var.set(v)
            except: pass

    def _save_cfg(self, silent=False):
        cfg = {k: getattr(self, f"v_{k}").get()
               for k in ("or_model","gh_repo","gh_branch","gh_folder","out_dir")}
        CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2))
        if not silent: self._log("Đã lưu cấu hình.", "ok")

    # ── Build ────────────────────────────────────────────────

    def _build(self):
        # Title bar
        tb = frm(self, bg=SURFACE, px=20, py=12)
        tb.pack(fill="x")
        lbl(tb, "⚡  Auto Code + GitHub Pusher", font=FONT_TITLE, fg=ACCENT, bg=SURFACE).pack(side="left")
        lbl(tb, "  OpenRouter AI  •  Miễn phí", fg=MUTED, bg=SURFACE).pack(side="left")
        tk.Frame(self, bg=ACCENT, height=2).pack(fill="x")

        pan = tk.PanedWindow(self, orient="horizontal", bg=BG, sashwidth=5, sashrelief="flat")
        pan.pack(fill="both", expand=True)
        left = frm(pan, bg=BG, px=16, py=10)
        pan.add(left, minsize=320, width=390)
        right = frm(pan, bg=BG, px=14, py=10)
        pan.add(right, minsize=420)

        self._build_left(left)
        self._build_right(right)

    # ── LEFT ─────────────────────────────────────────────────

    def _build_left(self, p):
        canvas = tk.Canvas(p, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(p, orient="vertical", command=canvas.yview)
        sf = frm(canvas, bg=BG)
        sf.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0), window=sf, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # ── OpenRouter ──
        sec(sf, "🤖", "OpenRouter API  (Miễn phí)")

        lbl(sf, "API Key", fg=MUTED).pack(anchor="w", pady=(6,2))
        rk = frm(sf); rk.pack(fill="x")
        self.ent_key = ent(rk, var=self.v_or_key, show="•", w=30)
        self.ent_key.pack(side="left", fill="x", expand=True)
        def tog_key():
            self.ent_key.config(show="" if self.v_show_key.get() else "•")
        tk.Checkbutton(rk, text="Hiện", variable=self.v_show_key, command=tog_key,
                       bg=BG, fg=MUTED, activebackground=BG, selectcolor=CARD,
                       font=("Consolas",8), bd=0).pack(side="left", padx=6)
        lbl(sf, "Lấy miễn phí tại: openrouter.ai/keys", fg=MUTED,
            font=("Consolas",8)).pack(anchor="w")

        lbl(sf, "Model AI", fg=MUTED).pack(anchor="w", pady=(10,2))
        models = [
            "openrouter/auto",
            "google/gemini-2.0-flash-exp:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "deepseek/deepseek-chat-v3-0324:free",
            "qwen/qwen3-235b-a22b:free",
            "mistralai/mistral-7b-instruct:free",
        ]
        style = ttk.Style(); style.theme_use("default")
        style.configure("TCombobox", fieldbackground=CARD, background=CARD,
                        foreground=TEXT, selectbackground=ACCENT)
        style.configure("TProgressbar", troughcolor=CARD, background=ACCENT, thickness=6)
        cb = ttk.Combobox(sf, textvariable=self.v_or_model, values=models,
                          font=FONT_UI, state="normal", width=36)
        cb.pack(fill="x")
        lbl(sf, "openrouter/auto = tự chọn model tốt nhất miễn phí", fg=MUTED,
            font=("Consolas",8)).pack(anchor="w")

        # ── GitHub ──
        sec(sf, "🐙", "GitHub")

        lbl(sf, "Personal Access Token", fg=MUTED).pack(anchor="w", pady=(6,2))
        rg = frm(sf); rg.pack(fill="x")
        self.ent_gh = ent(rg, var=self.v_gh_token, show="•", w=30)
        self.ent_gh.pack(side="left", fill="x", expand=True)
        def tog_gh():
            self.ent_gh.config(show="" if self.v_show_gh.get() else "•")
        tk.Checkbutton(rg, text="Hiện", variable=self.v_show_gh, command=tog_gh,
                       bg=BG, fg=MUTED, activebackground=BG, selectcolor=CARD,
                       font=("Consolas",8), bd=0).pack(side="left", padx=6)
        lbl(sf, "GitHub → Settings → Developer settings → Tokens (classic) → repo",
            fg=MUTED, font=("Consolas",8), wraplength=320, justify="left").pack(anchor="w")

        lbl(sf, "Repository  (username/ten-repo)", fg=MUTED).pack(anchor="w", pady=(10,2))
        ent(sf, var=self.v_gh_repo, w=36).pack(fill="x")

        rr = frm(sf); rr.pack(fill="x", pady=(8,0))
        cl = frm(rr); cl.pack(side="left", fill="x", expand=True, padx=(0,6))
        lbl(cl, "Branch", fg=MUTED).pack(anchor="w", pady=(0,2))
        ent(cl, var=self.v_gh_branch, w=14).pack(fill="x")
        cr = frm(rr); cr.pack(side="left", fill="x", expand=True)
        lbl(cr, "Thư mục con (trống = root)", fg=MUTED).pack(anchor="w", pady=(0,2))
        ent(cr, var=self.v_gh_folder, w=14).pack(fill="x")

        # ── Output ──
        sec(sf, "📁", "Lưu file local")
        lbl(sf, "Thư mục lưu file .py", fg=MUTED).pack(anchor="w", pady=(6,2))
        ro = frm(sf); ro.pack(fill="x")
        ent(ro, var=self.v_out_dir, w=26).pack(side="left", fill="x", expand=True)
        btn(ro, "Chọn...", self._browse, bg=CARD, fg=TEXT).pack(side="left", padx=(6,0))

        # ── Options ──
        sec(sf, "⚙️", "Tùy chọn")
        tk.Checkbutton(
            sf, text="  Tự động đẩy lên GitHub sau khi tạo code",
            variable=self.v_auto_push, bg=BG, fg=TEXT,
            activebackground=BG, selectcolor=CARD, font=FONT_UI, bd=0,
        ).pack(anchor="w", pady=4)

        tk.Frame(sf, bg=BORDER, height=1).pack(fill="x", pady=14)
        btn(sf, "💾  Lưu cấu hình", self._save_cfg, bg=CARD, fg=TEXT).pack(fill="x")

    # ── RIGHT ────────────────────────────────────────────────

    def _build_right(self, p):
        sec(p, "📝", "Đề bài")
        hint = frm(p); hint.pack(fill="x", pady=(0,4))
        lbl(hint, "Dán đề bài vào đây. Định dạng: ", fg=MUTED).pack(side="left")
        lbl(hint, "Bài X: nội dung...", font=FONT_MONO, fg=CYAN).pack(side="left")

        self.txt_in = scrolledtext.ScrolledText(
            p, font=FONT_MONO, bg=CARD, fg=TEXT, insertbackground=TEXT,
            relief="flat", bd=0, wrap="word", height=8,
            highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT,
            padx=8, pady=6,
        )
        self.txt_in.pack(fill="x")

        fr = frm(p); fr.pack(fill="x", pady=(6,0))
        btn(fr, "📂 Chọn file .txt", self._load_file, bg=CARD, fg=TEXT).pack(side="left")
        btn(fr, "✕ Xóa", self._clear, bg=CARD, fg=MUTED).pack(side="left", padx=6)
        self.lbl_file = lbl(fr, "", fg=MUTED)
        self.lbl_file.pack(side="left", padx=8)

        run_row = frm(p); run_row.pack(fill="x", pady=10)
        self.btn_run = btn(run_row, "▶  Tạo code + Đẩy GitHub", self._run, w=30)
        self.btn_run.pack(side="left")
        self.btn_push_all = btn(run_row, "☁ Push tất cả", self._push_all, bg=CARD, fg=TEXT)
        self.btn_push_all.pack(side="left", padx=6)
        self.btn_push_all.config(state="disabled")
        btn(run_row, "📁 Mở thư mục", self._open_dir, bg=CARD, fg=TEXT).pack(side="left")

        self.prog_var = tk.DoubleVar(value=0)
        ttk.Progressbar(p, variable=self.prog_var, maximum=100).pack(fill="x", pady=(0,4))
        self.lbl_status = lbl(p, "Sẵn sàng.", fg=MUTED)
        self.lbl_status.pack(anchor="w")

        sec(p, "📄", "Kết quả")
        self.file_frame = frm(p); self.file_frame.pack(fill="both", expand=True)

        sec(p, "📋", "Log")
        self.txt_log = scrolledtext.ScrolledText(
            p, font=FONT_MONO, bg=CARD, fg=TEXT,
            relief="flat", bd=0, wrap="word", height=6,
            highlightthickness=1, highlightbackground=BORDER, state="disabled",
        )
        self.txt_log.pack(fill="both")
        self.txt_log.tag_config("ok",   foreground=GREEN)
        self.txt_log.tag_config("err",  foreground=RED)
        self.txt_log.tag_config("info", foreground=CYAN)
        self.txt_log.tag_config("warn", foreground=YELLOW)

    # ── Helpers ─────────────────────────────────────────────

    def _browse(self):
        d = filedialog.askdirectory()
        if d: self.v_out_dir.set(d)

    def _load_file(self):
        fp = filedialog.askopenfilename(filetypes=[("Text","*.txt"),("All","*.*")])
        if fp:
            self.txt_in.delete("1.0","end")
            self.txt_in.insert("1.0", Path(fp).read_text(encoding="utf-8"))
            self.lbl_file.config(text=Path(fp).name)

    def _clear(self):
        self.txt_in.delete("1.0","end"); self.lbl_file.config(text="")

    def _open_dir(self):
        d = self.v_out_dir.get() or "output"
        Path(d).mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32": os.startfile(d)
        else: os.system(f'xdg-open "{d}"')

    def _log(self, msg, tag="info"):
        self.txt_log.config(state="normal")
        self.txt_log.insert("end", msg+"\n", tag)
        self.txt_log.see("end")
        self.txt_log.config(state="disabled")

    def _status(self, msg, fg=MUTED):
        self.lbl_status.config(text=msg, fg=fg)

    def _prog(self, v):
        self.prog_var.set(v); self.update_idletasks()

    # ── Cards ────────────────────────────────────────────────

    def _render_cards(self):
        for w in self.file_frame.winfo_children(): w.destroy()
        for i, item in enumerate(self.generated):
            prob   = item["prob"]
            code   = item.get("code","")
            pushed = item.get("pushed", False)
            error  = item.get("error","")
            gen_ok = bool(code)

            card = frm(self.file_frame, bg=SURFACE)
            card.pack(fill="x", pady=3)

            hrow = frm(card, bg=SURFACE); hrow.pack(fill="x", padx=10, pady=(8,4))
            dot = GREEN if pushed else (RED if error else (CYAN if gen_ok else YELLOW))
            lbl(hrow,"●", fg=dot, bg=SURFACE, font=("Consolas",13)).pack(side="left")
            lbl(hrow, f"  {prob['filename']}", font=FONT_BOLD, bg=SURFACE).pack(side="left")
            st = "✓ Đã push" if pushed else ("✗ Lỗi" if error else ("✓ Đã tạo" if gen_ok else "⏳ Đang xử lý..."))
            lbl(hrow, f"  {st}", fg=dot, bg=SURFACE).pack(side="left")

            if error and not pushed:
                lbl(card, f"  ⚠ {error}", fg=RED, bg=SURFACE,
                    font=("Consolas",8), wraplength=500, justify="left").pack(anchor="w", padx=10)

            if code:
                lines = code.splitlines()
                preview = "\n".join(lines[:8])
                if len(lines) > 8: preview += f"\n... ({len(lines)-8} dòng tiếp)"
                t = tk.Text(card, font=FONT_MONO, bg="#0d0d18", fg="#c8d3f0",
                            height=min(8, len(lines[:8])+1), relief="flat", bd=0,
                            padx=8, pady=6, wrap="none", state="normal")
                t.insert("1.0", preview); t.config(state="disabled")
                t.pack(fill="x", padx=10, pady=(0,6))

                brow = frm(card, bg=SURFACE); brow.pack(fill="x", padx=10, pady=(0,8))
                btn(brow, "📋 Copy",  lambda c=code: self._copy(c), bg=CARD, fg=TEXT).pack(side="left")
                btn(brow, "💾 Lưu",  lambda it=item: self._save_one(it), bg=CARD, fg=TEXT).pack(side="left", padx=6)
                if not pushed:
                    btn(brow, "☁ Push", lambda it=item: self._push_one_t(it), bg=ACCENT).pack(side="left")
                if item.get("url"):
                    btn(brow, "🔗 GitHub", lambda u=item["url"]: self._open_url(u), bg=CARD, fg=CYAN).pack(side="left", padx=6)

            tk.Frame(self.file_frame, bg=BORDER, height=1).pack(fill="x", pady=1)

    def _copy(self, code):
        self.clipboard_clear(); self.clipboard_append(code)
        self._log("Đã copy code vào clipboard.", "ok")

    def _save_one(self, item):
        fp = save_local(item["prob"], item["code"], self.v_out_dir.get() or "output")
        self._log(f"Đã lưu: {fp}", "ok")
        messagebox.showinfo("Lưu file", f"Đã lưu:\n{fp}")

    def _open_url(self, url):
        import webbrowser; webbrowser.open(url)

    # ── Validate ────────────────────────────────────────────

    def _validate(self, need_gh=True) -> bool:
        if not self.v_or_key.get().strip():
            messagebox.showerror("Thiếu thông tin",
                "Vui lòng nhập OpenRouter API Key.\n\nLấy miễn phí tại: openrouter.ai/keys")
            return False
        if need_gh:
            if not self.v_gh_token.get().strip():
                messagebox.showerror("Thiếu thông tin", "Vui lòng nhập GitHub Token.")
                return False
            if "/" not in self.v_gh_repo.get().strip():
                messagebox.showerror("Thiếu thông tin",
                    "Repository không hợp lệ.\nVí dụ: username/bai-tap-python")
                return False
        return True

    # ── Run ─────────────────────────────────────────────────

    def _run(self):
        if self.running: return
        text = self.txt_in.get("1.0","end").strip()
        if not text:
            messagebox.showwarning("Chưa có đề bài", "Vui lòng dán đề bài vào ô nhập liệu.")
            return
        problems = parse_problems(text)
        if not problems:
            messagebox.showerror("Không tìm thấy bài",
                "Không tìm thấy bài tập nào.\n\nĐịnh dạng cần có:\n  Bài 4: Viết chương trình...")
            return
        auto_push = self.v_auto_push.get()
        if not self._validate(need_gh=auto_push): return

        self.generated = [{"prob":p,"code":"","pushed":False,"error":"","url":""} for p in problems]
        self._render_cards()
        self.btn_run.config(state="disabled")
        self.btn_push_all.config(state="disabled")
        self.running = True
        threading.Thread(target=self._worker, args=(problems, auto_push), daemon=True).start()

    def _worker(self, problems, auto_push):
        try:
            client = OpenAI(base_url=OR_BASE_URL, api_key=self.v_or_key.get().strip())
            model  = self.v_or_model.get().strip() or "openrouter/auto"
            total  = len(problems)
            gen_ok = []

            for i, prob in enumerate(problems):
                self._status(f"⚙ Đang tạo {prob['filename']}... ({i+1}/{total})", CYAN)
                self._log(f"[{i+1}/{total}] Tạo {prob['filename']}...", "info")
                try:
                    code = generate_code(client, model, prob)
                    save_local(prob, code, self.v_out_dir.get() or "output")
                    self.generated[i]["code"] = code
                    self._log(f"✓ {prob['filename']}  ({len(code.splitlines())} dòng)", "ok")
                    gen_ok.append(i)
                except Exception as e:
                    self.generated[i]["error"] = str(e)
                    self._log(f"✗ {prob['filename']}: {e}", "err")
                self._prog((i+1)/total * (50 if auto_push else 100))
                self.after(0, self._render_cards)
                if i < total-1: time.sleep(0.3)

            if auto_push and gen_ok:
                for j, idx in enumerate(gen_ok):
                    item = self.generated[idx]
                    fn = item["prob"]["filename"]
                    self._status(f"☁ Push {fn}... ({j+1}/{len(gen_ok)})", YELLOW)
                    self._log(f"Push {fn}...", "info")
                    try:
                        res = push_to_github(
                            token=self.v_gh_token.get().strip(),
                            repo=self.v_gh_repo.get().strip(),
                            branch=self.v_gh_branch.get().strip() or "main",
                            folder=self.v_gh_folder.get().strip(),
                            filename=fn, code=item["code"],
                            commit_msg=f"{fn}: solution for exercise {item['prob']['num']}",
                        )
                        if res["success"]:
                            item["pushed"] = True; item["url"] = res.get("url","")
                            self._log(f"✓ Push xong {fn}", "ok")
                        else:
                            item["error"] = res.get("error","")
                            self._log(f"✗ {fn}: {item['error']}", "err")
                    except Exception as e:
                        item["error"] = str(e)
                        self._log(f"✗ {fn}: {e}", "err")
                    self._prog(50 + (j+1)/len(gen_ok)*50)
                    self.after(0, self._render_cards)
                    time.sleep(0.3)

            n_gen  = sum(1 for it in self.generated if it["code"])
            n_push = sum(1 for it in self.generated if it["pushed"])
            msg = f"✓ Xong! Tạo {n_gen}/{total} file"
            if auto_push: msg += f" • Push {n_push}/{n_gen} lên GitHub"
            self._status(msg, GREEN)
            self._log(msg, "ok")
            self._prog(100)

        except Exception as e:
            self._log(f"Lỗi: {e}", "err")
            self._status(f"✗ {e}", RED)
        finally:
            self.running = False
            self.after(0, lambda: self.btn_run.config(state="normal"))
            has_up = any(it["code"] and not it["pushed"] for it in self.generated)
            self.after(0, lambda: self.btn_push_all.config(
                state="normal" if has_up else "disabled"))
            self.after(0, self._render_cards)
            self._save_cfg(silent=True)

    # ── Push all ────────────────────────────────────────────

    def _push_all(self):
        if not self._validate(): return
        items = [it for it in self.generated if it["code"] and not it["pushed"]]
        if not items:
            messagebox.showinfo("OK", "Tất cả file đã được push rồi."); return
        self.btn_push_all.config(state="disabled")
        threading.Thread(target=self._push_all_w, args=(items,), daemon=True).start()

    def _push_all_w(self, items):
        for j, item in enumerate(items):
            fn = item["prob"]["filename"]
            self._status(f"☁ Push {fn}... ({j+1}/{len(items)})", YELLOW)
            try:
                res = push_to_github(
                    token=self.v_gh_token.get().strip(),
                    repo=self.v_gh_repo.get().strip(),
                    branch=self.v_gh_branch.get().strip() or "main",
                    folder=self.v_gh_folder.get().strip(),
                    filename=fn, code=item["code"],
                    commit_msg=f"{fn}: solution for exercise {item['prob']['num']}",
                )
                if res["success"]:
                    item["pushed"]=True; item["url"]=res.get("url",""); item["error"]=""
                    self._log(f"✓ {fn}", "ok")
                else:
                    item["error"]=res.get("error",""); self._log(f"✗ {fn}: {item['error']}", "err")
            except Exception as e:
                item["error"]=str(e); self._log(f"✗ {fn}: {e}", "err")
            self.after(0, self._render_cards)
            time.sleep(0.3)
        self._status("✓ Push xong.", GREEN)
        has_up = any(it["code"] and not it["pushed"] for it in self.generated)
        self.after(0, lambda: self.btn_push_all.config(
            state="normal" if has_up else "disabled"))

    def _push_one_t(self, item):
        if not self._validate(): return
        threading.Thread(target=self._push_one_w, args=(item,), daemon=True).start()

    def _push_one_w(self, item):
        fn = item["prob"]["filename"]
        self._status(f"☁ Push {fn}...", YELLOW)
        try:
            res = push_to_github(
                token=self.v_gh_token.get().strip(),
                repo=self.v_gh_repo.get().strip(),
                branch=self.v_gh_branch.get().strip() or "main",
                folder=self.v_gh_folder.get().strip(),
                filename=fn, code=item["code"],
                commit_msg=f"{fn}: solution for exercise {item['prob']['num']}",
            )
            if res["success"]:
                item["pushed"]=True; item["url"]=res.get("url",""); item["error"]=""
                self._log(f"✓ Push {fn} thành công", "ok")
                self._status(f"✓ Push {fn} thành công!", GREEN)
            else:
                item["error"]=res.get("error","")
                self._log(f"✗ {fn}: {item['error']}", "err")
                self._status(f"✗ Lỗi push {fn}", RED)
        except Exception as e:
            item["error"]=str(e); self._log(f"✗ {fn}: {e}", "err")
        self.after(0, self._render_cards)


# ════════════════════════════════════════════════════════════
if __name__ == "__main__":
    App().mainloop()
