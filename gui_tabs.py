import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

class GUITabs:
    def __init__(self, main_app):
        self.main_app = main_app
        self.conn = main_app.conn
        self.setup_styles()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", padding=6, font=('Helvetica', 10))
        style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff")
        style.configure("InProgress.Treeview", background="#fff8e1", fieldbackground="#fff8e1")

    def create_tabs(self):
        tab_control = ttk.Notebook(self.main_app.root)
        tab_control.pack(pady=15, padx=20, fill=tk.BOTH, expand=True)

        # Вкладка 1: Задачи на сегодня
        today_frame = tk.Frame(tab_control, bg="#f0f4f8")
        tab_control.add(today_frame, text=" Задачи на сегодня ")

        # Вкладка 2: В процессе
        in_progress_frame = tk.Frame(tab_control, bg="#f0f4f8")
        tab_control.add(in_progress_frame, text=" В процессе ")

        self.setup_task_tree(today_frame, "today")
        self.setup_task_tree(in_progress_frame, "in_progress")

    def setup_task_tree(self, parent, tab_type):
        frame = tk.LabelFrame(parent, text=" ", font=("Helvetica", 10))
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("ID", "Задача", "Время", "Важность", "Дедлайн", "Цель")
        style_name = "InProgress.Treeview" if tab_type == "in_progress" else "Treeview"
        
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=10, 
                           style=style_name, selectmode="extended")
        
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

        # Кнопки в зависимости от типа вкладки
        if tab_type == "today":
            ttk.Button(btn_frame, text="Отметить как выполнено",
                      command=lambda: self.mark_done(tree)).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Перенести на завтра",
                      command=lambda: self.postpone_selected(tree)).pack(side=tk.LEFT, padx=5)
        else:  # in_progress
            ttk.Button(btn_frame, text="Завершить задачу",
                      command=lambda: self.finish_task(tree)).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Перенести на завтра",
                      command=lambda: self.postpone_selected(tree)).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Вернуть в список",
                      command=lambda: self.return_to_todo(tree)).pack(side=tk.LEFT, padx=5)

        # Сохраняем ссылки на деревья
        if tab_type == "today":
            self.tree_today = tree
        else:
            self.tree_in_progress = tree

    def refresh_all_tabs(self):
        self.load_today_tasks()
        self.load_in_progress_tasks()

    def load_today_tasks(self):
        tree = self.tree_today
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