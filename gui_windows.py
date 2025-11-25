import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime, date, time
from tkcalendar import DateEntry

class GUIWindows:
    def __init__(self, main_app):
        self.main_app = main_app
        self.conn = main_app.conn

    def open_schedule(self):
        win = tk.Toplevel(self.main_app.root)
        win.title("Расписание")
        win.geometry("460x520")
        win.configure(bg="#f0f4f8")
        win.resizable(False, False)
        win.grab_set()

        days_ru = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']
        days_en = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        day_map = dict(zip(days_ru, days_en))
        time_widgets = {}

        # Загрзка текущего расписания
        cursor = self.conn.cursor()
        cursor.execute("SELECT day_of_week, start_time, end_time FROM schedule")
        saved_schedule = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

        def create_time_picker(parent, default="09:00"):
            frame = tk.Frame(parent, bg="#f0f4f8")
            
            # Часы
            hour_var = tk.StringVar(value=default.split(":")[0])
            hour_spin = tk.Spinbox(frame, from_=0, to=23, width=3, textvariable=hour_var,
                                   font=("Helvetica", 11), justify="center")
            hour_spin.pack(side=tk.LEFT, padx=2)
            
            tk.Label(frame, text=":", bg="#f0f4f8", font=("Helvetica", 12)).pack(side=tk.LEFT)
            
            minute_var = tk.StringVar(value=default.split(":")[1])
            minute_spin = tk.Spinbox(frame, values=tuple(f"{m:02d}" for m in range(0, 60, 5)),
                                     width=3, textvariable=minute_var,
                                     font=("Helvetica", 11), justify="center")
            minute_spin.pack(side=tk.LEFT, padx=2)
            
            return frame, hour_var, minute_var

        for day_ru in days_ru:
            frame = tk.Frame(win, bg="#f0f4f8")
            frame.pack(pady=8, fill=tk.X, padx=25)
            
            tk.Label(frame, text=day_ru.capitalize(), width=12, bg="#f0f4f8",
                     font=("Helvetica", 11), anchor="w").pack(side=tk.LEFT)
            
            start_time = "09:00"
            end_time = "18:00"
            day_en = day_map[day_ru]
            if day_en in saved_schedule:
                start_time, end_time = saved_schedule[day_en]
            
            start_picker, start_h, start_m = create_time_picker(frame, start_time)
            start_picker.pack(side=tk.LEFT, padx=5)
            
            tk.Label(frame, text="—", bg="#f0f4f8", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=5)
            
            end_picker, end_h, end_m = create_time_picker(frame, end_time)
            end_picker.pack(side=tk.LEFT, padx=5)
            
            time_widgets[day_ru] = (start_h, start_m, end_h, end_m)

        def save():
            cursor = self.conn.cursor()
            for day_ru, (sh, sm, eh, em) in time_widgets.items():
                start_str = f"{sh.get().zfill(2)}:{sm.get()}"
                end_str = f"{eh.get().zfill(2)}:{em.get()}"
                
                if not (sh.get().isdigit() and eh.get().isdigit()):
                    messagebox.showerror("Ошибка", f"Некорректное время для {day_ru}")
                    return
                
                day_en = day_map[day_ru]
                cursor.execute('''
                    INSERT OR REPLACE INTO schedule (day_of_week, start_time, end_time)
                    VALUES (?, ?, ?)
                ''', (day_en, start_str, end_str))
            
            self.conn.commit()
            messagebox.showinfo("Готово", "Расписание сохранено!")
            win.destroy()
            self.main_app.refresh_all()

        btn_frame = tk.Frame(win, bg="#f0f4f8")
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Сохранить", command=save).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Отмена", command=win.destroy).pack(side=tk.LEFT, padx=10)


    def open_add_goal(self):
        from tkcalendar import DateEntry
        from datetime import datetime, date

        win = tk.Toplevel(self.main_app.root)
        win.title("Добавить цель")
        win.geometry("480x460")
        win.configure(bg="#f0f4f8")
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text="Новая цель", font=("Helvetica", 16, "bold"), 
                 bg="#f0f4f8", fg="#2c3e50").pack(pady=(20, 10))

        tk.Label(win, text="Название цели:", bg="#f0f4f8", font=("Helvetica", 11), anchor="w").pack(pady=(10,5), padx=40, fill=tk.X)
        title_entry = tk.Entry(win, font=("Helvetica", 11), relief="solid", bd=1)
        title_entry.pack(pady=5, padx=40, fill=tk.X)
        title_entry.focus()

        tk.Label(win, text="Вес цели (важность):", bg="#f0f4f8", font=("Helvetica", 11), anchor="w").pack(pady=(15,5), padx=40, fill=tk.X)
        
        weight_frame = tk.Frame(win, bg="#f0f4f8")
        weight_frame.pack(pady=5)

        weight_var = tk.DoubleVar(value=1.0)
        weight_spin = tk.Spinbox(
            weight_frame,
            from_=0.1,
            to=1.0,
            increment=0.1,
            textvariable=weight_var,
            width=8,
            font=("Helvetica", 12),
            justify="center",
            bd=2,
            relief="solid"
        )
        weight_spin.pack(side=tk.LEFT)

        tk.Label(weight_frame, text=" — чем выше, тем важнее цель", 
                 bg="#f0f4f8", fg="#666", font=("Helvetica", 10)).pack(side=tk.LEFT, padx=15)

        tk.Label(win, text="Дедлайн:", bg="#f0f4f8", font=("Helvetica", 11), anchor="w").pack(pady=(20,5), padx=40, fill=tk.X)
        
        cal_frame = tk.Frame(win, bg="#f0f4f8")
        cal_frame.pack(pady=8, padx=40, fill=tk.X)

        today = date.today()

        cal = DateEntry(
            cal_frame,
            width=16,
            background='#1976d2',
            foreground='white',
            borderwidth=2,
            year=today.year,
            month=today.month,
            day=today.day,
            locale='ru_RU',
            date_pattern='yyyy-mm-dd',
            font=("Helvetica", 11),
            relief="solid",
            mindate=today,  
            state="normal"
        )
        cal.pack(side=tk.LEFT)
        cal.set_date(None)

        tk.Button(cal_frame, text="Очистить", 
                  command=lambda: cal.set_date(None),
                  font=("Helvetica", 10), bg="#e0e0e0", relief="flat").pack(side=tk.LEFT, padx=10)

        btn_frame = tk.Frame(win, bg="#f0f4f8")
        btn_frame.pack(pady=30)

        def save():
            title = title_entry.get().strip()
            if not title:
                messagebox.showerror("Ошибка", "Введите название цели!", parent=win)
                return

            weight = weight_var.get()
            selected_date = cal.get_date()

            if selected_date and selected_date < today:
                messagebox.showerror("Ошибка", "Некорректный дедлайн", parent=win)
                return

            deadline_str = selected_date.strftime("%Y-%m-%d") if selected_date else None

            cursor = self.conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO goals (title, weight, deadline) VALUES (?, ?, ?)",
                    (title, weight, deadline_str)
                )
                self.conn.commit()
                messagebox.showinfo("Готово!", f'Цель "{title}" успешно добавлена!', parent=win)
                win.destroy()
                self.main_app.refresh_all()
            except Exception as e:
                messagebox.showerror("Ошибка базы данных", f"Не удалось сохранить:\n{e}", parent=win)

        def cancel():
            win.destroy()

        ttk.Button(btn_frame, text="Добавить цель", command=save, width=18).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Отмена", command=cancel, width=12).pack(side=tk.LEFT, padx=10)

        win.bind("<Return>", lambda e: save())
        win.bind("<Escape>", lambda e: cancel())

    def open_add_task(self):

        win = tk.Toplevel(self.main_app.root)
        win.title("Добавить задачу")
        win.geometry("560x820")
        win.configure(bg="#f0f4f8")
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text="Новая задача", font=("Helvetica", 16, "bold"), bg="#f0f4f8", fg="#2c3e50").pack(pady=(20,15))

        tk.Label(win, text="Что нужно сделать:", bg="#f0f4f8", font=("Helvetica", 11), anchor="w").pack(pady=(5,3), padx=40, fill=tk.X)
        title_entry = tk.Entry(win, font=("Helvetica", 11), relief="solid", bd=1)
        title_entry.pack(pady=5, padx=40, fill=tk.X)
        title_entry.focus()

        tk.Label(win, text="Сколько минут займёт:", bg="#f0f4f8", font=("Helvetica", 11), anchor="w").pack(pady=(15,3), padx=40, fill=tk.X)
        duration_frame = tk.Frame(win, bg="#f0f4f8")
        duration_frame.pack(pady=5)
        duration_var = tk.IntVar(value=30)
        duration_spin = tk.Spinbox(duration_frame, from_=5, to=300, increment=5, textvariable=duration_var, width=10, font=("Helvetica", 12))
        duration_spin.pack(side=tk.LEFT)
        tk.Label(duration_frame, text=" мин", bg="#f0f4f8").pack(side=tk.LEFT, padx=8)

        tk.Label(win, text="Важность:", bg="#f0f4f8", font=("Helvetica", 11), anchor="w").pack(pady=(15,3), padx=40, fill=tk.X)
        importance_frame = tk.Frame(win, bg="#f0f4f8")
        importance_frame.pack(pady=5)
        importance_var = tk.IntVar(value=5)
        importance_spin = tk.Spinbox(importance_frame, from_=1, to=10, textvariable=importance_var, width=6, font=("Helvetica", 12))
        importance_spin.pack(side=tk.LEFT)
        tk.Label(importance_frame, text=" / 10", bg="#f0f4f8").pack(side=tk.LEFT, padx=8)

        tk.Label(win, text="Дедлайн:", bg="#f0f4f8", font=("Helvetica", 11), anchor="w").pack(pady=(20,5), padx=40, fill=tk.X)
        deadline_frame = tk.Frame(win, bg="#f0f4f8")
        deadline_frame.pack(pady=8, padx=40, fill=tk.X)

        today = date.today()

        cal = DateEntry(
            deadline_frame,
            width=16,
            background='#1976d2',
            foreground='white',
            borderwidth=2,
            locale='ru_RU',
            date_pattern='yyyy-mm-dd',
            mindate=today,
            font=("Helvetica", 11)
        )
        cal.pack(side=tk.LEFT)
        cal.set_date(None)

        time_frame = tk.Frame(deadline_frame, bg="#f0f4f8")
        time_frame.pack(side=tk.LEFT, padx=15)

        hour_var = tk.StringVar(value="10")
        minute_var = tk.StringVar(value="00")

        tk.Spinbox(time_frame, from_=0, to=23, width=3, textvariable=hour_var, font=("Helvetica", 11)).pack(side=tk.LEFT)
        tk.Label(time_frame, text=":", bg="#f0f4f8", font=("Helvetica", 12)).pack(side=tk.LEFT)
        tk.Spinbox(time_frame, values=tuple(f"{m:02d}" for m in range(0,60,5)), width=3, textvariable=minute_var, font=("Helvetica", 11)).pack(side=tk.LEFT)

        tk.Button(deadline_frame, text="Очистить", 
                  command=lambda: [cal.set_date(None), hour_var.set("10"), minute_var.set("00")],
                  font=("Helvetica", 9)).pack(side=tk.LEFT, padx=10)

        tk.Label(win, text="Привязать к цели:", bg="#f0f4f8", font=("Helvetica", 11), anchor="w").pack(pady=(20,5), padx=40, fill=tk.X)
        goal_var = tk.StringVar()
        goal_combo = ttk.Combobox(win, textvariable=goal_var, state="readonly", width=47)
        goal_combo.pack(pady=5, padx=40)
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, title FROM goals ORDER BY title")
        goals = cursor.fetchall()
        goal_combo['values'] = ["(не привязывать)"] + [f"{id}. {title}" for id, title in goals]
        goal_combo.current(0)

        tk.Label(win, text="Тип задачи:", bg="#f0f4f8", font=("Helvetica", 11), anchor="w").pack(pady=(15,5), padx=40, fill=tk.X)
        type_combo = ttk.Combobox(win, values=("Творческая", "Аналитическая", "Рутинная", "Общение"), state="readonly", width=47)
        type_combo.set("Рутинная")
        type_combo.pack(pady=5, padx=40)

        tk.Label(win, text="Требуемая энергия:", bg="#f0f4f8", font=("Helvetica", 11), anchor="w").pack(pady=(10,5), padx=40, fill=tk.X)
        energy_combo = ttk.Combobox(win, values=("Низкая", "Средняя", "Высокая"), state="readonly", width=47)
        energy_combo.set("Средняя")
        energy_combo.pack(pady=5, padx=40)

        tk.Label(win, text="Вклад в цель (0.0 – 1.0):", bg="#f0f4f8", font=("Helvetica", 11), anchor="w").pack(pady=(15,5), padx=40, fill=tk.X)
        contrib_var = tk.DoubleVar(value=0.8)
        contrib_spin = tk.Spinbox(win, from_=0.0, to=1.0, increment=0.1, textvariable=contrib_var, width=10, font=("Helvetica", 12))
        contrib_spin.pack(pady=5, padx=40, anchor="w")

        tk.Label(win, text="Разблокируется после задач (ID через запятую):", bg="#f0f4f8", font=("Helvetica", 11), anchor="w").pack(pady=(15,5), padx=40, fill=tk.X)
        blocks_entry = tk.Entry(win, width=50)
        blocks_entry.pack(pady=5, padx=40)

        btn_frame = tk.Frame(win, bg="#f0f4f8")
        btn_frame.pack(pady=30)

        TYPE_MAP = {"Творческая": "creative", "Аналитическая": "analytical", "Рутинная": "routine", "Общение": "communication"}
        ENERGY_MAP = {"Низкая": "low", "Средняя": "medium", "Высокая": "high"}

        def save():
            title = title_entry.get().strip()
            if not title:
                messagebox.showerror("Ошибка", "Введите название задачи!", parent=win)
                return

            duration = duration_var.get()
            importance = importance_var.get()
            contribution = round(contrib_var.get(), 1)

            selected_date = cal.get_date()
            deadline_str = None

            if selected_date: 
                if selected_date < today:
                    messagebox.showerror("Ошибка", "Некорректный дедлайн!", parent=win)
                    return
                try:
                    hour = int(hour_var.get())
                    minute = int(minute_var.get())
                    if not (0 <= hour <= 23 and 0 <= minute <= 59):
                        raise ValueError
                    deadline_dt = datetime.combine(selected_date, time(hour, minute))
                    deadline_str = deadline_dt.strftime("%Y-%m-%d %H:%M")
                except:
                    messagebox.showerror("Ошибка", "Некорректное время дедлайна!", parent=win)
                    return

            goal_id = None
            if goal_var.get() != "(не привязывать)" and goal_var.get():
                goal_id = int(goal_var.get().split('.')[0])

            blocks_json = "[]"
            if blocks_entry.get().strip():
                try:
                    ids = [int(x.strip()) for x in blocks_entry.get().split(",") if x.strip().isdigit()]
                    blocks_json = json.dumps(ids)
                except:
                    messagebox.showwarning("Внимание", "Некорректные ID зависимостей — будут проигнорированы")

            today_str = datetime.now().strftime("%Y-%m-%d")

            cursor = self.conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO tasks (
                        title, duration_minutes, importance_level, status, created_date,
                        scheduled_date, deadline, goal_id, energy_type, task_type,
                        blocks_task_ids, contribution
                    ) VALUES (?, ?, ?, 'todo', ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    title, duration, importance, today_str, today_str, deadline_str, goal_id,
                    ENERGY_MAP[energy_combo.get()], TYPE_MAP[type_combo.get()],
                    blocks_json, contribution
                ))
                self.conn.commit()
                messagebox.showinfo("Готово!", f'Задача "{title}" добавлена!', parent=win)
                win.destroy()
                self.main_app.refresh_all()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить:\n{e}", parent=win)

        ttk.Button(btn_frame, text="Добавить задачу", command=save, width=22).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Отмена", command=win.destroy, width=12).pack(side=tk.LEFT, padx=10)

        win.bind("<Escape>", lambda e: win.destroy())

    def open_set_energy(self):
        win = tk.Toplevel(self.main_app.root)
        win.title("Установить энергию")
        win.geometry("300x200")
        win.configure(bg="#f0f4f8")
        win.resizable(False, False)
        win.grab_set()

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