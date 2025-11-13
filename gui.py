import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
import json

from db.init_db import init_db
from priority_calculator import PriorityCalculator


class SmartAssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Умный Помощник")
        self.root.geometry("1000x750")
        self.root.configure(bg="#f0f4f8")

        self.conn = sqlite3.connect('assistant.db')
        init_db(self.conn)

        self.create_widgets()
        self.load_schedule()
        self.load_goals()

    def create_widgets(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", padding=6, font=('Helvetica', 10))
        style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff")
        style.configure("InProgress.Treeview", background="#fff8e1", fieldbackground="#fff8e1")

        # === Заголовок ===
        title = tk.Label(self.root, text="Умный Помощник", font=("Helvetica", 20, "bold"),
                         bg="#f0f4f8", fg="#2c3e50")
        title.pack(pady=10)

        # === Кнопки (без "Перенести на завтра") ===
        btn_frame = tk.Frame(self.root, bg="#f0f4f8")
        btn_frame.pack(pady=10)

        buttons = [
            ("Настроить расписание", self.open_schedule),
            ("Добавить цель", self.open_add_goal),
            ("Добавить задачу", self.open_add_task),
            ("Установить энергию", self.open_set_energy),
            ("Что делать сейчас?", self.show_recommendation),
            ("Обновить", self.refresh_all)
        ]

        for text, cmd in buttons:
            btn = ttk.Button(btn_frame, text=text, command=cmd, width=20)
            btn.pack(side=tk.LEFT, padx=5)

        # === Вкладки ===
        tab_control = ttk.Notebook(self.root)
        tab_control.pack(pady=15, padx=20, fill=tk.BOTH, expand=True)

        # Вкладка 1: Задачи на сегодня
        today_frame = tk.Frame(tab_control, bg="#f0f4f8")
        tab_control.add(today_frame, text=" Задачи на сегодня ")

        # Вкладка 2: В процессе
        in_progress_frame = tk.Frame(tab_control, bg="#f0f4f8")
        tab_control.add(in_progress_frame, text=" В процессе ")

        # === Задачи на сегодня ===
        self.setup_task_tree(
            today_frame,
            self.load_today_tasks,
            "mark_done",
            extra_cmd="postpone_selected_today"
        )

        # === В процессе ===
        self.setup_task_tree(
            in_progress_frame,
            self.load_in_progress_tasks,
            "finish_task",
            extra_cmd="postpone_selected_in_progress",
            style_name="InProgress.Treeview",
            return_cmd="return_to_todo"  # ← ВОЗВРАТ В СПИСОК
        )

        # === Рекомендация ===
        rec_frame = tk.LabelFrame(self.root, text=" Рекомендация ", font=("Helvetica", 12, "bold"),
                                  bg="#e8f4f8", fg="#2c3e50")
        rec_frame.pack(pady=10, padx=20, fill=tk.X)

        self.rec_label = tk.Label(rec_frame, text="Нажми «Что делать сейчас?»", font=("Helvetica", 11),
                                  bg="#e8f4f8", fg="#555", justify=tk.LEFT, anchor="w")
        self.rec_label.pack(fill=tk.X, padx=10, pady=5)

    def setup_task_tree(self, parent, load_func, done_cmd, extra_cmd=None, style_name="Treeview", return_cmd=None):
        frame = tk.LabelFrame(parent, text=" ", font=("Helvetica", 10))
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("ID", "Задача", "Время", "Важность", "Дедлайн", "Цель")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=10, style=style_name, selectmode="extended")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor="center")
        tree.column("Задача", width=300, anchor="w")
        tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=5)

        # Кнопка "Выполнено"
        ttk.Button(btn_frame, text="Отметить как выполнено",
                   command=lambda: getattr(self, done_cmd)()).pack(side=tk.LEFT, padx=5)

        # Кнопка "Перенести на завтра"
        if extra_cmd:
            ttk.Button(btn_frame, text="Перенести на завтра",
                       command=lambda: getattr(self, extra_cmd)()).pack(side=tk.LEFT, padx=5)

        # Кнопка "ВЕРНУТЬ В СПИСОК"
        if return_cmd:
            ttk.Button(btn_frame, text="Вернуть в список",
                       command=lambda: getattr(self, return_cmd)()).pack(side=tk.LEFT, padx=5)

        setattr(self, f"tree_{load_func.__name__}", tree)
        setattr(self, f"load_{load_func.__name__}", load_func)

    def load_today_tasks(self):
        tree = self.tree_load_today_tasks
        for i in tree.get_children():
            tree.delete(i)
        cursor = self.conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute('''
            SELECT t.id, t.title, t.duration_minutes, t.importance_level, t.deadline,
                   g.title, t.status
            FROM tasks t
            LEFT JOIN goals g ON t.goal_id = g.id
            WHERE t.scheduled_date = ? AND t.status IN ('todo', 'in_progress')
            ORDER BY t.importance_level DESC
        ''', (today,))
        for row in cursor.fetchall():
            deadline = row[4][:16].replace("T", " ") if row[4] else "-"
            status = " [в процессе]" if row[6] == "in_progress" else ""
            tree.insert("", tk.END, values=(
                row[0], f"{row[1]}{status}", f"{row[2]} мин", f"{row[3]}/10", deadline, row[5] or "-"
            ))

    def load_in_progress_tasks(self):
        tree = self.tree_load_in_progress_tasks
        for i in tree.get_children():
            tree.delete(i)
        cursor = self.conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute('''
            SELECT t.id, t.title, t.duration_minutes, t.importance_level, t.deadline,
                   g.title
            FROM tasks t
            LEFT JOIN goals g ON t.goal_id = g.id
            WHERE t.scheduled_date = ? AND t.status = 'in_progress'
        ''', (today,))
        for row in cursor.fetchall():
            deadline = row[4][:16].replace("T", " ") if row[4] else "-"
            tree.insert("", tk.END, values=(
                row[0], row[1], f"{row[2]} мин", f"{row[3]}/10", deadline, row[5] or "-"
            ))

    def refresh_all(self):
        self.load_schedule()
        self.load_goals()
        self.load_today_tasks()
        self.load_in_progress_tasks()

    def load_schedule(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT day_of_week, start_time, end_time FROM schedule")
        schedule = {row[0]: f"{row[1]}–{row[2]}" for row in cursor.fetchall()}
        day = datetime.now().strftime("%A").lower()
        today_str = schedule.get(day, "не задано")
        self.root.title(f"Умный Помощник | Сегодня: {today_str}")

    def load_goals(self):
        pass

    # === Перенос выбранных задач ===
    def postpone_selected(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите хотя бы одну задачу!")
            return

        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        cursor = self.conn.cursor()
        moved = 0
        for item in selected:
            task_id = tree.item(item)['values'][0]
            cursor.execute('''
                UPDATE tasks SET scheduled_date = ?, status = 'todo'
                WHERE id = ? AND status != 'done'
            ''', (tomorrow, task_id))
            moved += cursor.rowcount
        self.conn.commit()
        messagebox.showinfo("Готово", f"Перенесено задач: {moved}")
        self.refresh_all()

    def postpone_selected_today(self):
        self.postpone_selected(self.tree_load_today_tasks)

    def postpone_selected_in_progress(self):
        self.postpone_selected(self.tree_load_in_progress_tasks)

    # === Вернуть в список ===
    def return_to_todo(self):
        tree = self.tree_load_in_progress_tasks
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите задачу!")
            return
        cursor = self.conn.cursor()
        returned = 0
        for item in selected:
            task_id = tree.item(item)['values'][0]
            cursor.execute("UPDATE tasks SET status = 'todo' WHERE id = ?", (task_id,))
            returned += cursor.rowcount
        self.conn.commit()
        messagebox.showinfo("Готово", f"Возвращено в список: {returned}")
        self.refresh_all()

    # === Рекомендация ===
    def show_recommendation(self):
        calc = PriorityCalculator(self.conn)
        rec = calc.recommend_task()
        if not rec:
            self.rec_label.config(text="Сейчас не рабочее время или нет задач. Отдыхай!")
            return

        t = rec["task"]
        text = (f"{t.title}\n"
                f"Время: {t.duration} мин | Важность: {t.importance_level}/10\n"
                f"Приоритет: {rec['score']:.3f}\n"
                f"Почему: {rec['reason']}")

        self.rec_label.config(text=text)

        cursor = self.conn.cursor()
        cursor.execute('UPDATE tasks SET status = "in_progress" WHERE id = ?', (t.id,))
        self.conn.commit()
        self.refresh_all()

    # === Выполнено ===
    def mark_done(self):
        tree = self.tree_load_today_tasks
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите задачу!")
            return
        cursor = self.conn.cursor()
        done = 0
        for item in selected:
            task_id = tree.item(item)['values'][0]
            cursor.execute("UPDATE tasks SET status = 'done' WHERE id = ?", (task_id,))
            done += cursor.rowcount
        self.conn.commit()
        messagebox.showinfo("Готово", f"Выполнено задач: {done}")
        self.refresh_all()

    def finish_task(self):
        tree = self.tree_load_in_progress_tasks
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите задачу!")
            return
        cursor = self.conn.cursor()
        done = 0
        for item in selected:
            task_id = tree.item(item)['values'][0]
            cursor.execute("UPDATE tasks SET status = 'done' WHERE id = ?", (task_id,))
            done += cursor.rowcount
        self.conn.commit()
        messagebox.showinfo("Готово", f"Завершено задач: {done}")
        self.refresh_all()

    # === Окна ===
    def open_schedule(self):
        win = tk.Toplevel(self.root)
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
            self.refresh_all()

        ttk.Button(win, text="Сохранить", command=save).pack(pady=10)

    def open_add_goal(self):
        win = tk.Toplevel(self.root)
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
            self.refresh_all()

        ttk.Button(win, text="Добавить", command=save).pack(pady=15)

    def open_add_task(self):
        win = tk.Toplevel(self.root)
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

        tk.Label(win, text="Разблокирует задачи (ID через запятую):", bg="#f0f4f8").pack(anchor="w", padx=20, pady=(10,2))
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
            self.refresh_all()

        ttk.Button(win, text="Добавить задачу", command=save).pack(pady=15)

    def open_set_energy(self):
        win = tk.Toplevel(self.root)
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

    def edit_task(self):
        messagebox.showinfo("Редактирование", "Функция в разработке")

    def __del__(self):
        self.conn.close()


def run_gui():
    root = tk.Tk()
    app = SmartAssistantGUI(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()