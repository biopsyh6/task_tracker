import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta

from init_db import init_db
from priority_calculator import PriorityCalculator
from gui_windows import GUIWindows
from gui_tabs import GUITabs


class SmartAssistantGUI:
    def __init__(self, root):
        self.root = root
        self.setup_main_window()
        
        self.conn = sqlite3.connect('assistant.db')
        init_db(self.conn)
        
        self.gui_windows = GUIWindows(self)
        self.gui_tabs = GUITabs(self)
        
        self.create_widgets()
        self.refresh_all()

    def setup_main_window(self):
        self.root.title("Трекер задач")
        self.root.geometry("1000x750")
        self.root.configure(bg="#f0f4f8")
        

    def create_widgets(self):
        self.create_title()
        self.create_buttons()
        self.gui_tabs.create_tabs()
        self.create_recommendation_section()

    def create_title(self):
        title = tk.Label(self.root, text="Трекер задач", font=("Helvetica", 20, "bold"),
                         bg="#f0f4f8", fg="#2c3e50")
        title.pack(pady=10)

    def create_buttons(self):
        btn_frame = tk.Frame(self.root, bg="#f0f4f8")
        btn_frame.pack(pady=10)

        buttons = [
            ("Настроить расписание", self.open_schedule),
            ("Добавить цель", self.open_add_goal),
            ("Добавить задачу", self.open_add_task),
            ("Установить энергию", self.open_set_energy),
            ("Обновить", self.refresh_all)
        ]

        for text, cmd in buttons:
            btn = ttk.Button(btn_frame, text=text, command=cmd, width=20)
            btn.pack(side=tk.LEFT, padx=5)

        special_btn = tk.Button(btn_frame, 
                            text="Что делать сейчас?", 
                            command=self.show_recommendation,  
                            width=20, 
                            bg="#486581",
                            fg='white', 
                            padx=10,  
                            pady=6)   
        special_btn.pack(side=tk.LEFT, padx=5)
        
    def create_recommendation_section(self):
        rec_frame = tk.LabelFrame(self.root, text=" Рекомендация ", font=("Helvetica", 12, "bold"),
                                  bg="#e8f4f8", fg="#2c3e50")
        rec_frame.pack(pady=10, padx=20, fill=tk.X)

        self.rec_label = tk.Label(rec_frame, text="Нажми «Что делать сейчас?»", font=("Helvetica", 11),
                                  bg="#e8f4f8", fg="#555", justify=tk.LEFT, anchor="w")
        self.rec_label.pack(fill=tk.X, padx=10, pady=5)

    # === Основные методы обновления ===
    def refresh_all(self):
        self.load_schedule()
        self.gui_tabs.refresh_all_tabs()

    def load_schedule(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT day_of_week, start_time, end_time FROM schedule")
        schedule = {row[0]: f"{row[1]}–{row[2]}" for row in cursor.fetchall()}
        day = datetime.now().strftime("%A").lower()
        today_str = schedule.get(day, "не задано")
        self.root.title(f"Трекер задач | Сегодня: {today_str}")

    # === Методы открытия окон (делегируем GUIWindows) ===
    def open_schedule(self):
        self.gui_windows.open_schedule()

    def open_add_goal(self):
        self.gui_windows.open_add_goal()

    def open_add_task(self):
        self.gui_windows.open_add_task()

    def open_set_energy(self):
        self.gui_windows.open_set_energy()

    # === Рекомендация ===
    def show_recommendation(self):
        calc = PriorityCalculator(self.conn)
        rec = calc.recommend_task()
        if not rec:
            self.rec_label.config(text="Сейчас не рабочее время или нет задач. Отдыхай!")
            return

        t = rec["task"]
        original_importance = t.importance_level * 2

        text = (f"{t.title}\n"
                f"Время: {t.duration} мин | Важность: {original_importance}/10\n"
                f"Приоритет: {rec['score']:.3f}\n"
                f"Почему именно сейчас:\n"
                f"{rec['reason']}"
                )
        
        self.rec_label.config(
            text=text,
            fg="#1b5e20",
            font=("Helvetica", 11, "bold"),
            justify=tk.LEFT,
            anchor="w",
            wraplength=900
        )

        cursor = self.conn.cursor()
        cursor.execute('UPDATE tasks SET status = "in_progress" WHERE id = ?', (t.id,))
        self.conn.commit()
        self.refresh_all()

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()