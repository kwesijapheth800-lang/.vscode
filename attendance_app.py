import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import csv
import os
import re  # For "Regular Expressions" to check text patterns
from datetime import datetime


class AttendanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("KAAF University - Attendance Manager")
        self.root.geometry("700x800")

        # --- DATA STORAGE ---
        self.students = {}  # {index: name}
        self.attendance_vars = {}  # {index: StringVar}

        # --- TOP HEADER BAR ---
        top_bar = ttk.Frame(root)
        top_bar.pack(fill="x", padx=10, pady=5)

        ttk.Label(top_bar, text="KAAF Attendance System",
                  font=("Arial", 10, "bold")).pack(side="left")

        # The Help Button
        help_btn = tk.Button(top_bar, text="❓ Help", command=self.show_help,
                             bg="#f0f0f0", relief="flat", cursor="hand2")
        help_btn.pack(side="right")

        # --- TABS LAYOUT ---
        # We use a Notebook to create the "Tabs" effect
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Create the two main tabs
        self.tab_setup = ttk.Frame(self.notebook)
        self.tab_mark = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_setup, text=" 1. Setup Class & Students ")
        self.notebook.add(self.tab_mark, text=" 2. Mark Attendance ")

        # Build the contents
        self.build_setup_tab()
        self.build_attendance_tab()

        # Load any existing students on startup
        self.load_students_from_file()

    # ==========================================
    # TAB 1: SETUP (Updated with "Enter" Key Logic)
    # ==========================================
    def build_setup_tab(self):
        # --- SECTION A: COURSE DETAILS ---
        info_frame = ttk.LabelFrame(
            self.tab_setup, text=" Course Information ", padding="15")
        info_frame.pack(fill="x", padx=10, pady=10)

        # 1. Course Name
        ttk.Label(info_frame, text="Course Name:").grid(
            row=0, column=0, sticky="w", pady=5)
        self.entry_course_name = ttk.Entry(info_frame, width=30)
        self.entry_course_name.grid(row=0, column=1, padx=5)

        # 2. Course Code
        ttk.Label(info_frame, text="Course Code:").grid(
            row=0, column=2, sticky="w", pady=5, padx=(20, 0))
        self.entry_course_code = ttk.Entry(info_frame, width=15)
        self.entry_course_code.grid(row=0, column=3, padx=5)

        # 3. Lecturer
        ttk.Label(info_frame, text="Lecturer:").grid(
            row=1, column=0, sticky="w", pady=5)
        self.entry_lecturer = ttk.Entry(info_frame, width=30)
        self.entry_lecturer.grid(row=1, column=1, padx=5)

        # 4. Duration
        ttk.Label(info_frame, text="Duration:").grid(
            row=1, column=2, sticky="w", pady=5, padx=(20, 0))
        self.entry_duration = ttk.Entry(info_frame, width=15)
        self.entry_duration.grid(row=1, column=3, padx=5)

        # --- THE MAGIC: LINKING THE ENTER KEY ---
        # When you hit Enter in Name, go to Code
        self.entry_course_name.bind(
            "<Return>", lambda e: self.entry_course_code.focus_set())
        # When you hit Enter in Code, go to Lecturer
        self.entry_course_code.bind(
            "<Return>", lambda e: self.entry_lecturer.focus_set())
        # When you hit Enter in Lecturer, go to Duration
        self.entry_lecturer.bind(
            "<Return>", lambda e: self.entry_duration.focus_set())
        # When you hit Enter in Duration, jump down to the "Add Student" Index box
        self.entry_duration.bind(
            "<Return>", lambda e: self.new_index.focus_set())

        # --- SECTION B: MANAGE STUDENTS ---
        student_frame = ttk.LabelFrame(
            self.tab_setup, text=" Create / Import List of Students ", padding="15")
        student_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Input Area
        input_inner_frame = ttk.Frame(student_frame)
        input_inner_frame.pack(fill="x", pady=5)

        ttk.Label(input_inner_frame, text="Index No:").pack(side="left")
        self.new_index = ttk.Entry(input_inner_frame, width=15)
        self.new_index.pack(side="left", padx=5)

        ttk.Label(input_inner_frame, text="Name:").pack(
            side="left", padx=(10, 0))
        self.new_name = ttk.Entry(input_inner_frame, width=25)
        self.new_name.pack(side="left", padx=5)

        # SPEED ENTRY: Move from Index -> Name, and Name -> Add Button
        self.new_index.bind("<Return>", lambda e: self.new_name.focus_set())
        # This one actually calls the add function when you hit Enter!
        self.new_name.bind("<Return>", lambda e: self.add_single_student())

        add_btn = tk.Button(input_inner_frame, text="+ Add",
                            bg="#4CAF50", fg="white", command=self.add_single_student)
        add_btn.pack(side="left", padx=10)

        # Bulk Import Button
        import_btn = tk.Button(
            student_frame, text="Import CSV List", command=self.import_csv)
        import_btn.pack(anchor="ne", pady=5)

        # Student Table (Treeview)
        columns = ("index", "name")
        self.tree = ttk.Treeview(
            student_frame, columns=columns, show="headings", height=15)
        self.tree.heading("index", text="Index No.")
        self.tree.heading("name", text="Student Name")

        self.tree.column("index", width=150)
        self.tree.column("name", width=350)

        self.tree.pack(fill="both", expand=True)

        # Delete Button
        del_btn = ttk.Button(
            student_frame, text="Delete Selected Student", command=self.delete_student)
        del_btn.pack(pady=10)

    # ==========================================
    # TAB 2: MARKING (Matches bottom half of sketch)
    # ==========================================
    def build_attendance_tab(self):
        # Refresh Button (Important to sync tabs)
        refresh_frame = ttk.Frame(self.tab_mark, padding=10)
        refresh_frame.pack(fill="x")
        ttk.Button(refresh_frame, text="🔄 Refresh Student List",
                   command=self.refresh_marking_list).pack(side="right")

        # Search Bar
        search_frame = ttk.LabelFrame(
            self.tab_mark, text=" Search ", padding="10")
        search_frame.pack(fill="x", padx=10)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_marking_list)
        ttk.Entry(search_frame, textvariable=self.search_var).pack(fill="x")

        # Scrollable Area
        list_frame = ttk.LabelFrame(
            self.tab_mark, text=" Mark Attendance (P=Present, A=Absent) ", padding="10")
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

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
        save_btn = tk.Button(self.tab_mark, text="SAVE ATTENDANCE SHEET", bg="#0066cc", fg="white",
                             font=("Arial", 12, "bold"), command=self.save_attendance)
        save_btn.pack(fill="x", padx=20, pady=20)

    # ==========================================
    # LOGIC & FUNCTIONS
    # ==========================================

    def add_single_student(self):
        idx = self.new_index.get().strip()
        name = self.new_name.get().strip()

        # VALIDATION: Check for empty fields
        if not idx or not name:
            messagebox.showwarning("Error", "Index and Name cannot be empty.")
            return

        # VALIDATION: "names can only contain letters and whitespace" (Regex)
        if not re.match(r"^[a-zA-Z\s]+$", name):
            messagebox.showerror(
                "Invalid Name", "Name must only contain letters and spaces.")
            return

        if idx in self.students:
            messagebox.showwarning(
                "Duplicate", "This Index Number already exists.")
            return

        self.students[idx] = name
        self.save_students_to_file()
        self.update_student_table()

        # Clear inputs
        self.new_index.delete(0, 'end')
        self.new_name.delete(0, 'end')

        # Sync the other tab immediately
        self.refresh_marking_list()

    def import_csv(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV Files", "*.csv")])
        if file_path:
            with open(file_path, "r") as f:
                reader = csv.reader(f)
                count = 0
                for row in reader:
                    if len(row) >= 2:
                        idx, name = row[0].strip(), row[1].strip()
                        self.students[idx] = name
                        count += 1
            self.save_students_to_file()
            self.update_student_table()
            self.refresh_marking_list()
            messagebox.showinfo("Success", f"Imported {count} students!")

    def delete_student(self):
        selected_item = self.tree.selection()
        if not selected_item:
            return

        # Get the index from the selected row
        item = self.tree.item(selected_item)
        idx = item['values'][0]  # The first column is Index
        idx = str(idx)  # Ensure it's a string

        if idx in self.students:
            del self.students[idx]
            self.save_students_to_file()
            self.update_student_table()
            self.refresh_marking_list()

    def update_student_table(self):
        # Clear table
        for item in self.tree.get_children():
            self.tree.delete(item)
        # Re-populate
        for idx, name in self.students.items():
            self.tree.insert("", "end", values=(idx, name))

    def load_students_from_file(self):
        if os.path.exists("students.csv"):
            with open("students.csv", "r") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        self.students[row[0]] = row[1]
            self.update_student_table()
            self.refresh_marking_list()

    def save_students_to_file(self):
        with open("students.csv", "w", newline="") as f:
            writer = csv.writer(f)
            for idx, name in self.students.items():
                writer.writerow([idx, name])

    # --- MARKING LOGIC ---

    def refresh_marking_list(self):
        # Rebuild the list in Tab 2
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.attendance_vars = {}  # Reset vars

        for idx, name in self.students.items():
            self.create_student_row(idx, name)

    def create_student_row(self, idx, name):
        row = ttk.Frame(self.scrollable_frame)
        row.pack(fill="x", pady=2)

        # Label: "Index - Name"
        lbl_text = f"{idx} - {name}"
        ttk.Label(row, text=lbl_text, width=40).pack(side="left", padx=5)

        # Radio Buttons
        var = tk.StringVar(value="None")
        self.attendance_vars[idx] = var

        # P and A buttons
        ttk.Radiobutton(row, text="P", variable=var,
                        value="Present").pack(side="left", padx=10)
        ttk.Radiobutton(row, text="A", variable=var,
                        value="Absent").pack(side="left", padx=10)

    def filter_marking_list(self, *args):
        query = self.search_var.get().lower()

        # Clear view
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Re-add only matching students
        for idx, name in self.students.items():
            if query in name.lower() or query in str(idx).lower():
                # We need to preserve the state of the buttons, so we reuse the variable
                row = ttk.Frame(self.scrollable_frame)
                row.pack(fill="x", pady=2)
                ttk.Label(row, text=f"{idx} - {name}",
                          width=40).pack(side="left", padx=5)

                var = self.attendance_vars[idx]
                ttk.Radiobutton(row, text="P", variable=var,
                                value="Present").pack(side="left", padx=10)
                ttk.Radiobutton(row, text="A", variable=var,
                                value="Absent").pack(side="left", padx=10)

    def save_attendance(self):
        c_name = self.entry_course_name.get()
        c_code = self.entry_course_code.get()
        lecturer = self.entry_lecturer.get()
        duration = self.entry_duration.get()

        if not c_name or not c_code:
            messagebox.showwarning(
                "Missing Info", "Please fill in Course Name and Code in the Setup tab.")
            return

        # Check for unmarked students
        unmarked = [idx for idx, var in self.attendance_vars.items()
                    if var.get() == "None"]
        if unmarked:
            confirm = messagebox.askyesno(
                "Unmarked Students", f"You have {len(unmarked)} students unmarked. Save anyway?")
            if not confirm:
                return

        date_str = datetime.now().strftime("%Y-%m-%d")
        time_str = datetime.now().strftime("%H:%M")
        filename = "attendance_master_log.csv"
        file_exists = os.path.exists(filename)

        with open(filename, "a", newline="") as f:
            writer = csv.writer(f)
            # Write Header if new file
            if not file_exists:
                writer.writerow(["Date", "Time", "Course Name", "Course Code",
                                "Lecturer", "Duration", "Index", "Name", "Status"])

            # Write Data
            for idx, name in self.students.items():
                status = self.attendance_vars[idx].get()
                if status == "None":
                    status = "Unmarked"
                writer.writerow([date_str, time_str, c_name,
                                c_code, lecturer, duration, idx, name, status])

        messagebox.showinfo(
            "Saved", "Attendance saved successfully to attendance_master_log.csv!")

    def show_help(self):
        """Displays instructions and developer contact info."""
        help_message = (
            "KAAF ATTENDANCE PRO - USER GUIDE\n"
            "--------------------------------\n\n"
            "1. SETUP: Enter course details in Tab 1. Use 'Enter' to jump fields.\n"
            "2. STUDENTS: Add students manually (Index, Name) or import a CSV.\n"
            "3. MARKING: Go to Tab 2 to mark P (Present) or A (Absent).\n"
            "4. SEARCH: Use the search bar to find students by name or index.\n"
            "5. SAVING: Click 'SAVE ATTENDANCE' to generate the log file.\n\n"
            "DEVELOPER SUPPORT:\n"
            "Built by: [Arthur Japheth/Level 100 CS]\n"
            "Contact: +233 543629142\n"
            "Issues? Please send a screenshot of the error."
        )
        messagebox.showinfo("Help & Support", help_message)


if __name__ == "__main__":
    root = tk.Tk()
    app = AttendanceApp(root)
    root.mainloop()
