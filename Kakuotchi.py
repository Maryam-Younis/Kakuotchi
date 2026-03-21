"""
Kakuotchi — Budget Town
Wild-west desert scene with horizontal scrolling.
Each cactus is a budget category — scroll sideways to see them all.
Stay under budget → happy green cactus.
Near the limit   → worried yellow cactus.
Over budget      → dried-up angry tumbleweed!
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import json, os, math
from datetime import datetime

# ─── Layout constants ─────────────────────────────────────────────────────────

W        = 480          # window / header / footer width
HEADER_H = 122          # fixed header height
FOOTER_H = 58           # fixed footer height
SCENE_H  = 580          # scrollable scene height
H        = HEADER_H + SCENE_H + FOOTER_H   # = 760

CAT_SLOT = 170          # horizontal pixels allocated per cactus

def world_w(n_cats):
    """Total scrollable width for n cacti."""
    return max(W, n_cats * CAT_SLOT + 60)

# ─── Persistence ──────────────────────────────────────────────────────────────

DATA_FILE = os.path.join(os.path.expanduser("~"), "kakuotchi_data.json")

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "current_month": datetime.now().strftime("%Y-%m"),
        "categories": [
            {"name": "Food",          "budget": 300.0, "expenses": []},
            {"name": "Clothing",      "budget": 150.0, "expenses": []},
            {"name": "Entertainment", "budget": 120.0, "expenses": []},
        ],
    }

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def month_spent(cat, month):
    return sum(e["amount"] for e in cat["expenses"] if e["month"] == month)

def budget_ratio(cat, month):
    s = month_spent(cat, month)
    b = cat.get("budget", 1) or 1
    return s / b

def state_for_ratio(r):
    if r > 1.0:   return "sad"
    if r >= 0.75: return "warning"
    return "happy"

# ─── Bezier helper ────────────────────────────────────────────────────────────

def bezier(p0, p1, p2, steps=12):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        x = (1-t)**2*p0[0] + 2*(1-t)*t*p1[0] + t**2*p2[0]
        y = (1-t)**2*p0[1] + 2*(1-t)*t*p1[1] + t**2*p2[1]
        pts += [x, y]
    return pts

# ─── Dialogs ──────────────────────────────────────────────────────────────────

DLOG_BG   = "#D2B48C"
DLOG_TEXT = "#3E1F00"
BTN_BG    = "#8B4513"
BTN_FG    = "#FFD700"

class AddExpenseDialog(tk.Toplevel):
    def __init__(self, parent, cat_name):
        super().__init__(parent)
        self.result = None
        self.title(f"Log Expense — {cat_name}")
        self.resizable(False, False)
        self.configure(bg=DLOG_BG)
        self.grab_set()

        tk.Label(self, text=f"Log expense for  {cat_name}",
                 font=("Georgia", 13, "bold"), bg=DLOG_BG, fg=DLOG_TEXT).pack(pady=(14, 4))

        form = tk.Frame(self, bg=DLOG_BG)
        form.pack(padx=24, pady=8)
        tk.Label(form, text="Amount ($):", bg=DLOG_BG, fg=DLOG_TEXT,
                 font=("Georgia", 11)).grid(row=0, column=0, sticky="e", pady=5)
        self.amt = tk.StringVar()
        e = tk.Entry(form, textvariable=self.amt, width=14, font=("Georgia", 11))
        e.grid(row=0, column=1, padx=8, pady=5)
        e.focus_set()

        tk.Label(form, text="Note:", bg=DLOG_BG, fg=DLOG_TEXT,
                 font=("Georgia", 11)).grid(row=1, column=0, sticky="e", pady=5)
        self.note = tk.StringVar()
        tk.Entry(form, textvariable=self.note, width=20,
                 font=("Georgia", 11)).grid(row=1, column=1, padx=8, pady=5)

        row = tk.Frame(self, bg=DLOG_BG)
        row.pack(pady=10)
        tk.Button(row, text="Log It!", command=self._ok,
                  bg=BTN_BG, fg=BTN_FG, font=("Georgia", 11, "bold"),
                  relief="raised", padx=10).pack(side="left", padx=6)
        tk.Button(row, text="Cancel", command=self.destroy,
                  bg="#666", fg="#fff", font=("Georgia", 10),
                  relief="raised", padx=8).pack(side="left", padx=6)
        self.bind("<Return>", lambda _: self._ok())
        self.bind("<Escape>", lambda _: self.destroy())

    def _ok(self):
        try:
            amount = float(self.amt.get())
            assert amount > 0
        except Exception:
            messagebox.showerror("Oops", "Enter a valid positive amount.", parent=self)
            return
        self.result = {"amount": amount, "description": self.note.get().strip() or "—"}
        self.destroy()


class AddCactusDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.result = None
        self.title("Plant a New Cactus")
        self.resizable(False, False)
        self.configure(bg=DLOG_BG)
        self.grab_set()

        tk.Label(self, text="Plant a new budget cactus!",
                 font=("Georgia", 13, "bold"), bg=DLOG_BG, fg=DLOG_TEXT).pack(pady=(14, 4))

        form = tk.Frame(self, bg=DLOG_BG)
        form.pack(padx=24, pady=8)
        tk.Label(form, text="Category name:", bg=DLOG_BG, fg=DLOG_TEXT,
                 font=("Georgia", 11)).grid(row=0, column=0, sticky="e", pady=5)
        self.name = tk.StringVar()
        e = tk.Entry(form, textvariable=self.name, width=18, font=("Georgia", 11))
        e.grid(row=0, column=1, padx=8, pady=5)
        e.focus_set()

        tk.Label(form, text="Monthly budget ($):", bg=DLOG_BG, fg=DLOG_TEXT,
                 font=("Georgia", 11)).grid(row=1, column=0, sticky="e", pady=5)
        self.budget = tk.StringVar()
        tk.Entry(form, textvariable=self.budget, width=14,
                 font=("Georgia", 11)).grid(row=1, column=1, padx=8, pady=5)

        row = tk.Frame(self, bg=DLOG_BG)
        row.pack(pady=10)
        tk.Button(row, text="Plant It!", command=self._ok,
                  bg=BTN_BG, fg=BTN_FG, font=("Georgia", 11, "bold"),
                  relief="raised", padx=10).pack(side="left", padx=6)
        tk.Button(row, text="Cancel", command=self.destroy,
                  bg="#666", fg="#fff", font=("Georgia", 10),
                  relief="raised", padx=8).pack(side="left", padx=6)
        self.bind("<Return>", lambda _: self._ok())
        self.bind("<Escape>", lambda _: self.destroy())

    def _ok(self):
        name = self.name.get().strip()
        if not name:
            messagebox.showerror("Oops", "Please enter a category name.", parent=self)
            return
        try:
            budget = float(self.budget.get())
            assert budget > 0
        except Exception:
            messagebox.showerror("Oops", "Enter a valid positive budget.", parent=self)
            return
        self.result = {"name": name, "budget": budget, "expenses": []}
        self.destroy()


class HistoryDialog(tk.Toplevel):
    def __init__(self, parent, cat, month, on_change):
        super().__init__(parent)
        self.cat = cat
        self.on_change = on_change
        self.title(f"{cat['name']}  •  {month}")
        self.resizable(True, True)
        self.geometry("440x380")
        self.configure(bg=DLOG_BG)
        self.grab_set()

        tk.Label(self, text=cat["name"],
                 font=("Georgia", 14, "bold"), bg=DLOG_BG, fg=DLOG_TEXT).pack(pady=(12, 0))
        tk.Label(self, text=month, font=("Georgia", 10), bg=DLOG_BG, fg=DLOG_TEXT).pack()

        lf = tk.Frame(self, bg="#F5DEB3", relief="sunken", bd=1)
        lf.pack(fill="both", expand=True, padx=16, pady=8)

        expenses = sorted([e for e in cat["expenses"] if e["month"] == month],
                          key=lambda x: x.get("date", ""))
        if not expenses:
            tk.Label(lf, text="No expenses logged yet.",
                     font=("Georgia", 11, "italic"), bg="#F5DEB3", fg=DLOG_TEXT).pack(pady=20)
        else:
            sb = tk.Scrollbar(lf)
            sb.pack(side="right", fill="y")
            lb = tk.Listbox(lf, yscrollcommand=sb.set, font=("Courier", 10),
                            bg="#F5DEB3", fg=DLOG_TEXT, bd=0,
                            selectbackground="#DAA520", activestyle="none")
            lb.pack(fill="both", expand=True, padx=4, pady=4)
            sb.config(command=lb.yview)
            total = 0.0
            for e in expenses:
                total += e["amount"]
                lb.insert("end", f"  {e.get('date','')}   ${e['amount']:>8.2f}   {e.get('description','—')}")
            lb.insert("end", "  " + "─"*42)
            lb.insert("end", f"  {'TOTAL':>18}   ${total:>8.2f}")

        bf = tk.Frame(self, bg=DLOG_BG)
        bf.pack(pady=6)
        tk.Button(bf, text="Edit Budget", command=self._edit_budget,
                  bg=BTN_BG, fg=BTN_FG, font=("Georgia", 10, "bold"), padx=8).pack(side="left", padx=6)
        tk.Button(bf, text="Close", command=self.destroy,
                  bg="#666", fg="#fff", font=("Georgia", 10), padx=8).pack(side="left", padx=6)

    def _edit_budget(self):
        new_b = simpledialog.askfloat(
            "Edit Budget", f"New monthly budget for  {self.cat['name']}:",
            initialvalue=self.cat["budget"], minvalue=0.01, parent=self)
        if new_b:
            self.cat["budget"] = new_b
            self.on_change()
            self.destroy()

# ─── Main App ─────────────────────────────────────────────────────────────────

class KakuotchiApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Kakuotchi — Budget Town")
        self.resizable(False, False)
        self.geometry(f"{W}x{H}")
        self.configure(bg="#5C3010")

        self.data     = load_data()
        self._cat_map = {}      # canvas tag → category dict
        self._did_drag = False  # distinguishes click vs drag

        self._build_layout()
        self.protocol("WM_DELETE_WINDOW", self._quit)
        self._draw()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_layout(self):
        # Fixed header
        self.hdr_cv = tk.Canvas(self, width=W, height=HEADER_H,
                                bd=0, highlightthickness=0, bg="#5C3010")
        self.hdr_cv.pack(side="top")

        # Horizontally scrollable scene (no visible scrollbar — drag to scroll)
        self.scene_cv = tk.Canvas(self, width=W, height=SCENE_H,
                                  bd=0, highlightthickness=0, bg="#87CEEB")
        self.scene_cv.pack(side="top")

        self.scene_cv.bind("<ButtonPress-1>",   self._drag_start)
        self.scene_cv.bind("<B1-Motion>",        self._drag_move)
        self.scene_cv.bind("<ButtonRelease-1>",  self._drag_end)

        # Arrow-key scrolling
        self.bind("<Left>",  lambda _: self.scene_cv.xview_scroll(-3, "units"))
        self.bind("<Right>", lambda _: self.scene_cv.xview_scroll( 3, "units"))

        # Fixed footer
        self.ftr_cv = tk.Canvas(self, width=W, height=FOOTER_H,
                                bd=0, highlightthickness=0, bg="#5C3010")
        self.ftr_cv.pack(side="top")

    # ── Drag-to-scroll ────────────────────────────────────────────────────────

    def _drag_start(self, event):
        self._drag_x0  = event.x
        self._did_drag = False
        self.scene_cv.scan_mark(event.x, 0)

    def _drag_move(self, event):
        if abs(event.x - self._drag_x0) > 4:
            self._did_drag = True
        self.scene_cv.scan_dragto(event.x, 0, gain=1)

    def _drag_end(self, event):
        pass  # cactus tags handle release

    # ── Master draw ───────────────────────────────────────────────────────────

    def _draw(self):
        self.hdr_cv.delete("all")
        self.scene_cv.delete("all")
        self.ftr_cv.delete("all")
        self._cat_map.clear()

        cats = self.data["categories"]
        ww   = world_w(len(cats))
        self.scene_cv.configure(scrollregion=(0, 0, ww, SCENE_H))

        self._draw_sky(ww)
        self._draw_rocks(ww)
        self._draw_ground(ww)
        if ww > W:
            self._draw_scroll_hint(ww)
        self._draw_cacti(ww)
        self._draw_header()
        self._draw_footer()

    # ── Sky ───────────────────────────────────────────────────────────────────

    def _draw_sky(self, ww):
        cv = self.scene_cv
        bands = [(0, 90, "#5FA8C8"), (90, 180, "#72B8D8"),
                 (180, 265, "#87CEEB"), (265, 295, "#9DD5F0")]
        cv.create_rectangle(0, 0, ww, SCENE_H, fill="#5FA8C8", outline="")
        for y1, y2, col in bands:
            cv.create_rectangle(0, y1, ww, y2, fill=col, outline="")
        # Sun near right end
        sx, sy, sr = ww - 60, 60, 26
        for i in range(10):
            a = math.radians(i * 36)
            cv.create_line(sx+(sr+4)*math.cos(a), sy+(sr+4)*math.sin(a),
                           sx+(sr+14)*math.cos(a), sy+(sr+14)*math.sin(a),
                           fill="#FFB800", width=2)
        cv.create_oval(sx-sr, sy-sr, sx+sr, sy+sr, fill="#FFD700", outline="#FFB800", width=2)

    # ── Rock formations ───────────────────────────────────────────────────────

    def _draw_rocks(self, ww):
        cv = self.scene_cv
        # Left formation
        cv.create_polygon(
            [0,305, 0,195, 25,168, 58,150, 90,136, 122,148, 148,170, 164,205, 180,305],
            fill="#C06035", outline="")
        cv.create_polygon(
            [0,310, 0,210, 22,180, 52,158, 84,142, 118,155, 144,178, 158,210, 172,310],
            fill="#9B3A12", outline="")
        cv.create_line(22,180, 84,142, 144,178, fill="#7A2A05", width=2)
        # Right formation
        cv.create_polygon(
            [ww,305, ww,195, ww-25,168, ww-58,150, ww-90,136,
             ww-122,148, ww-148,170, ww-164,205, ww-180,305],
            fill="#C06035", outline="")
        cv.create_polygon(
            [ww,310, ww,210, ww-22,180, ww-52,158, ww-84,142,
             ww-118,155, ww-144,178, ww-158,210, ww-172,310],
            fill="#9B3A12", outline="")
        cv.create_line(ww-22,180, ww-84,142, ww-144,178, fill="#7A2A05", width=2)
        # Center butte
        mid = ww // 2
        cv.create_polygon(
            [mid-80,310, mid-70,230, mid-45,208, mid,195,
             mid+45,208, mid+70,230, mid+80,310],
            fill="#B04A20", outline="")
        # Extra buttes for wide worlds
        if ww > W:
            for qx in [ww // 4, 3 * ww // 4]:
                cv.create_polygon(
                    [qx-50,310, qx-40,248, qx-15,232, qx+15,232,
                     qx+40,248, qx+50,310],
                    fill="#C06035", outline="")

    # ── Ground ────────────────────────────────────────────────────────────────

    def _draw_ground(self, ww):
        cv = self.scene_cv
        gy = 295
        cv.create_rectangle(0, gy, ww, SCENE_H, fill="#C8A96E", outline="")
        cv.create_rectangle(0, gy, ww, gy+16, fill="#A88040", outline="")
        for y in range(gy+30, SCENE_H, 44):
            for x in range(10, ww-10, 55):
                cv.create_oval(x, y, x+20, y+6, fill="#BBAA60", outline="")

    # ── Scroll hint ───────────────────────────────────────────────────────────

    def _draw_scroll_hint(self, ww):
        cv = self.scene_cv
        gy = 284
        cv.create_text(20,    gy, text="◀", font=("Georgia", 14, "bold"), fill="#7A5520")
        cv.create_text(ww-20, gy, text="▶", font=("Georgia", 14, "bold"), fill="#7A5520")
        cv.create_text(ww//2, gy, text="← drag or arrow keys to scroll →",
                       font=("Georgia", 8, "italic"), fill="#9A7540")

    # ── Header (fixed) ────────────────────────────────────────────────────────

    def _draw_header(self):
        cv = self.hdr_cv
        # Wooden bar
        cv.create_rectangle(0, 0, W, 30, fill="#5C3010", outline="")
        for y in [8, 16, 24]:
            cv.create_line(0, y, W, y, fill="#6E3D18")
        for bx in [18, W-18]:
            cv.create_rectangle(bx-12, 2, bx+12, 28, fill="#888", outline="#555")
            cv.create_oval(bx-4, 11, bx+4, 19, fill="#555", outline="")
        # Ropes
        for rx in [148, 332]:
            pts = bezier((rx, 30), (rx+4, 50), (rx, 66))
            cv.create_line(*pts, fill="#5C3A10", width=3, smooth=True)
        # Sign board
        sx1, sy1, sx2, sy2 = 128, 40, 352, 114
        cv.create_rectangle(sx1+4, sy1+4, sx2+4, sy2+4, fill="#3A1A00", outline="")
        cv.create_rectangle(sx1, sy1, sx2, sy2, fill="#9B6010", outline="#5C3010", width=3)
        for py in range(sy1+18, sy2, 18):
            cv.create_line(sx1+3, py, sx2-3, py, fill="#7A4A08")
        for cx2, cy2 in [(sx1+10, sy1+10), (sx2-10, sy1+10),
                         (sx1+10, sy2-10), (sx2-10, sy2-10)]:
            cv.create_oval(cx2-4, cy2-4, cx2+4, cy2+4, fill="#888", outline="#555")
            cv.create_line(cx2-3, cy2, cx2+3, cy2, fill="#444")
            cv.create_line(cx2, cy2-3, cx2, cy2+3, fill="#444")
        mid_y = (sy1+sy2) // 2
        cv.create_text(W//2+2, mid_y+2, text="KAKUOTCHI",
                       font=("Georgia", 22, "bold"), fill="#3A1800")
        cv.create_text(W//2,   mid_y,   text="KAKUOTCHI",
                       font=("Georgia", 22, "bold"), fill="#FFE88A")
        # Bull skull
        self._draw_skull(cv, W//2, 16)
        # Settings gear
        cv.create_oval(W-34, 6, W-6, 34, fill="#5C3010", outline="#DAA520", width=2,
                       tags="btn_settings_hdr")
        cv.create_text(W-20, 20, text="⚙", font=("Arial", 12), fill="#FFD700",
                       tags="btn_settings_hdr")
        cv.tag_bind("btn_settings_hdr", "<Button-1>", lambda e: self._open_settings())
        cv.tag_bind("btn_settings_hdr", "<Enter>",    lambda e: cv.config(cursor="hand2"))
        cv.tag_bind("btn_settings_hdr", "<Leave>",    lambda e: cv.config(cursor=""))

    def _draw_skull(self, cv, cx, cy):
        cream, dark = "#F0EDE0", "#CCC5A8"
        for pts in [bezier((cx-18, cy-8), (cx-45, cy-35), (cx-68, cy-22)),
                    bezier((cx+18, cy-8), (cx+45, cy-35), (cx+68, cy-22))]:
            cv.create_line(*pts, fill=cream, width=7, smooth=True)
            cv.create_line(*pts, fill=dark,  width=3, smooth=True)
        cv.create_oval(cx-22, cy-14, cx+22, cy+18, fill=cream, outline=dark, width=2)
        cv.create_oval(cx-14, cy-8,  cx-4,  cy+2,  fill="#444", outline="")
        cv.create_oval(cx+4,  cy-8,  cx+14, cy+2,  fill="#444", outline="")
        cv.create_oval(cx-6, cy+5, cx-1, cy+12, fill="#888", outline="")
        cv.create_oval(cx+1, cy+5, cx+6, cy+12, fill="#888", outline="")

    # ── Footer (fixed) ────────────────────────────────────────────────────────

    def _draw_footer(self):
        cv    = self.ftr_cv
        month = self.data["current_month"]
        try:
            label = datetime.strptime(month, "%Y-%m").strftime("%B  %Y")
        except Exception:
            label = month

        cv.create_rectangle(0, 0, W, FOOTER_H, fill="#5C3010", outline="")
        cv.create_line(0, 0, W, 0, fill="#3A1A00", width=2)
        cv.create_text(34,    FOOTER_H//2, text="◀",
                       font=("Georgia", 18, "bold"), fill="#FFD700", tags="btn_prev")
        cv.create_text(W-34,  FOOTER_H//2, text="▶",
                       font=("Georgia", 18, "bold"), fill="#FFD700", tags="btn_next")
        cv.create_text(W//2,  FOOTER_H//2, text=label,
                       font=("Georgia", 14, "bold"), fill="#FFE88A")

        for tag, cmd in [("btn_prev", self._prev_month), ("btn_next", self._next_month)]:
            cv.tag_bind(tag, "<Button-1>", lambda e, c=cmd: c())
            cv.tag_bind(tag, "<Enter>",    lambda e: cv.config(cursor="hand2"))
            cv.tag_bind(tag, "<Leave>",    lambda e: cv.config(cursor=""))

        # + button: embedded window in scene so it stays at bottom-right of viewport
        add_btn = tk.Canvas(self.scene_cv, width=44, height=44,
                            bd=0, highlightthickness=0, cursor="hand2")
        add_btn.create_oval(0, 0, 44, 44, fill="#228B22", outline="#1A6A1A", width=2)
        add_btn.create_text(22, 22, text="+", font=("Georgia", 20, "bold"), fill="#FFF")
        add_btn.bind("<Button-1>", lambda e: self._add_cactus())
        self.scene_cv.create_window(W-30, SCENE_H-30, window=add_btn, tags="btn_add")

    # ── Cacti ─────────────────────────────────────────────────────────────────

    def _draw_cacti(self, ww):
        cats  = self.data["categories"]
        month = self.data["current_month"]
        n     = len(cats)
        if n == 0:
            return
        slot     = ww / n
        base_y   = 415
        y_jitter = [0, -16, 12, -6, 18, -10]

        for i, cat in enumerate(cats):
            cx    = slot * i + slot / 2
            cy    = base_y + y_jitter[i % len(y_jitter)]
            r     = budget_ratio(cat, month)
            st    = state_for_ratio(r)
            scale = 0.8 if cat["budget"] < 120 else (1.15 if cat["budget"] > 280 else 1.0)
            tag   = f"cactus_{i}"
            self._draw_cactus(cx, cy, cat, st, r, scale, tag)

    def _draw_cactus(self, cx, ground_y, cat, state, ratio, scale, tag):
        if state == "sad":
            self._draw_tumbleweed(cx, ground_y, cat, ratio, tag)
        else:
            self._draw_green_cactus(cx, ground_y, cat, state, ratio, scale, tag)
        self._cat_map[tag] = cat
        cv = self.scene_cv
        cv.tag_bind(tag, "<ButtonRelease-1>",
                    lambda e, t=tag: (None if self._did_drag else self._on_cactus_click(t)))
        cv.tag_bind(tag, "<Button-3>",
                    lambda e, t=tag: self._on_cactus_click(t))
        cv.tag_bind(tag, "<Enter>", lambda e: cv.config(cursor="hand2"))
        cv.tag_bind(tag, "<Leave>", lambda e: cv.config(cursor=""))

    def _draw_green_cactus(self, cx, ground_y, cat, state, ratio, scale, tag):
        cv = self.scene_cv
        s  = scale
        body_c, lite_c, spine_c = (
            ("#1A7A1A", "#2ECC2E", "#98FB98") if state == "happy"
            else ("#787800", "#BABA00", "#DDDD44")
        )
        bw  = int(52 * s)
        bh  = int(105 * s)
        top = ground_y - bh

        # Shadow
        cv.create_oval(cx-int(28*s), ground_y-4, cx+int(28*s), ground_y+9,
                       fill="#9A7540", outline="", tags=tag)
        # Arms (behind body)
        arm_y = top + int(40*s)
        ah    = int(16*s)
        al    = int(42*s)
        cv.create_oval(cx-bw//2-al, arm_y-ah, cx-bw//2+int(12*s), arm_y+ah,
                       fill=body_c, outline=lite_c, width=2, tags=tag)
        cv.create_oval(cx+bw//2-int(12*s), arm_y-ah, cx+bw//2+al, arm_y+ah,
                       fill=body_c, outline=lite_c, width=2, tags=tag)
        # Body
        cv.create_oval(cx-bw//2, top, cx+bw//2, ground_y,
                       fill=body_c, outline=lite_c, width=2, tags=tag)
        cv.create_oval(cx-bw//2+int(7*s), top+int(12*s),
                       cx-bw//2+int(14*s), ground_y-int(10*s),
                       fill=lite_c, outline="", tags=tag)
        # Spines
        for sy in range(int(top+14*s), int(ground_y-8*s), int(16*s)):
            for side, sign in [(cx-bw//2, -1), (cx+bw//2, 1)]:
                cv.create_line(side+sign*int(7*s), sy-int(3*s), side, sy,
                               fill=spine_c, width=1, tags=tag)
                cv.create_line(side+sign*int(7*s), sy+int(3*s), side, sy,
                               fill=spine_c, width=1, tags=tag)
        # Face
        fy = top + int(48*s)
        if state == "happy":
            ew = int(14*s)
            for ex in [cx-int(18*s), cx+int(4*s)]:
                cv.create_arc(ex, fy-int(6*s), ex+ew, fy+int(6*s),
                              start=0, extent=180, style=tk.ARC,
                              outline="#000", width=max(2, int(2.5*s)), tags=tag)
            cv.create_arc(cx-int(18*s), fy+int(5*s), cx+int(18*s), fy+int(22*s),
                          start=200, extent=140, style=tk.ARC,
                          outline="#000", width=max(2, int(2.5*s)), tags=tag)
            cv.create_rectangle(cx-int(13*s), fy+int(12*s),
                                 cx+int(13*s), fy+int(19*s),
                                 fill="#FFF", outline="", tags=tag)
            for tx in range(int(cx-10*s), int(cx+10*s), max(1, int(6*s))):
                cv.create_line(tx, fy+int(12*s), tx, fy+int(19*s),
                               fill="#DDD", width=1, tags=tag)
            cv.create_oval(cx-int(24*s), fy+int(4*s), cx-int(13*s), fy+int(12*s),
                           fill="#FFB0B0", outline="", tags=tag)
            cv.create_oval(cx+int(13*s), fy+int(4*s), cx+int(24*s), fy+int(12*s),
                           fill="#FFB0B0", outline="", tags=tag)
        else:  # warning
            ev = int(8*s)
            cv.create_oval(cx-int(19*s), fy-ev, cx-int(7*s), fy+ev,
                           fill="#fff", outline="", tags=tag)
            cv.create_oval(cx+int(7*s),  fy-ev, cx+int(19*s), fy+ev,
                           fill="#fff", outline="", tags=tag)
            cv.create_oval(cx-int(16*s), fy-int(4*s), cx-int(10*s), fy+int(4*s),
                           fill="#000", outline="", tags=tag)
            cv.create_oval(cx+int(10*s), fy-int(4*s), cx+int(16*s), fy+int(4*s),
                           fill="#000", outline="", tags=tag)
            cv.create_line(cx-int(20*s), fy-int(13*s), cx-int(6*s),  fy-int(10*s),
                           fill="#000", width=max(2, int(2*s)), tags=tag)
            cv.create_line(cx+int(6*s),  fy-int(10*s), cx+int(20*s), fy-int(13*s),
                           fill="#000", width=max(2, int(2*s)), tags=tag)
            cv.create_line(cx-int(14*s), fy+int(12*s), cx-int(5*s), fy+int(9*s),
                           cx+int(5*s),  fy+int(12*s), cx+int(14*s), fy+int(9*s),
                           fill="#000", width=max(2, int(2*s)), tags=tag)

        self._draw_label_bar(cx, ground_y, cat, ratio, state, tag)

    def _draw_tumbleweed(self, cx, ground_y, cat, ratio, tag):
        cv  = self.scene_cv
        rad = 38
        cy  = ground_y - rad

        cv.create_oval(cx-22, ground_y-4, cx+22, ground_y+9,
                       fill="#9A7540", outline="", tags=tag)
        cv.create_oval(cx-rad, ground_y-rad*2, cx+rad, ground_y,
                       fill="#8B6510", outline="#5C3D08", width=2, tags=tag)
        for ang in range(0, 180, 25):
            a = math.radians(ang)
            cv.create_line(cx-rad*math.cos(a), cy-rad*math.sin(a),
                           cx+rad*math.cos(a), cy+rad*math.sin(a),
                           fill="#5C3D08", width=1, tags=tag)
        cv.create_oval(cx-rad, cy-rad//2, cx+rad, cy+rad//2,
                       fill="", outline="#5C3D08", width=1, tags=tag)
        cv.create_oval(cx-rad//2, cy-rad, cx+rad//2, cy+rad,
                       fill="", outline="#5C3D08", width=1, tags=tag)
        cv.create_rectangle(cx-14, ground_y-2, cx-4,  ground_y+14,
                            fill="#7A5510", outline="", tags=tag)
        cv.create_rectangle(cx+4,  ground_y-2, cx+14, ground_y+14,
                            fill="#7A5510", outline="", tags=tag)
        fy = cy - 4
        for ex in [cx-12, cx+12]:
            cv.create_line(ex-5, fy-5, ex+5, fy+5, fill="#000", width=2, tags=tag)
            cv.create_line(ex+5, fy-5, ex-5, fy+5, fill="#000", width=2, tags=tag)
        cv.create_line(cx-18, fy-10, cx-6,  fy-5,  fill="#000", width=3, tags=tag)
        cv.create_line(cx+6,  fy-5,  cx+18, fy-10, fill="#000", width=3, tags=tag)
        cv.create_arc(cx-12, fy+4, cx+12, fy+18,
                      start=20, extent=140, style=tk.ARC, outline="#000", width=2, tags=tag)

        pct    = int(ratio * 100)
        spent  = month_spent(cat, self.data["current_month"])
        budget = cat.get("budget", 0)
        cv.create_text(cx, ground_y+18, text=cat["name"],
                       font=("Georgia", 11, "bold"), fill="#3E1F00", tags=tag)
        cv.create_text(cx, ground_y+34, text=f"OVER BUDGET! ({pct}%)",
                       font=("Georgia", 8, "bold"), fill="#CC0000", tags=tag)
        cv.create_text(cx, ground_y+48, text=f"${spent:.0f} / ${budget:.0f}",
                       font=("Georgia", 8), fill="#884400", tags=tag)

    def _draw_label_bar(self, cx, ground_y, cat, ratio, state, tag):
        cv     = self.scene_cv
        spent  = month_spent(cat, self.data["current_month"])
        budget = cat.get("budget", 0)
        pct    = int(ratio * 100)
        cv.create_text(cx+1, ground_y+14, text=cat["name"],
                       font=("Georgia", 11, "bold"), fill="#2A0F00", tags=tag)
        cv.create_text(cx,   ground_y+13, text=cat["name"],
                       font=("Georgia", 11, "bold"), fill="#3E1F00", tags=tag)
        cv.create_text(cx, ground_y+28,
                       text=f"${spent:.0f} / ${budget:.0f}  ({pct}%)",
                       font=("Georgia", 8), fill="#5C3A10", tags=tag)
        bw       = 70
        by       = ground_y + 40
        bar_fill = min(int(bw * ratio), bw)
        bar_col  = "#2E8B2E" if state == "happy" else "#CC8800"
        cv.create_rectangle(cx-bw//2, by, cx+bw//2, by+8,
                            fill="#9A7540", outline="", tags=tag)
        if bar_fill > 0:
            cv.create_rectangle(cx-bw//2, by, cx-bw//2+bar_fill, by+8,
                                fill=bar_col, outline="", tags=tag)

    # ── Interaction ───────────────────────────────────────────────────────────

    def _on_cactus_click(self, tag):
        cat = self._cat_map.get(tag)
        if not cat:
            return
        spent = month_spent(cat, self.data["current_month"])
        menu  = tk.Menu(self, tearoff=0)
        menu.add_command(
            label=f"  {cat['name']}  —  ${spent:.2f} / ${cat['budget']:.2f}",
            state="disabled")
        menu.add_separator()
        menu.add_command(label="💰  Log Expense",   command=lambda: self._log_expense(cat))
        menu.add_command(label="📋  View History",   command=lambda: self._show_history(cat))
        menu.add_separator()
        menu.add_command(label="✏️  Edit Budget",    command=lambda: self._edit_budget(cat))
        menu.add_command(label="🗑️  Remove Cactus",  command=lambda: self._remove_cactus(cat))
        try:
            menu.tk_popup(self.winfo_rootx() + W//2 - 80,
                          self.winfo_rooty() + H//2)
        finally:
            menu.grab_release()

    def _log_expense(self, cat):
        dlg = AddExpenseDialog(self, cat["name"])
        self.wait_window(dlg)
        if dlg.result:
            cat["expenses"].append({
                "month":       self.data["current_month"],
                "amount":      dlg.result["amount"],
                "description": dlg.result["description"],
                "date":        datetime.now().strftime("%Y-%m-%d"),
            })
            save_data(self.data)
            self._draw()

    def _show_history(self, cat):
        dlg = HistoryDialog(self, cat, self.data["current_month"],
                            on_change=lambda: (save_data(self.data), self._draw()))
        self.wait_window(dlg)
        self._draw()

    def _edit_budget(self, cat):
        new_b = simpledialog.askfloat("Edit Budget",
                                      f"New monthly budget for  {cat['name']}:",
                                      initialvalue=cat["budget"], minvalue=0.01, parent=self)
        if new_b:
            cat["budget"] = new_b
            save_data(self.data)
            self._draw()

    def _remove_cactus(self, cat):
        if messagebox.askyesno("Remove Cactus",
                               f"Remove '{cat['name']}' and all its data?\nThis cannot be undone."):
            self.data["categories"].remove(cat)
            save_data(self.data)
            self._draw()

    def _add_cactus(self):
        dlg = AddCactusDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            self.data["categories"].append(dlg.result)
            save_data(self.data)
            self._draw()

    def _open_settings(self):
        win = tk.Toplevel(self)
        win.title("Budget Settings")
        win.configure(bg=DLOG_BG)
        win.resizable(False, False)
        win.grab_set()
        tk.Label(win, text="Monthly Budgets", font=("Georgia", 14, "bold"),
                 bg=DLOG_BG, fg=DLOG_TEXT).pack(pady=(12, 4))
        frame   = tk.Frame(win, bg=DLOG_BG)
        frame.pack(padx=24, pady=8)
        entries = []
        for i, cat in enumerate(self.data["categories"]):
            tk.Label(frame, text=cat["name"], bg=DLOG_BG, fg=DLOG_TEXT,
                     font=("Georgia", 11), width=16, anchor="e").grid(row=i, column=0, pady=4)
            var = tk.StringVar(value=str(cat["budget"]))
            tk.Entry(frame, textvariable=var, width=10,
                     font=("Georgia", 11)).grid(row=i, column=1, padx=8)
            entries.append((cat, var))

        def _save():
            for cat2, var2 in entries:
                try:
                    b = float(var2.get())
                    if b > 0:
                        cat2["budget"] = b
                except ValueError:
                    pass
            save_data(self.data)
            self._draw()
            win.destroy()

        row2 = tk.Frame(win, bg=DLOG_BG)
        row2.pack(pady=10)
        tk.Button(row2, text="Save",   command=_save,
                  bg=BTN_BG, fg=BTN_FG, font=("Georgia", 11, "bold"), padx=10).pack(side="left", padx=6)
        tk.Button(row2, text="Cancel", command=win.destroy,
                  bg="#666", fg="#fff", font=("Georgia", 10), padx=8).pack(side="left", padx=6)

    def _prev_month(self):
        dt   = datetime.strptime(self.data["current_month"], "%Y-%m")
        m, y = (12, dt.year-1) if dt.month == 1 else (dt.month-1, dt.year)
        self.data["current_month"] = f"{y:04d}-{m:02d}"
        save_data(self.data)
        self._draw()

    def _next_month(self):
        dt   = datetime.strptime(self.data["current_month"], "%Y-%m")
        m, y = (1, dt.year+1) if dt.month == 12 else (dt.month+1, dt.year)
        self.data["current_month"] = f"{y:04d}-{m:02d}"
        save_data(self.data)
        self._draw()

    def _quit(self):
        save_data(self.data)
        self.destroy()

# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = KakuotchiApp()
    app.mainloop()