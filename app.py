import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import json
import os
import subprocess
import logging
import tempfile
import shutil
import fitz  # PyMuPDF
import sqlite3
from email_utils import send_email
from database import add_config, get_config, add_user, get_users, add_audit_question, get_audit_questions, delete_audit_question, schedule_audit, get_audit_schedules
from config import HEADER_IMAGE_PATH, ICON_PATH, WINDOW_BG_COLOR, BUTTON_FONT, LABEL_FONT, CONFIG_DB_PATH

class FileOpenerApp:
    def __init__(self, root):
        try:
            self.root = root
            self.root.title('TMMTN Standardized Work Display')
            self.root.state('zoomed')
            self.root.iconbitmap(ICON_PATH)
            self.root.configure(background=WINDOW_BG_COLOR)
            
            self.keyboard_window = None
            self.changing_path = False
            self.audit_mode = False
            self.current_auditor = ""
            
            self.screen_width = self.root.winfo_screenwidth()
            self.screen_height = self.root.winfo_screenheight()
            self.base_width = 1920
            self.base_height = 1080
            self.scale_factor_width = self.screen_width / self.base_width
            self.scale_factor_height = self.screen_height / self.base_height

            self.button_font = ('Calibri', int(14 * self.scale_factor_height))
            self.label_font = ('Calibri', int(24 * self.scale_factor_height), 'bold')

            self.load_config()
            self.load_users()
            self.create_menu()
            self.create_header()
            self.create_notebook()
        except Exception as e:
            logging.critical(f"Initialization failed: {e}")
            self.send_error_report(str(e))
            messagebox.showerror("Error", f"Initialization failed: {e}")

    def load_config(self):
        try:
            config_data = get_config('tabs')
            if config_data:
                self.config = {"tabs": json.loads(config_data)}
                logging.info("Configuration loaded successfully")
            else:
                raise ValueError("No configuration data found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {e}")
            logging.error(f"Failed to load configuration: {e}")
            self.send_error_report(str(e))
            self.config = {"tabs": []}

    def load_users(self):
        try:
            self.users = get_users()
            logging.info("User data loaded successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load user data: {e}")
            logging.error(f"Failed to load user data: {e}")
            self.send_error_report(str(e))
            self.users = []

    def save_config(self):
        try:
            add_config('tabs', json.dumps(self.config["tabs"]))
            logging.info("Configuration saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
            logging.error(f"Failed to save configuration: {e}")
            self.send_error_report(str(e))

    def create_menu(self):
        try:
            logging.info("Creating menu")
            self.menubar = tk.Menu(self.root)
            self.root.config(menu=self.menubar)

            settings_menu = tk.Menu(self.menubar, tearoff=0)
            self.menubar.add_cascade(label="Settings", menu=settings_menu)
            settings_menu.add_command(label="Configure Paths", command=self.authenticate_user)
            settings_menu.add_command(label="Audit Mode", command=self.authenticate_audit_user)
            settings_menu.add_command(label="Manage Questions", command=self.create_question_manager)
            settings_menu.add_command(label="Schedule Audit", command=self.create_schedule_audit_ui)
            settings_menu.add_command(label="View Notifications", command=self.create_view_notifications_ui)
            settings_menu.add_separator()
            settings_menu.add_command(label="Exit", command=self.root.quit)
        except Exception as e:
            logging.error(f"Failed to create menu: {e}")
            self.send_error_report(str(e))

    def authenticate_user(self):
        try:
            logging.info("Authenticating user for configuration")
            self.auth_window = tk.Toplevel(self.root)
            self.auth_window.title("User Authentication")
            self.auth_window.iconbitmap(ICON_PATH)
            self.auth_window.geometry(f"{int(400 * self.scale_factor_width)}x{int(300 * self.scale_factor_height)}")
            self.auth_window.attributes("-topmost", True)

            container = ttk.Frame(self.auth_window)
            container.pack(expand=True, fill='both', padx=10, pady=10)

            emp_num_label = ttk.Label(container, text="Employee Number:", font=self.label_font)
            emp_num_label.pack(pady=10)
            self.emp_num_entry = ttk.Entry(container, font=self.button_font)
            self.emp_num_entry.pack(pady=10)
            self.emp_num_entry.bind("<FocusIn>", lambda event: self.show_keypad(self.emp_num_entry))

            pin_label = ttk.Label(container, text="Pin:", font=self.label_font)
            pin_label.pack(pady=10)
            self.pin_entry = ttk.Entry(container, show='*', font=self.button_font)
            self.pin_entry.pack(pady=10)
            self.pin_entry.bind("<FocusIn>", lambda event: self.show_keypad(self.pin_entry))

            login_button = ttk.Button(container, text="Login", command=self.check_credentials, style='Custom.TButton')
            login_button.pack(pady=0)
        except Exception as e:
            logging.error(f"Failed to authenticate user: {e}")
            self.send_error_report(str(e))
            messagebox.showerror("Error", f"Failed to authenticate user: {e}")

    def authenticate_audit_user(self):
        try:
            logging.info("Authenticating user for audit mode")
            self.auth_window = tk.Toplevel(self.root)
            self.auth_window.title("User Authentication")
            self.auth_window.iconbitmap(ICON_PATH)
            self.auth_window.geometry(f"{int(400 * self.scale_factor_width)}x{int(300 * self.scale_factor_height)}")
            self.auth_window.attributes("-topmost", True)

            container = ttk.Frame(self.auth_window)
            container.pack(expand=True, fill='both', padx=10, pady=10)

            emp_num_label = ttk.Label(container, text="Employee Number:", font=self.label_font)
            emp_num_label.pack(pady=10)
            self.emp_num_entry = ttk.Entry(container, font=self.button_font)
            self.emp_num_entry.pack(pady=10)
            self.emp_num_entry.bind("<FocusIn>", lambda event: self.show_keypad(self.emp_num_entry))

            pin_label = ttk.Label(container, text="Pin:", font=self.label_font)
            pin_label.pack(pady=10)
            self.pin_entry = ttk.Entry(container, show='*', font=self.button_font)
            self.pin_entry.pack(pady=10)
            self.pin_entry.bind("<FocusIn>", lambda event: self.show_keypad(self.pin_entry))

            login_button = ttk.Button(container, text="Login", command=self.check_audit_credentials, style='Custom.TButton')
            login_button.pack(pady=0)
        except Exception as e:
            logging.error(f"Failed to authenticate audit user: {e}")
            self.send_error_report(str(e))
            messagebox.showerror("Error", f"Failed to authenticate audit user: {e}")

    def show_keypad(self, entry):
        try:
            logging.info("Showing keypad")
            if self.keyboard_window and self.keyboard_window.winfo_exists():
                self.keyboard_window.lift()
                self.keyboard_window.focus_force()
                return

            self.keyboard_window = tk.Toplevel(self.root)
            self.keyboard_window.title("On-Screen Keypad")
            self.keyboard_window.iconbitmap(ICON_PATH)
            self.keyboard_window.geometry(f"{int(300 * self.scale_factor_width)}x{int(400 * self.scale_factor_height)}")
            self.keyboard_window.protocol("WM_DELETE_WINDOW", self.hide_keyboard)
            self.keyboard_window.attributes("-topmost", True)

            keypad_frame = ttk.Frame(self.keyboard_window)
            keypad_frame.pack(expand=True, fill='both', padx=10, pady=10)

            buttons = [
                '1', '2', '3', 
                '4', '5', '6', 
                '7', '8', '9', 
                '0', 'Backspace', 'Enter'
            ]
            row_val = 0
            col_val = 0

            for button in buttons:
                command = lambda b=button: self.on_key_press(b, entry)
                ttk.Button(keypad_frame, text=button, command=command, width=10).grid(row=row_val, column=col_val, sticky='nsew', padx=5, pady=5)
                col_val += 1
                if col_val > 2:
                    col_val = 0
                    row_val += 1

            for i in range(3):
                keypad_frame.grid_columnconfigure(i, weight=1)
            for i in range(4):
                keypad_frame.grid_rowconfigure(i, weight=1)
        except Exception as e:
            logging.error(f"Failed to show keypad: {e}")
            self.send_error_report(str(e))
            messagebox.showerror("Error", f"Failed to show keypad: {e}")

    def hide_keyboard(self):
        try:
            logging.info("Hiding keypad")
            if self.keyboard_window:
                self.keyboard_window.destroy()
        except Exception as e:
            logging.error(f"Failed to hide keypad: {e}")
            self.send_error_report(str(e))
            messagebox.showerror("Error", f"Failed to hide keypad: {e}")

    def on_key_press(self, key, entry):
        try:
            logging.info(f"Key pressed: {key}")
            if key == "Backspace":
                current_text = entry.get()
                entry.delete(len(current_text)-1, tk.END)
            elif key == "Enter":
                self.hide_keyboard()
                entry.tk_focusNext().focus()
            else:
                entry.insert(tk.END, key)
        except Exception as e:
            logging.error(f"Failed to handle key press: {e}")
            self.send_error_report(str(e))
            messagebox.showerror("Error", f"Failed to handle key press: {e}")

    def check_credentials(self):
        try:
            emp_num = self.emp_num_entry.get()
            pin = self.pin_entry.get()
            logging.info(f"Checking credentials for emp_num: {emp_num}")
            if self.verify_credentials(emp_num, pin):
                self.current_auditor = emp_num
                self.auth_window.destroy()
                self.enable_path_change()
            else:
                messagebox.showerror("Login Failed", "Invalid credentials!")
        except Exception as e:
            logging.error(f"Failed to check credentials: {e}")
            self.send_error_report(str(e))
            messagebox.showerror("Error", f"Failed to check credentials: {e}")

    def check_audit_credentials(self):
        try:
            emp_num = self.emp_num_entry.get()
            pin = self.pin_entry.get()
            logging.info(f"Checking audit credentials for emp_num: {emp_num}")
            if self.verify_credentials(emp_num, pin):
                self.current_auditor = emp_num
                self.auth_window.destroy()
                self.audit_mode = True
                messagebox.showinfo("Audit Mode", "Audit mode activated.")
            else:
                messagebox.showerror("Login Failed", "Invalid credentials!")
        except Exception as e:
            logging.error(f"Failed to check audit credentials: {e}")
            self.send_error_report(str(e))
            messagebox.showerror("Error", f"Failed to check audit credentials: {e}")

    def verify_credentials(self, emp_num, pin):
        try:
            logging.info(f"Verifying credentials for emp_num: {emp_num}")
            for user in self.users:
                if user[1] == emp_num and user[2] == pin:
                    return True
            return False
        except Exception as e:
            logging.error(f"Failed to verify credentials: {e}")
            self.send_error_report(str(e))
            messagebox.showerror("Error", f"Failed to verify credentials: {e}")

    def enable_path_change(self):
        try:
            logging.info("Enabling path change")
            messagebox.showinfo("Path Configuration", "Select a button to change its file path.")
            self.changing_path = True
        except Exception as e:
            logging.error(f"Failed to enable path change: {e}")
            self.send_error_report(str(e))
            messagebox.showerror("Error", f"Failed to enable path change: {e}")

    def configure_path(self, button, button_info):
        try:
            logging.info("Configuring path")
            if self.changing_path:
                new_path = filedialog.askopenfilename(title=f"Select new file for {button_info['text']}")
                if new_path:
                    button_info["path"] = new_path
                    self.save_config()
                    button.config(command=lambda: self.open_file(button_info["path"], 'pdf' if new_path.endswith('.pdf') else 'video'))
                    messagebox.showinfo("Path Configuration", f"Path for {button_info['text']} has been updated.")
                self.changing_path = False
        except Exception as e:
            logging.error(f"Failed to configure path: {e}")
            self.send_error_report(str(e))
            messagebox.showerror("Error", f"Failed to configure path: {e}")

    def create_header(self):
        try:
            logging.info("Creating header")
            header_image = Image.open(HEADER_IMAGE_PATH)
            header_image = header_image.resize((int(self.screen_width / 6), int(self.screen_height / 8)))
            header_photo = ImageTk.PhotoImage(header_image)
            header_label = ttk.Label(self.root, image=header_photo, background=WINDOW_BG_COLOR)
            header_label.image = header_photo
            header_label.pack(pady=5)
        except Exception as e:
            logging.error(f"Failed to create header: {e}")
            self.send_error_report(str(e))
            messagebox.showerror("Error", f"Failed to create header: {e}")

    def create_notebook(self):
        try:
            notebook_style = ttk.Style()
            notebook_style.configure('Custom.TNotebook.Tab', padding=[20, 10], font=BUTTON_FONT)
            notebook = ttk.Notebook(self.root, style='Custom.TNotebook')
            notebook.pack(expand=1, fill='both')
            
            custom_style = ttk.Style()
            custom_style.configure('Custom.TFrame', background=WINDOW_BG_COLOR)
            custom_style.configure('CustomLabel.TLabel', background=WINDOW_BG_COLOR)
            custom_style.configure('Custom.TButton', font=BUTTON_FONT, padding=10)
            
            for tab in self.config["tabs"]:
                frame = ttk.Frame(notebook, style='Custom.TFrame')
                notebook.add(frame, text=tab["label"])
                for group in tab["groups"]:
                    group_frame = self.create_button_group(frame, group["label"], group["buttons"])
                    group_frame.pack(side=tk.LEFT, padx=20, pady=20, anchor='nw')
        except Exception as e:
            logging.error(f"Failed to create notebook: {e}")
            self.send_error_report(str(e))
            messagebox.showerror("Error", f"Failed to create notebook: {e}")

    def create_button_group(self, master, label_text, buttons):
        try:
            logging.info(f"Creating button group for label: {label_text}")
            group_frame = ttk.Frame(master=master, style='Custom.TFrame')
            label = ttk.Label(group_frame, text=label_text, font=self.label_font, style='CustomLabel.TLabel')
            label.pack(side=tk.TOP, pady=5)
            
            for button_info in buttons:
                button = self.create_button(group_frame, button_info["text"], None)
                button.bind("<Button-1>", lambda e, btn=button, info=button_info: self.configure_path(btn, info) if self.changing_path else self.open_file(info["path"], 'pdf' if info["path"].endswith('.pdf') else 'video'))
            
            return group_frame
        except Exception as e:
            logging.error(f"Failed to create button group: {e}")
            self.send_error_report(str(e))
            messagebox.showerror("Error", f"Failed to create button group: {e}")

    def create_button(self, master, text, command=None, tooltip_text=None, style='Custom.TButton', width=20):
        try:
            logging.info(f"Creating button with text: {text}")
            button = ttk.Button(master=master, text=text, style=style, width=width)
            button.pack(side=tk.TOP, pady=5)
            return button
        except Exception as e:
            logging.error(f"Failed to create button: {e}")
            self.send_error_report(str(e))
            messagebox.showerror("Error", f"Failed to create button: {e}")

    def open_file(self, file_path, file_type='pdf'):
        try:
            logging.info(f"Opening file: {file_path} as {file_type}")
            if file_type == 'pdf':
                self.open_pdf(file_path)
            elif file_type == 'video':
                self.open_video(file_path)
            self.audit_mode = False
        except Exception as e:
            logging.error(f"Failed to open file: {e}")
            self.send_error_report(str(e))
            messagebox.showerror("Error", f"Failed to open file: {e}")

    def open_pdf(self, file_path):
        try:
            logging.info(f"Opening PDF: {file_path}")
            if self.audit_mode:
                try:
                    temp_dir = tempfile.mkdtemp()
                    temp_file_path = os.path.join(temp_dir, os.path.basename(file_path))
                    shutil.copyfile(file_path, temp_file_path)
                    
                    doc = fitz.open(temp_file_path)
                    self.display_pdf(doc)
                except PermissionError:
                    messagebox.showerror("Error", "Access is denied. Permission error.")
                    logging.error("Access is denied. Permission error.")
                except OSError as e:
                    messagebox.showerror("Error", f"Failed to open PDF: {e}")
                    logging.error(f"Failed to open PDF: {e}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to open PDF: {e}")
                    logging.error(f"Failed to open PDF: {e}")
            else:
                try:
                    os.startfile(file_path)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to open PDF: {e}")
                    logging.error(f"Failed to open PDF: {e}")
        except Exception as e:
            logging.error(f"Failed to open PDF: {e}")
            self.send_error_report(str(e))
            messagebox.showerror("Error", f"Failed to open PDF: {e}")

    def display_pdf(self, doc):
        try:
            logging.info("Displaying PDF")
            pdf_window = tk.Toplevel(self.root)
            pdf_window.title("PDF Viewer")
            pdf_window.iconbitmap(ICON_PATH)
            pdf_window.state('zoomed')
            pdf_window.attributes("-topmost", True)

            main_frame = ttk.Frame(pdf_window)
            main_frame.grid(row=0, column=0, sticky="nsew")

            pdf_frame = ttk.Frame(main_frame)
            pdf_frame.grid(row=0, column=0, sticky="nsew")

            audit_frame = ttk.Frame(main_frame)
            audit_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

            canvas = tk.Canvas(pdf_frame, bg='white')
            scrollbar = ttk.Scrollbar(pdf_frame, orient=tk.VERTICAL, command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(
                    scrollregion=canvas.bbox("all")
                )
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                photo = ImageTk.PhotoImage(img)

                label = ttk.Label(scrollable_frame, image=photo, background='white')
                label.image = photo
                label.pack(pady=10, padx=10)

            if self.audit_mode:
                self.create_audit_form(audit_frame)

            pdf_window.grid_columnconfigure(0, weight=1)
            pdf_window.grid_rowconfigure(0, weight=1)
            main_frame.grid_columnconfigure(0, weight=3)
            main_frame.grid_columnconfigure(1, weight=1)
            main_frame.grid_rowconfigure(0, weight=1)
        except Exception as e:
            logging.error(f"Failed to display PDF: {e}")
            self.send_error_report(str(e))
            messagebox.showerror("Error", f"Failed to display PDF: {e}")

    def create_audit_form(self, audit_frame):
        try:
            logging.info("Creating dynamic audit form")
            
            ttk.Label(audit_frame, text="Standardized Work Audit Form", font=self.label_font).pack(pady=10)
            ttk.Label(audit_frame, text=f"Auditor: {self.current_auditor}", font=self.button_font).pack(pady=5)
            ttk.Label(audit_frame, text="Team Member:", font=self.button_font).pack(pady=5)
            team_member_entry = ttk.Entry(audit_frame, font=self.button_font)
            team_member_entry.pack(pady=5)

            questions = get_audit_questions()
            response_entries = []

            for question in questions:
                question_id, question_text = question
                frame = ttk.Frame(audit_frame)
                frame.pack(fill='x', pady=5)
                ttk.Label(frame, text=question_text, font=self.button_font).pack(side='left', padx=5)
                response_combobox = ttk.Combobox(frame, values=["O", "X"], state="readonly", font=self.button_font, width=5)
                response_combobox.pack(side='left', padx=5)
                response_entries.append((question_id, response_combobox))

            ttk.Label(audit_frame, text="Comments:", font=self.button_font).pack(pady=5)
            comments_text = tk.Text(audit_frame, font=self.button_font, height=10, width=40)
            comments_text.pack(pady=5)

            submit_button = ttk.Button(audit_frame, text="Submit Audit", style='Custom.TButton', 
                                       command=lambda: self.submit_audit(self.current_auditor, team_member_entry.get(), response_entries, comments_text.get("1.0", tk.END)))
            submit_button.pack(pady=10)
        except Exception as e:
            logging.error(f"Failed to create audit form: {e}")
            self.send_error_report(str(e))
            messagebox.showerror("Error", f"Failed to create audit form: {e}")

    def submit_audit(self, auditor_name, team_member, responses, comments):
        try:
            logging.info(f"Submitting audit: Auditor={auditor_name}, Team Member={team_member}")
            conn = sqlite3.connect(CONFIG_DB_PATH)
            cursor = conn.cursor()

            for question_id, response_combobox in responses:
                response = response_combobox.get()
                cursor.execute('INSERT INTO audit_results (auditor, team_member, question_id, response, comments) VALUES (?, ?, ?, ?, ?)', 
                               (auditor_name, team_member, question_id, response, comments))

            conn.commit()
            conn.close()
            
            messagebox.showinfo("Audit Submitted", "Audit has been submitted successfully.")
            logging.info(f"Audit submitted: Auditor={auditor_name}, Team Member={team_member}")
            self.audit_mode = False
        except Exception as e:
            logging.error(f"Failed to submit audit: {e}")
            self.send_error_report(str(e))
            messagebox.showerror("Error", f"Failed to submit audit: {e}")

    def open_video(self, file_path):
        try:
            logging.info(f"Opening video file: {file_path}")
            try:
                subprocess.Popen([file_path], shell=True)
            except FileNotFoundError:
                messagebox.showerror("Error", f"File not found: {file_path}")
                logging.error(f"File not found: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")
                logging.error(f"An error occurred: {e}")
        except Exception as e:
            logging.error(f"Failed to open video: {e}")
            self.send_error_report(str(e))
            messagebox.showerror("Error", f"Failed to open video: {e}")

    def create_question_manager(self):
        try:
            logging.info("Creating question manager")
            question_window = tk.Toplevel(self.root)
            question_window.title("Manage Audit Questions")
            question_window.iconbitmap(ICON_PATH)
            question_window.geometry(f"{int(500 * self.scale_factor_width)}x{int(400 * self.scale_factor_height)}")

            ttk.Label(question_window, text="Add New Question:", font=self.label_font).pack(pady=10)
            new_question_entry = ttk.Entry(question_window, font=self.button_font)
            new_question_entry.pack(pady=5)

            add_button = ttk.Button(question_window, text="Add Question", style='Custom.TButton',
                                    command=lambda: self.add_new_question(new_question_entry.get(), questions_frame))
            add_button.pack(pady=5)

            ttk.Label(question_window, text="Existing Questions:", font=self.label_font).pack(pady=10)
            questions_frame = ttk.Frame(question_window)
            questions_frame.pack(pady=10)

            self.populate_questions(questions_frame)
        except Exception as e:
            logging.error(f"Failed to create question manager: {e}")
            self.send_error_report(str(e))
            messagebox.showerror("Error", f"Failed to create question manager: {e}")

    def add_new_question(self, question_text, frame):
        try:
            if question_text:
                add_audit_question(question_text)
                messagebox.showinfo("Success", "Question added successfully.")
                self.refresh_questions(frame)
            else:
                messagebox.showerror("Error", "Question text cannot be empty.")
        except Exception as e:
            logging.error(f"Failed to add new question: {e}")
            self.send_error_report(str(e))
            messagebox.showerror("Error", f"Failed to add new question: {e}")

    def populate_questions(self, frame):
        try:
            logging.info("Populating questions")
            questions = get_audit_questions()
            for question_id, question_text in questions:
                question_label = ttk.Label(frame, text=question_text, font=self.button_font)
                question_label.pack(pady=5, anchor='w')
                delete_button = ttk.Button(frame, text="Delete", style='Custom.TButton',
                                           command=lambda qid=question_id: self.delete_question(qid, frame))
                delete_button.pack(pady=5)
        except Exception as e:
            logging.error(f"Failed to populate questions: {e}")
            self.send_error_report(str(e))
            messagebox.showerror("Error", f"Failed to populate questions: {e}")

    def delete_question(self, question_id, frame):
        try:
            logging.info(f"Deleting question ID: {question_id}")
            delete_audit_question(question_id)
            messagebox.showinfo("Success", "Question deleted successfully.")
            self.refresh_questions(frame)
        except Exception as e:
            logging.error(f"Failed to delete question: {e}")
            self.send_error_report(str(e))
            messagebox.showerror("Error", f"Failed to delete question: {e}")

    def refresh_questions(self, frame):
        try:
            logging.info("Refreshing questions")
            for widget in frame.winfo_children():
                widget.destroy()
            self.populate_questions(frame)
        except Exception as e:
            logging.error(f"Failed to refresh questions: {e}")
            self.send_error_report(str(e))
            messagebox.showerror("Error", f"Failed to refresh questions: {e}")

    def create_schedule_audit_ui(self):
        try:
            logging.info("Creating schedule audit UI")
            schedule_window = tk.Toplevel(self.root)
            schedule_window.title("Schedule Audit")
            schedule_window.iconbitmap(ICON_PATH)
            schedule_window.geometry(f"{int(500 * self.scale_factor_width)}x{int(400 * self.scale_factor_height)}")

            ttk.Label(schedule_window, text="Auditor ID:", font=self.label_font).pack(pady=10)
            auditor_id_entry = ttk.Entry(schedule_window, font=self.button_font)
            auditor_id_entry.pack(pady=5)

            ttk.Label(schedule_window, text="Audit Date (YYYY-MM-DD):", font=self.label_font).pack(pady=10)
            audit_date_entry = ttk.Entry(schedule_window, font=self.button_font)
            audit_date_entry.pack(pady=5)

            ttk.Label(schedule_window, text="Audit Time (HH:MM):", font=self.label_font).pack(pady=10)
            audit_time_entry = ttk.Entry(schedule_window, font=self.button_font)
            audit_time_entry.pack(pady=5)

            ttk.Label(schedule_window, text="Description:", font=self.label_font).pack(pady=10)
            description_entry = tk.Text(schedule_window, font=self.button_font, height=4, width=40)
            description_entry.pack(pady=5)

            schedule_button = ttk.Button(schedule_window, text="Schedule Audit", style='Custom.TButton',
                                         command=lambda: self.schedule_audit(auditor_id_entry.get(), audit_date_entry.get(), audit_time_entry.get(), description_entry.get("1.0", tk.END)))
            schedule_button.pack(pady=10)
        except Exception as e:
            logging.error(f"Failed to create schedule audit UI: {e}")
            self.send_error_report(str(e))
            messagebox.showerror("Error", f"Failed to create schedule audit UI: {e}")

    def schedule_audit(self, auditor_id, audit_date, audit_time, description):
        try:
            schedule_audit(int(auditor_id), audit_date, audit_time, description.strip())
            messagebox.showinfo("Success", "Audit scheduled successfully.")
        except Exception as e:
            logging.error(f"Failed to schedule audit: {e}")
            self.send_error_report(str(e))
            messagebox.showerror("Error", f"Failed to schedule audit: {e}")

    def create_view_notifications_ui(self):
        try:
            logging.info("Creating view notifications UI")
            notification_window = tk.Toplevel(self.root)
            notification_window.title("View Notifications")
            notification_window.iconbitmap(ICON_PATH)
            notification_window.geometry(f"{int(500 * self.scale_factor_width)}x{int(400 * self.scale_factor_height)}")

            notifications = get_audit_schedules()

            for schedule in notifications:
                ttk.Label(notification_window, text=f"Audit ID: {schedule[0]}\nAuditor ID: {schedule[1]}\nDate: {schedule[2]}\nTime: {schedule[3]}\nDescription: {schedule[4]}",
                          font=self.button_font, justify=tk.LEFT, wraplength=int(400 * self.scale_factor_width)).pack(pady=5, anchor='w')
        except Exception as e:
            logging.error(f"Failed to create view notifications UI: {e}")
            self.send_error_report(str(e))
            messagebox.showerror("Error", f"Failed to create view notifications UI: {e}")

    def send_error_report(self, error_message):
        try:
            sender_email = "your_email@example.com"
            receiver_email = "admin@example.com"
            subject = "Error Report"
            body = f"An error occurred:\n\n{error_message}"

            send_email(sender_email, receiver_email, subject, body, 'smtp.example.com', 587, sender_email, "your_password")
            logging.info("Error report sent successfully.")
        except Exception as e:
            logging.error(f"Failed to send error report: {e}")
