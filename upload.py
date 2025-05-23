import os
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, font
import clipboard
from PIL import Image, ImageTk, ImageFont, ImageDraw
import ctypes


class CuteGradeTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("🌸💖 Cute Grade Upload Tracker 💖🌸")

        # Set DPI awareness for 4K compatibility
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass

        # Set initial size based on screen resolution
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        self.root.geometry(f"{int(screen_width * 0.7)}x{int(screen_height * 0.8)}")

        # Configure main window
        self.root.configure(bg="#fff0f5")
        self.root.minsize(1000, 700)
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Load fonts (with fallback)
        self.load_fonts()

        # Create emoji images for colored emojis
        self.create_emoji_images()

        # UI Setup
        self.setup_ui()

        # Data storage
        self.current_quiz = None
        self.student_data = []
        self.quiz_number = None

    def load_fonts(self):
        # Try to load Snowfall font, fallback to Comic Sans MS
        self.title_font = font.Font(family="Snowfall", size=24)
        self.button_font = font.Font(family="Snowfall", size=22)
        self.label_font = font.Font(family="Snowfall", size=20)
        self.list_font = font.Font(family="Snowfall", size=20)

        # Verify fonts exist
        available_fonts = font.families()
        if "Snowfall" not in available_fonts:
            self.title_font.configure(family="Comic Sans MS")
            self.button_font.configure(family="Comic Sans MS")
            self.label_font.configure(family="Comic Sans MS")
            self.list_font.configure(family="Comic Sans MS")

    def create_emoji_images(self):
        # Create colored emoji images
        emoji_size = (24, 24)
        emojis = {
            "flower": "🌸",
            "heart": "💖",
            "sparkles": "✨",
            "rainbow": "🌈",
            "book": "📚",
            "ribbon": "🎀",
            "seedling": "🌱",
            "clipboard": "📋",
            "up_arrow": "📤",
            "down_arrow": "📥",
            "pencil": "📝",
            "star": "🌟"
        }

        self.emoji_images = {}
        for name, emoji in emojis.items():
            img = Image.new('RGBA', emoji_size, (255, 240, 245, 0))
            draw = ImageDraw.Draw(img)
            try:
                fnt = ImageFont.truetype("seguiemj.ttf", 20)  # Windows emoji font
            except:
                fnt = ImageFont.load_default()
            draw.text((0, 0), emoji, font=fnt, embedded_color=True)
            self.emoji_images[name] = ImageTk.PhotoImage(img)

    def setup_ui(self):
        # Title frame with emojis
        title_frame = tk.Frame(self.root, bg="#fff0f5")
        title_frame.grid(row=0, column=0, pady=(20, 10))

        # Left sparkle emoji
        tk.Label(title_frame, image=self.emoji_images["sparkles"], bg="#fff0f5").pack(side="left")

        # Main title label
        tk.Label(
            title_frame,
            text="Grade Upload Tracker",
            font=self.title_font,
            fg="#ff66b2",
            bg="#fff0f5"
        ).pack(side="left", padx=10)

        # Right rainbow emoji
        tk.Label(title_frame, image=self.emoji_images["rainbow"], bg="#fff0f5").pack(side="left")

        # Quiz number input
        self.quiz_frame = tk.Frame(self.root, bg="#fff0f5")
        self.quiz_frame.grid(row=1, column=0, pady=10)

        # Rounded button with emoji
        self.quiz_button = tk.Canvas(
            self.quiz_frame,
            width=350,
            height=60,
            bg="#fff0f5",
            highlightthickness=0
        )
        self.quiz_button.pack(pady=5)
        self.draw_rounded_rect(
            self.quiz_button,
            5, 5, 345, 55,
            radius=25,
            fill="#ff66b2",
            outline="#ff1493",
            width=3
        )
        self.quiz_button.create_text(
            175, 30,
            text="Enter Quiz Number",
            font=self.button_font,
            fill="white"
        )
        self.quiz_button.create_image(60, 30, image=self.emoji_images["pencil"])
        self.quiz_button.create_image(290, 30, image=self.emoji_images["pencil"])
        self.quiz_button.bind("<Button-1>", lambda e: self.get_quiz_number())

        self.current_quiz_label = tk.Label(
            self.quiz_frame,
            text="No quiz selected yet!",
            font=self.label_font,
            fg="#ff66b2",
            bg="#fff0f5",
            bd=2,
            relief="groove",
            padx=20,
            pady=10
        )
        self.current_quiz_label.pack(pady=10)

        # Student list
        self.student_frame = tk.Frame(self.root, bg="#fff0f5")
        self.student_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.student_frame.grid_rowconfigure(1, weight=1)
        self.student_frame.grid_columnconfigure(0, weight=1)

        # Student label with ribbon emoji
        student_label_frame = tk.Frame(self.student_frame, bg="#fff0f5")
        student_label_frame.grid(row=0, column=0, sticky="w", pady=(0, 5))
        tk.Label(
            student_label_frame,
            text="Students",
            font=self.label_font,
            fg="#ff66b2",
            bg="#fff0f5",
            anchor="w"
        ).pack(side="left")
        tk.Label(
            student_label_frame,
            image=self.emoji_images["ribbon"],
            bg="#fff0f5"
        ).pack(side="left", padx=5)

        # Treeview for student list
        self.tree = ttk.Treeview(
            self.student_frame,
            columns=("ID", "Name", "Grade", "Status"),
            show="headings",
            selectmode="extended"
        )

        # Style configuration
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Treeview",
                        background="#fff0f5",
                        foreground="#ff66b2",
                        rowheight=35,
                        fieldbackground="#fff0f5",
                        font=self.list_font,
                        borderwidth=0
                        )
        style.configure("Treeview.Heading",
                        font=self.button_font,
                        background="#ffb6c1",
                        foreground="white",
                        relief="flat"
                        )
        style.map("Treeview",
                  background=[("selected", "#ff66b2")],
                  foreground=[("selected", "white")]
                  )

        # Configure columns with emoji text
        self.tree.heading("ID", text="ID 🌟")
        self.tree.heading("Name", text="Name 💖")
        self.tree.heading("Grade", text="Grade 📚")
        self.tree.heading("Status", text="Status 🌸")

        self.tree.column("ID", width=120, anchor="center")
        self.tree.column("Name", width=300, anchor="w")
        self.tree.column("Grade", width=120, anchor="center")
        self.tree.column("Status", width=180, anchor="center")

        self.tree.grid(row=1, column=0, sticky="nsew")

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.student_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Button frame
        self.button_frame = tk.Frame(self.root, bg="#fff0f5")
        self.button_frame.grid(row=3, column=0, pady=20)

        # Upload button
        self.upload_btn_canvas = tk.Canvas(
            self.button_frame,
            width=350,
            height=60,
            bg="#fff0f5",
            highlightthickness=0
        )
        self.upload_btn_canvas.grid(row=0, column=0, padx=10)
        self.draw_rounded_rect(
            self.upload_btn_canvas,
            5, 5, 345, 55,
            radius=25,
            fill="#ff66b2",
            outline="#ff1493",
            width=3
        )
        self.upload_btn_canvas.create_text(
            175, 30,
            text="Mark as Uploaded",
            font=self.button_font,
            fill="white"
        )
        self.upload_btn_canvas.create_image(60, 30, image=self.emoji_images["up_arrow"])
        self.upload_btn_canvas.create_image(290, 30, image=self.emoji_images["up_arrow"])
        self.upload_btn_canvas.bind("<Button-1>", lambda e: self.mark_as_uploaded())

        # Unupload button
        self.unupload_btn_canvas = tk.Canvas(
            self.button_frame,
            width=350,
            height=60,
            bg="#fff0f5",
            highlightthickness=0
        )
        self.unupload_btn_canvas.grid(row=0, column=1, padx=10)
        self.draw_rounded_rect(
            self.unupload_btn_canvas,
            5, 5, 345, 55,
            radius=25,
            fill="#ffb6c1",
            outline="#ff69b4",
            width=3
        )
        self.unupload_btn_canvas.create_text(
            175, 30,
            text="Mark as Not Uploaded",
            font=self.button_font,
            fill="white"
        )
        self.unupload_btn_canvas.create_image(60, 30, image=self.emoji_images["down_arrow"])
        self.unupload_btn_canvas.create_image(290, 30, image=self.emoji_images["down_arrow"])
        self.unupload_btn_canvas.bind("<Button-1>", lambda e: self.mark_as_not_uploaded())

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready to track your grades!")
        status_frame = tk.Frame(self.root, bg="#fff0f5")
        status_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=10)

        # Status bar emojis
        tk.Label(status_frame, image=self.emoji_images["flower"], bg="#fff0f5").pack(side="left", padx=5)
        tk.Label(
            status_frame,
            textvariable=self.status_var,
            font=self.label_font,
            fg="#ff66b2",
            bg="#fff0f5",
            bd=1,
            relief="sunken",
            padx=10,
            pady=5
        ).pack(side="left", fill="x", expand=True)
        tk.Label(status_frame, image=self.emoji_images["heart"], bg="#fff0f5").pack(side="right", padx=5)

        # Right-click menu
        self.context_menu = tk.Menu(self.root, tearoff=0, font=self.label_font)
        self.context_menu.configure(
            bg="#fff0f5",
            fg="#ff66b2",
            activebackground="#ffb6c1",
            activeforeground="white",
            bd=0
        )
        self.context_menu.add_command(
            label="Copy ID to Clipboard",
            command=self.copy_id_to_clipboard
        )

        # Bind right-click event
        self.tree.bind("<Button-3>", self.show_context_menu)

    def draw_rounded_rect(self, canvas, x1, y1, x2, y2, radius=25, **kwargs):
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
            x1 + radius, y1
        ]
        return canvas.create_polygon(points, **kwargs, smooth=True)

    def get_quiz_number(self):
        quiz_num = simpledialog.askinteger(
            "Enter Quiz Number",
            "Please enter the quiz number (1-100):",
            parent=self.root,
            minvalue=1,
            maxvalue=100
        )

        if quiz_num is not None:
            self.quiz_number = quiz_num
            self.current_quiz_label.config(text=f"Quiz {self.quiz_number}")
            tk.Label(
                self.quiz_frame,
                image=self.emoji_images["book"],
                bg="#fff0f5"
            ).pack(side="right", anchor="ne")
            self.load_students()

    def load_students(self):
        if not self.quiz_number:
            return

        filename = f"quiz-{self.quiz_number} students.csv"
        directory = f"their data/quiz {self.quiz_number}/feedback"
        filepath = os.path.join(directory, filename)

        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)

        try:
            # Check if file exists
            if not os.path.exists(filepath):
                # Create a default empty file if it doesn't exist
                default_data = pd.DataFrame(columns=['id', 'name', 'grade'])
                default_data.to_csv(filepath, index=False)
                messagebox.showinfo(
                    "New Quiz Created",
                    f"Created a new empty file for Quiz {self.quiz_number}.\n\nPlease add student data."
                )
                self.student_data = []
                self.update_student_list()
                return

            df = pd.read_csv(filepath)

            # Check if 'uploaded' column exists, if not create it
            if 'uploaded' not in df.columns:
                df['uploaded'] = False


            # Sort by ID in descending order
            df = df.sort_values('id')

            self.student_data = df.to_dict('records')
            self.update_student_list()

            self.status_var.set(f"Loaded {len(self.student_data)} students from Quiz {self.quiz_number}")

        except Exception as e:
            messagebox.showerror("Error", f"Could not load file: {str(e)}")

    def update_student_list(self):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add new items
        for student in self.student_data:
            status_emoji = "🌸" if student.get('uploaded', False) else "🌱"
            status_text = f"{status_emoji} Uploaded" if student.get('uploaded',
                                                                    False) else f"{status_emoji} Not Uploaded"

            self.tree.insert("", "end",
                             values=(
                                 student['id'],
                                 student['name'],
                                 student['total'],
                                 status_text
                             ),
                             tags=("uploaded" if student.get('uploaded', False) else "not_uploaded")
                             )

        # Configure tags for colors
        self.tree.tag_configure("uploaded", background="#ffb6c1", foreground="#8b0062")
        self.tree.tag_configure("not_uploaded", background="#fff0f5", foreground="#ff66b2")

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def copy_id_to_clipboard(self):
        selected_items = self.tree.selection()
        if selected_items:
            item = self.tree.item(selected_items[0])
            student_id = item['values'][0]
            clipboard.copy(str(student_id))
            self.status_var.set(f"Copied ID {student_id} to clipboard!")
            self.root.after(3000, lambda: self.status_var.set("Ready to track your grades!"))

    def mark_as_uploaded(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo(
                "Attention",
                "Please select students to mark as uploaded."
            )
            return

        for item in selected_items:
            item_data = self.tree.item(item)
            student_id = item_data['values'][0]

            # Update in our data
            for student in self.student_data:
                if student['id'] == student_id:
                    student['uploaded'] = True

            # Update the display
            self.tree.item(item,
                           values=(
                               item_data['values'][0],
                               item_data['values'][1],
                               item_data['values'][2],
                               "🌸 Uploaded"
                           ),
                           tags="uploaded"
                           )

        self.save_current_data()
        self.status_var.set("Marked selected students as uploaded!")
        self.root.after(3000, lambda: self.status_var.set("Ready to track your grades!"))

    def mark_as_not_uploaded(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo(
                "Attention",
                "Please select students to mark as not uploaded."
            )
            return

        for item in selected_items:
            item_data = self.tree.item(item)
            student_id = item_data['values'][0]

            # Update in our data
            for student in self.student_data:
                if student['id'] == student_id:
                    student['uploaded'] = False

            # Update the display
            self.tree.item(item,
                           values=(
                               item_data['values'][0],
                               item_data['values'][1],
                               item_data['values'][2],
                               "🌱 Not Uploaded"
                           ),
                           tags="not_uploaded"
                           )

        self.save_current_data()
        self.status_var.set("Marked selected students as not uploaded!")
        self.root.after(3000, lambda: self.status_var.set("Ready to track your grades!"))

    def save_current_data(self):
        if not self.quiz_number:
            return

        filename = f"quiz-{self.quiz_number} students.csv"
        directory = f"their data/quiz {self.quiz_number}/feedback"
        filepath = os.path.join(directory, filename)

        df = pd.DataFrame(self.student_data)
        # Maintain descending order when saving
        df = df.sort_values('id', ascending=False)
        df.to_csv(filepath, index=False)

    def on_closing(self):
        self.save_current_data()
        messagebox.showinfo(
            "Goodbye!",
            "All your grade data has been saved safely.\n\nSee you next time!"
        )
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = CuteGradeTracker(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
