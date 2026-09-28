import sqlite3
from datetime import datetime, date


DB_NAME = "todo.db"


# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# --------------------------------------------------
# CREATE TABLES
# --------------------------------------------------

def create_tables():

    conn = get_connection()
    cursor = conn.cursor()

    # USERS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # TASKS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            company TEXT,
            role TEXT,
            description TEXT,
            due_date TEXT,
            completed INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            scheduled_time TEXT,

            location_name TEXT,
            location_lat REAL,
            location_lon REAL,
            location_radius REAL DEFAULT 200,

            location_required INTEGER DEFAULT 0,
            location_verified INTEGER DEFAULT 0,

            checkin_time TEXT,

            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # NOTES
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(task_id) REFERENCES tasks(id)
        )
    """)

    # DAILY ACTIVITY
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_date TEXT NOT NULL,
            UNIQUE(user_id, activity_date),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()

    # --------------------------------------------------
    # DATABASE MIGRATION
    # --------------------------------------------------
    # This is important because you already have todo.db.
    # It adds new columns to your old tasks table.

    cursor.execute("PRAGMA table_info(tasks)")
    existing_columns = {
        row["name"] for row in cursor.fetchall()
    }

    new_columns = {
        "scheduled_time": "TEXT",
        "location_name": "TEXT",
        "location_lat": "REAL",
        "location_lon": "REAL",
        "location_radius": "REAL DEFAULT 200",
        "location_required": "INTEGER DEFAULT 0",
        "location_verified": "INTEGER DEFAULT 0",
        "checkin_time": "TEXT"
    }

    for column, definition in new_columns.items():

        if column not in existing_columns:

            cursor.execute(
                f"ALTER TABLE tasks ADD COLUMN {column} {definition}"
            )

    conn.commit()
    conn.close()


# --------------------------------------------------
# USER FUNCTIONS
# --------------------------------------------------

def create_user(username, email, password):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO users
            (username, email, password)
            VALUES (?, ?, ?)
        """, (username, email, password))

        conn.commit()

        return True

    except sqlite3.IntegrityError:

        return False

    finally:

        conn.close()


def login_user(email, password):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        WHERE email = ?
        AND password = ?
    """, (email, password))

    user = cursor.fetchone()

    conn.close()

    if user:
        return dict(user)

    return None


# --------------------------------------------------
# TASK FUNCTIONS
# --------------------------------------------------

def add_task(
    user_id,
    title,
    company,
    role,
    description,
    due_date,
    scheduled_time=None,
    location_name=None,
    location_lat=None,
    location_lon=None,
    location_radius=200,
    location_required=0
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO tasks (
            user_id,
            title,
            company,
            role,
            description,
            due_date,
            scheduled_time,
            location_name,
            location_lat,
            location_lon,
            location_radius,
            location_required
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        title,
        company,
        role,
        description,
        due_date,
        scheduled_time,
        location_name,
        location_lat,
        location_lon,
        location_radius,
        location_required
    ))

    conn.commit()

    task_id = cursor.lastrowid

    conn.close()

    return task_id


def get_tasks(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM tasks
        WHERE user_id = ?
        ORDER BY
            due_date ASC,
            scheduled_time ASC,
            id DESC
    """, (user_id,))

    tasks = cursor.fetchall()

    conn.close()

    return [dict(task) for task in tasks]


def get_task(task_id, user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM tasks
        WHERE id = ?
        AND user_id = ?
    """, (task_id, user_id))

    task = cursor.fetchone()

    conn.close()

    if task:
        return dict(task)

    return None


def complete_task(task_id, user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE tasks
        SET completed = 1
        WHERE id = ?
        AND user_id = ?
    """, (task_id, user_id))

    conn.commit()

    conn.close()

    # Record activity for streak
    record_daily_activity(user_id)


def mark_task_location_verified(task_id, user_id):

    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        UPDATE tasks
        SET
            completed = 1,
            location_verified = 1,
            checkin_time = ?
        WHERE id = ?
        AND user_id = ?
    """, (
        now,
        task_id,
        user_id
    ))

    conn.commit()

    conn.close()

    # Update streak
    record_daily_activity(user_id)


def delete_task(task_id, user_id):

    conn = get_connection()
    cursor = conn.cursor()

    # Delete notes belonging to task
    cursor.execute("""
        DELETE FROM notes
        WHERE task_id = ?
    """, (task_id,))

    # Delete task
    cursor.execute("""
        DELETE FROM tasks
        WHERE id = ?
        AND user_id = ?
    """, (task_id, user_id))

    conn.commit()

    conn.close()


# --------------------------------------------------
# NOTES
# --------------------------------------------------

def add_note(task_id, content):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO notes
        (task_id, content)
        VALUES (?, ?)
    """, (task_id, content))

    conn.commit()

    conn.close()


def get_notes(task_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM notes
        WHERE task_id = ?
        ORDER BY created_at DESC
    """, (task_id,))

    notes = cursor.fetchall()

    conn.close()

    return [dict(note) for note in notes]


def delete_note(note_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM notes
        WHERE id = ?
    """, (note_id,))

    conn.commit()

    conn.close()


def get_all_notes(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            notes.id,
            notes.content,
            notes.created_at,
            tasks.title,
            tasks.company,
            tasks.role

        FROM notes

        JOIN tasks
        ON notes.task_id = tasks.id

        WHERE tasks.user_id = ?

        ORDER BY notes.created_at DESC
    """, (user_id,))

    notes = cursor.fetchall()

    conn.close()

    return [dict(note) for note in notes]


# --------------------------------------------------
# STREAK
# --------------------------------------------------

def record_daily_activity(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    today = date.today().isoformat()

    cursor.execute("""
        INSERT OR IGNORE INTO daily_activity
        (user_id, activity_date)
        VALUES (?, ?)
    """, (user_id, today))

    conn.commit()

    conn.close()


def check_in(user_id):

    record_daily_activity(user_id)


def get_activity_dates(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT activity_date
        FROM daily_activity
        WHERE user_id = ?
        ORDER BY activity_date
    """, (user_id,))

    rows = cursor.fetchall()

    conn.close()

    return [row["activity_date"] for row in rows]


def get_streak(user_id):

    dates = get_activity_dates(user_id)

    if not dates:
        return 0

    date_objects = sorted(
        datetime.strptime(d, "%Y-%m-%d").date()
        for d in dates
    )

    today = date.today()

    # If today isn't completed,
    # streak is counted from yesterday.
    if today in date_objects:

        current_day = today

    elif (today.fromordinal(today.toordinal() - 1)
          in date_objects):

        current_day = today.fromordinal(
            today.toordinal() - 1
        )

    else:

        return 0

    streak = 0

    while current_day in date_objects:

        streak += 1

        current_day = current_day.fromordinal(
            current_day.toordinal() - 1
        )

    return streak


def get_longest_streak(user_id):

    dates = get_activity_dates(user_id)

    if not dates:
        return 0

    date_objects = sorted(
        datetime.strptime(d, "%Y-%m-%d").date()
        for d in dates
    )

    longest = 1
    current = 1

    for i in range(1, len(date_objects)):

        difference = (
            date_objects[i] - date_objects[i - 1]
        ).days

        if difference == 1:

            current += 1

            longest = max(
                longest,
                current
            )

        else:

            current = 1

    return longest


def reset_streak(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM daily_activity
        WHERE user_id = ?
    """, (user_id,))

    conn.commit()

    conn.close()