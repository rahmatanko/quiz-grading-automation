import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import pandas as pd
import os
import shutil


class ValidateNames:
    def __init__(self, root):
        self.root = root
        self.root.title("Quiz Attendance Tracker")
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg="#f0f2f5")

        # Configure for high DPI
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass

        # Custom fonts
        self.custom_font = ("Segoe UI", 18)
        self.title_font = ("Segoe UI", 22, "bold")

        # Variables
        self.quiz_number = None
        self.student_csv_path = None
        self.attendance_path = None
        self.charts_dir = None
        self.student_data = None
        self.current_image = None
        self.paned_window = None  # For resizable panes
        self.list_frame = None
        self.preview_frame = None

        # Setup UI
        self.setup_ui()
        self.root.bind("<Escape>", lambda e: self.root.attributes('-fullscreen', False))

    def setup_ui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg="#f0f2f5", padx=20, pady=20)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Header
        header_frame = tk.Frame(main_frame, bg="#f0f2f5")
        header_frame.pack(fill=tk.X, pady=(0, 30))

        tk.Label(
            header_frame,
            text="Attendance Tracker",
            font=self.title_font,
            bg="#f0f2f5",
            fg="#333333"
        ).pack(side=tk.LEFT)

        # Fullscreen toggle button
        tk.Button(
            header_frame,
            text="Toggle Fullscreen",
            command=self.toggle_fullscreen,
            bg="#607D8B",
            fg="white",
            font=self.custom_font,
            borderwidth=0,
            relief=tk.FLAT,
            padx=15,
            pady=8
        ).pack(side=tk.RIGHT, padx=10)

        # Quiz selection
        quiz_frame = tk.Frame(main_frame, bg="#f0f2f5")
        quiz_frame.pack(fill=tk.X, pady=(0, 20))

        tk.Label(
            quiz_frame,
            text="Quiz Number:",
            font=self.custom_font,
            bg="#f0f2f5"
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.quiz_entry = tk.Entry(quiz_frame, font=self.custom_font, width=10)
        self.quiz_entry.pack(side=tk.LEFT, padx=(0, 10))

        button_style = {
            "font": self.custom_font,
            "borderwidth": 0,
            "relief": tk.FLAT,
            "padx": 15,
            "pady": 8,
            "activebackground": "#e0e0e0"
        }

        self.load_btn = tk.Button(
            quiz_frame,
            text="Load Quiz",
            command=self.load_quiz_data,
            bg="#4CAF50",
            fg="white",
            **button_style
        )
        self.load_btn.pack(side=tk.LEFT, padx=5)

        self.refresh_btn = tk.Button(
            quiz_frame,
            text="Refresh Data",
            command=self.refresh_student_data,
            bg="#2196F3",
            fg="white",
            **button_style,
            state=tk.DISABLED
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=5)

        # Create PanedWindow for resizable split view
        self.paned_window = tk.PanedWindow(
            main_frame,
            orient=tk.HORIZONTAL,
            bg="#f0f2f5",
            sashwidth=8,
            sashrelief=tk.RAISED,
            sashpad=3,
            opaqueresize=True
        )
        self.paned_window.pack(expand=True, fill=tk.BOTH)

        # Student list (left pane)
        self.list_frame = tk.Frame(self.paned_window, bg="#f0f2f5")
        self.paned_window.add(self.list_frame, minsize=300, width=500)  # Initial width

        # Student listbox
        self.student_list = tk.Listbox(
            self.list_frame,
            font=self.custom_font,
            bg="white",
            selectbackground="#2196F3",
            selectforeground="white",
            activestyle="none"
        )
        self.student_list.pack(expand=True, fill=tk.BOTH)
        self.student_list.bind("<<ListboxSelect>>", self.show_student_chart)

        # List controls
        controls_frame = tk.Frame(self.list_frame, bg="#f0f2f5")
        controls_frame.pack(fill=tk.X, pady=(10, 0))

        self.validate_btn = tk.Button(
            controls_frame,
            text="Validate",
            command=self.validate_student,
            bg="#8BC34A",
            fg="white",
            **button_style,
            state=tk.DISABLED
        )
        self.validate_btn.pack(side=tk.LEFT, padx=5)

        self.unvalidate_btn = tk.Button(
            controls_frame,
            text="Unvalidate",
            command=self.unvalidate_student,
            bg="#FF9800",
            fg="white",
            **button_style,
            state=tk.DISABLED
        )
        self.unvalidate_btn.pack(side=tk.LEFT, padx=5)

        self.edit_id_btn = tk.Button(
            controls_frame,
            text="Edit ID",
            command=self.edit_student_id,
            bg="#607D8B",
            fg="white",
            **button_style,
            state=tk.DISABLED
        )
        self.edit_id_btn.pack(side=tk.LEFT, padx=5)

        # Image preview (right pane)
        self.preview_frame = tk.Frame(self.paned_window, bg="#e0e0e0")
        self.paned_window.add(self.preview_frame, minsize=400)

        self.canvas = tk.Canvas(
            self.preview_frame,
            bg="white"
        )
        self.canvas.pack(expand=True, fill=tk.BOTH)

        self.scroll_x = tk.Scrollbar(
            self.preview_frame,
            orient=tk.HORIZONTAL,
            command=self.canvas.xview
        )
        self.scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.scroll_y = tk.Scrollbar(
            self.preview_frame,
            orient=tk.VERTICAL,
            command=self.canvas.yview
        )
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.configure(
            xscrollcommand=self.scroll_x.set,
            yscrollcommand=self.scroll_y.set
        )

        # Status bar
        self.status_bar = tk.Label(
            main_frame,
            text="Ready - Please enter quiz number",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            font=self.custom_font,
            bg="#e0e0e0",
            fg="#333333"
        )
        self.status_bar.pack(fill=tk.X, pady=(20, 0))

    def toggle_fullscreen(self):
        self.root.attributes('-fullscreen', not self.root.attributes('-fullscreen'))

    # [Rest of your methods remain exactly the same...]
    def load_quiz_data(self):
        quiz_num = self.quiz_entry.get()
        if not quiz_num.isdigit():
            messagebox.showerror("Error", "Please enter a valid quiz number")
            return

        self.quiz_number = quiz_num
        base_dir = "their data"
        quiz_dir = os.path.join(base_dir, f"quiz {self.quiz_number}")
        feedback_dir = os.path.join(quiz_dir, "feedback")
        self.student_csv_path = os.path.join(feedback_dir, f"quiz-{self.quiz_number} students.csv")
        self.attendance_path = os.path.join(feedback_dir, f"quiz-{self.quiz_number} attendance.txt")
        self.charts_dir = os.path.join(quiz_dir, "charts")

        # Create directories if needed
        os.makedirs(feedback_dir, exist_ok=True)

        # Initialize or load student CSV
        if not os.path.exists(self.student_csv_path):
            # Create new CSV with required columns
            columns = ["id", "name", "grade", "validated"]
            pd.DataFrame(columns=columns).to_csv(self.student_csv_path, index=False)

        # Process attendance data
        self.process_attendance()
        self.refresh_student_data()
        self.refresh_btn.config(state=tk.NORMAL)
        self.status_bar.config(text=f"Quiz {self.quiz_number} loaded | Students: {len(self.student_data)}")

    def process_attendance(self):
        # Read existing student data
        try:
            self.student_data = pd.read_csv(self.student_csv_path)
        except:
            self.student_data = pd.DataFrame(columns=["id", "name", "grade", "validated"])

        # Read attendance file
        if os.path.exists(self.attendance_path):
            with open(self.attendance_path, 'r') as f:
                attendance_ids = {line.strip() for line in f if line.strip()}
        else:
            attendance_ids = set()

        # Get new IDs from attendance that aren't in student data
        existing_ids = set(self.student_data['id'].astype(str))
        new_ids = attendance_ids - existing_ids

        if new_ids:
            # Add new students with default values
            new_students = pd.DataFrame({
                "id": list(new_ids),
                "name": "",
                "grade": "",
                "validated": False
            })
            self.student_data = pd.concat([self.student_data, new_students], ignore_index=True)

        # ALWAYS update names from master sheet (for all students)
        self.update_names_from_master()

        # Save updated CSV
        self.student_data.to_csv(self.student_csv_path, index=False)

    def update_names_from_master(self):
        try:
            # Load master spreadsheet
            master_sheet = pd.read_excel("sheets/students.xlsx", sheet_name="quizzes")

            # Create mapping dictionary for faster lookup
            id_to_info = {}
            for _, row in master_sheet.iterrows():
                student_id = str(row['number'])
                id_to_info[student_id] = {
                    'name': row['name']
                }

            # Update all student records
            for idx, row in self.student_data.iterrows():
                student_id = str(float(row['id']))
                if student_id in id_to_info:
                    # Always update name and grade from master sheet
                    self.student_data.at[idx, 'name'] = id_to_info[student_id]['name']

            self.student_data.to_csv(self.student_csv_path)

        except Exception as e:
            messagebox.showerror("Error", f"Could not update from master sheet: {str(e)}")

    def refresh_student_data(self):
        if not self.quiz_number:
            return

        try:
            # Reload student data
            self.student_data = pd.read_csv(self.student_csv_path)

            # Update listbox
            self.student_list.delete(0, tk.END)

            for _, row in self.student_data.iterrows():
                display_text = f"{row['id']} | {row['name']}"
                self.student_list.insert(tk.END, display_text)

                # Color validated entries
                if row['validated']:
                    self.student_list.itemconfig(tk.END, {'bg': '#E8F5E9'})  # Pastel green

            self.status_bar.config(text=f"Data refreshed | Students: {len(self.student_data)}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not refresh data: {str(e)}")

    def show_student_chart(self, event):
        selection = self.student_list.curselection()
        if not selection:
            return

        selected_idx = selection[0]
        student_id = self.student_data.iloc[selected_idx]['id']

        # Enable/disable buttons based on validation status
        is_validated = self.student_data.iloc[selected_idx]['validated']
        self.validate_btn.config(state=tk.NORMAL if not is_validated else tk.DISABLED)
        self.unvalidate_btn.config(state=tk.NORMAL if is_validated else tk.DISABLED)
        self.edit_id_btn.config(state=tk.NORMAL)

        # Load and display chart image
        chart_path = os.path.join(self.charts_dir, f"quiz-{self.quiz_number} {student_id}.png")
        if os.path.exists(chart_path):
            try:
                img = Image.open(chart_path)

                # Calculate display size (fit to canvas)
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()

                # Maintain aspect ratio
                img_ratio = img.width / img.height
                new_width = min(canvas_width, img.width)
                new_height = int(new_width / img_ratio)

                if new_height > canvas_height:
                    new_height = canvas_height
                    new_width = int(new_height * img_ratio)

                # High quality resize
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                self.current_image = ImageTk.PhotoImage(img)

                # Clear canvas and display image
                self.canvas.delete("all")
                self.canvas.create_image(
                    canvas_width // 2,
                    canvas_height // 2,
                    image=self.current_image,
                    anchor=tk.CENTER
                )

                # Update scroll region
                self.canvas.config(scrollregion=(0, 0, new_width, new_height))

            except Exception as e:
                messagebox.showerror("Error", f"Could not load chart: {str(e)}")
        else:
            self.canvas.delete("all")
            self.canvas.create_text(
                self.canvas.winfo_width() // 2,
                self.canvas.winfo_height() // 2,
                text="No chart found for this student",
                font=self.custom_font
            )

    def validate_student(self):
        selection = self.student_list.curselection()
        if not selection:
            return

        selected_idx = selection[0]
        self.student_data.at[selected_idx, 'validated'] = True
        self.student_data.to_csv(self.student_csv_path, index=False)
        self.refresh_student_data()

        # Keep the selection after refresh
        self.student_list.selection_set(selected_idx)
        self.student_list.see(selected_idx)
        self.show_student_chart(None)

    def unvalidate_student(self):
        selection = self.student_list.curselection()
        if not selection:
            return

        selected_idx = selection[0]
        self.student_data.at[selected_idx, 'validated'] = False
        self.student_data.to_csv(self.student_csv_path, index=False)
        self.refresh_student_data()

        # Keep the selection after refresh
        self.student_list.selection_set(selected_idx)
        self.student_list.see(selected_idx)
        self.show_student_chart(None)

    def edit_student_id(self):
        selection = self.student_list.curselection()
        if not selection:
            return

        selected_idx = selection[0]
        old_id = str(self.student_data.iloc[selected_idx]['id'])

        # Get new ID from user
        new_id = simpledialog.askstring(
            "Edit Student ID",
            f"Current ID: {old_id}\nEnter new ID:",
            parent=self.root
        )

        if not new_id or new_id == old_id:
            return

        try:
            # Update ID in student data
            self.student_data.at[selected_idx, 'id'] = new_id

            # Update name from master sheet
            self.update_names_from_master()

            # Rename chart file if exists
            old_chart = os.path.join(self.charts_dir, f"quiz-{self.quiz_number} {old_id}.png")
            new_chart = os.path.join(self.charts_dir, f"quiz-{self.quiz_number} {new_id}.png")

            if os.path.exists(old_chart):
                shutil.move(old_chart, new_chart)

            # Update attendance file
            if os.path.exists(self.attendance_path):
                with open(self.attendance_path, 'r') as f:
                    lines = [line.strip() for line in f if line.strip()]

                if old_id in lines:
                    lines[lines.index(old_id)] = new_id
                    with open(self.attendance_path, 'w') as f:
                        f.write("\n".join(lines) + "\n")

            # Save changes and refresh
            self.student_data.to_csv(self.student_csv_path, index=False)
            self.refresh_student_data()

            # Keep the selection after refresh
            self.student_list.selection_set(selected_idx)
            self.student_list.see(selected_idx)
            self.show_student_chart(None)

        except Exception as e:
            messagebox.showerror("Error", f"Could not update ID: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ValidateNames(root)
    root.mainloop()
