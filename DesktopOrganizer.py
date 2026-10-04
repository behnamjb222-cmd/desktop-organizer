#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Desktop Organizer GUI  -  مرتب‌کننده‌ی فایل‌ها با محیط گرافیکی (Tkinter)
=====================================================================
• انتخاب یک یا چند پوشه (Desktop، Downloads، Documents یا هر پوشه‌ی دلخواه)
• انتخاب اینکه کدام دسته‌ها مرتب شوند (عکس، ویدیو، سند و ...)
• پوشه‌ی هر دسته «فقط وقتی» ساخته می‌شود که حداقل یک فایل از آن نوع وجود داشته باشد
• پیش‌نمایش قبل از هر تغییر، تاریخچه و برگرداندن (Undo)
• تشخیص فایل‌های تکراری، زیرپوشه‌ی تاریخ، حالت عمیق
• هیچ فایلی حذف یا بازنویسی نمی‌شود
فقط از کتابخانه‌های خود پایتون استفاده می‌کند (سبک و بدون نصب چیز اضافه).
"""

from __future__ import annotations

import hashlib
import json
import queue
import shutil
import sys
import threading
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

# ----------------------------------------------------------------------------
# تنظیمات
# ----------------------------------------------------------------------------
APP_TITLE = "مرتب‌کننده‌ی فایل‌ها"
HISTORY_NAME = ".organizer_history.json"
MAX_HISTORY = 20
OTHER = "Others"
DUP_FOLDER = "Duplicates"

CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".tiff", ".heic", ".raw"],
    "Videos": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".3gp"],
    "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".md", ".epub", ".djvu"],
    "Spreadsheets": [".xls", ".xlsx", ".csv", ".ods"],
    "Presentations": [".ppt", ".pptx", ".odp", ".key"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso"],
    "Programs": [".exe", ".msi", ".apk", ".dmg", ".deb", ".bat"],
    "Code": [".py", ".js", ".ts", ".html", ".css", ".java", ".c", ".cpp", ".cs", ".php", ".json",
             ".xml", ".sql", ".sh", ".go", ".rs", ".ipynb"],
    "Design": [".psd", ".ai", ".fig", ".sketch", ".xd", ".indd", ".dwg"],
    "Fonts": [".ttf", ".otf", ".woff", ".woff2"],
}
# اگر کلمه‌ای از این لیست در اسم فایل بود، به همان دسته می‌رود
NAME_RULES = {"Screenshots": ["screenshot", "screen shot", "snip", "اسکرین"]}
ALL_CATEGORIES = list(CATEGORIES) + list(NAME_RULES) + [OTHER]

CAT_FA = {
    "Images": "تصاویر", "Videos": "ویدیوها", "Audio": "صوت", "Documents": "اسناد",
    "Spreadsheets": "اکسل/جداول", "Presentations": "پرزنتیشن", "Archives": "فشرده",
    "Programs": "برنامه‌ها", "Code": "کد", "Design": "طراحی", "Fonts": "فونت",
    "Screenshots": "اسکرین‌شات", OTHER: "سایر",
}

EXT_MAP = {e.lower(): c for c, exts in CATEGORIES.items() for e in exts}
IGNORE_EXT = {".lnk", ".url", ".ini", ".tmp", ".part", ".crdownload", ".download", ".opdownload"}
IGNORE_NAMES = {"desktop.ini", "thumbs.db", ".ds_store"}

BY_DATE_LABELS = {"بدون زیرپوشه‌ی تاریخ": "none", "زیرپوشه‌ی سال": "year", "زیرپوشه‌ی سال-ماه": "month"}
DEDUPE_LABELS = {"خاموش": "off", "فقط گزارش": "report", "انتقال به Duplicates": "move"}


# ----------------------------------------------------------------------------
# هسته‌ی مرتب‌سازی (مستقل از رابط گرافیکی)
# ----------------------------------------------------------------------------
def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


def known_folder(name: str) -> Path | None:
    home = Path.home()
    for c in [home / name, *home.glob(f"OneDrive*/{name}")]:
        if c.is_dir():
            return c
    return None


def is_unsafe(p: Path) -> bool:
    """جلوگیری از مرتب‌کردن ریشه‌ی درایو، پوشه‌ی کاربر و پوشه‌های سیستمی."""
    try:
        p = p.resolve()
    except OSError:
        return True
    if p.parent == p or p == Path.home():
        return True
    parts = [x.lower() for x in p.parts]
    return len(parts) > 1 and parts[1] in {"windows", "program files", "program files (x86)", "programdata"}


def classify(path: Path) -> str:
    name = path.name.lower()
    for cat, kws in NAME_RULES.items():
        if any(k.lower() in name for k in kws):
            return cat
    return EXT_MAP.get(path.suffix.lower(), OTHER)


def unique_target(target: Path) -> Path:
    if not target.exists():
        return target
    i = 1
    while True:
        new = target.with_name(f"{target.stem} ({i}){target.suffix}")
        if not new.exists():
            return new
        i += 1


def file_hash(path: Path) -> str | None:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while chunk := f.read(1024 * 1024):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def load_history(target: Path) -> list:
    p = target / HISTORY_NAME
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_history(target: Path, history: list):
    try:
        (target / HISTORY_NAME).write_text(
            json.dumps(history[-MAX_HISTORY:], ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass


def own_names() -> set:
    names = {HISTORY_NAME.lower(), Path(sys.argv[0]).name.lower(), Path(sys.executable).name.lower()}
    return names


def collect_files(target: Path, deep: bool, min_age: float):
    now = time.time()
    own = own_names()
    files, stats = [], Counter()
    if deep:
        skip_dirs = {c.lower() for c in ALL_CATEGORIES} | {DUP_FOLDER.lower()}
        items = list(target.iterdir())
        for d in [i for i in items if i.is_dir() and not i.name.startswith(".")]:
            if d.name.lower() in skip_dirs:
                continue
            try:
                items.extend(f for f in d.rglob("*") if f.is_file())
            except OSError:
                pass
    else:
        items = target.iterdir()
    for item in items:
        try:
            if not item.is_file():
                stats["folders"] += 1
                continue
            name = item.name.lower()
            ext = item.suffix.lower()
            if ext in (".lnk", ".url"):
                stats["shortcuts"] += 1
                continue
            if name in own or name in IGNORE_NAMES or name.startswith(".") or ext in IGNORE_EXT:
                stats["ignored"] += 1
                continue
            st = item.stat()
        except OSError:
            stats["errors"] += 1
            continue
        if now - st.st_mtime < min_age:
            stats["too_new"] += 1
            continue
        files.append((item, st))
    return files, stats


def find_duplicates(files, max_bytes: int) -> dict:
    by_size = defaultdict(list)
    for p, st in files:
        if 0 < st.st_size <= max_bytes:
            by_size[st.st_size].append((p, st))
    dups = {}
    for group in by_size.values():
        if len(group) < 2:
            continue
        by_hash = defaultdict(list)
        for p, st in group:
            h = file_hash(p)
            if h:
                by_hash[h].append((p, st))
        for same in by_hash.values():
            if len(same) > 1:
                same.sort(key=lambda x: x[1].st_mtime)
                for p, _ in same[1:]:
                    dups[p] = same[0][0]
    return dups


def make_dirs(directory: Path, root: Path, created: list):
    """پوشه فقط همین‌جا و در لحظه‌ی نیاز ساخته می‌شود (یعنی هیچ پوشه‌ی خالی‌ای ساخته نمی‌شود)."""
    missing, d = [], directory
    while d != root and not d.exists():
        missing.append(d)
        d = d.parent
    directory.mkdir(parents=True, exist_ok=True)
    created.extend(str(m) for m in reversed(missing))


def organize(target: Path, opts: dict, dry_run: bool, log, progress) -> int:
    log(f"\n📁 {target}")
    files, cs = collect_files(target, opts["deep"], opts["min_age"])

    before = len(files)
    files = [(p, st) for p, st in files if classify(p) in opts["cats"]]
    skipped_cat = before - len(files)

    dups = {}
    if opts["dedupe"] != "off" and files:
        dups = find_duplicates(files, opts["dedupe_max_mb"] * 1024 * 1024)
        if opts["dedupe"] == "report" and dups:
            log(f"🔍 {len(dups)} فایل تکراری پیدا شد:")
            for d, o in dups.items():
                log(f"   {d.name}  ==  {o.name}")

    if not files:
        log("✨ فایلی برای مرتب‌کردن پیدا نشد.")
        log(f"   پوشه‌ها: {cs['folders']} | میانبرها: {cs['shortcuts']} | نادیده/سیستمی: {cs['ignored']} | "
            f"تازه‌تغییرکرده: {cs['too_new']} | خارج از دسته‌های انتخابی: {skipped_cat}")
        if not opts["deep"] and cs["folders"]:
            log("   💡 اگر فایل‌ها داخل پوشه‌ها هستند، گزینه‌ی «حالت عمیق» را روشن کن.")
        return 0

    moves, created = [], []
    count, size = Counter(), Counter()
    total = len(files)
    for i, (src, st) in enumerate(files, 1):
        if src in dups and opts["dedupe"] == "move":
            cat, sub = DUP_FOLDER, ""
        else:
            cat = classify(src)
            sub = ""
            if opts["by_date"] != "none":
                dt = datetime.fromtimestamp(st.st_mtime)
                sub = dt.strftime("%Y") if opts["by_date"] == "year" else dt.strftime("%Y-%m")
        dest_dir = target / cat / sub if sub else target / cat
        label = dest_dir.relative_to(target)
        if dry_run:
            log(f"[پیش‌نمایش] {src.name}  ←  {label}/")
        else:
            try:
                make_dirs(dest_dir, target, created)
                dest = unique_target(dest_dir / src.name)
                shutil.move(str(src), str(dest))
                moves.append({"from": str(src), "to": str(dest)})
                log(f"{src.name}  ←  {label}/")
            except Exception as e:
                log(f"   ⚠️ «{src.name}» جابه‌جا نشد: {e}")
                progress(i, total)
                continue
        count[cat] += 1
        size[cat] += st.st_size
        progress(i, total)

    if moves:
        history = load_history(target)
        run_id = (history[-1]["id"] + 1) if history else 1
        history.append({"id": run_id, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "moves": moves, "created_dirs": created})
        save_history(target, history)

    log("\n📊 گزارش" + (" (پیش‌نمایش)" if dry_run else "") + ":")
    for cat, n in count.most_common():
        log(f"   {CAT_FA.get(cat, cat):<14} {n:>4} فایل   {human(size[cat])}")
    log(f"   جمع: {sum(count.values())} فایل، {human(sum(size.values()))}")
    if cs["too_new"]:
        log(f"   ({cs['too_new']} فایل تازه‌تغییرکرده رد شد؛ احتمالاً هنوز در حال دانلود است)")
    return sum(count.values())


def undo_run(target: Path, run_id: int, log) -> int:
    history = load_history(target)
    run = next((r for r in history if r["id"] == run_id), None)
    if not run:
        log("اجرای موردنظر پیدا نشد.")
        return 0
    restored = 0
    for m in reversed(run["moves"]):
        src, dst = Path(m["to"]), Path(m["from"])
        if not src.exists():
            continue
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(unique_target(dst)))
            restored += 1
        except Exception as e:
            log(f"⚠️ «{src.name}» برنگشت: {e}")
    for d in reversed(run.get("created_dirs", [])):
        p = Path(d)
        try:
            if p.is_dir() and not any(p.iterdir()):
                p.rmdir()
        except OSError:
            pass
    save_history(target, [r for r in history if r["id"] != run_id])
    log(f"↩️ {restored} فایل به جای اصلی برگشت. ({target})")
    return restored


def clean_empty(target: Path, log) -> int:
    removed = 0
    for d in target.iterdir():
        try:
            if d.is_dir() and not d.name.startswith(".") and not any(d.iterdir()):
                d.rmdir()
                removed += 1
                log(f"🧹 پوشه‌ی خالی حذف شد: {d.name}")
        except OSError:
            pass
    return removed


# ----------------------------------------------------------------------------
# رابط گرافیکی
# ----------------------------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("820x760")
        self.minsize(760, 680)
        self.q: queue.Queue = queue.Queue()
        self.busy = False
        self.folders: list[Path] = []
        self.cat_vars: dict[str, tk.BooleanVar] = {}

        style = ttk.Style(self)
        try:
            style.theme_use("vista" if sys.platform == "win32" else "clam")
        except tk.TclError:
            pass
        self.option_add("*Font", "Tahoma 10")
        style.configure("Big.TButton", padding=8, font=("Tahoma", 10, "bold"))

        self._build()
        desktop = known_folder("Desktop")
        if desktop:
            self.add_folder(desktop)
        self.after(100, self.poll)

    # ---------- ساخت رابط ----------
    def _build(self):
        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)

        # پوشه‌ها
        f1 = ttk.LabelFrame(root, text=" ۱) کدام پوشه‌ها مرتب شوند؟ ", padding=8)
        f1.pack(fill="x")
        left = ttk.Frame(f1)
        left.pack(side="left", fill="both", expand=True)
        self.lb = tk.Listbox(left, height=4, selectmode="extended", activestyle="none")
        self.lb.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(left, command=self.lb.yview)
        sb.pack(side="left", fill="y")
        self.lb.config(yscrollcommand=sb.set)
        btns = ttk.Frame(f1)
        btns.pack(side="left", padx=(8, 0))
        ttk.Button(btns, text="➕ افزودن پوشه…", command=self.browse).grid(row=0, column=0, sticky="ew", pady=1)
        ttk.Button(btns, text="➖ حذف از لیست", command=self.remove_selected).grid(row=1, column=0, sticky="ew", pady=1)
        quick = ttk.Frame(btns)
        quick.grid(row=2, column=0, pady=(4, 0))
        for text, name in (("Desktop", "Desktop"), ("Downloads", "Downloads"), ("Documents", "Documents")):
            ttk.Button(quick, text=text, width=10, command=lambda n=name: self.add_known(n)).pack(side="left", padx=1)

        # دسته‌ها
        f2 = ttk.LabelFrame(root, text=" ۲) کدام نوع فایل‌ها مرتب شوند؟ ", padding=8)
        f2.pack(fill="x", pady=(8, 0))
        grid = ttk.Frame(f2)
        grid.pack(fill="x")
        for i, cat in enumerate(ALL_CATEGORIES):
            v = tk.BooleanVar(value=True)
            self.cat_vars[cat] = v
            ttk.Checkbutton(grid, text=CAT_FA.get(cat, cat), variable=v).grid(row=i // 5, column=i % 5, sticky="w", padx=6, pady=2)
        sel = ttk.Frame(f2)
        sel.pack(anchor="w", pady=(4, 0))
        ttk.Button(sel, text="انتخاب همه", command=lambda: self.set_all(True)).pack(side="left", padx=2)
        ttk.Button(sel, text="هیچ‌کدام", command=lambda: self.set_all(False)).pack(side="left", padx=2)
        ttk.Label(f2, text="ℹ️ پوشه‌ی هر دسته فقط وقتی ساخته می‌شود که فایلی از همان نوع پیدا شود؛ پوشه‌ی خالی ساخته نمی‌شود.",
                  foreground="#555").pack(anchor="w", pady=(4, 0))

        # تنظیمات
        f3 = ttk.LabelFrame(root, text=" ۳) تنظیمات ", padding=8)
        f3.pack(fill="x", pady=(8, 0))
        ttk.Label(f3, text="زیرپوشه‌ی تاریخ:").grid(row=0, column=0, sticky="w", padx=4, pady=3)
        self.by_date = ttk.Combobox(f3, values=list(BY_DATE_LABELS), state="readonly", width=24)
        self.by_date.current(0)
        self.by_date.grid(row=0, column=1, sticky="w", padx=4)
        ttk.Label(f3, text="فایل‌های تکراری:").grid(row=0, column=2, sticky="w", padx=(16, 4))
        self.dedupe = ttk.Combobox(f3, values=list(DEDUPE_LABELS), state="readonly", width=24)
        self.dedupe.current(0)
        self.dedupe.grid(row=0, column=3, sticky="w", padx=4)
        self.deep = tk.BooleanVar(value=False)
        ttk.Checkbutton(f3, text="حالت عمیق (فایل‌های داخل پوشه‌ها را هم بیرون بکش و مرتب کن)",
                        variable=self.deep).grid(row=1, column=0, columnspan=3, sticky="w", padx=4, pady=3)
        ttk.Label(f3, text="رد کردن فایل‌های تازه (ثانیه):").grid(row=2, column=0, sticky="w", padx=4, pady=3)
        self.min_age = tk.IntVar(value=30)
        ttk.Spinbox(f3, from_=0, to=3600, width=8, textvariable=self.min_age).grid(row=2, column=1, sticky="w", padx=4)

        # دکمه‌ها
        f4 = ttk.Frame(root)
        f4.pack(fill="x", pady=(10, 0))
        self.action_buttons = []
        for text, cmd in (("👁 پیش‌نمایش", self.on_preview), ("▶ شروع مرتب‌سازی", self.on_start),
                          ("↩ برگرداندن (Undo)", self.on_undo), ("🧹 حذف پوشه‌های خالی", self.on_clean)):
            b = ttk.Button(f4, text=text, command=cmd, style="Big.TButton")
            b.pack(side="left", expand=True, fill="x", padx=2)
            self.action_buttons.append(b)

        self.pb = ttk.Progressbar(root, mode="determinate")
        self.pb.pack(fill="x", pady=(10, 4))
        self.logbox = scrolledtext.ScrolledText(root, height=12, state="disabled", wrap="word")
        self.logbox.pack(fill="both", expand=True)

    # ---------- پوشه‌ها ----------
    def add_folder(self, p: Path):
        p = Path(p)
        if p in self.folders:
            return
        if is_unsafe(p):
            messagebox.showwarning(APP_TITLE, f"این پوشه برای مرتب‌سازی امن نیست:\n{p}")
            return
        self.folders.append(p)
        self.lb.insert("end", str(p))

    def add_known(self, name: str):
        p = known_folder(name)
        if p:
            self.add_folder(p)
        else:
            messagebox.showinfo(APP_TITLE, f"پوشه‌ی {name} پیدا نشد.")

    def browse(self):
        d = filedialog.askdirectory(title="یک پوشه برای مرتب‌سازی انتخاب کن")
        if d:
            self.add_folder(Path(d))

    def remove_selected(self):
        for i in reversed(self.lb.curselection()):
            self.lb.delete(i)
            del self.folders[i]

    def set_all(self, value: bool):
        for v in self.cat_vars.values():
            v.set(value)

    def targets(self) -> list[Path]:
        """اگر در لیست چیزی انتخاب شده باشد همان‌ها، وگرنه همه‌ی پوشه‌های لیست."""
        sel = self.lb.curselection()
        chosen = [self.folders[i] for i in sel] if sel else list(self.folders)
        if not chosen:
            messagebox.showinfo(APP_TITLE, "اول حداقل یک پوشه به لیست اضافه کن.")
        return chosen

    def options(self) -> dict | None:
        cats = {c for c, v in self.cat_vars.items() if v.get()}
        if not cats:
            messagebox.showinfo(APP_TITLE, "حداقل یک نوع فایل را انتخاب کن.")
            return None
        try:
            min_age = max(0, int(self.min_age.get()))
        except (tk.TclError, ValueError):
            min_age = 30
        return {"cats": cats, "by_date": BY_DATE_LABELS[self.by_date.get()],
                "dedupe": DEDUPE_LABELS[self.dedupe.get()], "dedupe_max_mb": 500,
                "deep": self.deep.get(), "min_age": min_age}

    # ---------- لاگ و ترد ----------
    def log_write(self, text: str):
        self.logbox.config(state="normal")
        self.logbox.insert("end", text + "\n")
        self.logbox.see("end")
        self.logbox.config(state="disabled")

    def set_busy(self, busy: bool):
        self.busy = busy
        for b in self.action_buttons:
            b.config(state="disabled" if busy else "normal")
        if not busy:
            self.pb["value"] = 0

    def poll(self):
        try:
            while True:
                kind, *data = self.q.get_nowait()
                if kind == "log":
                    self.log_write(data[0])
                elif kind == "progress":
                    self.pb["maximum"] = max(1, data[1])
                    self.pb["value"] = data[0]
                elif kind == "done":
                    self.set_busy(False)
                    if data[0]:
                        messagebox.showinfo(APP_TITLE, data[0])
        except queue.Empty:
            pass
        self.after(100, self.poll)

    def run_task(self, fn, done_message=None):
        if self.busy:
            return
        self.set_busy(True)

        def worker():
            msg = done_message
            try:
                result = fn(lambda t: self.q.put(("log", t)), lambda a, b: self.q.put(("progress", a, b)))
                if callable(msg):
                    msg = msg(result)
            except Exception as e:  # حتی در خطا برنامه نبندد
                self.q.put(("log", f"❌ خطا: {e}"))
                msg = None
            self.q.put(("done", msg))

        threading.Thread(target=worker, daemon=True).start()

    # ---------- دکمه‌ها ----------
    def _run_organize(self, dry_run: bool):
        targets, opts = self.targets(), None
        if not targets:
            return
        opts = self.options()
        if not opts:
            return
        if not dry_run:
            names = "\n".join(f"• {t}" for t in targets)
            if not messagebox.askyesno(APP_TITLE, f"فایل‌های این پوشه‌ها مرتب شوند؟\n\n{names}\n\n"
                                                  "(هر لحظه می‌توانی با «برگرداندن» همه‌چیز را به حالت قبل برگردانی.)"):
                return

        def job(log, progress):
            total = 0
            for t in targets:
                total += organize(t, opts, dry_run, log, progress)
            log("\n" + ("— پایان پیش‌نمایش —" if dry_run else "✅ — پایان —"))
            return total

        if dry_run:
            self.run_task(job)
        else:
            self.run_task(job, lambda n: f"✅ {n} فایل مرتب شد." if n else "فایلی برای مرتب‌کردن پیدا نشد.")

    def on_preview(self):
        self._run_organize(True)

    def on_start(self):
        self._run_organize(False)

    def on_clean(self):
        targets = self.targets()
        if not targets:
            return

        def job(log, progress):
            n = sum(clean_empty(t, log) for t in targets)
            log(f"🧹 {n} پوشه‌ی خالی حذف شد." if n else "پوشه‌ی خالی‌ای وجود نداشت.")
            return n

        self.run_task(job)

    def on_undo(self):
        targets = self.targets()
        if not targets:
            return
        target = targets[0]
        history = load_history(target)
        if not history:
            messagebox.showinfo(APP_TITLE, f"برای این پوشه تاریخچه‌ای وجود ندارد:\n{target}")
            return

        win = tk.Toplevel(self)
        win.title("برگرداندن یک مرتب‌سازی")
        win.geometry("460x320")
        win.transient(self)
        win.grab_set()
        ttk.Label(win, text=f"پوشه: {target}\nکدام مرتب‌سازی برگردانده شود؟", padding=8).pack(anchor="w")
        lb = tk.Listbox(win, activestyle="none")
        lb.pack(fill="both", expand=True, padx=8)
        for r in reversed(history):
            lb.insert("end", f"#{r['id']}   {r['time']}   —   {len(r['moves'])} فایل")
        lb.selection_set(0)

        def do_undo():
            idx = lb.curselection()
            if not idx:
                return
            run = list(reversed(history))[idx[0]]
            win.destroy()
            self.run_task(lambda log, prog: undo_run(target, run["id"], log),
                          lambda n: f"↩️ {n} فایل برگشت.")

        ttk.Button(win, text="برگردان", command=do_undo, style="Big.TButton").pack(pady=8)


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
