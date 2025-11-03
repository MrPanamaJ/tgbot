from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.operations import DatabaseManager
from database.models import ServiceOrder
from utils.keyboards import KeyboardManager
from utils.error_handling import handle_errors
from utils.validators import InputValidator
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ServicesHandler:
    """Обработчик заказа услуг"""
    
    def __init__(self, bot: TeleBot, db: DatabaseManager, keyboards: KeyboardManager):
        self.bot = bot
        self.db = db
        self.keyboards = keyboards
        self.validator = InputValidator()
        
        # Описания услуг
        self.services = {
            '👩‍⚕️ Консультация логопеда': {
                'description': (
                    "👩‍⚕️ **Консультация логопеда**\n\n"
                    "Профессиональная помощь в коррекции речи для детей и взрослых\n\n"
                    "**Услуги включают:**\n"
                    "• Диагностика речевых нарушений\n"
                    "• Коррекция звукопроизношения\n"
                    "• Развитие фонематического слуха\n"
                    "• Работа над дикцией и темпом речи\n\n"
                    "**Стоимость:** от 1500 руб./занятие\n"
                    "**Длительность:** 45-60 минут\n"
                    "**Формат:** онлайн или очно (Москва)"
                ),
                'price_range': "от 1500 руб./занятие",
                'duration': "45-60 минут",
                'contact_prompt': "Для заказа укажите:\n• Ваше имя\n• Контактный телефон\n• Возраст пациента\n• Краткое описание проблемы"
            },
            '🎬 Создание видеоролика': {
                'description': (
                    "🎬 **Создание видеоролика**\n\n"
                    "Профессиональное производство видео для бизнеса и личных целей\n\n"
                    "**Услуги включают:**\n"
                    "• Сценарий и раскадровка\n"
                    "• Съемка и монтаж\n"
                    "• Цветокоррекция и звук\n"
                    "• Графика и анимация\n\n"
                    "**Стоимость:** от 5000 руб./проект\n"
                    "**Сроки:** от 3 дней\n"
                    "**Формат:** любые видеоролики"
                ),
                'price_range': "от 5000 руб./проект",
                'duration': "от 3 дней",
                'contact_prompt': "Для заказа укажите:\n• Ваше имя\n• Контактный телефон\n• Тип видеоролика\n• Примерные сроки\n• Бюджет"
            }
        }
    
    def register_handlers(self):
        """Регистрация обработчиков"""
        
        @self.bot.message_handler(func=lambda message: message.text == '💼 Заказать услугу')
        @handle_errors
        def handle_services_menu(message: Message):
            """Обработчик меню услуг"""
            instructions = (
                "💼 **Выберите услугу:**\n\n"
                "• 👩‍⚕️ Консультация логопеда\n"
                "• 🎬 Создание видеоролика\n\n"
                "Выберите нужную услугу:"
            )
            
            markup = self.keyboards.services_menu()
            self.bot.send_message(
                message.chat.id,
                instructions,
                reply_markup=markup
            )
        
        @self.bot.message_handler(func=lambda message: message.text in self.services.keys())
        @handle_errors
        def handle_service_selection(message: Message):
            """Обработчик выбора услуги"""
            service_name = message.text
            service_info = self.services.get(service_name)
            
            if not service_info:
                self.bot.send_message(
                    message.chat.id,
                    "❌ Услуга не найдена.",
                    reply_markup=self.keyboards.main_menu()
                )
                return
            
            # Сохраняем выбранную услугу во временные данные
            self.db.save_temp_data(message.chat.id, 'selected_service', service_name)
            
            # Отправляем описание услуги
            self.bot.send_message(
                message.chat.id,
                service_info['description'],
                parse_mode='Markdown'
            )
            
            # Запрашиваем контактные данные
            self.bot.send_message(
                message.chat.id,
                service_info['contact_prompt']
            )
            
            self.bot.register_next_step_handler(message, self.process_service_order)
    
    @handle_errors
    def process_service_order(self, message: Message):
        """Обработка заказа услуги"""
        try:
            user_info = message.text.strip()
            
            if not user_info:
                self.bot.send_message(
                    message.chat.id,
                    "❌ Контактная информация не может быть пустой.",
                    reply_markup=self.keyboards.services_menu()
                )
                return
            
            # Получаем выбранную услугу
            service_name = self.db.get_temp_data(message.chat.id, 'selected_service')
            
            if not service_name:
                self.bot.send_message(
                    message.chat.id,
                    "❌ Ошибка: услуга не выбрана.",
                    reply_markup=self.keyboards.main_menu()
                )
                return
            
            # Создаем заказ
            order = ServiceOrder(
                id=0,
                user_id=message.chat.id,
                service_type=service_name,
                contact_info=user_info,
                created_at=datetime.now()
            )
            
            order_id = self.db.add_service_order(order)
            
            # Очищаем временные данные
            self.db.clear_temp_data(message.chat.id, ['selected_service'])
            
            # Отправляем подтверждение
            service_info = self.services.get(service_name, {})
            
            response = (
                f"✅ **Заказ #{order_id} принят!**\n\n"
                f"💼 **Услуга:** {service_name}\n"
                f"💰 **Стоимость:** {service_info.get('price_range', 'уточняется')}\n"
                f"⏱ **Сроки:** {service_info.get('duration', 'уточняются')}\n\n"
                f"📞 **Ваши контакты:**\n{user_info}\n\n"
                f"💡 **Мы свяжемся с вами в ближайшее время для уточнения деталей!**\n\n"
                f"🆔 **Номер заказа:** #{order_id}"
            )
            
            # Клавиатура для дополнительных действий
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("📞 Связаться сейчас", callback_data="contact_now"),
                InlineKeyboardButton("💼 Другие услуги", callback_data="more_services")
            )
            
            self.bot.send_message(
                message.chat.id,
                response,
                parse_mode='Markdown',
                reply_markup=markup
            )
            
            # Логирование заказа
            logger.info(f"New service order: #{order_id}, User: {message.chat.id}, Service: {service_name}")
            
        except Exception as e:
            logger.error(f"Service order processing error: {e}")
            self.bot.send_message(
                message.chat.id,
                "❌ Ошибка при обработке заказа. Попробуйте еще раз.",
                reply_markup=self.keyboards.main_menu()
            )
    
    @handle_errors
    def handle_callback_query(self, call):
        """Обработка callback запросов для услуг"""
        chat_id = call.message.chat.id
        data = call.data
        
        try:
            if data == "contact_now":
                self.bot.answer_callback_query(call.id, "📞 Контактная информация отправлена")
                
                contact_info = (
                    "📞 **Контактная информация:**\n\n"
                    "**Для логопедических услуг:**\n"
                    "• Телефон: +7 (XXX) XXX-XX-XX\n"
                    "• Email: logoped@example.com\n"
                    "• График: Пн-Пт 9:00-18:00\n\n"
                    "**Для видеопроизводства:**\n"
                    "• Телефон: +7 (XXX) XXX-XX-XX\n"
                    "• Email: video@example.com\n"
                    "• Сайт: example-video.ru\n\n"
                    "💡 *Укажите номер вашего заказа при обращении*"
                )
                
                self.bot.send_message(
                    chat_id,
                    contact_info,
                    parse_mode='Markdown'
                )
            
            elif data == "more_services":
                self.bot.delete_message(chat_id, call.message.message_id)
                self.bot.send_message(
                    chat_id,
                    "💼 Возвращаю к выбору услуг...",
                    reply_markup=self.keyboards.services_menu()
                )
        
        except Exception as e:
            logger.error(f"Callback error in services: {e}")
            self.bot.answer_callback_query(call.id, "❌ Произошла ошибка")
    
    def get_service_statistics(self, user_id: int) -> Dict[str, Any]:
        """Получение статистики по заказам услуг"""
        try:
            orders = self.db.get_user_service_orders(user_id)
            
            total_orders = len(orders)
            recent_orders = [order for order in orders if order.created_at]
            
            service_types = {}
            for order in orders:
                service_types[order.service_type] = service_types.get(order.service_type, 0) + 1
            
            return {
                'total_orders': total_orders,
                'recent_orders_count': len(recent_orders),
                'service_types': service_types,
                'last_order_date': max([order.created_at for order in orders]) if orders else None
            }
            
        except Exception as e:
            logger.error(f"Service statistics error: {e}")
            return {}