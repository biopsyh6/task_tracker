import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from priority_calculator import PriorityCalculator
import json

class GUITabs:
    def __init__(self, main_app):
        self.main_app = main_app
        self.conn = main_app.conn
        self.setup_styles()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        bg = "#f8fafc"
        accent = "#3b82f6"
        success = "#10b981"
        warning = "#f59e0b"
        danger = "#ef4444"
        muted = "#64748b"

        style.configure("TButton", font=("Helvetica", 10, "bold"), padding=8)
        style.map("TButton",
                  background=[('active', accent), ('pressed', '#2563eb')],
                  foreground=[('active', 'white')])

        style.configure("Accent.TButton", background=accent, foreground="white")
        style.map("Accent.TButton",
                  background=[('active', '#2563eb')])

        style.configure("Success.TButton", background=success, foreground="white")
        style.map("Success.TButton",
                  background=[('active', '#059669')])

        style.configure("Danger.TButton", background=danger, foreground="white")
        style.map("Danger.TButton",
                  background=[('active', '#dc2626')])

        style.configure("Treeview",
                        background="white",
                        fieldbackground="white",
                        borderwidth=1,
                        relief="flat",
                        rowheight=32,
                        font=("Helvetica", 10))
        style.configure("Treeview.Heading", font=("Helvetica", 11, "bold"), foreground=muted)
        style.map("Treeview", background=[('selected', accent)])

        style.configure("goal.Treeview", background="white")
        style.configure("completed", background="#ecfdf5", foreground="#166534")
        style.configure("on_fire",   background="#fee2e2", foreground="#991b1b", font=("Helvetica", 10, "bold"))
        style.configure("hot",       background="#fecaca", foreground="#991b1b")
        style.configure("warm",      background="#fed7aa", foreground="#9c4221")
        style.configure("normal",  background="white", foreground="#1e293b")

        style.configure("blocked",     background="#fee2e2", foreground="#991b1b")
        style.configure("in_progress", background="#fffbeb", foreground="#92400e")
        style.configure("done",        background="#f0fdf4", foreground="#166534")

    def create_tabs(self):
        tab_control = ttk.Notebook(self.main_app.root)
        tab_control.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0,15))

        icons = ["today", "progress", "done", "goals"]
        titles = [" Задачи на сегодня ", " В процессе ", " Выполненные задачи ", " Цели "]

        for title in titles:
            frame = tk.Frame(tab_control, bg="#ffffff", relief="flat")
            frame.pack(fill=tk.BOTH, expand=True)
            tab_control.add(frame, text=title)

        self.setup_task_tree(tab_control.tabs()[0], "today")
        self.setup_task_tree(tab_control.tabs()[1], "in_progress")
        self.setup_task_tree(tab_control.tabs()[2], "done")
        self.setup_goals_tree(tab_control.tabs()[3])

    def setup_task_tree(self, parent, tab_type):
        parent = tk.Frame(self.main_app.root.nametowidget(parent), bg="white")
        parent.pack(fill=tk.BOTH, expand=True)

        frame = tk.Frame(parent, bg="white")
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        columns = ("ID", "Задача", "Время", "Важность", "Дедлайн", "Цель")
        tree = ttk.Treeview(frame, columns=columns, show="headings", style="Treeview", selectmode="extended")
        
        widths = [60, 380, 100, 100, 140, 180]
        for i, col in enumerate(columns):
            tree.heading(col, text=col, anchor="center")
            tree.column(col, width=widths[i], anchor="center")
        tree.column("Задача", anchor="w")
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        btn_frame = tk.Frame(parent, bg="white")
        btn_frame.pack(pady=8)

        if tab_type == "today":
            ttk.Button(btn_frame, text="Отметить как выполнено", style="Success.TButton",
                      command=lambda: self.mark_done(tree)).pack(side=tk.LEFT, padx=4)
            ttk.Button(btn_frame, text="Перенести на завтра", 
                      command=lambda: self.postpone_selected(tree)).pack(side=tk.LEFT, padx=4)
        elif tab_type == "in_progress":
            ttk.Button(btn_frame, text="Завершить задачу", style="Success.TButton",
                      command=lambda: self.finish_task(tree)).pack(side=tk.LEFT, padx=4)
            ttk.Button(btn_frame, text="Перенести на завтра",
                      command=lambda: self.postpone_selected(tree)).pack(side=tk.LEFT, padx=4)
            ttk.Button(btn_frame, text="Вернуть в список",
                      command=lambda: self.return_to_todo(tree)).pack(side=tk.LEFT, padx=4)
        elif tab_type == "done":
            ttk.Button(btn_frame, text="Удалить навсегда", style="Danger.TButton",
                      command=lambda: self.delete_done(tree)).pack(side=tk.LEFT, padx=4)

        setattr(self, f"tree_{tab_type}", tree)

    def setup_goals_tree(self, parent):
        parent = tk.Frame(self.main_app.root.nametowidget(parent), bg="white")
        parent.pack(fill=tk.BOTH, expand=True)

        frame = tk.Frame(parent, bg="white")
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        columns = ("ID", "Цель", "Вес", "Дедлайн", "Выполнено", "Всего", "Прогресс")
        tree = ttk.Treeview(frame, columns=columns, show="headings", style="goal.Treeview", selectmode="browse")
        
        widths = [60, 320, 110, 120, 100, 80, 160]
        for i, col in enumerate(columns):
            tree.heading(col, text=col, anchor="center")
            tree.column(col, width=widths[i], anchor="center")
        tree.column("Цель", anchor="w")
        tree.column("Прогресс", anchor="w")
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        btn_frame = tk.Frame(parent, bg="white")
        btn_frame.pack(pady=8)
        ttk.Button(btn_frame, text="Показать задачи", style="Accent.TButton",
                  command=lambda: self.show_goal_tasks(tree)).pack(padx=4)

        self.tree_goals = tree

    def refresh_all_tabs(self):
        self.load_today_tasks()
        self.load_in_progress_tasks()
        self.load_done_tasks()
        self.load_goals()

    def load_goals(self):
        if not hasattr(self, 'tree_goals'):
            return
        tree = self.tree_goals
        for i in tree.get_children():
            tree.delete(i)

        calc = PriorityCalculator(self.conn)
        cursor = self.conn.cursor()

        cursor.execute('''
            SELECT g.id, g.title, g.weight, g.deadline
            FROM goals g
            ORDER BY 
                CASE WHEN g.deadline IS NULL THEN 1 ELSE 0 END,
                g.deadline ASC
        ''')
        goals = cursor.fetchall()

        for goal in goals:
            goal_id, title, base_weight, deadline = goal
            deadline_str = deadline or "—"

            cursor.execute("""
                SELECT 
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as done_tasks,
                    SUM(importance_level) as total_importance,
                    SUM(CASE WHEN status = 'done' THEN importance_level ELSE 0 END) as done_importance
                FROM tasks 
                WHERE goal_id = ?
            """, (goal_id,))
            
            row = cursor.fetchone()
            total_tasks = row[0] or 0
            done_tasks = row[1] or 0
            total_importance = row[2] or 0
            done_importance = row[3] or 0

            if total_importance > 0:
                percent = int(100 * done_importance / total_importance)
                progress_text = f"{done_importance}/{total_importance} важн. ({percent}%)"
            else:
                percent = 0 if total_tasks == 0 else int(100 * done_tasks / total_tasks)
                progress_text = f"{done_tasks}/{total_tasks} задач ({percent}%)"

            if percent == 100 and total_tasks > 0:
                progress_text += " [Выполнена]"

            current_weight = calc.get_dynamic_goal_weight(goal_id)

            if abs(current_weight - base_weight) < 0.05:
                weight_display = f"{base_weight:.2f}"
            else:
                weight_display = f"{base_weight:.2f} → {current_weight:.2f}"

            if percent == 100 and total_tasks > 0:
                tag = "completed"
            elif current_weight >= base_weight * 2.5:
                tag = "on_fire"     
            elif current_weight >= base_weight * 1.8:
                tag = "hot"
            elif current_weight >= base_weight * 1.3:
                tag = "warm"
            else:
                tag = "normal"

            tree.insert("", tk.END, values=(
                goal_id,
                title,
                weight_display,
                deadline_str,
                done_tasks,
                total_tasks,
                progress_text
            ), tags=(tag,))

        tree.tag_configure("completed", background="#e8f5e9", foreground="#2e7d32")
        tree.tag_configure("on_fire",   background="#ffebee", foreground="#c62828", font=("Helvetica", 10, "bold"))
        tree.tag_configure("hot",       background="#ffcdd2", foreground="#b71c1c")
        tree.tag_configure("warm",      background="#fff3e0", foreground="#ef6c00")
        tree.tag_configure("normal",    background="#ffffff", foreground="#000000")

    def load_today_tasks(self):
        tree = self.tree_today
        for i in tree.get_children():
            tree.delete(i)

        cursor = self.conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")

        cursor.execute('''
            SELECT t.id, t.title, t.duration_minutes, t.importance_level, t.deadline,
                g.title, t.status, t.blocks_task_ids
            FROM tasks t
            LEFT JOIN goals g ON t.goal_id = g.id
            WHERE t.scheduled_date = ? AND t.status IN ('todo', 'in_progress')
            ORDER BY t.importance_level DESC
        ''', (today,))

        for row in cursor.fetchall():
            task_id, title, duration, importance, deadline, goal_title, status, blocks_json = row

            deadline_str = deadline[:16].replace("T", " ") if deadline else "-"
            status_suffix = " [в процессе]" if status == "in_progress" else ""

            # Проверка: заблокирована ли задача
            blocked = False
            blocking_tasks = []
            if blocks_json:
                try:
                    blocked_ids = json.loads(blocks_json)
                    if blocked_ids:
                        placeholders = ','.join('?' * len(blocked_ids))
                        cursor.execute(f'''
                            SELECT id, title FROM tasks
                            WHERE id IN ({placeholders}) AND status != 'done'
                        ''', blocked_ids)
                        blocking = cursor.fetchall()
                        if blocking:
                            blocked = True
                            blocking_tasks = [f"{tid}: {tname}" for tid, tname in blocking]
                except Exception as e:
                    print(f"JSON error: {e}")

            # Отображение
            if blocked:
                hint = ", ".join(blocking_tasks[:2])
                if len(blocking_tasks) > 2:
                    hint += f" и ещё {len(blocking_tasks)-2}"
                title_display = f"[Заблокирована: {hint}] {title}"
                tag = "blocked"
            else:
                title_display = f"{title}{status_suffix}"
                tag = "normal" if status == "todo" else "in_progress"

            tree.insert("", tk.END, values=(
                task_id, title_display, f"{duration} мин", f"{importance}/10",
                deadline_str, goal_title or "-"
            ), tags=(tag,))

        # Стили
        tree.tag_configure("blocked", background="#ffebee", foreground="#c62828")
        tree.tag_configure("in_progress", background="#fff8e1", foreground="#e65100")
        tree.tag_configure("normal", background="#ffffff", foreground="#000000")

    def load_in_progress_tasks(self):
        tree = self.tree_in_progress
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

    def load_done_tasks(self):
        if not hasattr(self, 'tree_done') or not self.tree_done:
            return
        tree = self.tree_done
        for i in tree.get_children():
            tree.delete(i)
        cursor = self.conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute('''
            SELECT t.id, t.title, t.duration_minutes, t.importance_level, t.deadline,
                g.title
            FROM tasks t
            LEFT JOIN goals g ON t.goal_id = g.id
            WHERE t.scheduled_date = ? AND t.status = 'done'
            ORDER BY t.id DESC
        ''', (today,))
        for row in cursor.fetchall():
            deadline = row[4][:16].replace("T", " ") if row[4] else "-"
            tree.insert("", tk.END, values=(
                row[0], row[1], f"{row[2]} мин", f"{row[3]}/10", deadline, row[5] or "-"
            ))

    def show_goal_tasks(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите цель!")
            return
        goal_id = tree.item(selected[0])['values'][0]

        win = tk.Toplevel(self.main_app.root)
        win.title("Задачи цели")
        win.geometry("1200x500")
        win.configure(bg="#f0f4f8")
        win.grab_set()

        task_tree = ttk.Treeview(win, columns=("ID", "Задача", "Статус", "Дедлайн"), show="headings")
        for col in task_tree["columns"]:
            task_tree.heading(col, text=col)
            task_tree.column(col, width=150, anchor="center")
        task_tree.column("Задача", width=300, anchor="w")
        task_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, title, status, deadline
            FROM tasks
            WHERE goal_id = ?
            ORDER BY status, deadline
        ''', (goal_id,))
        for row in cursor.fetchall():
            deadline = row[3][:16].replace("T", " ") if row[3] else "-"
            status_ru = {"todo": "к выполнению", "in_progress": "в процессе", "done": "выполнена"}[row[2]]
            task_tree.insert("", tk.END, values=(row[0], row[1], status_ru, deadline))

    # === Общие методы работы с задачами ===
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
        self.refresh_all_tabs()

    def mark_done(self, tree):
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
        self.refresh_all_tabs()

    def delete_done(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите задачу для удаления!")
            return
        if not messagebox.askyesno("Удалить", "Удалить выбранные задачи навсегда?"):
            return

        cursor = self.conn.cursor()
        deleted = 0
        for item in selected:
            task_id = tree.item(item)['values'][0]
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            deleted += cursor.rowcount
        self.conn.commit()
        messagebox.showinfo("Готово", f"Удалено задач: {deleted}")
        self.refresh_all_tabs()

    def finish_task(self, tree):
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
        self.refresh_all_tabs()

    def return_to_todo(self, tree):
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
        self.refresh_all_tabs()