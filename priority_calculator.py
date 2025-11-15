from datetime import datetime
import sqlite3
from typing import Optional, List, Dict, Any
import json
import math

WEIGHTS = {
    "urgency": 0.35,
    "importance": 0.25,
    "goal_alignment": 0.15,
    "dependency_bonus": 0.08,
    "context_match": 0.08,
    "time_cost": 0.09
}

TIME_OF_DAY_MATCH = {
    "morning":   {"creative": 1.0, "analytical": 0.9, "routine": 0.7, "communication": 0.6},
    "afternoon": {"creative": 0.6, "analytical": 0.8, "routine": 1.0, "communication": 1.0},
    "evening":   {"creative": 0.3, "analytical": 0.5, "routine": 0.9, "communication": 0.8},
    "night":     {"creative": 0.1, "analytical": 0.2, "routine": 0.6, "communication": 0.4},
}

ENERGY_MATCH = {
    "high":  {"high": 1.0, "medium": 0.4, "low": 0.3},
    "medium":{"high": 0.8, "medium": 0.8, "low": 0.5},
    "low":   {"high": 0.3, "medium": 0.5, "low": 1.0}
}

class Task:
    def __init__(self, id, title, duration, importance_level, deadline=None, goal_weight=1.0,
                 contribution=1.0, energy_type="medium", task_type="routine", dependents=0):
        self.id = id
        self.title = title
        self.duration = duration
        self.importance_level = min(5, max(1, importance_level // 2))  # 1-10 → 1-5
        self.deadline = datetime.fromisoformat(deadline) if deadline else None
        self.goal_weight = goal_weight
        self.contribution = contribution
        self.energy_type = energy_type
        self.task_type = task_type
        self.dependents = dependents

class PriorityCalculator:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get_current_context(self) -> Dict[str, Any]:
        now = datetime.now()
        hour = now.hour
        time_of_day = ("morning" if 5 <= hour < 12 else
                       "afternoon" if 12 <= hour < 17 else
                       "evening" if 17 <= hour < 22 else "night")
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT energy_level FROM user_energy ORDER BY updated_at DESC LIMIT 1")
        row = cursor.fetchone()
        energy_level = row[0] if row else "medium"

        day_en = now.strftime("%A").lower()

        return {"now": now, "time_of_day": time_of_day, "energy_level": energy_level, 
                "day": day_en}
    
    def is_working_time(self, context: Dict) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("SELECT start_time, end_time FROM schedule WHERE day_of_week = ?", (context["day"],))
        row = cursor.fetchone()
        if not row: return False
        start_str, end_str = row
        try:
            start = datetime.strptime(start_str, "%H:%M").time()
            end = datetime.strptime(end_str, "%H:%M").time()
            return start <= context["now"].time() <= end
        except: return False

    def fetch_tasks(self) -> List[Task]:
        cursor = self.conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")

        cursor.execute('''
            SELECT t.id, t.title, t.duration_minutes, t.importance_level, t.deadline,
                t.goal_id, g.weight, t.energy_type, t.task_type, t.blocks_task_ids,
                t.contribution
            FROM tasks t
            LEFT JOIN goals g ON t.goal_id = g.id
            WHERE t.scheduled_date = ? AND t.status = 'todo'
        ''', (today,))
        
        rows = cursor.fetchall()
        tasks = []

        for row in rows:
            task_id = row[0]
            blocks_json = row[9] 

            # Проверяем: есть ли среди "заблокированных" невыполненные
            blocked = False
            if blocks_json:
                try:
                    blocked_ids = json.loads(blocks_json)
                    if blocked_ids:
                        placeholders = ','.join('?' * len(blocked_ids))
                        cursor.execute(f'''
                            SELECT COUNT(*) FROM tasks
                            WHERE id IN ({placeholders}) AND status != 'done'
                        ''', blocked_ids)
                        if cursor.fetchone()[0] > 0:
                            blocked = True
                except:
                    pass

            if blocked:
                continue 

            # Если дошли сюда — задача доступна
            dependents = self.count_dependents(task_id)
            goal_weight = row[6] if row[6] is not None else 1.0
            contribution = row[10] if row[10] is not None else 0.8
            tasks.append(Task(
                id=task_id, title=row[1], duration=row[2], importance_level=row[3],
                deadline=row[4], goal_weight=goal_weight, contribution=contribution,
                energy_type=row[7], task_type=row[8], dependents=dependents
            ))
        return tasks
    
    def count_dependents(self, task_id: int) -> int:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM tasks
            WHERE blocks_task_ids LIKE ? AND status = 'todo'
        ''', (f'%"{task_id}"%',))
        return cursor.fetchone()[0]
    
    # === Компоненты ===
    def calculate_urgency(self, task: Task, now: datetime) -> float:
        if not task.deadline: return 0.3
        hours_left = max(0.1, (task.deadline - now).total_seconds() / 3600)
        return min(1.0, 1 / (hours_left ** 0.7))
    
    def calculate_importance(self, task: Task) -> float:
        return task.importance_level / 5.0
    
    def calculate_goal_alignment(self, task: Task) -> float:
        return min(1.0, task.goal_weight * task.contribution)
    
    def calculate_dependency_bonus(self, task: Task) -> float:
        return min(0.5, math.log(1 + task.dependents) * 0.3)
    
    def calculate_context_match(self, task: Task, context: Dict) -> float:
        energy_match = ENERGY_MATCH[context["energy_level"]][task.energy_type]
        time_match = TIME_OF_DAY_MATCH[context["time_of_day"]].get(task.task_type, 0.5)
        return (energy_match + time_match + 1.0) / 3.0

    def calculate_time_cost(self, task: Task) -> float:
        return min(1.0, task.duration / 240.0)
    
    def calculate_priority(self, task: Task, context: Dict) -> Dict:
        components = {
            "urgency": self.calculate_urgency(task, context["now"]),
            "importance": self.calculate_importance(task),
            "goal_alignment": self.calculate_goal_alignment(task),
            "dependency_bonus": self.calculate_dependency_bonus(task),
            "context_match": self.calculate_context_match(task, context),
            "time_cost": self.calculate_time_cost(task)
        }
        score = sum(WEIGHTS[k] * v for k, v in components.items())
        return {"task": task, "score": round(score, 3), "breakdown": {k: round(v, 3) for k, v in components.items()}}
    
    def recommend_task(self) -> Optional[Dict]:
        context = self.get_current_context()
        if not self.is_working_time(context): 
            return None
        tasks = self.fetch_tasks()
        if not tasks: 
            return None

        scored = [self.calculate_priority(t, context) for t in tasks]
        scored.sort(key=lambda x: x["score"], reverse=True)
        best = scored[0]

        return {
            "task": best["task"],
            "score": best["score"],
            "reason": self.format_reason(best["breakdown"], context)
        }

    def format_reason(self, b: Dict, ctx: Dict) -> str:
        parts = []
        if b["urgency"] > 0.6: parts.append("горит дедлайн")
        if b["importance"] > 0.8: parts.append("очень важно")
        if b["goal_alignment"] > 0.6: parts.append("шаг к цели")
        if b["dependency_bonus"] > 0.2: parts.append(f"разблокирует {int(math.exp(b['dependency_bonus']/0.3))-1} задач")
        if b["context_match"] > 0.7: parts.append(f"подходит для {ctx['time_of_day']} и энергии")
        if b["time_cost"] < 0.2: parts.append("быстро")
        return ", ".join(parts) or "хороший баланс"
    
def what_to_do_now_smart(conn: sqlite3.Connection):
    calc = PriorityCalculator(conn)
    rec = calc.recommend_task()
    if not rec:
        print("Сейчас не рабочее время или нет задач. Отдыхай!")
        return
    
    t = rec["task"]
    print(f"\nСейчас лучше всего:")
    print(f"   {t.title}")
    print(f"   Время: {t.duration} мин | Важность: {t.importance}/5")
    print(f"   Приоритет: {rec['score']:.3f}")
    print(f"   Почему: {rec['reason']}")

    cursor = conn.cursor()
    cursor.execute('UPDATE tasks SET status = "in_progress" WHERE id = ?', (t.id,))
    conn.commit()

        