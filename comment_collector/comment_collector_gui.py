#!/usr/bin/env python3
"""
YouTube Comment Collector GUI
A simple Tkinter GUI for comment_collector.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import subprocess
import sys
from pathlib import Path
import comment_collector  # Must be in the same folder

class CommentCollectorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Comment Collector")
        self.geometry("800x600")
        self.resizable(True, True)

        # Styling
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TEntry", font=("Segoe UI", 10))

        # Main frames
        self.frame_inputs = ttk.Frame(self, padding=15)
        self.frame_inputs.pack(fill="x")

        self.frame_options = ttk.Frame(self, padding=15)
        self.frame_options.pack(fill="x")

        self.frame_log = ttk.Frame(self)
        self.frame_log.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # ─── Input: URLs ───
        ttk.Label(self.frame_inputs, text="YouTube URLs (one per line):").grid(row=0, column=0, sticky="nw", pady=(0, 5))
        self.urls_text = tk.Text(self.frame_inputs, height=8, width=70, font=("Consolas", 10))
        self.urls_text.grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)

        url_buttons_frame = ttk.Frame(self.frame_inputs)
        url_buttons_frame.grid(row=1, column=3, padx=(10, 0), sticky="n")
        ttk.Button(url_buttons_frame, text="Load from File", command=self.load_urls_file).pack(pady=5)
        ttk.Button(url_buttons_frame, text="Clear", command=lambda: self.urls_text.delete(1.0, tk.END)).pack(pady=5)

        self.frame_inputs.columnconfigure(0, weight=1)

        # ─── Output Directory ───
        ttk.Label(self.frame_options, text="Output Directory:").grid(row=0, column=0, sticky="w", pady=10)
        self.output_dir_var = tk.StringVar(value="comment_sections")
        self.output_entry = ttk.Entry(self.frame_options, textvariable=self.output_dir_var, width=60)
        self.output_entry.grid(row=0, column=1, padx=(5, 10), sticky="ew")
        ttk.Button(self.frame_options, text="Browse", command=self.browse_output_dir).grid(row=0, column=2)

        # ─── Delay between requests ───
        ttk.Label(self.frame_options, text="Delay between videos (seconds):").grid(row=1, column=0, sticky="w", pady=10)
        self.delay_var = tk.DoubleVar(value=0.0)
        delay_spin = ttk.Spinbox(self.frame_options, from_=0.0, to=30.0, increment=0.5, textvariable=self.delay_var, width=10)
        delay_spin.grid(row=1, column=1, sticky="w")

        self.frame_options.columnconfigure(1, weight=1)

        # ─── Progress & Start ───
        self.progress_frame = ttk.Frame(self)
        self.progress_frame.pack(fill="x", padx=15, pady=10)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, mode="determinate")
        self.progress_bar.pack(fill="x", pady=(0, 10))

        self.status_label = ttk.Label(self.progress_frame, text="Ready", foreground="gray")
        self.status_label.pack(anchor="w")

        self.start_button = ttk.Button(self.progress_frame, text="Start Collecting Comments", command=self.start_collection)
        self.start_button.pack(pady=10)

        # ─── Log Output ───
        ttk.Label(self.frame_log, text="Log Output:").pack(anchor="w")
        self.log_text = scrolledtext.ScrolledText(self.frame_log, state="disabled", font=("Consolas", 10), bg="#f8f8f8")
        self.log_text.pack(fill="both", expand=True)

        # Detect yt-dlp
        self.ytdlp_path = comment_collector.find_ytdlp_executable()
        if not self.ytdlp_path:
            self.log("yt-dlp not found! Please install it or place it in ./bin/\n", "error")
            self.start_button.config(state="disabled")

    def log(self, message, tag="info"):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
        self.update_idletasks()

    def browse_output_dir(self):
        path = filedialog.askdirectory(title="Select Output Directory")
        if path:
            self.output_dir_var.set(path)

    def load_urls_file(self):
        path = filedialog.askopenfilename(
            title="Select URLs Text File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if path:
            try:
                urls = comment_collector.read_urls_from_file(path)
                self.urls_text.delete(1.0, tk.END)
                self.urls_text.insert(tk.END, "\n".join(urls))
                self.log(f"Loaded {len(urls)} URLs from: {Path(path).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not read file:\n{e}")

    def start_collection(self):
        urls_text = self.urls_text.get(1.0, tk.END).strip()
        if not urls_text:
            messagebox.showerror("Error", "Please enter at least one YouTube URL.")
            return

        urls = [line.strip() for line in urls_text.splitlines() if line.strip()]
        if not urls:
            messagebox.showerror("Error", "No valid URLs found.")
            return

        output_dir = Path(self.output_dir_var.get().strip())
        delay = self.delay_var.get()

        # Reset UI
        self.start_button.config(state="disabled")
        self.progress_var.set(0)
        self.status_label.config(text="Running...", foreground="blue")
        self.log(f"\nStarting collection of {len(urls)} video(s)...")
        self.log(f"Output directory: {output_dir.resolve()}")

        # Run in background thread
        threading.Thread(
            target=self.run_collection,
            args=(urls, output_dir, delay),
            daemon=True
        ).start()

    def run_collection(self, urls, output_dir, delay):
        try:
            success_count = 0
            total = len(urls)

            output_dir.mkdir(parents=True, exist_ok=True)

            for i, url in enumerate(urls, 1):
                self.log(f"\n[{i}/{total}] Processing: {url}")
                self.progress_var.set(i / total * 100)
                self.status_label.config(text=f"Processing {i}/{total}...")

                success = comment_collector.download_comments(url, output_dir, self.ytdlp_path)
                if success:
                    success_count += 1
                    self.log("Success")
                else:
                    self.log("Failed")

                if delay > 0 and i < total:
                    time.sleep(delay)

            self.log(f"\nFinished! Successfully collected comments from {success_count}/{total} videos.")
            self.log(f"Files saved in: {output_dir.resolve()}")
            self.status_label.config(text="Completed", foreground="green")

        except Exception as e:
            self.log(f"\nUnexpected error: {e}", "error")
            self.status_label.config(text="Error occurred", foreground="red")
        finally:
            self.start_button.config(state="normal")
            self.progress_var.set(100 if success_count == len(urls) else (success_count / len(urls) * 100))

if __name__ == "__main__":
    # Optional: Check if yt-dlp is available early
    if not comment_collector.find_ytdlp_executable():
        print("yt-dlp not found. The GUI will show a warning.")
        print("Download from: https://github.com/yt-dlp/yt-dlp/releases")
        print("Or place yt-dlp.exe / yt-dlp in a 'bin' folder next to this script.")

    app = CommentCollectorGUI()
    app.mainloop()