import tkinter as tk
import logging
from tkinter import messagebox
from logging_config import setup_logging
from database import init_db
from app import FileOpenerApp

def start_tkinter():
    try:
        setup_logging()
        init_db()
        root = tk.Tk()
        app = FileOpenerApp(root)
        root.mainloop()
    except Exception as e:
        logging.error(f"Failed to run main application: {e}")
        messagebox.showerror("Error", f"Failed to run main application: {e}")

if __name__ == '__main__':
    start_tkinter()
