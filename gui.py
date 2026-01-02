#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
from pathlib import Path
import url_collector  # your script must be in the same folder

class URLCollectorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube URL Collector")
        self.geometry("650x400")
        self.resizable(False, False)

        # ─── Styling ───
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TEntry", font=("Segoe UI", 10))
        style.configure("TCombobox", font=("Segoe UI", 10))

        # ─── Frames ───
        self.frame_inputs = ttk.Frame(self)
        self.frame_inputs.pack(padx=15, pady=10, fill="x")

        self.frame_progress = ttk.Frame(self)
        self.frame_progress.pack(padx=15, pady=10, fill="x")

        self.frame_output = ttk.Frame(self)
        self.frame_output.pack(padx=15, pady=10, fill="both", expand=True)

        # ─── Input Widgets ───
        ttk.Label(self.frame_inputs, text="Search Query:").grid(row=0, column=0, sticky="w")
        self.query_entry = ttk.Entry(self.frame_inputs, width=60)
        self.query_entry.grid(row=0, column=1, columnspan=3, pady=5, sticky="ew")

        ttk.Label(self.frame_inputs, text="Sort By:").grid(row=1, column=0, sticky="w", pady=5)
        self.sort_var = tk.StringVar(value="relevance")
        self.sort_menu = ttk.Combobox(self.frame_inputs, textvariable=self.sort_var,
                                      values=["relevance", "date", "views", "rating"], state="readonly", width=15)
        self.sort_menu.grid(row=1, column=1, sticky="w", padx=(0, 10))

        ttk.Label(self.frame_inputs, text="Max Results:").grid(row=1, column=2, sticky="e")
        self.max_entry = ttk.Entry(self.frame_inputs, width=10)
        self.max_entry.insert(0, "10")
        self.max_entry.grid(row=1, column=3, sticky="w")

        ttk.Label(self.frame_inputs, text="Output File (optional):").grid(row=2, column=0, sticky="w", pady=5)
        self.output_entry = ttk.Entry(self.frame_inputs, width=50)
        self.output_entry.grid(row=2, column=1, columnspan=2, sticky="ew")
        self.browse_button = ttk.Button(self.frame_inputs, text="Browse", command=self.browse_file)
        self.browse_button.grid(row=2, column=3, sticky="w", padx=(5, 0))

        # ─── Progress Widgets ───
        ttk.Label(self.frame_progress, text="Progress:").pack(anchor="w")
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.frame_progress, orient="horizontal",
                                            length=600, mode="determinate",
                                            variable=self.progress_var, maximum=100)
        self.progress_bar.pack(pady=5)

        # ─── Start Button ───
        self.start_button = ttk.Button(self.frame_progress, text="Start Scraping", command=self.start_scraping)
        self.start_button.pack(pady=5)

        # ─── Output Text ───
        self.output_text = tk.Text(self.frame_output, wrap="word", state="disabled", font=("Segoe UI", 10))
        self.output_text.pack(fill="both", expand=True)
        self.scrollbar = ttk.Scrollbar(self.frame_output, command=self.output_text.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.output_text.config(yscrollcommand=self.scrollbar.set)

    def browse_file(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if path:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, path)

    def start_scraping(self):
        query = self.query_entry.get().strip()
        if not query:
            messagebox.showerror("Error", "Search query cannot be empty.")
            return

        try:
            max_results = int(self.max_entry.get())
            if max_results <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Max results must be a positive integer.")
            return

        sort_by = self.sort_var.get()
        output_file = self.output_entry.get().strip() or None

        # Disable UI while running
        self.start_button.config(state="disabled")
        self.progress_var.set(0)
        self.append_text(f"Starting search for '{query}'...\n")

        threading.Thread(target=self.run_scraper, args=(query, max_results, sort_by, output_file), daemon=True).start()

    def run_scraper(self, query, max_results, sort_by, output_file):
        try:
            # Use the internal function to capture video URLs
            urls = []
            seen_ids = set()
            total_expected = max_results

            self.append_text("Searching YouTube...\n")

            headers = None  # not used in this approach, handled inside url_collector
            urls = url_collector.search_youtube(query, max_results, sort_by)

            # Update progress bar incrementally
            for i, url in enumerate(urls, 1):
                self.progress_var.set(i / total_expected * 100)
                self.update_idletasks()
                time.sleep(0.01)  # small delay for smooth progress

            if not urls:
                self.append_text("❌ No URLs found.\n")
                return

            # Determine output path
            if output_file:
                output_path = Path(output_file)
                if output_path.parent == Path('.'):
                    output_file = str(Path(url_collector.DEFAULT_OUTPUT_DIR) / output_path.name)
                else:
                    output_file = output_file
            else:
                output_file = url_collector.generate_output_filename(query, sort_by, max_results)

            url_collector.save_urls(urls, output_file)

            self.append_text(f"✅ Found {len(urls)} URLs.\nSaved to: {output_file}\n")
            self.append_text("Preview of first 5 URLs:\n")
            for u in urls[:5]:
                self.append_text(u + "\n")
            if len(urls) > 5:
                self.append_text(f"...and {len(urls)-5} more\n")

            self.progress_var.set(100)
        except Exception as e:
            self.append_text(f"❌ Error: {e}\n")
        finally:
            self.start_button.config(state="normal")

    def append_text(self, text):
        self.output_text.config(state="normal")
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.output_text.config(state="disabled")


if __name__ == "__main__":
    app = URLCollectorGUI()
    app.mainloop()
