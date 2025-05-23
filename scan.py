import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from PIL import Image, ImageTk, ImageOps
import os
from wia_scan import *


class HighResScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quiz Scanner")
        self.root.geometry("1200x1000")
        self.root.configure(bg="#f0f2f5")

        # Configure for high DPI (Windows)
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass

        # Custom font - larger for 4K
        self.custom_font = ("Segoe UI", 12)
        self.title_font = ("Segoe UI", 18, "bold")

        # Initialize variables
        self.pillow_image = None
        self.original_image = None
        self.quiz_number = None
        self.student_id = None
        self.scale_factor = 1.0
        self.scanned_students = set()
        self.total_scanned = 0

        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        # Main container frame
        main_frame = tk.Frame(self.root, bg="#f0f2f5", padx=30, pady=30)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Header
        header_frame = tk.Frame(main_frame, bg="#f0f2f5")
        header_frame.pack(fill=tk.X, pady=(0, 30))

        tk.Label(
            header_frame,
            text="Quiz Scanner",
            font=self.title_font,
            bg="#f0f2f5",
            fg="#333333"
        ).pack(side=tk.LEFT)

        # Info display
        self.info_frame = tk.Frame(main_frame, bg="#f0f2f5")
        self.info_frame.pack(fill=tk.X, pady=(0, 20))

        self.quiz_info_label = tk.Label(
            self.info_frame,
            text="Quiz: Not set | Students: 0",
            font=self.custom_font,
            bg="#f0f2f5",
            fg="#555555"
        )
        self.quiz_info_label.pack(side=tk.LEFT)

        # Button frame
        button_frame = tk.Frame(main_frame, bg="#f0f2f5")
        button_frame.pack(fill=tk.X, pady=(0, 30))

        # Buttons with modern style
        button_style = {
            "font": self.custom_font,
            "borderwidth": 0,
            "relief": tk.FLAT,
            "padx": 20,
            "pady": 10,
            "activebackground": "#e0e0e0"
        }

        self.set_quiz_button = tk.Button(
            button_frame,
            text="Set Quiz Number",
            command=self.set_quiz_number,
            bg="#607D8B",
            fg="white",
            **button_style
        )
        self.set_quiz_button.pack(side=tk.LEFT, padx=10)

        self.scan_button = tk.Button(
            button_frame,
            text="Scan",
            command=self.scan_image,
            bg="#4CAF50",
            fg="white",
            **button_style
        )
        self.scan_button.pack(side=tk.LEFT, padx=10)

        self.zoom_in_button = tk.Button(
            button_frame,
            text="Zoom In (+)",
            command=lambda: self.adjust_zoom(1.25),
            bg="#2196F3",
            fg="white",
            **button_style
        )
        self.zoom_in_button.pack(side=tk.LEFT, padx=10)

        self.zoom_out_button = tk.Button(
            button_frame,
            text="Zoom Out (-)",
            command=lambda: self.adjust_zoom(0.8),
            bg="#2196F3",
            fg="white",
            **button_style
        )
        self.zoom_out_button.pack(side=tk.LEFT, padx=10)

        self.save_button = tk.Button(
            button_frame,
            text="Save",
            command=self.save_image,
            bg="#FF9800",
            fg="white",
            **button_style,
            state=tk.DISABLED
        )
        self.save_button.pack(side=tk.LEFT, padx=10)

        # Preview frame with scrollbars
        self.preview_frame = tk.Frame(main_frame, bg="#e0e0e0")
        self.preview_frame.pack(expand=True, fill=tk.BOTH)

        # Canvas with scrollbars
        self.canvas = tk.Canvas(
            self.preview_frame,
            bg="white",
            width=800,
            height=1000,
            scrollregion=(0, 0, 800, 1000)
        )

        self.h_scroll = tk.Scrollbar(
            self.preview_frame,
            orient=tk.HORIZONTAL,
            command=self.canvas.xview
        )
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.v_scroll = tk.Scrollbar(
            self.preview_frame,
            orient=tk.VERTICAL,
            command=self.canvas.yview
        )
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.configure(
            xscrollcommand=self.h_scroll.set,
            yscrollcommand=self.v_scroll.set
        )
        self.canvas.pack(expand=True, fill=tk.BOTH)

        # Image container on canvas
        self.image_container = self.canvas.create_rectangle(0, 0, 1, 1, outline="")

        # Status bar
        self.status_bar = tk.Label(
            main_frame,
            text="Ready - Please set quiz number first",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            font=self.custom_font,
            bg="#e0e0e0",
            fg="#333333"
        )
        self.status_bar.pack(fill=tk.X, pady=(30, 0))

    def set_quiz_number(self):
        try:
            quiz_num = simpledialog.askinteger(
                "Quiz Number",
                "Enter the quiz number:",
                parent=self.root,
                minvalue=1,
                maxvalue=100
            )

            if quiz_num is not None:
                self.quiz_number = quiz_num
                self.initialize_attendance_file()
                self.save_button.config(state=tk.NORMAL)
            else:
                self.status_bar.config(text="Quiz number not set")

        except Exception as e:
            self.status_bar.config(text=f"Error: {str(e)}")

    def initialize_attendance_file(self):
        """Find or create attendance file and load existing student IDs"""
        try:
            # Set up directory structure
            base_dir = "their data"
            quiz_dir = os.path.join(base_dir, f"quiz {self.quiz_number}")
            feedback_dir = os.path.join(quiz_dir, "feedback")
            attendance_file = os.path.join(feedback_dir, f"quiz-{self.quiz_number} attendance.txt")

            # Create directories if needed
            os.makedirs(feedback_dir, exist_ok=True)

            # Reset counters
            self.scanned_students = set()
            self.total_scanned = 0

            # Load existing student IDs if file exists
            if os.path.exists(attendance_file):
                with open(attendance_file, 'r', encoding='utf-8') as f:
                    self.scanned_students = {line.strip() for line in f if line.strip()}
                    self.total_scanned = len(self.scanned_students)
            else:
                # Create empty file
                with open(attendance_file, 'w', encoding='utf-8') as f:
                    pass

            self.update_status_count()
            self.status_bar.config(text=f"Quiz {self.quiz_number} ready | Students: {self.total_scanned}")

        except Exception as e:
            messagebox.showerror("Error", f"Could not initialize attendance file: {str(e)}")
            self.status_bar.config(text=f"Error initializing quiz {self.quiz_number}")

    def update_status_count(self):
        """Update status bar with current counts"""
        quiz_text = f"Quiz: {self.quiz_number}" if self.quiz_number else "Quiz: Not set"
        status_text = f"{quiz_text} | Students: {self.total_scanned}"
        if hasattr(self, 'student_id') and self.student_id:
            status_text += f" | Last ID: {self.student_id}"
        self.quiz_info_label.config(text=status_text)
        self.status_bar.config(text=status_text)

    def scan_image(self):
        if self.quiz_number is None:
            messagebox.showwarning("Warning", "Please set quiz number first")
            return

        try:
            self.status_bar.config(text="Scanning at high resolution...")
            self.root.update()

            device_manager = get_device_manager()
            device = connect_device(device_manager, 'scanner-device-ID')

            # Scan at highest possible resolution
            self.original_image = scan_side(device=device)
            self.pillow_image = self.original_image.copy()

            # Initial display at fit-to-window size
            self.scale_factor = 1.0
            self.display_image()

            self.status_bar.config(text=f"Scan completed | Students: {self.total_scanned}")

        except Exception as e:
            self.status_bar.config(text=f"Error: {str(e)}")

    def display_image(self):
        if not self.pillow_image:
            return

        try:
            # Calculate dimensions to fit canvas while maintaining aspect ratio
            canvas_width = self.canvas.winfo_width() - 20
            canvas_height = self.canvas.winfo_height() - 20

            img_width, img_height = self.original_image.size

            # Calculate scale to fit canvas
            width_ratio = canvas_width / img_width
            height_ratio = canvas_height / img_height
            self.scale_factor = min(width_ratio, height_ratio, 1.0)

            # Create high-quality resized version for display
            display_width = int(img_width * self.scale_factor)
            display_height = int(img_height * self.scale_factor)

            # Use LANCZOS (high-quality downsampling)
            display_image = self.original_image.resize(
                (display_width, display_height),
                Image.Resampling.LANCZOS
            )

            # Convert to PhotoImage
            self.tk_image = ImageTk.PhotoImage(display_image)

            # Update canvas
            self.canvas.delete("all")
            self.canvas.create_image(
                canvas_width // 2,
                canvas_height // 2,
                image=self.tk_image,
                anchor=tk.CENTER
            )

            # Update scroll region
            self.canvas.config(scrollregion=(
                0, 0,
                max(canvas_width, display_width),
                max(canvas_height, display_height)
            ))

        except Exception as e:
            self.status_bar.config(text=f"Display error: {str(e)}")

    def adjust_zoom(self, factor):
        if not self.original_image:
            return

        self.scale_factor *= factor
        self.scale_factor = max(0.1, min(self.scale_factor, 4.0))

        # Create high-quality resized version
        img_width, img_height = self.original_image.size
        display_width = int(img_width * self.scale_factor)
        display_height = int(img_height * self.scale_factor)

        display_image = self.original_image.resize(
            (display_width, display_height),
            Image.Resampling.LANCZOS
        )

        # Convert to PhotoImage
        self.tk_image = ImageTk.PhotoImage(display_image)

        # Update canvas
        self.canvas.delete("all")
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        self.canvas.create_image(
            canvas_width // 2,
            canvas_height // 2,
            image=self.tk_image,
            anchor=tk.CENTER
        )

        # Update scroll region
        self.canvas.config(scrollregion=(
            0, 0,
            max(canvas_width, display_width),
            max(canvas_height, display_height)
        ))

    def save_image(self):
        if not self.original_image:
            self.status_bar.config(text="No image to save")
            return

        if self.quiz_number is None:
            messagebox.showwarning("Warning", "Please set quiz number first")
            return

        try:
            # Get student ID
            student_id = simpledialog.askstring(
                "Student ID",
                "Enter student ID:",
                parent=self.root
            )

            if not student_id:
                self.status_bar.config(text="Save cancelled - no ID provided")
                return

            self.student_id = student_id

            # Set up directory structure
            base_dir = "their data"
            quiz_dir = os.path.join(base_dir, f"quiz {self.quiz_number}")
            charts_dir = os.path.join(quiz_dir, "charts")
            feedback_dir = os.path.join(quiz_dir, "feedback")
            attendance_file = os.path.join(feedback_dir, f"quiz-{self.quiz_number} attendance.txt")

            # Create directories if needed
            os.makedirs(charts_dir, exist_ok=True)
            os.makedirs(feedback_dir, exist_ok=True)

            # Only proceed if student ID is new
            if student_id not in self.scanned_students:
                self.scanned_students.add(student_id)
                self.total_scanned += 1

                # Record attendance
                with open(attendance_file, 'a', encoding='utf-8') as f:
                    f.write(f"{student_id}\n")

                self.update_status_count()
            else:
                messagebox.showinfo("Notice", f"Student {student_id} already scanned")
                self.status_bar.config(text=f"Student {student_id} already scanned")

            # Save image
            filename = f"quiz-{self.quiz_number} {student_id}.png"
            file_path = os.path.join(charts_dir, filename)
            self.original_image.save(
                file_path,
                format="PNG",
                compress_level=9,
                dpi=(300, 300)
            )

            messagebox.showinfo(
                "Success",
                f"Quiz saved:\n\n"
                f"Student: {student_id}\n"
                f"Total scanned: {self.total_scanned}\n"
                f"Location: {file_path}"
            )

        except Exception as e:
            self.status_bar.config(text=f"Save error: {str(e)}")
            messagebox.showerror("Error", f"Failed to save: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    root.tk.call('tk', 'scaling', 2.0)  # Adjust for high DPI
    app = HighResScannerApp(root)

    try:
        root.iconbitmap("scanner_icon.ico")
    except:
        pass

    root.mainloop()
