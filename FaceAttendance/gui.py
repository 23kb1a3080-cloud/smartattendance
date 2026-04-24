"""
GUI Module for Face Attendance System
Provides a user-friendly interface for all operations.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import os
import sys
import subprocess
from datetime import datetime

# Configuration
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 500


class FaceAttendanceGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Attendance System")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(False, False)
        
        # Center window
        self.center_window()
        
        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Create UI
        self.create_widgets()
        
        # Status variables
        self.is_running = False
    
    def center_window(self):
        """Center window on screen."""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        x = (screen_width - WINDOW_WIDTH) // 2
        y = (screen_height - WINDOW_HEIGHT) // 2
        
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")
    
    def create_widgets(self):
        """Create all UI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="Face Attendance System",
            font=("Arial", 20, "bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Roll Number Input
        input_frame = ttk.LabelFrame(main_frame, text="Student Information", padding="15")
        input_frame.grid(row=1, column=0, pady=(0, 20), sticky=(tk.W, tk.E))
        
        ttk.Label(input_frame, text="Roll Number:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.roll_var = tk.StringVar()
        self.roll_entry = ttk.Entry(input_frame, textvariable=self.roll_var, width=30)
        self.roll_entry.grid(row=0, column=1, pady=5, padx=5)
        
        # Buttons
        button_frame = ttk.LabelFrame(main_frame, text="Actions", padding="15")
        button_frame.grid(row=2, column=0, pady=(0, 20), sticky=(tk.W, tk.E))
        
        # Registration button
        self.reg_button = ttk.Button(
            button_frame,
            text="📝 Register Student",
            command=self.run_registration,
            width=25
        )
        self.reg_button.grid(row=0, column=0, pady=5, padx=5)
        
        # Training button
        self.train_button = ttk.Button(
            button_frame,
            text="🧠 Train Model",
            command=self.run_training,
            width=25
        )
        self.train_button.grid(row=1, column=0, pady=5, padx=5)
        
        # Attendance button
        self.attendance_button = ttk.Button(
            button_frame,
            text="✅ Mark Attendance",
            command=self.run_attendance,
            width=25
        )
        self.attendance_button.grid(row=2, column=0, pady=5, padx=5)
        
        # Database button
        self.db_button = ttk.Button(
            button_frame,
            text="📊 View Attendance",
            command=self.view_attendance,
            width=25
        )
        self.db_button.grid(row=3, column=0, pady=5, padx=5)
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="System Status", padding="10")
        status_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        
        self.status_label = ttk.Label(
            status_frame,
            text="System Ready",
            foreground="green",
            font=("Arial", 10)
        )
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(
            main_frame,
            height=8,
            width=70,
            state='disabled',
            font=("Courier", 9)
        )
        self.log_text.grid(row=4, column=0, pady=(10, 0), sticky=(tk.W, tk.E))
        
        # Progress bar
        self.progress = ttk.Progressbar(
            main_frame,
            mode='indeterminate',
            length=560
        )
        self.progress.grid(row=5, column=0, pady=(10, 0))
    
    def log_message(self, message):
        """Add message to log text area."""
        self.log_text.config(state='normal')
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
    
    def update_status(self, message, color="green"):
        """Update status label."""
        self.status_label.config(text=message, foreground=color)
        self.root.update()
    
    def run_in_thread(self, target_func, *args):
        """Run function in background thread."""
        self.progress.start()
        self.root.config(cursor="wait")
        
        def target():
            try:
                result = target_func(*args)
                self.root.after(0, lambda: self.on_task_complete(result))
            except Exception as e:
                self.root.after(0, lambda: self.on_task_error(str(e)))
        
        thread = threading.Thread(target=target, daemon=True)
        thread.start()
    
    def on_task_complete(self, result):
        """Handle task completion."""
        self.progress.stop()
        self.root.config(cursor="")
        if result:
            self.log_message("✓ Task completed successfully")
    
    def on_task_error(self, error):
        """Handle task error."""
        self.progress.stop()
        self.root.config(cursor="")
        self.log_message(f"✗ Error: {error}")
        messagebox.showerror("Error", error)
    
    def run_registration(self):
        """Run registration module."""
        roll_number = self.roll_var.get().strip()
        
        if not roll_number:
            messagebox.showwarning("Input Error", "Please enter a roll number")
            return
        
        self.log_message(f"Starting registration for {roll_number}...")
        self.update_status("Registration in progress...", "orange")
        
        # Import and run registration
        import registration
        
        # Override print to log
        original_print = print
        
        def custom_print(*args, **kwargs):
            message = ' '.join(map(str, args))
            self.log_message(message)
        
        # Temporarily replace print
        import sys
        sys.stdout.write = lambda x: self.log_message(x.strip())
        
        try:
            success = registration.capture_faces(roll_number)
            self.on_task_complete(success)
        except Exception as e:
            self.on_task_error(str(e))
        finally:
            # Restore print
            sys.stdout.write = sys.__stdout__.write
    
    def run_training(self):
        """Run training module."""
        self.log_message("Starting model training...")
        self.update_status("Training in progress...", "orange")
        
        import train_model
        
        try:
            success = train_model.train_encodings()
            self.on_task_complete(success)
        except Exception as e:
            self.on_task_error(str(e))
    
    def run_attendance(self):
        """Run attendance module."""
        roll_number = self.roll_var.get().strip()
        
        if not roll_number:
            messagebox.showwarning("Input Error", "Please enter a roll number")
            return
        
        self.log_message(f"Starting attendance for {roll_number}...")
        self.update_status("Attendance verification in progress...", "orange")
        
        import attendance
        
        try:
            attendance.recognize_face(roll_number)
            self.on_task_complete(True)
        except Exception as e:
            self.on_task_error(str(e))
    
    def view_attendance(self):
        """View attendance records."""
        self.log_message("Opening attendance records...")
        
        import sqlite3
        from datetime import datetime
        
        conn = sqlite3.connect("attendance_db/attendance.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT roll_no, name, date, time, status, confidence 
            FROM attendance 
            ORDER BY date DESC, time DESC
        ''')
        
        records = cursor.fetchall()
        conn.close()
        
        # Create popup window
        popup = tk.Toplevel(self.root)
        popup.title("Attendance Records")
        popup.geometry("800x500")
        
        # Treeview
        columns = ('Roll No', 'Name', 'Date', 'Time', 'Status', 'Confidence')
        tree = ttk.Treeview(popup, columns=columns, show='headings')
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(popup, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add records
        for record in records:
            confidence_str = f"{record[5]:.2%}" if record[5] else "N/A"
            tree.insert('', tk.END, values=record[:5] + (confidence_str,))
        
        # Stats
        if records:
            total = len(records)
            present = len([r for r in records if r[4] == 'Present'])
            stats = f"Total: {total} | Present: {present}"
            ttk.Label(popup, text=stats).pack(pady=5)


def main():
    """Main GUI function."""
    root = tk.Tk()
    app = FaceAttendanceGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
