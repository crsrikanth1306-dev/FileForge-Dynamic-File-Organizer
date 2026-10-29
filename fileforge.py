import json
import shutil
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# FileForge: Dynamic File Organizer
# Core algorithm: scan -> classify -> preview -> safely move -> report.

CATEGORY_RULES = {
    "Images": {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg", ".tiff"},
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".ppt", ".pptx", ".xls", ".xlsx", ".csv"},
    "Code": {".py", ".java", ".c", ".cpp", ".js", ".ts", ".html", ".css", ".json", ".sql", ".ipynb"},
    "Audio": {".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"},
    "Video": {".mp4", ".mkv", ".mov", ".avi", ".webm", ".wmv"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz"},
    "Executables": {".exe", ".msi", ".bat", ".sh", ".app"},
}

def classify_file(path: Path) -> str:
    """Return a category for a file based on its lowercase suffix."""
    suffix = path.suffix.lower()
    for category, extensions in CATEGORY_RULES.items():
        if suffix in extensions:
            return category
    return "Others"

def scan_files(folder: Path):
    """Scan only the selected folder's immediate files; do not recurse into output folders."""
    return sorted((p for p in folder.iterdir() if p.is_file() and p.name != "fileforge_report.json"),
                  key=lambda p: p.name.lower())

def unique_destination(destination: Path) -> Path:
    """Avoid overwriting a file by adding a numbered suffix when needed."""
    if not destination.exists():
        return destination
    stem, suffix = destination.stem, destination.suffix
    counter = 1
    while True:
        candidate = destination.with_name(f"{stem}_{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1

def build_plan(folder: Path):
    plan = []
    for source in scan_files(folder):
        category = classify_file(source)
        destination = folder / category / source.name
        plan.append({"source": source, "category": category, "destination": destination})
    return plan

def organize(folder: Path, dry_run=True):
    """Preview or execute moves and return a report dictionary."""
    report = {
        "project": "FileForge - Dynamic File Organizer",
        "folder": str(folder),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "mode": "preview" if dry_run else "organize",
        "moved": [], "skipped": [], "errors": []
    }
    for item in build_plan(folder):
        source = item["source"]
        category = item["category"]
        destination_dir = folder / category
        if source.parent == destination_dir:
            report["skipped"].append({"file": source.name, "reason": "Already organized"})
            continue
        if dry_run:
            report["moved"].append({
                "file": source.name, "category": category,
                "destination": str(destination_dir / source.name), "status": "Preview only"
            })
            continue
        try:
            destination_dir.mkdir(parents=True, exist_ok=True)
            destination = unique_destination(destination_dir / source.name)
            shutil.move(str(source), str(destination))
            report["moved"].append({
                "file": source.name, "category": category,
                "destination": str(destination), "status": "Moved"
            })
        except (OSError, shutil.Error) as exc:
            report["errors"].append({"file": source.name, "error": str(exc)})
    if not dry_run:
        report_path = folder / "fileforge_report.json"
        try:
            report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        except OSError as exc:
            report["errors"].append({"file": "fileforge_report.json", "error": str(exc)})
    return report

class FileForgeApp:
    def __init__(self, root):
        self.root = root
        root.title("FileForge | Dynamic File Organizer")
        root.geometry("900x600")
        root.minsize(760, 500)
        root.configure(bg="#f4f7fb")
        self.folder = tk.StringVar()
        self.status = tk.StringVar(value="Choose a folder, then preview the proposed changes.")
        self._build_ui()

    def _build_ui(self):
        header = tk.Frame(self.root, bg="#152a46", padx=22, pady=18)
        header.pack(fill="x")
        tk.Label(header, text="FILEFORGE", font=("Segoe UI", 23, "bold"),
                 fg="white", bg="#152a46").pack(anchor="w")
        tk.Label(header, text="Dynamic File Organizer • Scan  |  Classify  |  Organize",
                 font=("Segoe UI", 10), fg="#c9d8ec", bg="#152a46").pack(anchor="w", pady=(3, 0))

        body = tk.Frame(self.root, bg="#f4f7fb", padx=22, pady=18)
        body.pack(fill="both", expand=True)
        tk.Label(body, text="Folder to organize", font=("Segoe UI", 11, "bold"),
                 bg="#f4f7fb", fg="#152a46").pack(anchor="w")
        row = tk.Frame(body, bg="#f4f7fb")
        row.pack(fill="x", pady=(7, 12))
        ttk.Entry(row, textvariable=self.folder).pack(side="left", fill="x", expand=True, ipady=6)
        ttk.Button(row, text="Browse…", command=self.choose_folder).pack(side="left", padx=(8, 0), ipady=3)

        buttons = tk.Frame(body, bg="#f4f7fb")
        buttons.pack(fill="x", pady=(0, 12))
        ttk.Button(buttons, text="Preview Changes", command=self.preview).pack(side="left")
        ttk.Button(buttons, text="Organize Files", command=self.run_organize).pack(side="left", padx=8)
        ttk.Button(buttons, text="Clear Results", command=self.clear).pack(side="left")

        self.table = ttk.Treeview(body, columns=("category", "destination", "status"),
                                  show="headings", height=15)
        self.table.heading("category", text="Category")
        self.table.heading("destination", text="Destination")
        self.table.heading("status", text="Status")
        self.table.column("category", width=130, stretch=False)
        self.table.column("destination", width=450)
        self.table.column("status", width=130, stretch=False)
        scroll = ttk.Scrollbar(body, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        self.table.pack(side="left", fill="both", expand=True)
        scroll.pack(side="left", fill="y")

        footer = tk.Label(self.root, textvariable=self.status, anchor="w",
                          bg="#e5edf7", fg="#152a46", padx=22, pady=10)
        footer.pack(fill="x")

    def choose_folder(self):
        selected = filedialog.askdirectory(title="Choose a folder")
        if selected:
            self.folder.set(selected)
            self.status.set(f"Selected: {selected}")

    def _selected_folder(self):
        value = self.folder.get().strip()
        if not value:
            messagebox.showwarning("Folder required", "Please choose a folder first.")
            return None
        folder = Path(value).expanduser()
        if not folder.exists() or not folder.is_dir():
            messagebox.showerror("Invalid folder", "The selected path is not a valid folder.")
            return None
        return folder

    def _show_report(self, report):
        self.clear()
        for item in report["moved"]:
            self.table.insert("", "end", values=(item["category"], item["destination"], item["status"]))
        for item in report["skipped"]:
            self.table.insert("", "end", values=("-", item["file"], item["reason"]))
        for item in report["errors"]:
            self.table.insert("", "end", values=("-", item["file"], "Error: " + item["error"]))
        self.status.set(
            f"Mode: {report['mode']} | Planned/moved: {len(report['moved'])} | "
            f"Skipped: {len(report['skipped'])} | Errors: {len(report['errors'])}"
        )

    def preview(self):
        folder = self._selected_folder()
        if folder:
            self._show_report(organize(folder, dry_run=True))

    def run_organize(self):
        folder = self._selected_folder()
        if not folder:
            return
        if not messagebox.askyesno("Confirm organization",
            "This will move files into category folders. A JSON report will be saved. Continue?"):
            return
        report = organize(folder, dry_run=False)
        self._show_report(report)
        messagebox.showinfo("FileForge finished",
            f"Organization complete.\nMoved: {len(report['moved'])}\n"
            f"Errors: {len(report['errors'])}\n\nReport: {folder / 'fileforge_report.json'}")

    def clear(self):
        for item in self.table.get_children():
            self.table.delete(item)

if __name__ == "__main__":
    root = tk.Tk()
    app = FileForgeApp(root)
    root.mainloop()
