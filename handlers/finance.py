from telebot import TeleBot
from telebot.types import Message, CallbackQuery
from database.operations import DatabaseManager
from database.models import FinancialRecord
from utils.keyboards import KeyboardManager
from utils.validators import InputValidator
from utils.error_handling import handle_errors
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

class FinanceHandler:
    """Обработчик финансов"""
    
    def __init__(self, bot: TeleBot, db: DatabaseManager, keyboards: KeyboardManager):
        self.bot = bot
        self.db = db
        self.keyboards = keyboards
        self.validator = InputValidator()
    
    def register_handlers(self):
        """Регистрация обработчиков"""
        
        @self.bot.message_handler(func=lambda message: message.text == '💰 Финансы')
        @handle_errors
        def handle_finance_menu(message: Message):
            """Обработчик меню финансов"""
            instructions = (
                "💰 **Управление финансами**\n\n"
                "Отслеживайте доходы и расходы:\n\n"
                "• ➕ Добавить доход\n"
                "• ➖ Добавить расход\n"
                "• 📊 Просмотреть отчет\n\n"
                "Выберите действие:"
            )
            self.bot.send_message(
                message.chat.id,
                instructions,
                reply_markup=self.keyboards.finance_menu()
            )
        
        @self.bot.message_handler(func=lambda message: message.text == '➕ Доход')
        @handle_errors
        def handle_income_start(message: Message):
            """Начало добавления дохода"""
            self.bot.send_message(message.chat.id, "💰 Введите сумму дохода:")
            self.bot.register_next_step_handler(message, self.process_income_amount)
        
        @self.bot.message_handler(func=lambda message: message.text == '➖ Расход')
        @handle_errors  
        def handle_expense_start(message: Message):
            """Начало добавления расхода"""
            self.bot.send_message(message.chat.id, "💸 Введите сумму расхода:")
            self.bot.register_next_step_handler(message, self.process_expense_amount)
        
        @self.bot.message_handler(func=lambda message: message.text == '📊 Отчет')
        @handle_errors
        def handle_finance_report(message: Message):
            """Обработчик финансового отчета"""
            self.show_finance_report(message.chat.id)
    
    @handle_errors
    def process_income_amount(self, message: Message):
        """Обработка суммы дохода"""
        try:
            amount_text = message.text.strip()
            is_valid, amount, message_text = self.validator.validate_amount(amount_text)
            
            if not is_valid:
                self.bot.send_message(
                    message.chat.id,
                    message_text,
                    reply_markup=self.keyboards.finance_menu()
                )
                return
            
            # Сохраняем временные данные
            self.db.save_temp_data(message.chat.id, 'finance_amount', str(amount))
            self.db.save_temp_data(message.chat.id, 'finance_type', 'income')
            
            self.bot.send_message(
                message.chat.id,
                "📝 Введите категорию дохода (например: Зарплата, Фриланс, Инвестиции):"
            )
            self.bot.register_next_step_handler(message, self.process_income_category)
        
        except Exception as e:
            logger.error(f"Error processing income amount: {e}")
            self.bot.send_message(
                message.chat.id,
                "❌ Ошибка при обработке суммы. Попробуйте еще раз.",
                reply_markup=self.keyboards.finance_menu()
            )
    
    @handle_errors
    def process_income_category(self, message: Message):
        """Обработка категории дохода"""
        category = message.text.strip()
        
        # Получаем сохраненные данные
        amount_str = self.db.get_temp_data(message.chat.id, 'finance_amount')
        amount = float(amount_str) if amount_str else 0
        
        self.db.save_temp_data(message.chat.id, 'finance_category', category)
        
        self.bot.send_message(
            message.chat.id,
            "💬 Введите описание дохода:"
        )
        self.bot.register_next_step_handler(
            message, 
            lambda m: self.process_income_description(m, amount, category)
        )
    
    @handle_errors
    def process_income_description(self, message: Message, amount: float, category: str):
        """Обработка описания дохода"""
        description = message.text.strip()
        
        # Создаем финансовую запись
        record = FinancialRecord(
            id=0,  # Будет сгенерировано БД
            user_id=message.chat.id,
            amount=amount,
            category=category,
            description=description,
            type='income',
            created_at=datetime.now()
        )
        
        record_id = self.db.add_financial_record(record)
        
        # Очищаем временные данные
        self.db.clear_temp_data(message.chat.id, ['finance_amount', 'finance_type', 'finance_category'])
        
        response = (
            f"✅ **Доход добавлен!**\n\n"
            f"💰 Сумма: {amount:.2f} руб.\n"
            f"📂 Категория: {category}\n"
            f"📝 Описание: {description}\n"
            f"🆔 ID записи: #{record_id}"
        )
        
        self.bot.send_message(
            message.chat.id,
            response,
            parse_mode='Markdown',
            reply_markup=self.keyboards.finance_menu()
        )
    
    @handle_errors
    def process_expense_amount(self, message: Message):
        """Обработка суммы расхода"""
        try:
            amount_text = message.text.strip()
            is_valid, amount, message_text = self.validator.validate_amount(amount_text)
            
            if not is_valid:
                self.bot.send_message(
                    message.chat.id,
                    message_text,
                    reply_markup=self.keyboards.finance_menu()
                )
                return
            
            # Сохраняем временные данные
            self.db.save_temp_data(message.chat.id, 'finance_amount', str(amount))
            self.db.save_temp_data(message.chat.id, 'finance_type', 'expense')
            
            self.bot.send_message(
                message.chat.id,
                "📝 Введите категорию расхода (например: Еда, Транспорт, Развлечения):"
            )
            self.bot.register_next_step_handler(message, self.process_expense_category)
        
        except Exception as e:
            logger.error(f"Error processing expense amount: {e}")
            self.bot.send_message(
                message.chat.id,
                "❌ Ошибка при обработке суммы. Попробуйте еще раз.",
                reply_markup=self.keyboards.finance_menu()
            )
    
    @handle_errors
    def process_expense_category(self, message: Message):
        """Обработка категории расхода"""
        category = message.text.strip()
        
        # Получаем сохраненные данные
        amount_str = self.db.get_temp_data(message.chat.id, 'finance_amount')
        amount = float(amount_str) if amount_str else 0
        
        self.db.save_temp_data(message.chat.id, 'finance_category', category)
        
        self.bot.send_message(
            message.chat.id,
            "💬 Введите описание расхода:"
        )
        self.bot.register_next_step_handler(
            message,
            lambda m: self.process_expense_description(m, amount, category)
        )
    
    @handle_errors
    def process_expense_description(self, message: Message, amount: float, category: str):
        """Обработка описания расхода"""
        description = message.text.strip()
        
        # Создаем финансовую запись
        record = FinancialRecord(
            id=0,  # Будет сгенерировано БД
            user_id=message.chat.id,
            amount=amount,
            category=category,
            description=description,
            type='expense',
            created_at=datetime.now()
        )
        
        record_id = self.db.add_financial_record(record)
        
        # Очищаем временные данные
        self.db.clear_temp_data(message.chat.id, ['finance_amount', 'finance_type', 'finance_category'])
        
        response = (
            f"✅ **Расход добавлен!**\n\n"
            f"💸 Сумма: {amount:.2f} руб.\n"
            f"📂 Категория: {category}\n"
            f"📝 Описание: {description}\n"
            f"🆔 ID записи: #{record_id}"
        )
        
        self.bot.send_message(
            message.chat.id,
            response,
            parse_mode='Markdown',
            reply_markup=self.keyboards.finance_menu()
        )
    
    @handle_errors
    def show_finance_report(self, user_id: int, days: int = 30):
        """Показать финансовый отчет"""
        report = self.db.get_financial_report(user_id, days)
        
        if not report:
            self.bot.send_message(
                user_id,
                "📊 За указанный период нет финансовых операций.",
                reply_markup=self.keyboards.finance_menu()
            )
            return
        
        response = f"📊 **Финансовый отчет за {report['period']}:**\n\n"
        response += f"💰 **Доходы:** {report['total_income']:.2f} руб.\n"
        response += f"💸 **Расходы:** {report['total_expense']:.2f} руб.\n"
        response += f"⚖️ **Баланс:** {report['balance']:.2f} руб.\n\n"
        
        if report['categories']:
            response += "**Детали по категориям:**\n"
            
            # Группируем по типам
            income_categories = [(cat, amount) for cat, type_, amount in report['categories'] if type_ == 'income']
            expense_categories = [(cat, amount) for cat, type_, amount in report['categories'] if type_ == 'expense']
            
            if income_categories:
                response += "\n💰 **Доходы:**\n"
                for category, amount in income_categories[:5]:  # Показываем топ-5
                    response += f"• {category}: {amount:.2f} руб.\n"
            
            if expense_categories:
                response += "\n💸 **Расходы:**\n"
                for category, amount in expense_categories[:5]:  # Показываем топ-5
                    response += f"• {category}: {amount:.2f} руб.\n"
        
        # Добавляем рекомендации
        if report['balance'] < 0:
            response += "\n⚠️ **Внимание:** Отрицательный баланс. Рекомендуется сократить расходы."
        elif report['total_expense'] > report['total_income'] * 0.7:
            response += "\n💡 **Совет:** Расходы составляют более 70% от доходов. Возможно стоит оптимизировать траты."
        else:
            response += "\n✅ **Отлично!** Финансы в порядке."
        
        self.bot.send_message(
            user_id,
            response,
            parse_mode='Markdown',
            reply_markup=self.keyboards.finance_menu()
        )