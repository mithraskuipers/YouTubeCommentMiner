#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path

# Import the modules
from url_getter_api import search_youtube_api
from url_getter_selenium import search_youtube_selenium, SELENIUM_AVAILABLE


def generate_output_filename(query, sort_by, max_results, output_dir="url_lists"):
    """Generate a descriptive filename"""
    import re
    from datetime import datetime
    
    safe_query = "".join(c if c.isalnum() or c in " _-" else "_" for c in query)
    safe_query = re.sub(r'_+', '_', safe_query)
    safe_query = safe_query.strip('_').lower()
    safe_query = safe_query[:60]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"yt_urls_{safe_query}_{sort_by}_n{max_results}_{timestamp}.txt"
    return str(Path(output_dir) / filename)


def save_urls(urls, output_file):
    """Save URLs to a text file"""
    try:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            for url in urls:
                f.write(f"{url}\n")
        return True
    except Exception as e:
        print(f"Error saving URLs: {e}")
        return False


class URLCollectorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube URL Getter")
        self.geometry("700x500")
        self.resizable(False, False)

        # ─── Styling ───
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TEntry", font=("Segoe UI", 10))
        style.configure("TCombobox", font=("Segoe UI", 10))
        style.configure("TCheckbutton", font=("Segoe UI", 10))

        # ─── Frames ───
        self.frame_inputs = ttk.Frame(self)
        self.frame_inputs.pack(padx=15, pady=10, fill="x")

        self.frame_options = ttk.Frame(self)
        self.frame_options.pack(padx=15, pady=5, fill="x")

        self.frame_progress = ttk.Frame(self)
        self.frame_progress.pack(padx=15, pady=10, fill="x")

        self.frame_output = ttk.Frame(self)
        self.frame_output.pack(padx=15, pady=10, fill="both", expand=True)

        # ─── Input Widgets ───
        ttk.Label(self.frame_inputs, text="Search Query:").grid(row=0, column=0, sticky="w", pady=5)
        self.query_entry = ttk.Entry(self.frame_inputs, width=60)
        self.query_entry.grid(row=0, column=1, columnspan=3, pady=5, sticky="ew")

        ttk.Label(self.frame_inputs, text="Sort By:").grid(row=1, column=0, sticky="w", pady=5)
        self.sort_var = tk.StringVar(value="relevance")
        self.sort_menu = ttk.Combobox(self.frame_inputs, textvariable=self.sort_var,
                                      values=["relevance", "date", "views", "rating"],
                                      state="readonly", width=15)
        self.sort_menu.grid(row=1, column=1, sticky="w", padx=(0, 20))

        ttk.Label(self.frame_inputs, text="Max Results:").grid(row=1, column=2, sticky="e", pady=5)
        self.max_entry = ttk.Entry(self.frame_inputs, width=10)
        self.max_entry.insert(0, "50")
        self.max_entry.grid(row=1, column=3, sticky="w")

        # ─── Options ───
        self.use_selenium_var = tk.BooleanVar(value=False)
        self.selenium_check = ttk.Checkbutton(self.frame_options, text="Use Selenium (slower, may need login)",
                                              variable=self.use_selenium_var)
        self.selenium_check.pack(side="left")

        self.login_var = tk.BooleanVar(value=False)
        self.login_check = ttk.Checkbutton(self.frame_options, text="Login (requires visible browser)",
                                           variable=self.login_var, state="disabled")
        self.login_check.pack(side="left", padx=20)

        # Enable/disable login checkbox based on selenium
        self.use_selenium_var.trace_add("write", self.toggle_login_option)

        # ─── Output File ───
        ttk.Label(self.frame_inputs, text="Output File (optional):").grid(row=2, column=0, sticky="w", pady=8)
        self.output_entry = ttk.Entry(self.frame_inputs, width=50)
        self.output_entry.grid(row=2, column=1, columnspan=2, sticky="ew", pady=8)
        self.browse_button = ttk.Button(self.frame_inputs, text="Browse", command=self.browse_file)
        self.browse_button.grid(row=2, column=3, sticky="w", padx=(10, 0))

        self.frame_inputs.columnconfigure(1, weight=1)

        # ─── Progress ───
        ttk.Label(self.frame_progress, text="Status:").pack(anchor="w")
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.frame_progress, orient="horizontal",
                                            length=650, mode="determinate",
                                            variable=self.progress_var)
        self.progress_bar.pack(pady=5, fill="x")

        self.status_label = ttk.Label(self.frame_progress, text="Ready", foreground="gray")
        self.status_label.pack(anchor="w")

        # ─── Start Button ───
        self.start_button = ttk.Button(self.frame_progress, text="Start Collecting URLs",
                                       command=self.start_scraping)
        self.start_button.pack(pady=10)

        # ─── Output Text ───
        self.output_text = tk.Text(self.frame_output, wrap="word", state="disabled",
                                   font=("Consolas", 10))
        self.output_text.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(self.frame_output, command=self.output_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.output_text.config(yscrollcommand=scrollbar.set)

    def toggle_login_option(self, *args):
        if self.use_selenium_var.get():
            self.login_check.config(state="normal")
        else:
            self.login_check.config(state="disabled")
            self.login_var.set(False)

    def browse_file(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            title="Save URLs to..."
        )
        if path:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, path)

    def start_scraping(self):
        query = self.query_entry.get().strip()
        if not query:
            messagebox.showerror("Error", "Please enter a search query.")
            return

        try:
            max_results = int(self.max_entry.get().strip())
            if max_results <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Max results must be a positive integer.")
            return

        sort_by = self.sort_var.get()
        output_file = self.output_entry.get().strip() or None
        use_selenium = self.use_selenium_var.get()
        login = self.login_var.get()

        if use_selenium and login:
            messagebox.showinfo("Note", "Login mode will open a browser window. Please log in manually.")

        # Reset UI
        self.start_button.config(state="disabled")
        self.progress_var.set(0)
        self.status_label.config(text="Running...", foreground="blue")
        self.clear_output()
        self.append_text(f"Starting collection for: '{query}'\n")
        self.append_text(f"Target: {max_results} URLs | Sort: {sort_by}\n")
        self.append_text(f"Method: {'Selenium' if use_selenium else 'YouTube Internal API (fast)'}\n\n")

        # Run in thread
        threading.Thread(
            target=self.run_scraper,
            args=(query, max_results, sort_by, output_file, use_selenium, login),
            daemon=True
        ).start()

    def run_scraper(self, query, max_results, sort_by, output_file, use_selenium, login):
        try:
            if use_selenium:
                if not SELENIUM_AVAILABLE:
                    self.append_text("❌ Selenium is not installed. Falling back to API method.\n")
                    use_selenium = False

            if use_selenium:
                self.append_text("Opening browser with Selenium...\n")
                urls = search_youtube_selenium(
                    query, max_results, sort_by, headless=False, login=login
                )
            else:
                self.append_text("Searching using YouTube internal API...\n")
                urls = search_youtube_api(query, max_results, sort_by)

            if not urls:
                self.append_text("❌ No video URLs were found.\n")
                return

            # Save file
            if output_file:
                final_path = output_file
            else:
                final_path = generate_output_filename(query, sort_by, max_results)

            save_urls(urls, final_path)

            self.append_text(f"✅ Successfully collected {len(urls)} URLs!\n")
            self.append_text(f"📁 Saved to: {final_path}\n\n")
            self.append_text("Preview (first 10 URLs):\n")
            for i, url in enumerate(urls[:10], 1):
                self.append_text(f"{i:2}. {url}\n")
            if len(urls) > 10:
                self.append_text(f"... and {len(urls) - 10} more.\n")

            self.progress_var.set(100)
            self.status_label.config(text="Completed successfully", foreground="green")

        except Exception as e:
            self.append_text(f"❌ Unexpected error: {str(e)}\n")
            self.status_label.config(text="Error occurred", foreground="red")
        finally:
            self.start_button.config(state="normal")

    def append_text(self, text):
        self.output_text.config(state="normal")
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.output_text.config(state="disabled")
        self.update_idletasks()

    def clear_output(self):
        self.output_text.config(state="normal")
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state="disabled")


if __name__ == "__main__":
    app = URLCollectorGUI()
    app.mainloop()