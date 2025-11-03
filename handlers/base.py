from telebot import TeleBot
from telebot.types import Message
from database.operations import DatabaseManager
from utils.keyboards import KeyboardManager
from utils.error_handling import handle_errors
import logging

logger = logging.getLogger(__name__)

class BaseHandler:
    """Базовый класс для обработчиков"""
    
    def __init__(self, bot: TeleBot, db: DatabaseManager, keyboards: KeyboardManager):
        self.bot = bot
        self.db = db
        self.keyboards = keyboards

class StartHandler(BaseHandler):
    """Обработчик команды start"""
    
    def register_handlers(self):
        @self.bot.message_handler(commands=['start', 'привет'])
        def handle_start(message: Message):
            user = self.db.get_or_create_user(
                message.chat.id,
                message.from_user.username,
                message.from_user.first_name,
                message.from_user.last_name
            )
            
            welcome_text = """
🎉 Добро пожаловать в многофункционального бота!

Я умею:
• 🎤 Преобразовывать голосовые сообщения в текст
• 🖼 Обрабатывать и улучшать фотографии
• 🌤️ Показывать прогноз погоды
• 🔔 Отправлять уведомления о погоде
• 💼 Принимать заказы на услуги
• 📊 Показывать случайные цитаты
• 🔲 Генерировать QR коды
• 📝 Вести заметки
• 💪 Отслеживать привычки
• 💰 Управлять финансами
• 🔧 Использовать полезные утилиты

Выберите действие в меню ниже! 👇
"""
            self.bot.send_message(
                message.chat.id, 
                welcome_text, 
                reply_markup=self.keyboards.main_menu()
            )

class HelpHandler(BaseHandler):
    """Обработчик команды помощи"""
    
    def register_handlers(self):
        @self.bot.message_handler(commands=['help'])
        @self.bot.message_handler(func=lambda message: message.text == '📋 Помощь')
        def handle_help(message: Message):
            help_text = """
📋 **Доступные функции:**

**Основные команды:**
/start - начать работу
/help - помощь

**Функции бота:**
• 🎤 Распознавание голоса
• 🖼 Обработка фото
• 🌤️ Прогноз погоды
• 💾 Сохранить локацию
• 🔔 Подписка на уведомления
• 💼 Заказ услуг
• 📊 Случайная цитата
• 🔲 Генератор QR кодов
• 📝 Заметки
• 💪 Трекер привычек
• 💰 Управление финансами
• 🔧 Полезные утилиты
"""
            self.bot.send_message(
                message.chat.id, 
                help_text, 
                parse_mode='Markdown',
                reply_markup=self.keyboards.main_menu()
            )
        
        @self.bot.message_handler(func=lambda message: message.text == '↩️ Назад в меню')
        def handle_back_to_menu(message: Message):
            """Обработчик возврата в главное меню"""
            self.bot.send_message(
                message.chat.id,
                "Возвращаю в главное меню...",
                reply_markup=self.keyboards.main_menu()
            )
        
        @self.bot.message_handler(func=lambda message: message.text == '📊 Случайная цитата')
        @handle_errors
        def handle_random_quote(message: Message):
            """Обработчик случайной цитаты"""
            try:
                from services.quote_parser import QuoteParser
                quote_parser = QuoteParser()
                quote = quote_parser.get_random_quote()
                
                response = (
                    f"💫 **Случайная цитата:**\n\n"
                    f"{quote['full']}\n\n"
                    f"📚 *Источник: citaty.info*"
                )
                
                self.bot.send_message(
                    message.chat.id,
                    response,
                    parse_mode='Markdown'
                )
                
            except Exception as e:
                logger.error(f"Quote error: {e}")
                self.bot.send_message(
                    message.chat.id,
                    "❌ Не удалось получить цитату. Попробуйте позже."
                )
        
        @self.bot.message_handler(func=lambda message: message.text == '🔲 QR генератор')
        def handle_qr_generator(message: Message):
            """Обработчик QR генератора"""
            instructions = (
                "🔲 **Генератор QR кодов**\n\n"
                "Отправьте текст или ссылку для создания QR кода:"
            )
            self.bot.send_message(message.chat.id, instructions)
            self.bot.register_next_step_handler(message, self.process_qr_generation)
    
    @handle_errors
    def process_qr_generation(self, message: Message):
        """Обработка генерации QR кода"""
        try:
            from services.qr_generator import QRCodeService
            qr_service = QRCodeService()
            
            data = message.text.strip()
            if not data:
                self.bot.send_message(message.chat.id, "❌ Текст не может быть пустым")
                return
            
            qr_image = qr_service.generate_qr(data)
            
            if qr_image:
                self.bot.send_photo(
                    message.chat.id,
                    qr_image,
                    caption=f"✅ QR код создан для:\n`{data}`",
                    parse_mode='Markdown'
                )
            else:
                self.bot.send_message(message.chat.id, "❌ Ошибка создания QR кода")
        
        except Exception as e:
            logger.error(f"QR generation error: {e}")
            self.bot.send_message(message.chat.id, "❌ Ошибка создания QR кода")