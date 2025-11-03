import sqlite3
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any, Tuple
from .models import *

class DatabaseManager:
    """Менеджер для работы с базой данных"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_adapters()
        self._create_tables()
    
    def _init_adapters(self):
        """Инициализация адаптеров для дат"""
        sqlite3.register_adapter(date, lambda val: val.isoformat())
        sqlite3.register_adapter(datetime, lambda val: val.isoformat())
        sqlite3.register_converter("DATE", lambda val: date.fromisoformat(val.decode() if isinstance(val, bytes) else val))
        sqlite3.register_converter("DATETIME", lambda val: datetime.fromisoformat(val.decode() if isinstance(val, bytes) else val))
    
    def _create_tables(self):
        """Создание таблиц"""
        with self._get_connection() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS weather_subscriptions (
                    user_id INTEGER PRIMARY KEY,
                    latitude REAL,
                    longitude REAL,
                    city_name TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS service_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    service_type TEXT,
                    contact_info TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    note_text TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS habits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    habit_name TEXT,
                    target_days INTEGER DEFAULT 21,
                    current_streak INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS habit_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    habit_id INTEGER,
                    track_date DATE,
                    completed BOOLEAN DEFAULT FALSE
                );
                
                CREATE TABLE IF NOT EXISTS finances (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount REAL,
                    category TEXT,
                    description TEXT,
                    type TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    reminder_text TEXT,
                    remind_time DATETIME,
                    is_completed BOOLEAN DEFAULT FALSE
                );
                
                CREATE TABLE IF NOT EXISTS user_data (
                    user_id INTEGER,
                    data_key TEXT,
                    data_value TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, data_key)
                );
            ''')
    
    def _get_connection(self) -> sqlite3.Connection:
        """Получение соединения с БД"""
        return sqlite3.connect(
            self.db_path,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
    
    # User operations
    def get_or_create_user(self, user_id: int, username: str, first_name: str, last_name: str) -> User:
        """Создание или получение пользователя"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR IGNORE INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)',
                (user_id, username, first_name, last_name)
            )
            cursor.execute('SELECT user_id, username, first_name, last_name, created_at FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                return User(
                    user_id=row[0],
                    username=row[1],
                    first_name=row[2],
                    last_name=row[3],
                    created_at=row[4]
                )
            return None
    
    # Weather operations
    def save_weather_subscription(self, subscription: WeatherSubscription) -> bool:
        """Сохранение подписки на погоду"""
        with self._get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO weather_subscriptions 
                (user_id, latitude, longitude, city_name, updated_at) VALUES (?, ?, ?, ?, ?)
            ''', (subscription.user_id, subscription.latitude, subscription.longitude, 
                subscription.city_name, subscription.updated_at))
            return True

    def get_weather_subscription(self, user_id: int) -> Optional[WeatherSubscription]:
        """Получение подписки на погоду"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id, latitude, longitude, city_name, updated_at FROM weather_subscriptions WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                return WeatherSubscription(
                    user_id=row[0],
                    latitude=row[1],
                    longitude=row[2],
                    city_name=row[3],
                    updated_at=row[4]
                )
            return None

    def get_weather_subscriptions(self) -> List[WeatherSubscription]:
        """Получение всех подписок на погоду"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id, latitude, longitude, city_name, updated_at FROM weather_subscriptions')
            subscriptions = []
            for row in cursor.fetchall():
                subscriptions.append(WeatherSubscription(
                    user_id=row[0],
                    latitude=row[1],
                    longitude=row[2],
                    city_name=row[3],
                    updated_at=row[4]
                ))
            return subscriptions
    
    def delete_weather_subscription(self, user_id: int) -> bool:
        """Удаление подписки на погоду"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM weather_subscriptions WHERE user_id = ?', (user_id,))
            return cursor.rowcount > 0
    
    # Service orders operations
    def add_service_order(self, order: ServiceOrder) -> int:
        """Добавление заказа услуги"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO service_orders (user_id, service_type, contact_info)
                VALUES (?, ?, ?)
            ''', (order.user_id, order.service_type, order.contact_info))
            return cursor.lastrowid
    
    def get_user_service_orders(self, user_id: int) -> List[ServiceOrder]:
        """Получение заказов пользователя"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, user_id, service_type, contact_info, created_at FROM service_orders WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
            orders = []
            for row in cursor.fetchall():
                orders.append(ServiceOrder(
                    id=row[0],
                    user_id=row[1],
                    service_type=row[2],
                    contact_info=row[3],
                    created_at=row[4]
                ))
            return orders
    
    # Notes operations
    def add_note(self, note: Note) -> int:
        """Добавление заметки"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO notes (user_id, note_text) VALUES (?, ?)', (note.user_id, note.note_text))
            return cursor.lastrowid
    
    def get_user_notes(self, user_id: int) -> List[Note]:
        """Получение заметок пользователя"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, user_id, note_text, created_at FROM notes WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
            notes = []
            for row in cursor.fetchall():
                notes.append(Note(
                    id=row[0],
                    user_id=row[1],
                    note_text=row[2],
                    created_at=row[3]
                ))
            return notes
    
    def get_note_by_id(self, note_id: int) -> Optional[Note]:
        """Получение заметки по ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, user_id, note_text, created_at FROM notes WHERE id = ?', (note_id,))
            row = cursor.fetchone()
            if row:
                return Note(
                    id=row[0],
                    user_id=row[1],
                    note_text=row[2],
                    created_at=row[3]
                )
            return None
    
    def delete_note(self, note_id: int) -> bool:
        """Удаление заметки"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
            return cursor.rowcount > 0
    
    # Habits operations
    def add_habit(self, habit: Habit) -> int:
        """Добавление привычки"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO habits (user_id, habit_name, target_days)
                VALUES (?, ?, ?)
            ''', (habit.user_id, habit.habit_name, habit.target_days))
            return cursor.lastrowid
    
    def get_user_habits(self, user_id: int) -> List[Habit]:
        """Получение привычек пользователя"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, user_id, habit_name, target_days, current_streak, created_at FROM habits WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
            habits = []
            for row in cursor.fetchall():
                habits.append(Habit(
                    id=row[0],
                    user_id=row[1],
                    habit_name=row[2],
                    target_days=row[3],
                    current_streak=row[4],
                    created_at=row[5]
                ))
            return habits

    def get_habit_by_id(self, habit_id: int) -> Optional[Habit]:
        """Получение привычки по ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, user_id, habit_name, target_days, current_streak, created_at FROM habits WHERE id = ?', (habit_id,))
            row = cursor.fetchone()
            if row:
                return Habit(
                    id=row[0],
                    user_id=row[1],
                    habit_name=row[2],
                    target_days=row[3],
                    current_streak=row[4],
                    created_at=row[5]
                )
            return None
    
    def is_habit_completed_today(self, habit_id: int) -> bool:
        """Проверка выполнения привычки сегодня"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            today = date.today().isoformat()
            cursor.execute('''
                SELECT id FROM habit_tracking 
                WHERE habit_id = ? AND track_date = ? AND completed = TRUE
            ''', (habit_id, today))
            return cursor.fetchone() is not None
    
    def toggle_habit_completion(self, habit_id: int) -> bool:
        """Переключение статуса выполнения привычки"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            today = date.today().isoformat()
            
            # Проверка, отмечена ли привычка сегодня
            cursor.execute('SELECT id FROM habit_tracking WHERE habit_id = ? AND track_date = ?', (habit_id, today))
            existing = cursor.fetchone()
            
            if existing:
                # Снимаем отметку
                cursor.execute('DELETE FROM habit_tracking WHERE habit_id = ? AND track_date = ?', (habit_id, today))
                completed = False
            else:
                # Ставим отметку
                cursor.execute('INSERT INTO habit_tracking (habit_id, track_date, completed) VALUES (?, ?, ?)', 
                             (habit_id, today, True))
                completed = True
            
            return completed
    
    def update_habit_streak(self, habit_id: int):
        """Обновление серии выполнения привычки"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Получаем даты выполнения за последние 30 дней
            cursor.execute('''
                SELECT track_date FROM habit_tracking 
                WHERE habit_id = ? AND completed = TRUE 
                ORDER BY track_date DESC LIMIT 30
            ''', (habit_id,))
            
            dates = [row[0] for row in cursor.fetchall()]
            current_streak = 0
            today = date.today()
            
            # Подсчет текущей серии (последовательных дней выполнения)
            for i in range(len(dates)):
                expected_date = (today - timedelta(days=i)).isoformat()
                if expected_date in dates:
                    current_streak += 1
                else:
                    break
            
            cursor.execute('UPDATE habits SET current_streak = ? WHERE id = ?', (current_streak, habit_id))
    
    def delete_habit(self, habit_id: int) -> bool:
        """Удаление привычки"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM habit_tracking WHERE habit_id = ?', (habit_id,))
            cursor.execute('DELETE FROM habits WHERE id = ?', (habit_id,))
            return cursor.rowcount > 0
    
    def get_todays_uncompleted_habits(self) -> List[Habit]:
        """Получение привычек, не выполненных сегодня"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            today = date.today().isoformat()
            cursor.execute('''
                SELECT h.id, h.user_id, h.habit_name, h.target_days, h.current_streak, h.created_at 
                FROM habits h
                WHERE NOT EXISTS (
                    SELECT 1 FROM habit_tracking ht 
                    WHERE ht.habit_id = h.id AND ht.track_date = ? AND ht.completed = TRUE
                )
            ''', (today,))
            habits = []
            for row in cursor.fetchall():
                habits.append(Habit(
                    id=row[0],
                    user_id=row[1],
                    habit_name=row[2],
                    target_days=row[3],
                    current_streak=row[4],
                    created_at=row[5]
                ))
            return habits
    
    # Finance operations
    def add_financial_record(self, record: FinancialRecord) -> int:
        """Добавление финансовой записи"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO finances (user_id, amount, category, description, type)
                VALUES (?, ?, ?, ?, ?)
            ''', (record.user_id, record.amount, record.category, record.description, record.type))
            return cursor.lastrowid
    
    def get_financial_report(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Получение финансового отчета"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            # Итоги по типам операций
            cursor.execute('''
                SELECT type, SUM(amount) as total
                FROM finances 
                WHERE user_id = ? AND date(created_at) >= ?
                GROUP BY type
            ''', (user_id, start_date))
            
            totals = cursor.fetchall()
            
            # Детализация по категориям
            cursor.execute('''
                SELECT category, type, SUM(amount) as total
                FROM finances 
                WHERE user_id = ? AND date(created_at) >= ?
                GROUP BY category, type
                ORDER BY total DESC
            ''', (user_id, start_date))
            
            categories = cursor.fetchall()
            
            # Расчет итоговых сумм
            total_income = 0
            total_expense = 0
            for record_type, total in totals:
                if record_type == 'income':
                    total_income = total or 0
                else:
                    total_expense = total or 0
            
            return {
                'total_income': total_income,
                'total_expense': total_expense,
                'balance': total_income - total_expense,
                'categories': categories,
                'period': f'{days} дней'
            }
    
    def get_users_with_finances(self) -> List[User]:
        """Получение пользователей с финансовыми операциями"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT u.user_id, u.username, u.first_name, u.last_name, u.created_at 
                FROM users u
                JOIN finances f ON u.user_id = f.user_id
            ''')
            users = []
            for row in cursor.fetchall():
                users.append(User(
                    user_id=row[0],
                    username=row[1],
                    first_name=row[2],
                    last_name=row[3],
                    created_at=row[4]
                ))
            return users
    
    # Reminders operations
    def create_reminder(self, user_id: int, reminder_text: str, remind_time: datetime) -> int:
        """Создание напоминания"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO reminders (user_id, reminder_text, remind_time)
                VALUES (?, ?, ?)
            ''', (user_id, reminder_text, remind_time))
            return cursor.lastrowid
    
    def get_pending_reminders(self) -> List[Reminder]:
        """Получение активных напоминаний"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('SELECT id, user_id, reminder_text, remind_time, is_completed FROM reminders WHERE remind_time <= ? AND is_completed = FALSE', (now,))
            reminders = []
            for row in cursor.fetchall():
                reminders.append(Reminder(
                    id=row[0],
                    user_id=row[1],
                    reminder_text=row[2],
                    remind_time=row[3],
                    is_completed=row[4]
                ))
            return reminders
    
    def complete_reminder(self, reminder_id: int):
        """Отметка напоминания как выполненного"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE reminders SET is_completed = TRUE WHERE id = ?', (reminder_id,))
    
    # User data operations (для временных данных)
    def save_temp_data(self, user_id: int, data_key: str, data_value: str):
        """Сохранение временных данных"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_data (user_id, data_key, data_value)
                VALUES (?, ?, ?)
            ''', (user_id, data_key, data_value))
    
    def get_temp_data(self, user_id: int, data_key: str) -> Optional[str]:
        """Получение временных данных"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT data_value FROM user_data WHERE user_id = ? AND data_key = ?', (user_id, data_key))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def clear_temp_data(self, user_id: int, keys: List[str] = None):
        """Очистка временных данных"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if keys:
                placeholders = ','.join('?' for _ in keys)
                cursor.execute(f'DELETE FROM user_data WHERE user_id = ? AND data_key IN ({placeholders})', 
                             (user_id, *keys))
            else:
                cursor.execute('DELETE FROM user_data WHERE user_id = ?', (user_id,))
    
    # General operations
    def get_active_users(self) -> List[User]:
        """Получение активных пользователей"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id, username, first_name, last_name, created_at FROM users')
            users = []
            for row in cursor.fetchall():
                users.append(User(
                    user_id=row[0],
                    username=row[1],
                    first_name=row[2],
                    last_name=row[3],
                    created_at=row[4]
                ))
            return users
    
    def close(self):
        """Закрытие соединения с БД"""
        pass  # SQLite автоматически закрывает соединения