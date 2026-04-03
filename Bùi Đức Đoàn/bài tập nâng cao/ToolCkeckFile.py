import re, difflib, ast, threading
from pathlib import Path
from collections import Counter
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ──────────────────────────────────────────────────────────────────
# PHÂN TÍCH
# ──────────────────────────────────────────────────────────────────
CODE_EXTS = {'.py', '.js', '.java', '.cpp', '.c', '.ts'}
DOC_EXTS  = {'.txt', '.md', '.rst'}

def read_file(path):
    for enc in ('utf-8', 'utf-16', 'latin-1'):
        try: return Path(path).read_text(encoding=enc)
        except: pass
    return ""

def load_project(folder):
    p = Path(folder)
    code, doc = {}, {}
    for f in sorted(p.rglob("*")):
        if not f.is_file(): continue
        content = read_file(f)
        if not content.strip(): continue
        if f.suffix in CODE_EXTS: code[f.name] = content
        elif f.suffix in DOC_EXTS: doc[f.name] = content
    return code, doc

def normalize(code):
    lines = []
    for line in code.splitlines():
        line = re.sub(r'#.*', '', line).strip()
        if line: lines.append(line)
    return '\n'.join(lines)

def tokenize(code):
    code = re.sub(r'#[^\n]*', '', code)
    code = re.sub(r'(""".*?"""|\'\'\'.*?\'\'\'|"[^"]*"|\'[^\']*\')', 'S', code, flags=re.DOTALL)
    code = re.sub(r'\b\d+\b', 'N', code)
    return re.sub(r'\s+', ' ', code).strip()

def seq_sim(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio() * 100

def ngrams(text, n=5):
    t = text.split()
    return set(' '.join(t[i:i+n]) for i in range(len(t)-n+1))

def jaccard(a, b):
    if not a or not b: return 0.0
    return len(a & b) / len(a | b) * 100

def find_clones(code_a, code_b, min_lines=4):
    la = [l.strip() for l in code_a.splitlines() if l.strip()]
    lb = [l.strip() for l in code_b.splitlines() if l.strip()]
    clones = []
    for blk in difflib.SequenceMatcher(None, la, lb, autojunk=False).get_matching_blocks():
        i, j, n = blk
        if n >= min_lines:
            clones.append({'a': (i+1, i+n), 'b': (j+1, j+n),
                           'n': n, 'snippet': '\n'.join(la[i:i+4])})
    return clones

def ast_features(code):
    f = {'fns': [], 'imports': [], 'cf': Counter(), 'calls': Counter()}
    try:
        for node in ast.walk(ast.parse(code)):
            if isinstance(node, ast.FunctionDef):
                f['fns'].append(node.name.lower())
                f['fns'].append(f"args{len(node.args.args)}")
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for a in getattr(node, 'names', []): f['imports'].append(a.name)
            elif isinstance(node, ast.For):   f['cf']['for'] += 1
            elif isinstance(node, ast.While): f['cf']['while'] += 1
            elif isinstance(node, ast.If):    f['cf']['if'] += 1
            elif isinstance(node, ast.Call):
                n = node.func
                name = n.id if isinstance(n, ast.Name) else (n.attr if isinstance(n, ast.Attribute) else '')
                if name: f['calls'][name] += 1
    except: pass
    return f

def compare_ast(fa, fb):
    scores = []
    if fa['imports'] or fb['imports']:
        scores.append(jaccard(set(fa['imports']), set(fb['imports'])))
    fn_a = {x for x in fa['fns'] if not x.startswith('args')}
    fn_b = {x for x in fb['fns'] if not x.startswith('args')}
    if fn_a or fn_b: scores.append(jaccard(fn_a, fn_b) * 0.8)
    cf_keys = set(fa['cf']) | set(fb['cf'])
    if cf_keys:
        scores.append(jaccard({f"{k}{fa['cf'][k]}" for k in cf_keys},
                               {f"{k}{fb['cf'][k]}" for k in cf_keys}))
    if fa['calls'] or fb['calls']:
        scores.append(jaccard(set(fa['calls']), set(fb['calls'])))
    return sum(scores)/len(scores) if scores else 0.0

def analyze(folder_a, folder_b, depth, threshold, progress_cb=None):
    def prog(msg): 
        if progress_cb: progress_cb(msg)

    prog("Đang đọc file...")
    code_a, doc_a = load_project(folder_a)
    code_b, doc_b = load_project(folder_b)

    result = {
        'code_a': len(code_a), 'doc_a': len(doc_a),
        'code_b': len(code_b), 'doc_b': len(doc_b),
        't1': None, 't2': None, 't3': None,
        'pairs': [], 'clones': [], 'similar_sents': [],
        'overall': 0, 'threshold': threshold,
    }

    # TIER 1
    prog("Tier 1: So sánh cú pháp...")
    t1_scores = []
    for na, ca in code_a.items():
        for nb, cb in code_b.items():
            na_n, nb_n = normalize(ca), normalize(cb)
            ta, tb = tokenize(na_n), tokenize(nb_n)
            sd = seq_sim(na_n, nb_n)
            st = seq_sim(ta, tb)
            sn = jaccard(ngrams(ta), ngrams(tb))
            sim = max(sd, st*0.9, sn*0.85)
            t1_scores.append(sim)
            clones = find_clones(na_n, nb_n) if sim >= 30 else []
            result['pairs'].append({'fa': na, 'fb': nb, 'sim': round(sim, 1),
                                    'direct': round(sd,1), 'token': round(st,1)})
            for cl in clones[:3]:
                result['clones'].append({'fa': na, 'fb': nb,
                    'la': cl['a'], 'lb': cl['b'], 'n': cl['n'],
                    'snippet': cl['snippet'][:200]})
    result['t1'] = round(max(t1_scores), 1) if t1_scores else 0

    # TIER 2
    if depth in ('normal', 'deep'):
        prog("Tier 2: Phân tích thuật toán (AST)...")
        t2 = []
        for na, ca in code_a.items():
            for nb, cb in code_b.items():
                fa, fb = ast_features(ca), ast_features(cb)
                sim = compare_ast(fa, fb) if (fa['fns'] or fb['fns']) else seq_sim(tokenize(ca), tokenize(cb))*0.7
                t2.append(sim)
        result['t2'] = round(max(t2), 1) if t2 else 0

    # TIER 3
    if depth == 'deep':
        prog("Tier 3: Kiểm tra đạo văn tài liệu...")
        t3 = []
        for na, ta in doc_a.items():
            for nb, tb in doc_b.items():
                na_t = re.sub(r'[^\w\s]', ' ', ta.lower())
                nb_t = re.sub(r'[^\w\s]', ' ', tb.lower())
                s1 = seq_sim(na_t, nb_t)
                s2 = jaccard(ngrams(na_t, 6), ngrams(nb_t, 6))
                sents_a = [s.strip() for s in re.split(r'(?<=[.!?])\s+', ta) if len(s.strip()) > 30]
                sents_b = [s.strip() for s in re.split(r'(?<=[.!?])\s+', tb) if len(s.strip()) > 30]
                pairs = []
                for sa in sents_a[:40]:
                    for sb in sents_b[:40]:
                        r = difflib.SequenceMatcher(None, sa, sb).ratio()
                        if r >= 0.7: pairs.append({'a': sa[:100], 'b': sb[:100], 'sim': round(r*100,1)})
                s3 = len(pairs)/max(len(sents_a), len(sents_b), 1)*100
                t3.append((s1+s2+s3)/3)
                result['similar_sents'].extend(sorted(pairs, key=lambda x:-x['sim'])[:4])
        result['t3'] = round(max(t3), 1) if t3 else 0

    vals = [v for v in [result['t1'], result['t2'], result['t3']] if v is not None]
    result['overall'] = round(sum(vals)/len(vals), 1) if vals else 0
    prog("Hoàn tất!")
    return result


# ──────────────────────────────────────────────────────────────────
# GIAO DIỆN TKINTER
# ──────────────────────────────────────────────────────────────────
CLR_BG     = "#f5f4f0"
CLR_WHITE  = "#ffffff"
CLR_DARK   = "#1a1a1a"
CLR_MUTED  = "#888888"
CLR_BORDER = "#e0ddd8"
CLR_SAFE   = "#16a34a"
CLR_WARN   = "#d97706"
CLR_DANGER = "#dc2626"
CLR_ACCENT = "#2563eb"
FONT_BODY  = ("Segoe UI", 10)
FONT_BOLD  = ("Segoe UI", 10, "bold")
FONT_MONO  = ("Courier New", 10)
FONT_TITLE = ("Segoe UI", 13, "bold")
FONT_BIG   = ("Segoe UI", 22, "bold")
FONT_SM    = ("Segoe UI", 9)


def pct_color(p):
    if p is None: return CLR_MUTED
    if p >= 70: return CLR_DANGER
    if p >= 40: return CLR_WARN
    return CLR_SAFE


def make_frame(parent, bg=CLR_WHITE, padx=16, pady=12, mb=10):
    outer = tk.Frame(parent, bg=CLR_BG)
    outer.pack(fill="x", padx=20, pady=(0, mb))
    inner = tk.Frame(outer, bg=bg, bd=0, relief="flat",
                     highlightthickness=1, highlightbackground=CLR_BORDER)
    inner.pack(fill="x")
    content = tk.Frame(inner, bg=bg)
    content.pack(fill="x", padx=padx, pady=pady)
    return content


def section_label(parent, text, bg=CLR_WHITE):
    tk.Label(parent, text=text, font=("Segoe UI", 8, "bold"),
             fg=CLR_MUTED, bg=bg, anchor="w").pack(fill="x", pady=(0, 8))


class CodeGuardApp:
    def __init__(self, root):
        self.root = root
        root.title("CodeGuard — Phát hiện Trùng lặp")
        root.configure(bg=CLR_BG)
        root.resizable(True, True)

        # Căn giữa màn hình
        w, h = 820, 780
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        root.minsize(700, 600)

        self._build_ui()

    def _build_ui(self):
        # ── Header ──
        hdr = tk.Frame(self.root, bg=CLR_DARK)
        hdr.pack(fill="x")
        tk.Label(hdr, text="CodeGuard", font=("Segoe UI", 15, "bold"),
                 fg="#a8ff78", bg=CLR_DARK).pack(side="left", padx=18, pady=14)
        tk.Label(hdr, text="Phát hiện trùng lặp code & tài liệu",
                 font=FONT_SM, fg="#888", bg=CLR_DARK).pack(side="left", pady=14)

        # ── Scrollable body ──
        canvas = tk.Canvas(self.root, bg=CLR_BG, highlightthickness=0)
        scroll = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self.body = tk.Frame(canvas, bg=CLR_BG)
        win_id = canvas.create_window((0, 0), window=self.body, anchor="nw")

        def on_resize(e):
            canvas.itemconfig(win_id, width=e.width)
        def on_frame(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.bind("<Configure>", on_resize)
        self.body.bind("<Configure>", on_frame)

        # Mouse wheel scroll
        def _scroll(e):
            canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _scroll)

        self._build_inputs()
        self._build_results()

    # ── INPUT SECTION ──────────────────────────────────────────────
    def _build_inputs(self):
        tk.Label(self.body, text="", bg=CLR_BG, height=1).pack()

        # Thư mục
        f = make_frame(self.body)
        section_label(f, "📁  ĐƯỜNG DẪN THƯ MỤC")

        self.var_a = tk.StringVar()
        self.var_b = tk.StringVar()

        for label, var, btn_cmd in [
            ("Sản phẩm A", self.var_a, lambda: self._browse(self.var_a)),
            ("Sản phẩm B", self.var_b, lambda: self._browse(self.var_b)),
        ]:
            row = tk.Frame(f, bg=CLR_WHITE)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=label, font=FONT_BOLD, bg=CLR_WHITE, width=12, anchor="w").pack(side="left")
            entry = tk.Entry(row, textvariable=var, font=FONT_MONO, bg="#fafaf8",
                             relief="flat", bd=0, highlightthickness=1,
                             highlightbackground=CLR_BORDER, highlightcolor=CLR_ACCENT)
            entry.pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 8))
            tk.Button(row, text="Chọn…", command=btn_cmd,
                      font=FONT_SM, bg=CLR_DARK, fg="white",
                      relief="flat", padx=10, cursor="hand2").pack(side="left")

        # Tùy chọn
        f2 = make_frame(self.body)
        section_label(f2, "⚙️  TÙY CHỌN")

        opts = tk.Frame(f2, bg=CLR_WHITE)
        opts.pack(fill="x")

        # Depth
        dl = tk.Frame(opts, bg=CLR_WHITE)
        dl.pack(side="left", fill="x", expand=True, padx=(0, 12))
        tk.Label(dl, text="Độ sâu phân tích", font=FONT_SM, fg=CLR_MUTED, bg=CLR_WHITE, anchor="w").pack(fill="x")
        self.var_depth = tk.StringVar(value="normal")
        cb_depth = ttk.Combobox(dl, textvariable=self.var_depth, state="readonly", font=FONT_SM,
                                 values=["quick  — Chỉ cú pháp (Tier 1)",
                                         "normal — Cú pháp + Thuật toán (Tier 1+2)",
                                         "deep   — Full 3 tầng (+ Tài liệu)"])
        cb_depth.current(1)
        cb_depth.pack(fill="x", ipady=4, pady=(2,0))

        # Threshold
        tl = tk.Frame(opts, bg=CLR_WHITE)
        tl.pack(side="left", fill="x", expand=True, padx=(0, 12))
        tk.Label(tl, text="Ngưỡng cảnh báo (%)", font=FONT_SM, fg=CLR_MUTED, bg=CLR_WHITE, anchor="w").pack(fill="x")
        self.var_thr = tk.StringVar(value="60")
        cb_thr = ttk.Combobox(tl, textvariable=self.var_thr, state="readonly", font=FONT_SM,
                               values=["40 — Nghiêm ngặt", "60 — Bình thường", "75 — Dễ chịu"])
        cb_thr.current(1)
        cb_thr.pack(fill="x", ipady=4, pady=(2,0))

        # Button + status
        f3 = make_frame(self.body, padx=16, pady=10)
        self.btn = tk.Button(f3, text="🔍  PHÂN TÍCH TRÙNG LẶP",
                             command=self._run,
                             font=("Segoe UI", 11, "bold"),
                             bg=CLR_DARK, fg="white", activebackground="#333",
                             relief="flat", padx=24, pady=10, cursor="hand2")
        self.btn.pack(fill="x")

        self.status_var = tk.StringVar(value="")
        self.status_lbl = tk.Label(f3, textvariable=self.status_var,
                                   font=FONT_SM, fg=CLR_MUTED, bg=CLR_WHITE)
        self.status_lbl.pack(pady=(6, 0))

    # ── RESULTS SECTION ────────────────────────────────────────────
    def _build_results(self):
        self.result_frame = tk.Frame(self.body, bg=CLR_BG)
        # Sẽ pack khi có kết quả

        # Score row
        self.score_frame = tk.Frame(self.result_frame, bg=CLR_BG)
        self.score_frame.pack(fill="x", padx=20, pady=(10, 0))

        # Verdict
        self.verdict_frame = make_frame(self.result_frame, padx=16, pady=12, mb=0)

        # Notebook (tabs)
        nb_outer = tk.Frame(self.result_frame, bg=CLR_BG)
        nb_outer.pack(fill="x", padx=20, pady=10)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=CLR_BG, borderwidth=0)
        style.configure("TNotebook.Tab", font=FONT_BOLD, padding=[12, 6],
                        background=CLR_BG, foreground=CLR_MUTED)
        style.map("TNotebook.Tab", background=[("selected", CLR_WHITE)],
                  foreground=[("selected", CLR_DARK)])

        self.nb = ttk.Notebook(nb_outer)
        self.nb.pack(fill="both")

        self.tab_pairs  = self._make_tab("★ Tier 1 — Cú pháp")
        self.tab_clones = self._make_tab("✂ Clone blocks")
        self.tab_doc    = self._make_tab("★★★ Tier 3 — Tài liệu")

    def _make_tab(self, title):
        frame = tk.Frame(self.nb, bg=CLR_WHITE,
                         highlightthickness=1, highlightbackground=CLR_BORDER)
        self.nb.add(frame, text=title)
        # Inner scrollable text
        txt = tk.Text(frame, font=FONT_MONO, bg=CLR_WHITE, fg=CLR_DARK,
                      relief="flat", bd=0, wrap="word", state="disabled",
                      padx=12, pady=10, height=18, cursor="arrow")
        sb = ttk.Scrollbar(frame, command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(fill="both", expand=True)

        # Tags
        txt.tag_configure("header",  font=("Segoe UI", 10, "bold"), foreground=CLR_DARK)
        txt.tag_configure("safe",    foreground=CLR_SAFE,   font=FONT_BOLD)
        txt.tag_configure("warn",    foreground=CLR_WARN,   font=FONT_BOLD)
        txt.tag_configure("danger",  foreground=CLR_DANGER, font=FONT_BOLD)
        txt.tag_configure("muted",   foreground=CLR_MUTED,  font=FONT_SM)
        txt.tag_configure("code",    font=("Courier New", 9), foreground="#444",
                          background="#f8f7f4", lmargin1=16, lmargin2=16)
        txt.tag_configure("sep",     foreground=CLR_BORDER)
        return txt

    # ── BROWSE & RUN ───────────────────────────────────────────────
    def _browse(self, var):
        d = filedialog.askdirectory(title="Chọn thư mục")
        if d: var.set(d)

    def _run(self):
        fa = self.var_a.get().strip()
        fb = self.var_b.get().strip()
        if not fa or not fb:
            messagebox.showwarning("Thiếu đường dẫn", "Vui lòng nhập đường dẫn cả 2 thư mục!")
            return
        if not Path(fa).exists():
            messagebox.showerror("Lỗi", f"Không tìm thấy thư mục:\n{fa}"); return
        if not Path(fb).exists():
            messagebox.showerror("Lỗi", f"Không tìm thấy thư mục:\n{fb}"); return

        depth = self.var_depth.get().split()[0]
        thr   = int(self.var_thr.get().split()[0])

        self.btn.config(state="disabled", text="⏳  Đang phân tích...")
        self.status_var.set("")

        def worker():
            try:
                r = analyze(fa, fb, depth, thr,
                            progress_cb=lambda m: self.root.after(0, lambda: self.status_var.set(m)))
                self.root.after(0, lambda: self._show(r))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Lỗi phân tích", str(e)))
            finally:
                self.root.after(0, lambda: self.btn.config(state="normal", text="🔍  PHÂN TÍCH TRÙNG LẶP"))

        threading.Thread(target=worker, daemon=True).start()

    # ── RENDER RESULTS ─────────────────────────────────────────────
    def _show(self, d):
        self.result_frame.pack(fill="x")

        # ── Score cards ──
        for w in self.score_frame.winfo_children(): w.destroy()

        items = [
            ("Tier 1\nCú pháp ★", d['t1']),
            ("Tier 2\nThuật toán ★★", d['t2']),
            ("Tier 3\nTài liệu ★★★", d['t3']),
            ("TỔNG\nĐiểm chung", d['overall']),
        ]
        for i, (lbl, val) in enumerate(items):
            box = tk.Frame(self.score_frame, bg=CLR_WHITE,
                           highlightthickness=1, highlightbackground=CLR_BORDER)
            box.grid(row=0, column=i, padx=(0 if i else 0, 8), sticky="ew")
            self.score_frame.grid_columnconfigure(i, weight=1)

            col = pct_color(val)
            txt = f"{val}%" if val is not None else "—"
            tk.Label(box, text=txt, font=("Segoe UI", 24, "bold"),
                     fg=col, bg=CLR_WHITE).pack(pady=(12, 2))
            tk.Label(box, text=lbl, font=("Segoe UI", 8),
                     fg=CLR_MUTED, bg=CLR_WHITE, justify="center").pack(pady=(0, 10))

        # ── Verdict ──
        for w in self.verdict_frame.winfo_children(): w.destroy()
        ov  = d['overall']
        thr = d['threshold']
        col = pct_color(ov)
        icon = "🚨" if ov >= 70 else "⚠️" if ov >= 40 else "✅"
        lbl  = "NGUY HIỂM — Có dấu hiệu sao chép rõ ràng" if ov >= 70 \
               else "CẦN XEM XÉT — Nên phỏng vấn/bảo vệ thêm" if ov >= 40 \
               else "CHẤP NHẬN ĐƯỢC — Trong ngưỡng cho phép"
        over_txt = "⚠ VƯỢT NGƯỠNG" if ov >= thr else "✓ Không vượt ngưỡng"

        top = tk.Frame(self.verdict_frame, bg=CLR_WHITE)
        top.pack(fill="x")
        tk.Label(top, text=f"{icon}  {ov}%  —  {lbl}",
                 font=FONT_BOLD, fg=col, bg=CLR_WHITE, anchor="w").pack(side="left")
        tk.Label(top, text=over_txt, font=FONT_BOLD,
                 fg=CLR_DANGER if ov>=thr else CLR_SAFE,
                 bg=CLR_WHITE, anchor="e").pack(side="right")

        tk.Label(self.verdict_frame,
                 text=f"Ngưỡng cảnh báo: {thr}%   |   "
                      f"A: {d['code_a']} file code + {d['doc_a']} tài liệu   |   "
                      f"B: {d['code_b']} file code + {d['doc_b']} tài liệu",
                 font=FONT_SM, fg=CLR_MUTED, bg=CLR_WHITE, anchor="w").pack(fill="x", pady=(4, 0))

        # ── Tab 1: Pairs ──
        self._fill_tab(self.tab_pairs, self._render_pairs, d)

        # ── Tab 2: Clones ──
        self._fill_tab(self.tab_clones, self._render_clones, d)

        # ── Tab 3: Documents ──
        self._fill_tab(self.tab_doc, self._render_docs, d)

    def _fill_tab(self, txt, fn, d):
        txt.config(state="normal")
        txt.delete("1.0", "end")
        fn(txt, d)
        txt.config(state="disabled")

    def _write(self, txt, text, *tags):
        txt.insert("end", text, tags)

    def _render_pairs(self, txt, d):
        pairs = sorted(d['pairs'], key=lambda x: -x['sim'])
        if not pairs:
            self._write(txt, "\n  Không có file code để so sánh.\n", "muted")
            return
        for p in pairs:
            col = "danger" if p['sim']>=70 else "warn" if p['sim']>=40 else "safe"
            self._write(txt, f"\n  {p['fa']}  ↔  {p['fb']}\n", "header")
            self._write(txt, f"  {'█'*int(p['sim']//3)}{'░'*(33-int(p['sim']//3))}  {p['sim']}%\n", col)
            self._write(txt, f"  Trực tiếp: {p['direct']}%   Sau chuẩn hóa token: {p['token']}%\n", "muted")
            self._write(txt, "  " + "─"*52 + "\n", "sep")

    def _render_clones(self, txt, d):
        clones = d['clones']
        if not clones:
            self._write(txt, "\n  Không phát hiện đoạn code clone (≥4 dòng giống nhau).\n", "muted")
            return
        for cl in clones:
            self._write(txt, f"\n  📌 {cl['fa']} [dòng {cl['la'][0]}–{cl['la'][1]}]"
                             f"  ↔  {cl['fb']} [dòng {cl['lb'][0]}–{cl['lb'][1]}]"
                             f"  ({cl['n']} dòng)\n", "warn")
            self._write(txt, cl['snippet'] + "\n", "code")
            self._write(txt, "  " + "─"*52 + "\n", "sep")

    def _render_docs(self, txt, d):
        sents = sorted(d['similar_sents'], key=lambda x: -x['sim'])
        if not sents:
            self._write(txt, "\n  Không có tài liệu để so sánh hoặc không phát hiện đạo văn.\n"
                             "  (Chọn độ sâu 'deep' để phân tích tài liệu .txt/.md)\n", "muted")
            return
        self._write(txt, f"\n  Phát hiện {len(sents)} cặp câu/đoạn tương tự:\n\n", "header")
        for s in sents:
            col = "danger" if s['sim']>=80 else "warn"
            self._write(txt, f"  [{s['sim']}% tương đồng]\n", col)
            self._write(txt, f"  A: {s['a']}...\n", "muted")
            self._write(txt, f"  B: {s['b']}...\n", "muted")
            self._write(txt, "  " + "─"*52 + "\n", "sep")


# ──────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = CodeGuardApp(root)
    root.mainloop()
