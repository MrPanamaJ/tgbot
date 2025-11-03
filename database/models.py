
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, List

@dataclass
class User:
    user_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    created_at: datetime

@dataclass
class WeatherSubscription:
    user_id: int
    latitude: Optional[float]
    longitude: Optional[float]
    city_name: Optional[str]
    updated_at: datetime

@dataclass
class ServiceOrder:
    id: int
    user_id: int
    service_type: str
    contact_info: str
    created_at: datetime

@dataclass
class Note:
    id: int
    user_id: int
    note_text: str
    created_at: datetime
    
    def __init__(self, id, user_id, note_text, created_at):
        self.id = id
        self.user_id = user_id
        self.note_text = note_text
        self.created_at = created_at

@dataclass
class Habit:
    id: int
    user_id: int
    habit_name: str
    target_days: int
    current_streak: int
    created_at: datetime

@dataclass
class HabitTracking:
    id: int
    habit_id: int
    track_date: date
    completed: bool

@dataclass
class FinancialRecord:
    id: int
    user_id: int
    amount: float
    category: str
    description: str
    type: str  # 'income' or 'expense'
    created_at: datetime

@dataclass
class Reminder:
    id: int
    user_id: int
    reminder_text: str
    remind_time: datetime
    is_completed: bool

@dataclass
class UserData:
    user_id: int
    data_key: str
    data_value: str
    created_at: datetime
