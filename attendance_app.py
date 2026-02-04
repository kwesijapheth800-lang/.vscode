import tkinter as tk
from tkinter import messagebox, ttk
import csv
import os
import re
import sqlite3
from datetime import datetime


class AttendanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("KAAF University - Attendance Manager")
        self.root.geometry("800x850")

        # --- DATABASE SETUP ---
        self.conn = sqlite3.connect("kaaf_data.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                index_number TEXT PRIMARY KEY,
                name TEXT
            )
        """)
        self.conn.commit()

        self.attendance_vars = {}

        # --- VALIDATION SETUP ---
        # Register the validation function so Tkinter can use it
        self.vcmd = (self.root.register(self.validate_number), '%P')

        # --- UI BUILDER ---
        self.setup_ui()

    def validate_number(self, new_value):
        # This function runs every time you type a key in the Duration box.
        # It returns True (allow) if the text is empty or a number.
        return new_value.isdigit() or new_value == ""

    def setup_ui(self):
        # 1. HEADER
        header_frame = tk.Frame(self.root, bg="#003366", height=60)
        header_frame.pack(fill="x")
        tk.Label(header_frame, text="KAAF ATTENDANCE SYSTEM",
                 font=("Helvetica", 16, "bold"), bg="#003366", fg="white").pack(pady=15)

        # 2. COURSE CONFIG SECTION
        self.frame_config = ttk.LabelFrame(
            self.root, text=" Step 1: Course Details ", padding="15")
        self.frame_config.pack(fill="x", padx=20, pady=10)

        # -- Inputs --
        ttk.Label(self.frame_config, text="Course Name:").grid(
            row=0, column=0, sticky="w")
        self.ent_cname = ttk.Entry(self.frame_config, width=25)
        self.ent_cname.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.frame_config, text="Course Code:").grid(
            row=0, column=2, sticky="w")
        self.ent_ccode = ttk.Entry(self.frame_config, width=15)
        self.ent_ccode.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(self.frame_config, text="Lecturer:").grid(
            row=1, column=0, sticky="w")
        self.ent_lecturer = ttk.Entry(self.frame_config, width=25)
        self.ent_lecturer.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(self.frame_config, text="Duration (Hrs):").grid(
            row=1, column=2, sticky="w")

        # --- THE CHANGE: Adding validation here ---
        self.ent_duration = ttk.Entry(
            self.frame_config, width=15, validate="key", validatecommand=self.vcmd)
        self.ent_duration.grid(row=1, column=3, padx=5, pady=5)

        # -- Key Bindings --
        self.ent_cname.bind("<Return>", lambda e: self.ent_ccode.focus_set())
        self.ent_ccode.bind(
            "<Return>", lambda e: self.ent_lecturer.focus_set())
        self.ent_lecturer.bind(
            "<Return>", lambda e: self.ent_duration.focus_set())
        self.ent_duration.bind("<Return>", lambda e: self.lock_and_load())

        # -- Continue Button --
        self.btn_continue = tk.Button(self.frame_config, text="CONTINUE ➤", bg="#4CAF50", fg="white",
                                      font=("Arial", 10, "bold"), command=self.lock_and_load)
        self.btn_continue.grid(
            row=0, column=4, rowspan=2, padx=20, sticky="ns")

        # 3. THE "BOLD TITLE" HEADER (Hidden initially)
        self.frame_active_header = tk.Frame(self.root, bg="#f0f0f0", pady=10)
        self.lbl_course_display = tk.Label(self.frame_active_header, text="",
                                           font=("Arial", 22, "bold"), bg="#f0f0f0", fg="#333")
        self.lbl_course_display.pack()

        # 4. CONTENT AREA
        self.container = tk.Frame(self.root)
        self.container.pack(fill="both", expand=True, padx=20, pady=5)

        self.build_marking_view()
        self.build_student_manager_view()

    # ==========================================
    # VIEW 1: MARKING
    # ==========================================
    def build_marking_view(self):
        self.frame_marking = tk.Frame(self.container)

        # Toolbar
        tool_bar = tk.Frame(self.frame_marking)
        tool_bar.pack(fill="x", pady=5)

        tk.Button(tool_bar, text="⚙ Manage Students / Add New", command=self.show_student_view,
                  bg="#FF9800", fg="white").pack(side="right")
        tk.Label(tool_bar, text="Mark Attendance Below:",
                 font=("Arial", 10, "bold")).pack(side="left")

        # Search Bar
        search_frame = tk.Frame(self.frame_marking, pady=5)
        search_frame.pack(fill="x")
        tk.Label(search_frame, text="Search Student: ").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_marking_list)
        ttk.Entry(search_frame, textvariable=self.search_var).pack(
            side="left", fill="x", expand=True)

        # List Area
        list_frame = ttk.Frame(self.frame_marking)
        list_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(list_frame)
        self.scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scroll_window = self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))

        # Save Button
        tk.Button(self.frame_marking, text="💾 SAVE ATTENDANCE SHEET", bg="#0066cc", fg="white",
                  font=("Arial", 12, "bold"), height=2, command=self.save_attendance).pack(fill="x", pady=10)

    # ==========================================
    # VIEW 2: STUDENT MANAGER
    # ==========================================
    def build_student_manager_view(self):
        self.frame_students = tk.Frame(self.container)

        tk.Button(self.frame_students, text="🔙 Back to Marking", command=self.show_marking_view,
                  bg="#607D8B", fg="white").pack(anchor="w", pady=5)

        add_frame = ttk.LabelFrame(
            self.frame_students, text=" Add New Student ", padding=10)
        add_frame.pack(fill="x", pady=5)

        ttk.Label(add_frame, text="Index:").pack(side="left")
        self.new_index = ttk.Entry(add_frame, width=15)
        self.new_index.pack(side="left", padx=5)

        ttk.Label(add_frame, text="Name:").pack(side="left")
        self.new_name = ttk.Entry(add_frame, width=25)
        self.new_name.pack(side="left", padx=5)

        # -- Key Bindings --
        self.new_index.bind("<Return>", lambda e: self.new_name.focus_set())
        self.new_name.bind("<Return>", lambda e: self.add_single_student())

        tk.Button(add_frame, text="+ Add", bg="#4CAF50", fg="white",
                  command=self.add_single_student).pack(side="left", padx=10)

        self.tree = ttk.Treeview(self.frame_students, columns=(
            "idx", "name"), show="headings", height=12)
        self.tree.heading("idx", text="Index Number")
        self.tree.heading("name", text="Student Name")
        self.tree.pack(fill="both", expand=True, pady=5)

        tk.Button(self.frame_students, text="Delete Selected",
                  command=self.delete_student).pack(pady=5)

    # ==========================================
    # LOGIC
    # ==========================================
    def lock_and_load(self):
        c_name = self.ent_cname.get().strip()
        c_code = self.ent_ccode.get().strip()

        if not c_name or not c_code:
            messagebox.showwarning(
                "Missing Info", "Please enter at least Course Name and Code.")
            return

        self.lbl_course_display.config(
            text=f"{c_name.upper()}  -  {c_code.upper()}")
        self.frame_active_header.pack(fill="x", after=self.frame_config)

        self.ent_cname.config(state="disabled")
        self.ent_ccode.config(state="disabled")
        self.ent_lecturer.config(state="disabled")
        self.ent_duration.config(state="disabled")
        self.btn_continue.config(text="LOCKED", state="disabled", bg="#999")

        self.refresh_marking_list()
        self.show_marking_view()

    def show_marking_view(self):
        self.frame_students.pack_forget()
        self.frame_marking.pack(fill="both", expand=True)

    def show_student_view(self):
        self.frame_marking.pack_forget()
        self.refresh_student_list()
        self.frame_students.pack(fill="both", expand=True)

    def add_single_student(self):
        idx, name = self.new_index.get().strip(), self.new_name.get().strip()
        if not idx or not name:
            return

        try:
            self.cursor.execute(
                "INSERT INTO students VALUES (?, ?)", (idx, name))
            self.conn.commit()
            self.new_index.delete(0, 'end')
            self.new_name.delete(0, 'end')
            self.new_index.focus_set()
            self.refresh_student_list()
            messagebox.showinfo("Saved", "Student Added!")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Index already exists!")

    def delete_student(self):
        sel = self.tree.selection()
        if sel:
            idx = self.tree.item(sel)['values'][0]
            self.cursor.execute(
                "DELETE FROM students WHERE index_number=?", (idx,))
            self.conn.commit()
            self.refresh_student_list()

    def refresh_student_list(self):
        self.cursor.execute("SELECT * FROM students")
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in self.cursor.fetchall():
            self.tree.insert("", "end", values=row)

    def refresh_marking_list(self):
        for w in self.scrollable_frame.winfo_children():
            w.destroy()
        self.attendance_vars = {}
        self.cursor.execute("SELECT * FROM students")
        for row in self.cursor.fetchall():
            self.create_student_row(row[0], row[1])

    def create_student_row(self, idx, name):
        row = ttk.Frame(self.scrollable_frame)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=f"{idx} - {name}",
                  width=35).pack(side="left", padx=5)
        var = tk.StringVar(value="None")
        self.attendance_vars[idx] = var
        ttk.Radiobutton(row, text="P", variable=var,
                        value="Present").pack(side="left", padx=10)
        ttk.Radiobutton(row, text="A", variable=var,
                        value="Absent").pack(side="left", padx=10)

    def filter_marking_list(self, *args):
        query = self.search_var.get().lower()
        for w in self.scrollable_frame.winfo_children():
            w.destroy()
        self.cursor.execute("SELECT * FROM students")
        for row in self.cursor.fetchall():
            if query in row[1].lower() or query in str(row[0]).lower():
                self.create_student_row(row[0], row[1])

    def save_attendance(self):
        c_name = self.ent_cname.get().strip()
        c_code = self.ent_ccode.get().strip()
        safe_name = re.sub(
            r'[\\/*?:"<>|]', "", f"{datetime.now().strftime('%d-%m-%Y')} - {c_name} - {c_code}")
        filename = f"{safe_name}.csv"

        try:
            with open(filename, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Index", "Name", "Status", "Time"])
                for idx, var in self.attendance_vars.items():
                    self.cursor.execute(
                        "SELECT name FROM students WHERE index_number=?", (idx,))
                    n_res = self.cursor.fetchone()
                    name = n_res[0] if n_res else "Unknown"
                    status = "Unmarked" if var.get() == "None" else var.get()
                    writer.writerow(
                        [idx, name, status, datetime.now().strftime("%H:%M")])
            messagebox.showinfo("Success", f"Saved as: {filename}")
        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = AttendanceApp(root)
    root.mainloop()
