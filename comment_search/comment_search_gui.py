#!/usr/bin/env python3
"""
GUI for YouTube Comment Search Tool
Calls comment_search.py as a subprocess
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
from pathlib import Path
import subprocess
import threading
import json
import os

class CommentSearchGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Comment Search")
        self.root.geometry("1100x750")
        
        # Variables
        self.comments_dir = tk.StringVar()
        self.keywords = tk.StringVar()
        self.username = tk.StringVar()
        self.search_mode = tk.StringVar(value="any")
        self.case_sensitive = tk.BooleanVar(value=False)
        self.min_likes = tk.IntVar(value=0)
        self.max_results = tk.IntVar(value=0)
        self.sort_by = tk.StringVar(value="relevance")
        self.auto_save = tk.BooleanVar(value=True)
        self.export_json = tk.BooleanVar(value=True)
        self.export_docx = tk.BooleanVar(value=False)
        self.highlight_docx = tk.BooleanVar(value=True)
        self.most_active_n = tk.IntVar(value=10)
        self.show_stats = tk.BooleanVar(value=False)
        
        self.running = False
        
        self.setup_ui()
        
    def setup_ui(self):
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tab 1: Search Comments
        search_frame = ttk.Frame(notebook)
        notebook.add(search_frame, text="🔍 Search Comments")
        self.setup_search_tab(search_frame)
        
        # Tab 2: User Analysis
        user_frame = ttk.Frame(notebook)
        notebook.add(user_frame, text="👤 User Analysis")
        self.setup_user_tab(user_frame)
        
        # Tab 3: Most Active Users
        active_frame = ttk.Frame(notebook)
        notebook.add(active_frame, text="📊 Most Active Users")
        self.setup_active_tab(active_frame)
        
    def setup_search_tab(self, parent):
        # Main container
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left panel - Settings
        left_frame = ttk.LabelFrame(main_frame, text="Search Settings", padding=10)
        left_frame.pack(side='left', fill='both', expand=False, padx=(0, 5))
        
        # Directory selection
        ttk.Label(left_frame, text="Comments Directory:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        dir_frame = ttk.Frame(left_frame)
        dir_frame.pack(fill='x', pady=(0, 10))
        ttk.Entry(dir_frame, textvariable=self.comments_dir, width=30).pack(side='left', fill='x', expand=True)
        ttk.Button(dir_frame, text="Browse", command=self.browse_directory, width=10).pack(side='left', padx=(5, 0))
        
        # Keywords
        ttk.Label(left_frame, text="Keywords (space-separated):", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        ttk.Entry(left_frame, textvariable=self.keywords, width=40).pack(fill='x', pady=(0, 10))
        
        # Search mode
        ttk.Label(left_frame, text="Search Mode:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        mode_frame = ttk.Frame(left_frame)
        mode_frame.pack(fill='x', pady=(0, 10))
        ttk.Radiobutton(mode_frame, text="Any keyword", variable=self.search_mode, value="any").pack(anchor='w')
        ttk.Radiobutton(mode_frame, text="All keywords", variable=self.search_mode, value="all").pack(anchor='w')
        ttk.Radiobutton(mode_frame, text="Exact phrase", variable=self.search_mode, value="phrase").pack(anchor='w')
        ttk.Radiobutton(mode_frame, text="Regex pattern", variable=self.search_mode, value="regex").pack(anchor='w')
        
        # Options
        ttk.Label(left_frame, text="Options:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        ttk.Checkbutton(left_frame, text="Case sensitive", variable=self.case_sensitive).pack(anchor='w')
        ttk.Checkbutton(left_frame, text="Show author statistics", variable=self.show_stats).pack(anchor='w')
        
        # Filters
        ttk.Label(left_frame, text="Filters:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        
        filter_frame1 = ttk.Frame(left_frame)
        filter_frame1.pack(fill='x', pady=(0, 5))
        ttk.Label(filter_frame1, text="Min likes:").pack(side='left')
        ttk.Spinbox(filter_frame1, from_=0, to=10000, textvariable=self.min_likes, width=10).pack(side='left', padx=(5, 0))
        
        filter_frame2 = ttk.Frame(left_frame)
        filter_frame2.pack(fill='x', pady=(0, 5))
        ttk.Label(filter_frame2, text="Max results:").pack(side='left')
        ttk.Spinbox(filter_frame2, from_=0, to=10000, textvariable=self.max_results, width=10).pack(side='left', padx=(5, 0))
        ttk.Label(filter_frame2, text="(0 = all)", font=('Arial', 8)).pack(side='left', padx=(5, 0))
        
        filter_frame3 = ttk.Frame(left_frame)
        filter_frame3.pack(fill='x', pady=(0, 10))
        ttk.Label(filter_frame3, text="Sort by:").pack(side='left')
        ttk.Combobox(filter_frame3, textvariable=self.sort_by, values=["relevance", "likes", "date"], width=12, state='readonly').pack(side='left', padx=(5, 0))
        
        # Export settings
        ttk.Label(left_frame, text="Export Settings:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        ttk.Checkbutton(left_frame, text="Auto-save results", variable=self.auto_save).pack(anchor='w')
        ttk.Checkbutton(left_frame, text="Export to JSON", variable=self.export_json).pack(anchor='w')
        ttk.Checkbutton(left_frame, text="Export to DOCX", variable=self.export_docx).pack(anchor='w')
        ttk.Checkbutton(left_frame, text="Highlight in DOCX", variable=self.highlight_docx).pack(anchor='w', padx=(20, 0))
        
        # Search button
        ttk.Button(left_frame, text="🔍 Search", command=self.run_search, style='Accent.TButton').pack(fill='x', pady=(20, 0))
        
        # Right panel - Output
        right_frame = ttk.LabelFrame(main_frame, text="Output", padding=10)
        right_frame.pack(side='left', fill='both', expand=True, padx=(5, 0))
        
        # Output text area
        self.search_output = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, font=('Consolas', 9))
        self.search_output.pack(fill='both', expand=True)
        
        # Configure text tags for highlighting
        self.search_output.tag_configure("keyword", foreground="red", font=('Consolas', 9, 'bold'))
        self.search_output.tag_configure("success", foreground="green", font=('Consolas', 9, 'bold'))
        self.search_output.tag_configure("error", foreground="red", font=('Consolas', 9, 'bold'))
        self.search_output.tag_configure("header", foreground="blue", font=('Consolas', 9, 'bold'))
        
        # Progress bar
        self.search_progress = ttk.Progressbar(right_frame, mode='indeterminate')
        self.search_progress.pack(fill='x', pady=(5, 0))
        
    def setup_user_tab(self, parent):
        # Main container
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left panel - Settings
        left_frame = ttk.LabelFrame(main_frame, text="User Extraction Settings", padding=10)
        left_frame.pack(side='left', fill='both', expand=False, padx=(0, 5))
        
        # Directory selection
        ttk.Label(left_frame, text="Comments Directory:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        dir_frame = ttk.Frame(left_frame)
        dir_frame.pack(fill='x', pady=(0, 10))
        ttk.Entry(dir_frame, textvariable=self.comments_dir, width=30).pack(side='left', fill='x', expand=True)
        ttk.Button(dir_frame, text="Browse", command=self.browse_directory, width=10).pack(side='left', padx=(5, 0))
        
        # Username
        ttk.Label(left_frame, text="Username (exact match):", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        ttk.Entry(left_frame, textvariable=self.username, width=40).pack(fill='x', pady=(0, 10))
        
        # Optional keyword filter
        ttk.Label(left_frame, text="Filter by Keywords (optional):", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        ttk.Entry(left_frame, textvariable=self.keywords, width=40).pack(fill='x', pady=(0, 10))
        
        # Search mode
        ttk.Label(left_frame, text="Search Mode:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        mode_frame = ttk.Frame(left_frame)
        mode_frame.pack(fill='x', pady=(0, 10))
        ttk.Radiobutton(mode_frame, text="Any keyword", variable=self.search_mode, value="any").pack(anchor='w')
        ttk.Radiobutton(mode_frame, text="All keywords", variable=self.search_mode, value="all").pack(anchor='w')
        ttk.Radiobutton(mode_frame, text="Exact phrase", variable=self.search_mode, value="phrase").pack(anchor='w')
        
        # Options
        ttk.Label(left_frame, text="Options:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        ttk.Checkbutton(left_frame, text="Case sensitive", variable=self.case_sensitive).pack(anchor='w')
        
        # Filters
        filter_frame1 = ttk.Frame(left_frame)
        filter_frame1.pack(fill='x', pady=(5, 5))
        ttk.Label(filter_frame1, text="Min likes:").pack(side='left')
        ttk.Spinbox(filter_frame1, from_=0, to=10000, textvariable=self.min_likes, width=10).pack(side='left', padx=(5, 0))
        
        filter_frame2 = ttk.Frame(left_frame)
        filter_frame2.pack(fill='x', pady=(0, 10))
        ttk.Label(filter_frame2, text="Max results:").pack(side='left')
        ttk.Spinbox(filter_frame2, from_=0, to=10000, textvariable=self.max_results, width=10).pack(side='left', padx=(5, 0))
        
        # Export settings
        ttk.Label(left_frame, text="Export Settings:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        ttk.Checkbutton(left_frame, text="Auto-save results", variable=self.auto_save).pack(anchor='w')
        ttk.Checkbutton(left_frame, text="Export to JSON", variable=self.export_json).pack(anchor='w')
        ttk.Checkbutton(left_frame, text="Export to DOCX", variable=self.export_docx).pack(anchor='w')
        ttk.Checkbutton(left_frame, text="Highlight in DOCX", variable=self.highlight_docx).pack(anchor='w', padx=(20, 0))
        
        # Extract button
        ttk.Button(left_frame, text="👤 Extract User Comments", command=self.run_user_extraction, style='Accent.TButton').pack(fill='x', pady=(20, 0))
        
        # Right panel - Output
        right_frame = ttk.LabelFrame(main_frame, text="Output", padding=10)
        right_frame.pack(side='left', fill='both', expand=True, padx=(5, 0))
        
        # Output text area
        self.user_output = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, font=('Consolas', 9))
        self.user_output.pack(fill='both', expand=True)
        
        # Configure text tags for highlighting
        self.user_output.tag_configure("keyword", foreground="red", font=('Consolas', 9, 'bold'))
        self.user_output.tag_configure("success", foreground="green", font=('Consolas', 9, 'bold'))
        self.user_output.tag_configure("error", foreground="red", font=('Consolas', 9, 'bold'))
        self.user_output.tag_configure("header", foreground="blue", font=('Consolas', 9, 'bold'))
        
        # Progress bar
        self.user_progress = ttk.Progressbar(right_frame, mode='indeterminate')
        self.user_progress.pack(fill='x', pady=(5, 0))
        
    def setup_active_tab(self, parent):
        # Main container
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left panel - Settings
        left_frame = ttk.LabelFrame(main_frame, text="Most Active Users Settings", padding=10)
        left_frame.pack(side='left', fill='both', expand=False, padx=(0, 5))
        
        # Directory selection
        ttk.Label(left_frame, text="Comments Directory:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        dir_frame = ttk.Frame(left_frame)
        dir_frame.pack(fill='x', pady=(0, 10))
        ttk.Entry(dir_frame, textvariable=self.comments_dir, width=30).pack(side='left', fill='x', expand=True)
        ttk.Button(dir_frame, text="Browse", command=self.browse_directory, width=10).pack(side='left', padx=(5, 0))
        
        # Number of users
        ttk.Label(left_frame, text="Number of Top Users:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        ttk.Spinbox(left_frame, from_=1, to=100, textvariable=self.most_active_n, width=20).pack(anchor='w', pady=(0, 10))
        
        # Optional keyword filter
        ttk.Label(left_frame, text="Search in Their Comments (optional):", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        ttk.Entry(left_frame, textvariable=self.keywords, width=40).pack(fill='x', pady=(0, 5))
        ttk.Label(left_frame, text="Leave empty to just export user stats", font=('Arial', 8, 'italic')).pack(anchor='w', pady=(0, 10))
        
        # Search mode
        ttk.Label(left_frame, text="Search Mode:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        mode_frame = ttk.Frame(left_frame)
        mode_frame.pack(fill='x', pady=(0, 10))
        ttk.Radiobutton(mode_frame, text="Any keyword", variable=self.search_mode, value="any").pack(anchor='w')
        ttk.Radiobutton(mode_frame, text="All keywords", variable=self.search_mode, value="all").pack(anchor='w')
        
        # Options
        ttk.Label(left_frame, text="Options:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        ttk.Checkbutton(left_frame, text="Case sensitive", variable=self.case_sensitive).pack(anchor='w')
        
        filter_frame1 = ttk.Frame(left_frame)
        filter_frame1.pack(fill='x', pady=(5, 10))
        ttk.Label(filter_frame1, text="Min likes:").pack(side='left')
        ttk.Spinbox(filter_frame1, from_=0, to=10000, textvariable=self.min_likes, width=10).pack(side='left', padx=(5, 0))
        
        # Export settings
        ttk.Label(left_frame, text="Export Settings:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        ttk.Checkbutton(left_frame, text="Auto-save results", variable=self.auto_save).pack(anchor='w')
        ttk.Checkbutton(left_frame, text="Export to JSON", variable=self.export_json).pack(anchor='w')
        ttk.Checkbutton(left_frame, text="Export to DOCX", variable=self.export_docx).pack(anchor='w')
        ttk.Checkbutton(left_frame, text="Highlight in DOCX", variable=self.highlight_docx).pack(anchor='w', padx=(20, 0))
        
        # Analyze button
        ttk.Button(left_frame, text="📊 Analyze Most Active", command=self.run_most_active, style='Accent.TButton').pack(fill='x', pady=(20, 0))
        
        # Right panel - Output
        right_frame = ttk.LabelFrame(main_frame, text="Output", padding=10)
        right_frame.pack(side='left', fill='both', expand=True, padx=(5, 0))
        
        # Output text area
        self.active_output = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, font=('Consolas', 9))
        self.active_output.pack(fill='both', expand=True)
        
        # Configure text tags for highlighting
        self.active_output.tag_configure("keyword", foreground="red", font=('Consolas', 9, 'bold'))
        self.active_output.tag_configure("success", foreground="green", font=('Consolas', 9, 'bold'))
        self.active_output.tag_configure("error", foreground="red", font=('Consolas', 9, 'bold'))
        self.active_output.tag_configure("header", foreground="blue", font=('Consolas', 9, 'bold'))
        
        # Progress bar
        self.active_progress = ttk.Progressbar(right_frame, mode='indeterminate')
        self.active_progress.pack(fill='x', pady=(5, 0))
        
    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.comments_dir.set(directory)
    
    def build_command(self, mode):
        """Build the command line arguments for comment_search.py"""
        cmd = ["python", "comment_search.py"]
        
        # Directory (required)
        if not self.comments_dir.get():
            messagebox.showerror("Error", "Please select a comments directory")
            return None
        cmd.extend(["-d", self.comments_dir.get()])
        
        # Mode-specific arguments
        if mode == "search":
            # Keywords (required for search)
            keywords = self.keywords.get().strip()
            if not keywords:
                messagebox.showerror("Error", "Please enter keywords to search")
                return None
            cmd.extend(keywords.split())
            
        elif mode == "user":
            # Username (required)
            if not self.username.get():
                messagebox.showerror("Error", "Please enter a username")
                return None
            cmd.extend(["--user", self.username.get()])
            
            # Optional keywords
            keywords = self.keywords.get().strip()
            if keywords:
                cmd.extend(keywords.split())
                
        elif mode == "active":
            # Most active
            cmd.extend(["--most-active", str(self.most_active_n.get())])
            
            # Optional keywords
            keywords = self.keywords.get().strip()
            if keywords:
                cmd.extend(keywords.split())
        
        # Common arguments
        cmd.extend(["-m", self.search_mode.get()])
        
        if self.case_sensitive.get():
            cmd.append("--case-sensitive")
        
        if self.min_likes.get() > 0:
            cmd.extend(["--min-likes", str(self.min_likes.get())])
        
        if mode != "active" and self.max_results.get() > 0:
            cmd.extend(["-n", str(self.max_results.get())])
        
        if mode == "search":
            cmd.extend(["-s", self.sort_by.get()])
            
            if self.show_stats.get():
                cmd.append("--stats")
        
        if not self.auto_save.get():
            cmd.append("--no-save")
        
        # Export formats
        export_formats = []
        if self.export_json.get():
            export_formats.append("json")
        if self.export_docx.get():
            export_formats.append("docx")
        
        if export_formats:
            cmd.extend(["--export"] + export_formats)
        
        if not self.highlight_docx.get():
            cmd.append("--no-docx-highlight")
        
        return cmd
    
    def run_command(self, cmd, output_widget, progress_bar):
        """Run the command in a separate thread"""
        def execute():
            try:
                self.running = True
                output_widget.delete(1.0, tk.END)
                output_widget.insert(tk.END, f"Running: {' '.join(cmd)}\n\n")
                output_widget.see(tk.END)
                
                progress_bar.start()
                
                # Get keywords for highlighting
                keywords = self.keywords.get().strip().split() if self.keywords.get().strip() else []
                
                # Run the command
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",      # ← ADD THIS
                    errors="replace",      # ← SAFETY NET
                    bufsize=1
                )
                
                # Read output line by line
                for line in process.stdout:
                    # Insert line and apply highlighting
                    start_pos = output_widget.index(tk.END)
                    output_widget.insert(tk.END, line)
                    
                    # Highlight special patterns
                    if line.startswith("✓"):
                        line_start = f"{start_pos.split('.')[0]}.0"
                        line_end = f"{start_pos.split('.')[0]}.end"
                        output_widget.tag_add("success", line_start, line_end)
                    elif line.startswith("✗") or "Error" in line:
                        line_start = f"{start_pos.split('.')[0]}.0"
                        line_end = f"{start_pos.split('.')[0]}.end"
                        output_widget.tag_add("error", line_start, line_end)
                    elif line.startswith("===") or line.startswith("Top ") or line.startswith("User:"):
                        line_start = f"{start_pos.split('.')[0]}.0"
                        line_end = f"{start_pos.split('.')[0]}.end"
                        output_widget.tag_add("header", line_start, line_end)
                    
                    # Highlight keywords in the line (case-insensitive)
                    if keywords:
                        line_lower = line.lower()
                        for keyword in keywords:
                            keyword_lower = keyword.lower()
                            start = 0
                            while True:
                                pos = line_lower.find(keyword_lower, start)
                                if pos == -1:
                                    break
                                
                                # Calculate actual position in text widget
                                line_num = start_pos.split('.')[0]
                                kw_start = f"{line_num}.{pos}"
                                kw_end = f"{line_num}.{pos + len(keyword)}"
                                output_widget.tag_add("keyword", kw_start, kw_end)
                                
                                start = pos + 1
                    
                    output_widget.see(tk.END)
                    self.root.update_idletasks()
                
                process.wait()
                
                if process.returncode == 0:
                    end_pos = output_widget.index(tk.END)
                    output_widget.insert(tk.END, "\n✅ Command completed successfully!\n")
                    line_num = end_pos.split('.')[0]
                    output_widget.tag_add("success", f"{int(line_num)+1}.0", f"{int(line_num)+1}.end")
                else:
                    end_pos = output_widget.index(tk.END)
                    output_widget.insert(tk.END, f"\n❌ Command failed with return code {process.returncode}\n")
                    line_num = end_pos.split('.')[0]
                    output_widget.tag_add("error", f"{int(line_num)+1}.0", f"{int(line_num)+1}.end")
                
                output_widget.see(tk.END)
                progress_bar.stop()
                self.running = False
                
            except Exception as e:
                output_widget.insert(tk.END, f"\n❌ Error: {str(e)}\n")
                progress_bar.stop()
                self.running = False
        
        thread = threading.Thread(target=execute, daemon=True)
        thread.start()
    
    def run_search(self):
        if self.running:
            messagebox.showwarning("Warning", "A command is already running!")
            return
        
        cmd = self.build_command("search")
        if cmd:
            self.run_command(cmd, self.search_output, self.search_progress)
    
    def run_user_extraction(self):
        if self.running:
            messagebox.showwarning("Warning", "A command is already running!")
            return
        
        cmd = self.build_command("user")
        if cmd:
            self.run_command(cmd, self.user_output, self.user_progress)
    
    def run_most_active(self):
        if self.running:
            messagebox.showwarning("Warning", "A command is already running!")
            return
        
        cmd = self.build_command("active")
        if cmd:
            self.run_command(cmd, self.active_output, self.active_progress)

def main():
    root = tk.Tk()
    
    # Set theme
    style = ttk.Style()
    try:
        style.theme_use('clam')
    except:
        pass
    
    # Configure accent button style
    style.configure('Accent.TButton', font=('Arial', 10, 'bold'))
    
    app = CommentSearchGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()