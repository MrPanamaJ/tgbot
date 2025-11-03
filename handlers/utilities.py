from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.operations import DatabaseManager
from utils.keyboards import KeyboardManager
from utils.helpers import TextAnalyzer, PasswordGenerator, HealthCalculator, DateTimeHelper
from utils.error_handling import handle_errors
from utils.validators import InputValidator
from services.qr_generator import QRCodeService
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class UtilitiesHandler:
    """Обработчик утилит"""
    
    def __init__(self, bot: TeleBot, db: DatabaseManager, keyboards: KeyboardManager):
        self.bot = bot
        self.db = db
        self.keyboards = keyboards
        self.text_analyzer = TextAnalyzer()
        self.password_generator = PasswordGenerator()
        self.health_calculator = HealthCalculator()
        self.date_helper = DateTimeHelper()
        self.validator = InputValidator()
        self.qr_service = QRCodeService()
    
    def register_handlers(self):
        """Регистрация обработчиков"""
        
        @self.bot.message_handler(func=lambda message: message.text == '🔧 Утилиты')
        @handle_errors
        def handle_utilities_menu(message: Message):
            """Обработчик меню утилит"""
            instructions = (
                "🔧 **Полезные утилиты**\n\n"
                "Доступные инструменты:\n\n"
                "• 📊 Анализ текста - статистика\n"
                "• 🔐 Генератор паролей\n"
                "• ⚖️ Калькулятор ИМТ\n"
                "• ⏰ Создать напоминание\n\n"
                "Выберите утилиту:"
            )
            self.bot.send_message(
                message.chat.id,
                instructions,
                reply_markup=self.keyboards.utilities_menu()
            )
        
        @self.bot.message_handler(func=lambda message: message.text == '📊 Анализ текста')
        @handle_errors
        def handle_text_analysis(message: Message):
            """Анализ текста"""
            self.bot.send_message(message.chat.id, "📝 Введите текст для анализа:")
            self.bot.register_next_step_handler(message, self.process_text_analysis)
        
        @self.bot.message_handler(func=lambda message: message.text == '🔐 Генератор паролей')
        @handle_errors
        def handle_password_generator(message: Message):
            """Генератор паролей"""
            self.generate_passwords(message.chat.id)
        
        @self.bot.message_handler(func=lambda message: message.text == '⚖️ Калькулятор ИМТ')
        @handle_errors
        def handle_bmi_calculator(message: Message):
            """Калькулятор ИМТ"""
            self.start_bmi_calculation(message.chat.id)
        
        @self.bot.message_handler(func=lambda message: message.text == '⏰ Создать напоминание')
        @handle_errors
        def handle_reminder_creation(message: Message):
            """Создание напоминания"""
            self.start_reminder_creation(message.chat.id)
    
    @handle_errors
    def process_text_analysis(self, message: Message):
        """Обработка анализа текста"""
        text = message.text.strip()
        
        if not text:
            self.bot.send_message(
                message.chat.id,
                "❌ Текст не может быть пустым.",
                reply_markup=self.keyboards.utilities_menu()
            )
            return
        
        analysis = self.text_analyzer.analyze(text)
        
        response = (
            f"📊 **Анализ текста:**\n\n"
            f"📝 **Слов:** {analysis['words']}\n"
            f"🔤 **Символов:** {analysis['characters']}\n"
            f"📏 **Символов (без пробелов):** {analysis['characters_no_spaces']}\n"
            f"📄 **Предложений:** {analysis['sentences']}\n"
            f"📐 **Средняя длина слова:** {analysis['average_word_length']} симв.\n"
            f"⏱ **Время чтения:** ~{analysis['reading_time_minutes']} мин.\n\n"
        )
        
        # Дополнительные рекомендации
        if analysis['words'] < 10:
            response += "💡 *Текст очень короткий*\n"
        elif analysis['average_word_length'] > 7:
            response += "💡 *Используются длинные слова*\n"
        elif analysis['sentences'] == 0:
            response += "💡 *Нет знаков препинания*\n"
        else:
            words_per_sentence = analysis['words'] / analysis['sentences']
            if words_per_sentence > 20:
                response += "💡 *Предложения слишком длинные*\n"
            elif words_per_sentence < 5:
                response += "💡 *Предложения слишком короткие*\n"
            else:
                response += "💡 *Текст хорошо сбалансирован*\n"
        
        self.bot.send_message(
            message.chat.id,
            response,
            parse_mode='Markdown',
            reply_markup=self.keyboards.utilities_menu()
        )
    
    @handle_errors
    def generate_passwords(self, user_id: int):
        """Генерация и отображение паролей"""
        # Генерация разных типов паролей
        standard_password = self.password_generator.generate(12, True)
        strong_password = self.password_generator.generate(16, True)
        simple_password = self.password_generator.generate(10, False)
        
        # Проверка сложности
        standard_strength = self.password_generator.strength_check(standard_password)
        strong_strength = self.password_generator.strength_check(strong_password)
        
        response = (
            f"🔐 **Сгенерированные пароли:**\n\n"
            f"🔒 **Стандартный** ({standard_strength['strength']}):\n"
            f"`{standard_password}`\n\n"
            f"🛡️ **Сильный** ({strong_strength['strength']}):\n"
            f"`{strong_password}`\n\n"
            f"🔓 **Простой** (без символов):\n"
            f"`{simple_password}`\n\n"
            f"💡 *Нажмите на пароль, чтобы скопировать*\n"
            f"⚠️ *Не сохраняйте пароли в открытом виде!*"
        )
        
        # Клавиатура для дополнительных действий
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("🔄 Сгенерировать новые", callback_data="regenerate_passwords"),
            InlineKeyboardButton("📋 Проверить сложность", callback_data="check_password_strength")
        )
        
        self.bot.send_message(
            user_id,
            response,
            parse_mode='Markdown',
            reply_markup=markup
        )
    
    @handle_errors
    def start_bmi_calculation(self, user_id: int):
        """Начало расчета ИМТ"""
        self.bot.send_message(
            user_id,
            "⚖️ **Калькулятор ИМТ**\n\n"
            "Введите ваш вес в килограммах:"
        )
        self.bot.register_next_step_handler_by_chat_id(user_id, self.process_bmi_weight)
    
    @handle_errors
    def process_bmi_weight(self, message: Message):
        """Обработка веса для ИМТ"""
        try:
            weight_text = message.text.strip()
            weight = float(weight_text)
            
            if weight < 20 or weight > 300:
                self.bot.send_message(
                    message.chat.id,
                    "❌ Вес должен быть в диапазоне 20-300 кг.",
                    reply_markup=self.keyboards.utilities_menu()
                )
                return
            
            # Сохраняем вес во временные данные
            self.db.save_temp_data(message.chat.id, 'bmi_weight', str(weight))
            
            self.bot.send_message(
                message.chat.id,
                "📏 Введите ваш рост в сантиметрах:"
            )
            self.bot.register_next_step_handler(message, self.process_bmi_height)
            
        except ValueError:
            self.bot.send_message(
                message.chat.id,
                "❌ Неверный формат веса. Введите число (например: 65 или 70.5):",
                reply_markup=self.keyboards.utilities_menu()
            )
    
    @handle_errors
    def process_bmi_height(self, message: Message):
        """Обработка роста для ИМТ"""
        try:
            height_text = message.text.strip()
            height = float(height_text)
            
            if height < 100 or height > 250:
                self.bot.send_message(
                    message.chat.id,
                    "❌ Рост должен быть в диапазоне 100-250 см.",
                    reply_markup=self.keyboards.utilities_menu()
                )
                return
            
            # Получаем сохраненный вес
            weight_str = self.db.get_temp_data(message.chat.id, 'bmi_weight')
            weight = float(weight_str) if weight_str else 0
            
            # Расчет ИМТ
            bmi_result = self.health_calculator.calculate_bmi(weight, height)
            
            # Очищаем временные данные
            self.db.clear_temp_data(message.chat.id, ['bmi_weight'])
            
            response = (
                f"⚖️ **Результат ИМТ:**\n\n"
                f"📊 **Индекс массы тела:** {bmi_result['bmi']}\n"
                f"📋 **Категория:** {bmi_result['category']}\n"
                f"🎯 **Идеальный вес:** {bmi_result['ideal_min']} - {bmi_result['ideal_max']} кг\n"
                f"💪 **Здоровый диапазон:** {bmi_result['healthy_range']}\n\n"
            )
            
            # Добавляем рекомендации
            if bmi_result['bmi'] < 18.5:
                response += (
                    "💡 **Рекомендации:**\n"
                    "• Увеличьте калорийность питания\n"
                    "• Включите силовые тренировки\n"
                    "• Проконсультируйтесь с врачом\n"
                )
            elif bmi_result['bmi'] < 25:
                response += (
                    "✅ **Отлично!** Ваш вес в норме.\n"
                    "💡 Продолжайте поддерживать здоровый образ жизни!\n"
                )
            elif bmi_result['bmi'] < 30:
                response += (
                    "💡 **Рекомендации:**\n"
                    "• Увеличьте физическую активность\n"
                    "• Сбалансируйте питание\n"
                    "• Снизьте потребление сахара\n"
                )
            else:
                response += (
                    "💡 **Рекомендации:**\n"
                    "• Проконсультируйтесь с врачом\n"
                    "• Разработайте план похудения\n"
                    "• Увеличьте физическую активность\n"
                )
            
            # Клавиатура для дополнительных расчетов
            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("🔥 Расчет калорий", callback_data="calorie_calculation"),
                InlineKeyboardButton("🔄 Новый расчет", callback_data="new_bmi_calculation")
            )
            
            self.bot.send_message(
                message.chat.id,
                response,
                parse_mode='Markdown',
                reply_markup=markup
            )
            
        except ValueError:
            self.bot.send_message(
                message.chat.id,
                "❌ Неверный формат роста. Введите число (например: 175):",
                reply_markup=self.keyboards.utilities_menu()
            )
    
    @handle_errors
    def start_reminder_creation(self, user_id: int):
        """Начало создания напоминания"""
        instructions = (
            "⏰ **Создание напоминания**\n\n"
            "Введите текст напоминания:"
        )
        
        self.bot.send_message(user_id, instructions)
        self.bot.register_next_step_handler_by_chat_id(user_id, self.process_reminder_text)
    
    @handle_errors
    def process_reminder_text(self, message: Message):
        """Обработка текста напоминания"""
        reminder_text = message.text.strip()
        
        if not reminder_text:
            self.bot.send_message(
                message.chat.id,
                "❌ Текст напоминания не может быть пустым.",
                reply_markup=self.keyboards.utilities_menu()
            )
            return
        
        # Сохраняем текст напоминания
        self.db.save_temp_data(message.chat.id, 'reminder_text', reminder_text)
        
        time_examples = (
            "\n\n**Примеры форматов времени:**\n"
            "• `31.12.2024 23:59` - конкретная дата\n"
            "• `20:00` - сегодня в 20:00\n"
            "• `через 2 часа` - через 2 часа\n"
            "• `через 1 день` - через 24 часа"
        )
        
        self.bot.send_message(
            message.chat.id,
            f"🕐 Теперь введите время напоминания:{time_examples}",
            parse_mode='Markdown'
        )
        self.bot.register_next_step_handler(message, self.process_reminder_time)
    
    @handle_errors
    def process_reminder_time(self, message: Message):
        """Обработка времени напоминания"""
        time_str = message.text.strip()
        reminder_text = self.db.get_temp_data(message.chat.id, 'reminder_text')
        
        if not reminder_text:
            self.bot.send_message(
                message.chat.id,
                "❌ Ошибка: текст напоминания не найден.",
                reply_markup=self.keyboards.utilities_menu()
            )
            return
        
        # Парсинг времени
        remind_time = self.date_helper.parse_reminder_time(time_str)
        
        if not remind_time:
            self.bot.send_message(
                message.chat.id,
                "❌ Не удалось распознать время. Попробуйте другой формат.",
                reply_markup=self.keyboards.utilities_menu()
            )
            return
        
        # Создание напоминания
        reminder_id = self.db.create_reminder(
            user_id=message.chat.id,
            reminder_text=reminder_text,
            remind_time=remind_time
        )
        
        # Очищаем временные данные
        self.db.clear_temp_data(message.chat.id, ['reminder_text'])
        
        response = (
            f"✅ **Напоминание создано!**\n\n"
            f"📝 Текст: {reminder_text}\n"
            f"🕐 Время: {remind_time.strftime('%d.%m.%Y в %H:%M')}\n"
            f"🆔 ID: #{reminder_id}\n\n"
            f"💡 Я пришлю уведомление в указанное время."
        )
        
        self.bot.send_message(
            message.chat.id,
            response,
            parse_mode='Markdown',
            reply_markup=self.keyboards.utilities_menu()
        )
    
    @handle_errors
    def handle_callback_query(self, call: CallbackQuery):
        """Обработка callback запросов для утилит"""
        chat_id = call.message.chat.id
        data = call.data
        
        try:
            if data == "regenerate_passwords":
                self.bot.delete_message(chat_id, call.message.message_id)
                self.generate_passwords(chat_id)
            
            elif data == "check_password_strength":
                self.bot.send_message(
                    chat_id,
                    "🔐 Введите пароль для проверки сложности:"
                )
                self.bot.register_next_step_handler_by_chat_id(chat_id, self.check_password_strength)
            
            elif data == "calorie_calculation":
                self.start_calorie_calculation(chat_id)
            
            elif data == "new_bmi_calculation":
                self.bot.delete_message(chat_id, call.message.message_id)
                self.start_bmi_calculation(chat_id)
        
        except Exception as e:
            logger.error(f"Callback error in utilities: {e}")
            self.bot.answer_callback_query(call.id, "❌ Произошла ошибка")
    
    @handle_errors
    def check_password_strength(self, message: Message):
        """Проверка сложности пароля"""
        password = message.text.strip()
        strength = self.password_generator.strength_check(password)
        
        response = (
            f"🔐 **Анализ пароля:**\n\n"
            f"📊 **Сложность:** {strength['score']}/6 - {strength['strength']}\n"
            f"📏 **Длина:** {len(password)} символов\n\n"
        )
        
        if strength['feedback']:
            response += "💡 **Рекомендации:**\n" + "\n".join(f"• {fb}" for fb in strength['feedback'])
        else:
            response += "✅ **Пароль отличный!**\n"
        
        self.bot.send_message(
            message.chat.id,
            response,
            parse_mode='Markdown',
            reply_markup=self.keyboards.utilities_menu()
        )
    
    @handle_errors
    def start_calorie_calculation(self, user_id: int):
        """Начало расчета калорий"""
        # Этот метод можно расширить для расчета калорий
        self.bot.send_message(
            user_id,
            "🔥 **Расчет калорий**\n\n"
            "Эта функция в разработке. Скоро будет доступна!",
            reply_markup=self.keyboards.utilities_menu()
        )