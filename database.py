import sqlite3
import logging

CONFIG_DB_PATH = "config.db"

def init_db():
    conn = sqlite3.connect(CONFIG_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS config (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT NOT NULL UNIQUE,
        value TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_number TEXT NOT NULL UNIQUE,
        pin TEXT NOT NULL,
        email TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS audit_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS audit_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        auditor_id INTEGER,
        audit_date TEXT,
        audit_time TEXT,
        description TEXT,
        FOREIGN KEY(auditor_id) REFERENCES users(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS audit_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        auditor TEXT NOT NULL,
        team_member TEXT NOT NULL,
        question_id INTEGER NOT NULL,
        response TEXT NOT NULL,
        comments TEXT,
        FOREIGN KEY (question_id) REFERENCES audit_questions (id)
    )
    ''')

    conn.commit()
    conn.close()

def add_config(key, value):
    try:
        conn = sqlite3.connect(CONFIG_DB_PATH)
        cursor = conn.cursor()
        cursor.execute('REPLACE INTO config (key, value) VALUES (?, ?)', (key, value))
        conn.commit()
    except Exception as e:
        logging.error(f"Failed to add config: {e}")
    finally:
        conn.close()

def get_config(key):
    try:
        conn = sqlite3.connect(CONFIG_DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM config WHERE key = ?', (key,))
        value = cursor.fetchone()
        return value[0] if value else None
    except Exception as e:
        logging.error(f"Failed to get config: {e}")
        return None
    finally:
        conn.close()

def add_user(employee_number, pin, email):
    try:
        conn = sqlite3.connect(CONFIG_DB_PATH)
        cursor = conn.cursor()
        cursor.execute('REPLACE INTO users (employee_number, pin, email) VALUES (?, ?, ?)', (employee_number, pin, email))
        conn.commit()
    except Exception as e:
        logging.error(f"Failed to add user: {e}")
    finally:
        conn.close()

def get_users():
    try:
        conn = sqlite3.connect(CONFIG_DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users')
        users = cursor.fetchall()
        return users
    except Exception as e:
        logging.error(f"Failed to get users: {e}")
        return []
    finally:
        conn.close()

def add_audit_question(question):
    try:
        conn = sqlite3.connect(CONFIG_DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO audit_questions (question) VALUES (?)', (question,))
        conn.commit()
    except Exception as e:
        logging.error(f"Failed to add audit question: {e}")
    finally:
        conn.close()

def get_audit_questions():
    try:
        conn = sqlite3.connect(CONFIG_DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM audit_questions')
        questions = cursor.fetchall()
        return questions
    except Exception as e:
        logging.error(f"Failed to get audit questions: {e}")
        return []
    finally:
        conn.close()

def delete_audit_question(question_id):
    try:
        conn = sqlite3.connect(CONFIG_DB_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM audit_questions WHERE id = ?', (question_id,))
        conn.commit()
    except Exception as e:
        logging.error(f"Failed to delete audit question: {e}")
    finally:
        conn.close()

def schedule_audit(auditor_id, audit_date, audit_time, description):
    try:
        conn = sqlite3.connect(CONFIG_DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO audit_schedule (auditor_id, audit_date, audit_time, description) VALUES (?, ?, ?, ?)',
                       (auditor_id, audit_date, audit_time, description))
        conn.commit()
        conn.close()
        send_audit_notification(auditor_id, audit_date, audit_time, description)
    except Exception as e:
        logging.error(f"Failed to schedule audit: {e}")

def get_audit_schedules():
    try:
        conn = sqlite3.connect(CONFIG_DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM audit_schedule')
        schedules = cursor.fetchall()
        conn.close()
        return schedules
    except Exception as e:
        logging.error(f"Failed to get audit schedules: {e}")
        return []
