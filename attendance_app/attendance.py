import os
from datetime import datetime

course_name = ""
course_code = ""
students = {}
attendance = {}

STUDENT_FILE = "students.csv"


def load_students():
    """Loads students from a file so you don't re-type them every time."""
    global students
    if os.path.exists(STUDENT_FILE):
        with open(STUDENT_FILE, "r") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) == 2:
                    students[parts[0]] = parts[1]
        print(f"Loaded {len(students)} students from record.")


def save_students():
    """Saves the student list to a file."""
    with open(STUDENT_FILE, "w") as f:
        for index, name in students.items():
            f.write(f"{index},{name}\n")


def set_course():
    global course_name, course_code

    course_name = input("Enter course name: ").strip()
    course_code = input("Enter course code: ").strip()

    print("Course details saved!\n")


def add_students():
    print("Enter student details (type 'done' to finish): ")

    while True:
        index = input("Index number: ").strip()

        if index.lower() == "done":
            break

        name = input("Student name: ").strip()

        students[index] = name
    save_students()  # Save to disk immediately
    print("Students added successfully!\n")


def mark_attendance():
    if not course_name:
        print("Please set course details first.\n")
        return

    if not students:
        print("No students found. Please add students first.\n")
        return

    print(f"Marking attendance for: {course_name} ({course_code})")
    print("Type 'P'for Present, 'A' for Absent")

    for index, name in students.items():
        while True:
            status = input(f"{index} - {name}: ").strip().upper()

            if status in ["P", "A"]:
                attendance[index] = "Present" if status == "P" else "Absent"
                break
            print("Invalid input. Please enter P or A")

    print("Attendance marked!\n")


def get_date_time():
    now = datetime.now()
    return now.strftime("%d-%m-%Y"), now.strftime("%H:%M")


def save_attendance_csv():
    if not attendance:
        print("No attendance to save. Please mark attendance first.\n")
        return

    file_exists = os.path.exists("attendance.csv")

    date, time = get_date_time()

    with open("attendance.csv", "a") as file:
        if not file_exists:
            file.write(
                "Date,Time,Course Code, Course Name,Index No,Name,Status\n")

        for index, status in attendance.items():
            name = students.get(index, "Unknown")
            file.write(
                f"{date},{time},{course_code},{course_name},{index},{name},{status}\n")

    attendance.clear()  # Clear  for next session
    print("Attendance saved to CSV and cleared for next session!\n")


def attendance_summary():
    if not os.path.exists("attendance.csv"):
        print("No attendance records found.\n")
        return

    summary = {}

    with open("attendance.csv", "r") as file:
        lines = file.readlines()

    # Skip header
    for line in lines[1:]:
        parts = line.strip().split(",")
        if len(parts) < 7:
            continue

        index = parts[4]
        name = parts[5]
        status = parts[6]

        if index not in summary:
            summary[index] = {"name": name, "present": 0, "total": 0}

        summary[index]["total"] += 1
        if status == "Present":
            summary[index]["present"] += 1

    print("\n--- ATTENDANCE SUMMARY ---")
    for index, data in summary.items():
        percent = (data["present"] / data["total"]) * 100
        print(
            f"{index} | {data['name']}: {data['present']}/{data['total']} sessions ({percent:.1f}%)")
    print("--------------------------\n")


def menu():
    load_students()
    while True:
        print("1. Set course details")
        print("2. Add/Update students list")
        print("3. Mark attendance")
        print("4. Save attendance (CSV)")
        print("5. Attendance summary")
        print("6. Exit")

        choice = input("Choose option: ")

        if choice == "1":
            set_course()
        elif choice == "2":
            add_students()
        elif choice == "3":
            mark_attendance()
        elif choice == "4":
            save_attendance_csv()
        elif choice == "5":
            attendance_summary()
        elif choice == "6":
            print("Done for the day!")
            break
        else:
            print("Invalid choice. Try again.\n")


if __name__ == "__main__":
    menu()
