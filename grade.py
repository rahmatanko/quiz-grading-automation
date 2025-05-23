import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import pandas as pd
import os
import numpy as np


class QuizMarker:
    def __init__(self, root):
        self.root = root
        self.root.title("Quiz Marker")
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg="#f0f2f5")

        # Configure for high DPI
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass

        # Custom fonts
        self.custom_font = ("Fira Code Retina", 22)
        self.title_font = ("Fira Code Retina", 24, "bold")
        self.section_font = ("Fira Code Retina", 22)

        # Variables
        self.quiz_number = None
        self.student_data = None
        self.markscheme = None
        self.grading_data = None
        self.current_student = None
        self.current_image = None
        self.bonus_criteria = set()  # Track which criteria are bonus

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
            text="Quiz Marker",
            font=self.title_font,
            bg="#f0f2f5",
            fg="#333333"
        ).pack(side=tk.LEFT)

        # Quiz selection
        quiz_frame = tk.Frame(header_frame, bg="#f0f2f5")
        quiz_frame.pack(side=tk.RIGHT)

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
        self.load_btn.pack(side=tk.LEFT)

        # Fullscreen toggle
        tk.Button(
            header_frame,
            text="Toggle Fullscreen",
            command=self.toggle_fullscreen,
            bg="#607D8B",
            fg="white",
            **button_style
        ).pack(side=tk.RIGHT, padx=10)

        # Create PanedWindow for resizable sections
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

        # Left pane - Flowchart preview (1/3 width)
        self.flowchart_frame = tk.Frame(self.paned_window, bg="#e0e0e0")
        self.paned_window.add(self.flowchart_frame, minsize=300, width=int(self.root.winfo_screenwidth() / 3))

        self.canvas = tk.Canvas(self.flowchart_frame, bg="white")
        self.canvas.pack(expand=True, fill=tk.BOTH)

        # Middle pane - Marking scheme (1/3 width)
        self.marking_frame = tk.Frame(self.paned_window, bg="#f0f2f5")
        self.paned_window.add(self.marking_frame, minsize=400)

        # Create scrollable frame for marking scheme
        self.marking_canvas = tk.Canvas(self.marking_frame, bg="#f0f2f5", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.marking_frame, orient="vertical", command=self.marking_canvas.yview)
        self.scrollable_frame = tk.Frame(self.marking_canvas, bg="#f0f2f5")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.marking_canvas.configure(
                scrollregion=self.marking_canvas.bbox("all")
            )
        )

        self.marking_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.marking_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.marking_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Right pane - Student list (1/3 width)
        self.student_frame = tk.Frame(self.paned_window, bg="#f0f2f5")
        self.paned_window.add(self.student_frame, minsize=300, width=int(self.root.winfo_screenwidth() / 3))

        # Statistics frame
        stats_frame = tk.Frame(self.student_frame, bg="#f0f2f5")
        stats_frame.pack(fill=tk.X, pady=(0, 10))

        self.stats_label = tk.Label(
            stats_frame,
            text="Stats: Loading...",
            font=self.custom_font,
            bg="#f0f2f5",
            fg="#555555"
        )
        self.stats_label.pack(side=tk.LEFT)

        # Student list
        self.student_list = tk.Listbox(
            self.student_frame,
            font=self.custom_font,
            bg="white",
            selectbackground="#2196F3",
            selectforeground="white",
            activestyle="none"
        )
        self.student_list.pack(expand=True, fill=tk.BOTH)
        self.student_list.bind("<<ListboxSelect>>", self.load_student_data)

        # Button frame
        button_frame = tk.Frame(self.student_frame, bg="#f0f2f5")
        button_frame.pack(fill=tk.X, pady=(10, 0))

        self.confirm_btn = tk.Button(
            button_frame,
            text="Confirm Graded",
            command=self.confirm_graded,
            bg="#8BC34A",
            fg="white",
            **button_style,
            state=tk.DISABLED
        )
        self.confirm_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        self.unconfirm_btn = tk.Button(
            button_frame,
            text="Unconfirm Graded",
            command=self.unconfirm_graded,
            bg="#FF9800",
            fg="white",
            **button_style,
            state=tk.DISABLED
        )
        self.unconfirm_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))

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

    def load_quiz_data(self):
        quiz_num = self.quiz_entry.get()
        if not quiz_num.isdigit():
            messagebox.showerror("Error", "Please enter a valid quiz number")
            return

        self.quiz_number = quiz_num
        base_dir = "their data"
        quiz_dir = os.path.join(base_dir, f"quiz {self.quiz_number}")
        feedback_dir = os.path.join(quiz_dir, "feedback")
        students_csv = os.path.join(feedback_dir, f"quiz-{self.quiz_number} students.csv")
        markscheme_path = os.path.join(feedback_dir, f"quiz-{self.quiz_number} markscheme.txt")
        grading_path = os.path.join(feedback_dir, f"quiz-{self.quiz_number} grading.csv")

        # Create directories if needed
        os.makedirs(feedback_dir, exist_ok=True)

        # Load markscheme first
        try:
            with open(markscheme_path, 'r') as f:
                self.markscheme = [line.strip() for line in f if line.strip()]
        except Exception as e:
            messagebox.showerror("Error", f"Could not load markscheme: {str(e)}")
            return

        # Then load student data
        try:
            self.student_data = pd.read_csv(students_csv)
            # Only show validated students
            validated_students = self.student_data[self.student_data['validated'] == True]
        except Exception as e:
            messagebox.showerror("Error", f"Could not load student data: {str(e)}")
            return

        # Initialize grading data (now that markscheme is loaded)
        self.init_grading_data(grading_path)

        # Load student list
        self.load_student_list(validated_students)

        # Process markscheme for UI
        self.process_markscheme()

        # Update stats
        self.update_stats()

        self.status_bar.config(text=f"Quiz {self.quiz_number} loaded")

    def load_student_list(self, students_df):
        self.student_list.delete(0, tk.END)

        for _, row in students_df.iterrows():
            display_text = f"{row['id']} | {row['name']}"
            self.student_list.insert(tk.END, display_text)

            # Check grading data to determine if student is graded
            student_id = row['id']
            graded = False

            # Look up in grading data (if available)
            if self.grading_data is not None:
                student_grading = self.grading_data[self.grading_data['student_id'] == student_id]
                if not student_grading.empty:
                    graded = student_grading['graded'].values[0] == True

            # Color graded entries green
            if graded:
                self.student_list.itemconfig(tk.END, {'bg': '#599e66'})  # green
            else:
                self.student_list.itemconfig(tk.END, {'bg': 'white'})  # Ensure non-graded are white

    def process_markscheme(self):
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.section_widgets = {}
        self.criteria_entries = {}
        self.bonus_criteria = set()  # Reset bonus criteria

        # Create feedback text box
        tk.Label(
            self.scrollable_frame,
            text="Feedback:",
            font=self.section_font,
            bg="#f0f2f5"
        ).pack(anchor="w", pady=(10, 5))

        self.feedback_text = tk.Text(
            self.scrollable_frame,
            height=10,
            font=self.custom_font,
            wrap=tk.WORD
        )
        self.feedback_text.pack(fill=tk.X, padx=5, pady=(0, 10))
        self.feedback_text.bind("<KeyRelease>", self.update_grading_data)

        # Add grade display
        self.grade_display = tk.Label(
            self.scrollable_frame,
            text="Overall Grade: -",
            font=self.section_font,
            bg="#f0f2f5"
        )
        self.grade_display.pack(anchor="w", pady=(0, 20))

        # Process each section in markscheme
        for line in self.markscheme:
            if ":" not in line:
                continue

            section_name, criteria_str = line.split(":", 1)
            criteria_pairs = [c.split(",") for c in criteria_str.split(";") if c]

            # Create main section frame
            section_frame = tk.Frame(self.scrollable_frame, bg="#f0f2f5")
            section_frame.pack(fill=tk.X, pady=(10, 0))

            # Section toggle button
            toggle_btn = tk.Button(
                section_frame,
                text=f"▼ {section_name}",
                font=self.section_font,
                bg="#607D8B",
                fg="white",
                relief=tk.FLAT,
                command=lambda s=section_name: self.toggle_section(s)
            )
            toggle_btn.pack(fill=tk.X)

            # Create nested frame for criteria (inside section frame)
            criteria_frame = tk.Frame(section_frame, bg="#f0f2f5")
            criteria_frame.pack(fill=tk.X, padx=20, pady=(0, 5))

            # Store widgets for later access
            self.section_widgets[section_name] = {
                'button': toggle_btn,
                'frame': criteria_frame,
                'visible': False
            }

            # Add criteria entries to the nested frame
            for max_mark, criteria in criteria_pairs:
                is_bonus = criteria.endswith("*")
                if is_bonus:
                    criteria = criteria[:-1]  # Remove the *
                    self.bonus_criteria.add(f"{section_name}_{criteria}")

                crit_frame = tk.Frame(criteria_frame, bg="#f0f2f5")
                crit_frame.pack(fill=tk.X, padx=5, pady=2)

                tk.Label(
                    crit_frame,
                    text=f"{criteria} (max {max_mark}){' [BONUS]' if is_bonus else ''}:",
                    font=self.custom_font,
                    bg="#f0f2f5",
                    width=60,
                    anchor="w",
                    fg="#FF9800" if is_bonus else "black"
                ).pack(side=tk.LEFT)

                entry = tk.Entry(
                    crit_frame,
                    font=self.custom_font,
                    width=5
                )
                entry.pack(side=tk.LEFT, padx=5)
                entry.bind("<KeyRelease>", self.update_grading_data)

                # Store entry for later access
                self.criteria_entries[f"{section_name}_{criteria}"] = entry

            # Hide criteria by default
            criteria_frame.pack_forget()

    def toggle_section(self, section_name):
        widget = self.section_widgets[section_name]
        if widget['visible']:
            widget['frame'].pack_forget()
            widget['button'].config(text=f"▼ {section_name}")
            widget['visible'] = False
        else:
            widget['frame'].pack(fill=tk.X)
            widget['button'].config(text=f"▲ {section_name}")
            widget['visible'] = True

    def init_grading_data(self, grading_path):
        if os.path.exists(grading_path):
            self.grading_data = pd.read_csv(grading_path)
        else:
            # Create new grading dataframe
            columns = ['student_id']

            # Add columns for each criteria
            if self.markscheme is not None:
                for line in self.markscheme:
                    if ":" not in line:
                        continue
                    section_name, criteria_str = line.split(":", 1)
                    criteria_pairs = [c.split(",") for c in criteria_str.split(";") if c]
                    for _, criteria in criteria_pairs:
                        if criteria.endswith("*"):
                            criteria = criteria[:-1]  # Remove the *
                        columns.append(f"{section_name}_{criteria}")

            # Add feedback and graded columns
            columns.extend(['feedback', 'graded', 'overall_grade'])

            # Initialize with all validated students
            validated_students = self.student_data[self.student_data['validated'] == True]
            self.grading_data = pd.DataFrame(columns=columns)

            # Create list of new rows
            new_rows = []
            for _, student in validated_students.iterrows():
                new_row = {'student_id': student['id'], 'graded': False}
                new_rows.append(new_row)

            # Concatenate all new rows at once
            if new_rows:
                self.grading_data = pd.concat(
                    [self.grading_data, pd.DataFrame(new_rows)],
                    ignore_index=True
                )

            # Save empty grading file
            self.grading_data.to_csv(grading_path, index=False)

    def load_student_data(self, event):
        selection = self.student_list.curselection()
        if not selection:
            return

        selected_idx = selection[0]
        student_id = self.student_data.iloc[selected_idx]['id']
        self.current_student = student_id

        # Load student's chart
        self.load_student_chart(student_id)

        # Load student's grading data
        student_grading = self.grading_data[self.grading_data['student_id'] == student_id]

        # Clear feedback and grade display
        self.feedback_text.delete(1.0, tk.END)
        self.grade_display.config(text="Overall Grade: -")

        if not student_grading.empty:
            # Initialize totals
            total_marks = 0
            total_max_marks = 0
            bonus_marks = 0

            # Fill in criteria marks
            for criteria, entry in self.criteria_entries.items():
                mark = student_grading[criteria].values[0]
                if pd.notna(mark):
                    entry.delete(0, tk.END)
                    entry.insert(0, str(int(mark)))  # Ensure integer display

                    # Calculate marks
                    if criteria in self.bonus_criteria:
                        bonus_marks += float(mark)
                    else:
                        section, crit = criteria.split("_", 1)
                        max_mark = self.get_max_mark(section, crit)
                        if max_mark:
                            total_marks += float(mark)
                            total_max_marks += float(max_mark)
                else:
                    entry.delete(0, tk.END)

            # Fill in feedback
            feedback = student_grading['feedback'].values[0]
            if pd.notna(feedback):
                self.feedback_text.insert(1.0, feedback)

            # Calculate and display overall grade
            if total_max_marks > 0:
                percentage = (total_marks / total_max_marks) * 100
                grade_text = f"Overall Grade: {total_marks:.0f}/{total_max_marks:.0f} ({percentage:.1f}%)"
                if bonus_marks > 0:
                    grade_text += f" + {bonus_marks:.0f} bonus"
                self.grade_display.config(text=grade_text)

        # Set button states
        is_graded = not student_grading.empty and student_grading['graded'].values[0] == True
        self.confirm_btn.config(state=tk.NORMAL if not is_graded else tk.DISABLED)
        self.unconfirm_btn.config(state=tk.NORMAL if is_graded else tk.DISABLED)

    def load_student_chart(self, student_id):
        chart_path = os.path.join(
            "their data",
            f"quiz {self.quiz_number}",
            "charts",
            f"quiz-{self.quiz_number} {student_id}.png"
        )

        self.canvas.delete("all")

        # Get current canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if os.path.exists(chart_path):
            try:
                img = Image.open(chart_path)

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

                # Display image
                self.canvas.create_image(
                    canvas_width // 2,
                    canvas_height // 2,
                    image=self.current_image,
                    anchor=tk.CENTER
                )

            except Exception as e:
                self.canvas.create_text(
                    canvas_width // 2,
                    canvas_height // 2,
                    text=f"Error loading chart: {str(e)}",
                    font=self.custom_font,
                    fill="black"
                )
        else:
            self.canvas.create_text(
                canvas_width // 2,
                canvas_height // 2,
                text="No chart found for this student",
                font=self.custom_font,
                fill="black"
            )

    def get_max_mark(self, section_name, criteria_name):
        for line in self.markscheme:
            if line.startswith(section_name + ":"):
                criteria_str = line.split(":", 1)[1]
                criteria_pairs = [c.split(",") for c in criteria_str.split(";") if c]
                for max_mark, crit in criteria_pairs:
                    if crit.endswith("*"):
                        crit = crit[:-1]  # Remove the *
                    if crit == criteria_name:
                        return float(max_mark)
        return None

    def update_grading_data(self, event=None):
        if not self.current_student:
            return

        # Find student in grading data
        student_idx = self.grading_data[self.grading_data['student_id'] == self.current_student].index

        if len(student_idx) == 0:
            return

        student_idx = student_idx[0]

        # Initialize totals
        total_marks = 0
        total_max_marks = 0
        bonus_marks = 0
        changed = False

        # Update criteria marks and calculate totals
        for criteria, entry in self.criteria_entries.items():
            mark = entry.get()
            current_value = self.grading_data.at[student_idx, criteria]

            # Only update if the value has changed
            if mark and mark.isdigit():
                mark_int = int(mark)
                if current_value != mark_int:
                    self.grading_data.at[student_idx, criteria] = mark_int
                    changed = True

                # Calculate marks differently for bonus criteria
                if criteria in self.bonus_criteria:
                    bonus_marks += mark_int
                else:
                    section, crit = criteria.split("_", 1)
                    max_mark = self.get_max_mark(section, crit)
                    if max_mark:
                        total_marks += mark_int
                        total_max_marks += float(max_mark)
            elif pd.notna(current_value):
                self.grading_data.at[student_idx, criteria] = None
                changed = True

        # Update feedback if changed
        feedback = self.feedback_text.get(1.0, tk.END).strip()
        current_feedback = self.grading_data.at[student_idx, 'feedback']
        if feedback != current_feedback:
            self.grading_data.at[student_idx, 'feedback'] = feedback
            changed = True

        # Only save if something changed
        if changed:
            # Update overall grade if calculated
            if total_max_marks > 0:
                percentage = (total_marks / total_max_marks) * 100
                grade_text = f"{total_marks:.0f}/{total_max_marks:.0f} ({percentage:.1f}%)"
                if bonus_marks > 0:
                    grade_text += f" + {bonus_marks:.0f} bonus"
                self.grade_display.config(text=f"Overall Grade: {grade_text}")
                self.grading_data.at[student_idx, 'overall_grade'] = grade_text

            # Save changes to grading CSV
            grading_path = os.path.join(
                "their data",
                f"quiz {self.quiz_number}",
                "feedback",
                f"quiz-{self.quiz_number} grading.csv"
            )
            self.grading_data.to_csv(grading_path, index=False)

            # Update student CSV with the total marks
            self.update_student_csv(total_marks, bonus_marks)

            # Update stats
            self.update_stats()

    def update_student_csv(self, total_marks, bonus_marks):
        """Update the student CSV with the total marks and feedback"""
        if not self.current_student or not self.quiz_number:
            return

        # Path to student CSV
        students_csv = os.path.join(
            "their data",
            f"quiz {self.quiz_number}",
            "feedback",
            f"quiz-{self.quiz_number} students.csv"
        )

        try:
            # Load student data
            student_df = pd.read_csv(students_csv)

            # Find the student
            mask = student_df['id'] == self.current_student
            if not mask.any():
                return

            # Update the row
            student_df.loc[mask, 'grade'] = total_marks
            student_df.loc[mask, 'bonus'] = bonus_marks
            student_df.loc[mask, 'total'] = total_marks + bonus_marks

            # Save back to CSV
            student_df.to_csv(students_csv, index=False)
        except Exception as e:
            messagebox.showerror("Error", f"Could not update student CSV: {str(e)}")

    def confirm_graded(self):
        if not self.current_student:
            return

        # Find student in grading data
        student_idx = self.grading_data[self.grading_data['student_id'] == self.current_student].index

        if len(student_idx) == 0:
            return

        student_idx = student_idx[0]

        # Mark as graded
        self.grading_data.at[student_idx, 'graded'] = True

        # Save changes
        self.update_grading_data()

        # Update student list color
        selection = self.student_list.curselection()
        if selection:
            self.student_list.itemconfig(selection[0], {'bg': '#599e66'})

        # Update button states
        self.confirm_btn.config(state=tk.DISABLED)
        self.unconfirm_btn.config(state=tk.NORMAL)

        # Update student CSV graded status
        self.update_student_graded_status(True)

        # Update stats
        self.update_stats()

    def unconfirm_graded(self):
        if not self.current_student:
            return

        # Find student in grading data
        student_idx = self.grading_data[self.grading_data['student_id'] == self.current_student].index

        if len(student_idx) == 0:
            return

        student_idx = student_idx[0]

        # Mark as not graded
        self.grading_data.at[student_idx, 'graded'] = False

        # Save changes
        self.update_grading_data()

        # Update student list color
        selection = self.student_list.curselection()
        if selection:
            self.student_list.itemconfig(selection[0], {'bg': 'white'})

        # Update button states
        self.confirm_btn.config(state=tk.NORMAL)
        self.unconfirm_btn.config(state=tk.DISABLED)

        # Update grading CSV graded status
        self.update_student_graded_status(False)

        # Update stats
        self.update_stats()

    def update_student_graded_status(self, graded):
        """Update the graded status in the student CSV"""
        if not self.current_student or not self.quiz_number:
            return

        # Path to student CSV
        students_csv = os.path.join(
            "their data",
            f"quiz {self.quiz_number}",
            "feedback",
            f"quiz-{self.quiz_number} grading.csv"
        )

        try:
            # Load student data
            student_df = pd.read_csv(students_csv)

            # Find the student
            mask = student_df['student_id'] == self.current_student
            if not mask.any():
                return

            # Update the graded status
            student_df.loc[mask, 'graded'] = graded

            # Save back to CSV
            student_df.to_csv(students_csv, index=False)
        except Exception as e:
            messagebox.showerror("Error", f"Could not update grading CSV: {str(e)}")

    def update_stats(self):
        if self.grading_data is None:
            return

        # Calculate stats
        graded_count = self.grading_data['graded'].sum()
        total_students = len(self.grading_data)
        percent_graded = (graded_count / total_students) * 100 if total_students > 0 else 0

        # Calculate average marks per criteria
        stats_text = f"Graded: {graded_count}/{total_students} ({percent_graded:.1f}%)"

        # Add section averages if available
        if len(self.grading_data) > 0:
            numeric_cols = [col for col in self.grading_data.columns
                            if col not in ['student_id', 'feedback', 'graded', 'overall_grade']
                            and pd.api.types.is_numeric_dtype(self.grading_data[col])]

            if numeric_cols:
                # Separate regular and bonus criteria
                regular_cols = [col for col in numeric_cols if col not in self.bonus_criteria]
                bonus_cols = [col for col in numeric_cols if col in self.bonus_criteria]

                # Calculate regular averages
                if regular_cols:
                    avg_regular = self.grading_data[regular_cols].mean().mean().round(1)
                    max_regular = self.grading_data[regular_cols].max().max().round(1)
                    min_regular = self.grading_data[regular_cols].min().min().round(1)
                    stats_text += f"\nRegular: Avg {avg_regular} | Max {max_regular} | Min {min_regular}"

                # Calculate bonus averages
                if bonus_cols:
                    avg_bonus = self.grading_data[bonus_cols].mean().mean().round(1)
                    max_bonus = self.grading_data[bonus_cols].max().max().round(1)
                    min_bonus = self.grading_data[bonus_cols].min().min().round(1)
                    stats_text += f"\nBonus: Avg {avg_bonus} | Max {max_bonus} | Min {min_bonus}"

        self.stats_label.config(text=stats_text)


if __name__ == "__main__":
    root = tk.Tk()
    app = QuizMarker(root)
    root.mainloop()
