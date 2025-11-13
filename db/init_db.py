def init_db(conn):
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY,
            day_of_week TEXT NOT NULL UNIQUE,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            weight REAL DEFAULT 1.0,  -- 0.1–1.0
            deadline TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL,
            importance_level INTEGER NOT NULL CHECK(importance_level BETWEEN 1 AND 10),
            status TEXT DEFAULT 'todo',
            created_date TEXT NOT NULL,
            scheduled_date TEXT NOT NULL,
            deadline TEXT,                    
            goal_id INTEGER,                  
            energy_type TEXT DEFAULT 'medium',-- low, medium, high
            task_type TEXT DEFAULT 'routine', -- creative, analytical, routine, communication
            blocks_task_ids TEXT,             -- JSON: "[2,5]" ЗАВИСИМОСТИ
            contribution REAL DEFAULT 0.8,
            FOREIGN KEY(goal_id) REFERENCES goals(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_energy (
            id INTEGER PRIMARY KEY,
            energy_level TEXT NOT NULL,  -- low, medium, high
            updated_at TEXT NOT NULL
        )
    ''')

    conn.commit()