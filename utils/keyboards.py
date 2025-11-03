from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any, Optional

class KeyboardManager:
    """Менеджер для создания клавиатур"""
    
    @staticmethod
    def main_menu() -> ReplyKeyboardMarkup:
        """Главное меню"""
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        buttons = [
            '🎤 Распознать голос', '🖼 Обработать фото', '🌤️ Прогноз погоды',
            '💾 Сохранить локацию', '🔔 Подписка', '💼 Заказать услугу',
            '📊 Случайная цитата', '🔲 QR генератор', '📝 Заметки',  # Изменено здесь
            '💪 Привычки', '💰 Финансы', '🔧 Утилиты', '📋 Помощь'
        ]
        for btn in buttons:
            markup.add(KeyboardButton(btn))
        return markup
    
    @staticmethod
    def weather_menu() -> ReplyKeyboardMarkup:
        """Меню погоды"""
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        markup.add(
            KeyboardButton('📍 Поделиться местоположением', request_location=True),
            KeyboardButton('↩️ Назад в меню')
        )
        return markup
    
    @staticmethod
    def finance_menu() -> ReplyKeyboardMarkup:
        """Меню финансов"""
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        buttons = ['➕ Доход', '➖ Расход', '📊 Отчет', '↩️ Назад в меню']
        for btn in buttons:
            markup.add(KeyboardButton(btn))
        return markup
    
    @staticmethod
    def notes_menu() -> ReplyKeyboardMarkup:
        """Меню заметок"""
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        buttons = ['➕ Новая заметка', '📋 Все заметки', '🗑️ Удалить заметку', '↩️ Назад в меню']
        for btn in buttons:
            markup.add(KeyboardButton(btn))
        return markup
    
    @staticmethod
    def habits_menu() -> ReplyKeyboardMarkup:
        """Меню привычек"""
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        buttons = [
            '➕ Новая привычка', '📊 Мои привычки', '✅ Отметить выполнение', 
            '🗑️ Удалить привычку', '↩️ Назад в меню'
        ]
        for btn in buttons:
            markup.add(KeyboardButton(btn))
        return markup
    
    @staticmethod
    def utilities_menu() -> ReplyKeyboardMarkup:
        """Меню утилит"""
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        buttons = [
            '📊 Анализ текста', '🔐 Генератор паролей', '⚖️ Калькулятор ИМТ',
            '⏰ Создать напоминание', '↩️ Назад в меню'
        ]
        for btn in buttons:
            markup.add(KeyboardButton(btn))
        return markup
    
    @staticmethod
    def qr_menu() -> ReplyKeyboardMarkup:
        """Меню QR-кодов"""
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        buttons = [
            '📱 QR для телефона', '🌐 QR для сайта', '📧 QR для email',
            '📝 QR для текста', '↩️ Назад в меню'
        ]
        for btn in buttons:
            markup.add(KeyboardButton(btn))
        return markup
    
    @staticmethod
    def services_menu() -> ReplyKeyboardMarkup:
        """Меню услуг"""
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        buttons = [
            '👩‍⚕️ Консультация логопеда',
            '🎬 Создание видеоролика',
            '↩️ Назад в меню'
        ]
        for btn in buttons:
            markup.add(KeyboardButton(btn))
        return markup
    
    @staticmethod
    def confirmation_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура подтверждения"""
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ Да", callback_data="confirm_yes"),
            InlineKeyboardButton("❌ Нет", callback_data="confirm_no")
        )
        return markup
    
    @staticmethod
    def habit_tracking_keyboard(habits: List[Dict]) -> InlineKeyboardMarkup:
        """Клавиатура для отслеживания привычек"""
        markup = InlineKeyboardMarkup()
        for habit in habits:
            markup.add(
                InlineKeyboardButton(
                    f"✅ {habit['name']} ({habit['streak']} дней)",
                    callback_data=f"track_habit_{habit['id']}"
                )
            )
        return markup