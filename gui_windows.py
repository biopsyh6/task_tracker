import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime

class GUIWindows:
    def __init__(self, main_app):
        self.main_app = main_app
        self.conn = main_app.conn

    def open_schedule(self):
        win = tk.Toplevel(self.main_app.root)
        win.title("Расписание")
        win.geometry("400x500")
        win.configure(bg="#f0f4f8")

        days_ru = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']
        days_en = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        day_map = dict(zip(days_ru, days_en))
        entries = {}

        for day_ru in days_ru:
            frame = tk.Frame(win, bg="#f0f4f8")
            frame.pack(pady=5, fill=tk.X, padx=20)
            tk.Label(frame, text=day_ru.capitalize(), width=12, bg="#f0f4f8", anchor="w").pack(side=tk.LEFT)
            start = tk.Entry(frame, width=8)
            end = tk.Entry(frame, width=8)
            start.pack(side=tk.LEFT, padx=2)
            tk.Label(frame, text="–", bg="#f0f4f8").pack(side=tk.LEFT)
            end.pack(side=tk.LEFT, padx=2)
            entries[day_ru] = (start, end)

        cursor = self.conn.cursor()
        cursor.execute("SELECT day_of_week, start_time, end_time FROM schedule")
        for row in cursor.fetchall():
            day_en = row[0]
            day_ru = next((ru for ru, en in day_map.items() if en == day_en), None)
            if day_ru and day_ru in entries:
                start, end = entries[day_ru]
                start.insert(0, row[1])
                end.insert(0, row[2])

        def save():
            cursor = self.conn.cursor()
            for day_ru, (start, end) in entries.items():
                s, e = start.get().strip(), end.get().strip()
                if s and e:
                    day_en = day_map[day_ru]
                    cursor.execute('''
                        INSERT OR REPLACE INTO schedule (day_of_week, start_time, end_time)
                        VALUES (?, ?, ?)
                    ''', (day_en, s, e))
            self.conn.commit()
            messagebox.showinfo("Готово", "Расписание сохранено!")
            win.destroy()
            self.main_app.refresh_all()

        ttk.Button(win, text="Сохранить", command=save).pack(pady=10)

    def open_add_goal(self):
        win = tk.Toplevel(self.main_app.root)
        win.title("Добавить цель")
        win.geometry("400x300")
        win.configure(bg="#f0f4f8")

        tk.Label(win, text="Название цели:", bg="#f0f4f8").pack(pady=5)
        title_entry = tk.Entry(win, width=40)
        title_entry.pack(pady=5)

        tk.Label(win, text="Вес (0.1–1.0, по ум. 1.0):", bg="#f0f4f8").pack(pady=5)
        weight_entry = tk.Entry(win, width=10)
        weight_entry.pack(pady=5)
        weight_entry.insert(0, "1.0")

        tk.Label(win, text="Дедлайн (YYYY-MM-DD):", bg="#f0f4f8").pack(pady=5)
        deadline_entry = tk.Entry(win, width=15)
        deadline_entry.pack(pady=5)

        def save():
            title = title_entry.get().strip()
            if not title:
                messagebox.showerror("Ошибка", "Название обязательно!")
                return
            try:
                weight = max(0.1, min(1.0, float(weight_entry.get() or "1.0")))
            except:
                weight = 1.0
            deadline = deadline_entry.get().strip() or None

            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO goals (title, weight, deadline) VALUES (?, ?, ?)",
                           (title, weight, deadline))
            self.conn.commit()
            messagebox.showinfo("Готово", f"Цель «{title}» добавлена!")
            win.destroy()
            self.main_app.refresh_all()

        ttk.Button(win, text="Добавить", command=save).pack(pady=15)

    def open_add_task(self):
        win = tk.Toplevel(self.main_app.root)
        win.title("Добавить задачу")
        win.geometry("500x700")
        win.configure(bg="#f0f4f8")

        fields = {}
        labels = [
            ("Что нужно сделать?", "title"),
            ("Сколько минут займёт?", "duration"),
            ("Важность (1–10)", "importance"),
            ("Дедлайн (YYYY-MM-DD HH:MM)", "deadline"),
        ]
        for label, key in labels:
            tk.Label(win, text=label, bg="#f0f4f8").pack(anchor="w", padx=20, pady=2)
            entry = tk.Entry(win, width=50)
            entry.pack(pady=2, padx=20)
            fields[key] = entry

        tk.Label(win, text="Привязать к цели:", bg="#f0f4f8").pack(anchor="w", padx=20, pady=(10,2))
        goal_var = tk.StringVar()
        goal_combo = ttk.Combobox(win, textvariable=goal_var, state="readonly", width=47)
        goal_combo.pack(pady=2, padx=20)
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, title FROM goals")
        goals = [(row[0], row[1]) for row in cursor.fetchall()]
        goal_combo['values'] = ["(не привязывать)"] + [f"{id}. {title}" for id, title in goals]
        goal_combo.current(0)

        tk.Label(win, text="Тип задачи:", bg="#f0f4f8").pack(anchor="w", padx=20, pady=(10,2))
        type_combo = ttk.Combobox(win, values=["creative", "analytical", "routine", "communication"], state="readonly", width=47)
        type_combo.set("routine")
        type_combo.pack(pady=2, padx=20)

        tk.Label(win, text="Требуемая энергия:", bg="#f0f4f8").pack(anchor="w", padx=20, pady=(10,2))
        energy_combo = ttk.Combobox(win, values=["low", "medium", "high"], state="readonly", width=47)
        energy_combo.set("medium")
        energy_combo.pack(pady=2, padx=20)

        tk.Label(win, text="Вклад в цель (0.0–1.0):", bg="#f0f4f8").pack(anchor="w", padx=20, pady=(10,2))
        contrib_entry = tk.Entry(win, width=10)
        contrib_entry.insert(0, "0.8")
        contrib_entry.pack(pady=2, padx=20)

        tk.Label(win, text="Будет разблокировано после выполнения следующих задач (ID через запятую):", bg="#f0f4f8").pack(anchor="w", padx=20, pady=(10,2))
        blocks_entry = tk.Entry(win, width=50)
        blocks_entry.pack(pady=2, padx=20)

        def save():
            title = fields["title"].get().strip()
            if not title:
                messagebox.showerror("Ошибка", "Название обязательно!")
                return
            try:
                duration = int(fields["duration"].get())
                if duration <= 0: raise ValueError
            except:
                messagebox.showerror("Ошибка", "Укажите время в минутах!")
                return
            try:
                importance = int(fields["importance"].get())
                if not 1 <= importance <= 10: raise ValueError
            except:
                messagebox.showerror("Ошибка", "Важность от 1 до 10!")
                return

            deadline = fields["deadline"].get().strip() or None
            goal_choice = goal_var.get()
            goal_id = None
            if goal_choice != "(не привязывать)" and goal_choice:
                goal_id = int(goal_choice.split('.')[0])

            task_type = type_combo.get()
            energy_type = energy_combo.get()

            try:
                contribution = max(0.0, min(1.0, float(contrib_entry.get() or "0.8")))
            except:
                contribution = 0.8

            blocks_input = blocks_entry.get().strip()
            blocks_json = "[]"
            if blocks_input:
                try:
                    ids = [int(x.strip()) for x in blocks_input.split(",") if x.strip().isdigit()]
                    blocks_json = json.dumps(ids)
                except:
                    messagebox.showwarning("Внимание", "Некорректные ID зависимостей")

            today = datetime.now().strftime("%Y-%m-%d")
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO tasks (
                    title, duration_minutes, importance_level, status, created_date,
                    scheduled_date, deadline, goal_id, energy_type, task_type,
                    blocks_task_ids, contribution
                ) VALUES (?, ?, ?, 'todo', ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (title, duration, importance, today, today, deadline, goal_id,
                  energy_type, task_type, blocks_json, contribution))
            self.conn.commit()
            messagebox.showinfo("Готово", f"Задача «{title}» добавлена!")
            win.destroy()
            self.main_app.refresh_all()

        ttk.Button(win, text="Добавить задачу", command=save).pack(pady=15)

    def open_set_energy(self):
        win = tk.Toplevel(self.main_app.root)
        win.title("Установить энергию")
        win.geometry("300x200")
        win.configure(bg="#f0f4f8")

        var = tk.StringVar(value="medium")
        for text, value in [("Низкая", "low"), ("Средняя", "medium"), ("Высокая", "high")]:
            tk.Radiobutton(win, text=text, variable=var, value=value, bg="#f0f4f8").pack(pady=5)

        def save():
            level = var.get()
            now = datetime.now().isoformat()
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO user_energy (energy_level, updated_at) VALUES (?, ?)", (level, now))
            self.conn.commit()
            messagebox.showinfo("Готово", f"Энергия: {level}")
            win.destroy()

        ttk.Button(win, text="Сохранить", command=save).pack(pady=10)