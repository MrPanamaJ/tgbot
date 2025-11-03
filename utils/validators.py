import re
from typing import Optional, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)

class InputValidator:
    """Валидатор вводимых данных"""
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Валидация email адреса"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_valid = bool(re.match(pattern, email))
        message = "✅ Email корректен" if is_valid else "❌ Неверный формат email"
        return is_valid, message
    
    @staticmethod
    def validate_phone(phone: str) -> Tuple[bool, str]:
        """Валидация номера телефона"""
        # Удаляем все нецифровые символы кроме +
        cleaned_phone = re.sub(r'[^\d+]', '', phone)
        pattern = r'^[\+]?[0-9\s\-\(\)]{10,15}$'
        is_valid = bool(re.match(pattern, phone))
        message = "✅ Телефон корректен" if is_valid else "❌ Неверный формат телефона"
        return is_valid, message
    
    @staticmethod
    def validate_amount(amount: str) -> Tuple[bool, Optional[float], str]:
        """Валидация денежной суммы"""
        try:
            # Обработка разных форматов ввода (300, 300р, 300 руб и т.д.)
            amount_text = amount.strip().lower()
            # Удаление всех нечисловых символов, кроме точки и запятой
            amount_clean = ''.join(c for c in amount_text if c.isdigit() or c in '.,')
            
            if not amount_clean:
                return False, None, "❌ Введите число"
            
            # Замена запятой на точку для корректного преобразования
            amount_clean = amount_clean.replace(',', '.')
            value = float(amount_clean)
            
            if value <= 0:
                return False, None, "❌ Сумма должна быть больше 0"
            
            return True, value, "✅ Сумма корректна"
            
        except ValueError:
            return False, None, "❌ Неверный формат числа"
    
    @staticmethod
    def validate_text_length(text: str, min_length: int = 1, max_length: int = 1000) -> Tuple[bool, str]:
        """Валидация длины текста"""
        length = len(text.strip())
        if length < min_length:
            return False, f"❌ Текст слишком короткий (минимум {min_length} символов)"
        elif length > max_length:
            return False, f"❌ Текст слишком длинный (максимум {max_length} символов)"
        else:
            return True, "✅ Текст корректен"
    
    @staticmethod
    def validate_date(date_str: str) -> Tuple[bool, Optional[str], str]:
        """Валидация даты"""
        try:
            from datetime import datetime
            
            # Попробуем разные форматы дат
            formats = [
                "%d.%m.%Y",
                "%d.%m.%Y %H:%M",
                "%d.%m %H:%M",
                "%H:%M",
                "%Y-%m-%d",
                "%Y-%m-%d %H:%M:%S"
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return True, dt.isoformat(), "✅ Дата корректна"
                except ValueError:
                    continue
            
            return False, None, "❌ Неверный формат даты"
            
        except Exception as e:
            logger.error(f"Date validation error: {e}")
            return False, None, "❌ Ошибка валидации даты"
    
    @staticmethod
    def validate_number_range(number: str, min_val: float, max_val: float) -> Tuple[bool, Optional[float], str]:
        """Валидация числа в диапазоне"""
        try:
            value = float(number)
            if min_val <= value <= max_val:
                return True, value, f"✅ Число в диапазоне {min_val}-{max_val}"
            else:
                return False, None, f"❌ Число должно быть от {min_val} до {max_val}"
        except ValueError:
            return False, None, "❌ Введите число"

class FinanceValidator:
    """Специализированный валидатор для финансовых операций"""
    
    @staticmethod
    def validate_financial_record(amount: float, category: str, description: str) -> Tuple[bool, str]:
        """Валидация финансовой записи"""
        errors = []
        
        # Проверка суммы
        if amount <= 0:
            errors.append("Сумма должна быть больше 0")
        
        # Проверка категории
        if not category or len(category.strip()) < 2:
            errors.append("Категория должна содержать минимум 2 символа")
        elif len(category) > 50:
            errors.append("Категория слишком длинная")
        
        # Проверка описания
        if description and len(description) > 200:
            errors.append("Описание слишком длинное")
        
        if errors:
            return False, " | ".join(errors)
        else:
            return True, "✅ Запись корректна"

class HabitValidator:
    """Валидатор для привычек"""
    
    @staticmethod
    def validate_habit_name(name: str) -> Tuple[bool, str]:
        """Валидация названия привычки"""
        name = name.strip()
        
        if not name:
            return False, "❌ Название привычки не может быть пустым"
        
        if len(name) < 3:
            return False, "❌ Название привычки слишком короткое"
        
        if len(name) > 100:
            return False, "❌ Название привычки слишком длинное"
        
        # Проверка на недопустимые символы
        if re.search(r'[^\w\sа-яА-ЯёЁ\-_!?.,]', name):
            return False, "❌ Название содержит недопустимые символы"
        
        return True, "✅ Название привычки корректно"

class NoteValidator:
    """Валидатор для заметок"""
    
    @staticmethod
    def validate_note_text(text: str) -> Tuple[bool, str]:
        """Валидация текста заметки"""
        text = text.strip()
        
        if not text:
            return False, "❌ Текст заметки не может быть пустым"
        
        if len(text) < 2:
            return False, "❌ Текст заметки слишком короткий"
        
        if len(text) > 5000:
            return False, "❌ Текст заметки слишком длинный"
        
        return True, "✅ Текст заметки корректен"