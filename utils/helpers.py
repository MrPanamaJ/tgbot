import random
import string
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class TextAnalyzer:
    """Анализатор текста"""
    
    @staticmethod
    def analyze(text: str) -> Dict[str, Any]:
        """Анализ текста"""
        words = text.split()
        characters = len(text)
        characters_no_spaces = len(text.replace(' ', ''))
        
        # Подсчет предложений (по точкам, восклицательным и вопросительным знакам)
        sentences = text.count('.') + text.count('!') + text.count('?')
        
        # Расчет средней длины слова
        if words:
            average_word_length = sum(len(word) for word in words) / len(words)
        else:
            average_word_length = 0
        
        # Расчет времени чтения (средняя скорость ~200 слов в минуту)
        reading_time_minutes = max(1, len(words) // 200)
        
        return {
            'words': len(words),
            'characters': characters,
            'characters_no_spaces': characters_no_spaces,
            'sentences': sentences,
            'average_word_length': round(average_word_length, 1),
            'reading_time_minutes': reading_time_minutes
        }

class PasswordGenerator:
    """Генератор паролей"""
    
    @staticmethod
    def generate(length: int = 12, use_symbols: bool = True) -> str:
        """Генерация безопасного пароля"""
        characters = string.ascii_letters + string.digits
        if use_symbols:
            characters += string.punctuation
        
        # Гарантируем наличие разных типов символов
        password_chars = [
            random.choice(string.ascii_lowercase),
            random.choice(string.ascii_uppercase),
            random.choice(string.digits)
        ]
        
        if use_symbols:
            password_chars.append(random.choice(string.punctuation))
        
        # Добиваем до нужной длины
        while len(password_chars) < length:
            password_chars.append(random.choice(characters))
        
        # Перемешиваем
        random.shuffle(password_chars)
        
        return ''.join(password_chars)
    
    @staticmethod
    def strength_check(password: str) -> Dict[str, Any]:
        """Проверка сложности пароля"""
        score = 0
        feedback = []
        
        # Длина пароля
        if len(password) >= 12:
            score += 2
        elif len(password) >= 8:
            score += 1
        else:
            feedback.append("❌ Слишком короткий пароль")
        
        # Строчные буквы
        if any(c.islower() for c in password):
            score += 1
        else:
            feedback.append("❌ Добавьте строчные буквы")
        
        # Заглавные буквы
        if any(c.isupper() for c in password):
            score += 1
        else:
            feedback.append("❌ Добавьте заглавные буквы")
        
        # Цифры
        if any(c.isdigit() for c in password):
            score += 1
        else:
            feedback.append("❌ Добавьте цифры")
        
        # Специальные символы
        if any(c in string.punctuation for c in password):
            score += 1
        else:
            feedback.append("❌ Добавьте специальные символы")
        
        # Определение уровня сложности
        strength_levels = {
            5: "🔒 Очень сильный",
            4: "💪 Сильный",
            3: "✅ Средний", 
            2: "⚠️ Слабый",
            1: "❌ Очень слабый",
            0: "❌ Небезопасный"
        }
        
        return {
            'score': score,
            'strength': strength_levels.get(score, "❌ Небезопасный"),
            'feedback': feedback
        }

class HealthCalculator:
    """Калькуляторы здоровья"""
    
    @staticmethod
    def calculate_bmi(weight: float, height: float) -> Dict[str, Any]:
        """Расчет индекса массы тела"""
        height_m = height / 100
        bmi = weight / (height_m * height_m)
        
        # Определение категории по ИМТ
        if bmi < 16:
            category = "Выраженный дефицит массы тела"
        elif bmi < 18.5:
            category = "Недостаточная масса тела"
        elif bmi < 25:
            category = "Нормальная масса тела"
        elif bmi < 30:
            category = "Избыточная масса тела"
        elif bmi < 35:
            category = "Ожирение 1 степени"
        elif bmi < 40:
            category = "Ожирение 2 степени"
        else:
            category = "Ожирение 3 степени"
        
        return {
            'bmi': round(bmi, 1),
            'category': category,
            'ideal_min': round(18.5 * (height_m * height_m), 1),
            'ideal_max': round(25 * (height_m * height_m), 1),
            'healthy_range': f"{round(18.5 * (height_m * height_m), 1)} - {round(25 * (height_m * height_m), 1)} кг"
        }
    
    @staticmethod
    def calculate_calories(weight: float, height: float, age: int, gender: str, activity: str = 'medium') -> Dict[str, Any]:
        """Расчет суточной нормы калорий"""
        # Базальный метаболизм (BMR)
        if gender.lower() == 'male':
            bmr = 88.36 + (13.4 * weight) + (4.8 * height) - (5.7 * age)
        else:
            bmr = 447.6 + (9.2 * weight) + (3.1 * height) - (4.3 * age)
        
        # Коэффициент активности
        activity_multipliers = {
            'sedentary': 1.2,      # Сидячий образ жизни
            'light': 1.375,        # Легкая активность
            'medium': 1.55,        # Умеренная активность
            'high': 1.725,         # Высокая активность
            'extreme': 1.9         # Экстремальная активность
        }
        
        maintenance = bmr * activity_multipliers.get(activity, 1.55)
        
        return {
            'bmr': round(bmr),
            'maintenance': round(maintenance),
            'weight_loss': round(maintenance * 0.85),  # -15% для похудения
            'weight_gain': round(maintenance * 1.15)   # +15% для набора массы
        }

class QuoteGenerator:
    """Генератор цитат"""
    
    def __init__(self):
        self.quotes = [
            {
                "text": "Самый лучший способ взяться за что-то — перестать говорить и начать делать.",
                "author": "Уолт Дисней",
                "category": "мотивация"
            },
            {
                "text": "Успех — это способность двигаться от неудачи к неудаче, не теряя энтузиазма.",
                "author": "Уинстон Черчилль", 
                "category": "успех"
            },
            {
                "text": "Единственный способ делать великие дела — любить то, что ты делаешь.",
                "author": "Стив Джобс",
                "category": "работа"
            },
            {
                "text": "Жизнь — это то, что происходит с тобой, пока ты строишь другие планы.",
                "author": "Джон Леннон",
                "category": "жизнь"
            },
            {
                "text": "Будь собой; все остальные роли уже заняты.",
                "author": "Оскар Уайльд",
                "category": "саморазвитие"
            },
            {
                "text": "Не откладывай на завтра то, что можно сделать сегодня.",
                "author": "Бенджамин Франклин", 
                "category": "продуктивность"
            },
            {
                "text": "Единственный предел нашему завтрашнему дню — наши сегодняшние сомнения.",
                "author": "Франклин Рузвельт",
                "category": "уверенность"
            }
        ]
    
    def get_daily_quote(self) -> Dict[str, str]:
        """Получить случайную цитату"""
        quote = random.choice(self.quotes)
        return {
            'text': f"«{quote['text']}»",
            'author': f"— {quote['author']}",
            'full': f"«{quote['text']}»\n— {quote['author']}",
            'category': quote['category']
        }
    
    def get_quote_by_category(self, category: str) -> Optional[Dict[str, str]]:
        """Получить цитату по категории"""
        category_quotes = [q for q in self.quotes if q['category'] == category]
        if category_quotes:
            quote = random.choice(category_quotes)
            return {
                'text': f"«{quote['text']}»",
                'author': f"— {quote['author']}",
                'full': f"«{quote['text']}»\n— {quote['author']}"
            }
        return None

class DateTimeHelper:
    """Помощник для работы с датой и временем"""
    
    @staticmethod
    def parse_reminder_time(time_str: str) -> Optional[datetime]:
        """Парсинг времени для напоминаний"""
        try:
            from datetime import datetime
            import re
            
            time_str = time_str.strip().lower()
            
            # Обработка относительного времени
            if time_str.startswith('через'):
                # Извлекаем число и единицу измерения
                match = re.search(r'через\s+(\d+)\s*(час|часа|часов|день|дня|дней|минут|минуты)', time_str)
                if match:
                    number = int(match.group(1))
                    unit = match.group(2)
                    
                    now = datetime.now()
                    
                    if unit in ['час', 'часа', 'часов']:
                        return now + timedelta(hours=number)
                    elif unit in ['день', 'дня', 'дней']:
                        return now + timedelta(days=number)
                    elif unit in ['минут', 'минуты']:
                        return now + timedelta(minutes=number)
            
            # Попробуем разные форматы абсолютного времени
            formats = [
                "%d.%m.%Y %H:%M",
                "%d.%m %H:%M", 
                "%H:%M",
                "%d.%m.%Y",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d"
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(time_str, fmt)
                    # Если год не указан, используем текущий/следующий
                    if dt.year == 1900:
                        now = datetime.now()
                        dt = dt.replace(year=now.year)
                        if dt < now:
                            dt = dt.replace(year=now.year + 1)
                    return dt
                except ValueError:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing time: {e}")
            return None
    
    @staticmethod
    def format_duration(minutes: int) -> str:
        """Форматирование длительности в читаемый вид"""
        if minutes < 60:
            return f"{minutes} мин"
        elif minutes < 1440:
            hours = minutes // 60
            mins = minutes % 60
            return f"{hours} ч {mins} мин" if mins > 0 else f"{hours} ч"
        else:
            days = minutes // 1440
            hours = (minutes % 1440) // 60
            return f"{days} д {hours} ч"
    
    @staticmethod
    def format_datetime(dt: datetime) -> str:
        """Форматирование datetime в читаемый вид"""
        now = datetime.now()
        
        if dt.date() == now.date():
            return f"сегодня в {dt.strftime('%H:%M')}"
        elif dt.date() == (now.date() - timedelta(days=1)):
            return f"вчера в {dt.strftime('%H:%M')}"
        elif dt.year == now.year:
            return dt.strftime('%d.%m в %H:%M')
        else:
            return dt.strftime('%d.%m.%Y в %H:%M')
        
        # ВРЕМЕННОЕ РЕШЕНИЕ для обратной совместимости
try:
    from .validators import InputValidator
except ImportError:
    # Простая заглушка
    class InputValidator:
        @staticmethod
        def validate_amount(amount_text):
            try:
                amount_clean = ''.join(c for c in amount_text if c.isdigit() or c in '.,')
                amount_clean = amount_clean.replace(',', '.')
                value = float(amount_clean)
                return True, value, "✅ Сумма корректна"
            except:
                return False, None, "❌ Неверный формат числа"