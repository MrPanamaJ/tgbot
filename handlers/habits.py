from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.operations import DatabaseManager
from database.models import Habit, HabitTracking
from utils.keyboards import KeyboardManager
from utils.error_handling import handle_errors
from utils.helpers import DateTimeHelper
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class HabitsHandler:
    """Обработчик привычек"""
    
    def __init__(self, bot: TeleBot, db: DatabaseManager, keyboards: KeyboardManager):
        self.bot = bot
        self.db = db
        self.keyboards = keyboards
        self.date_helper = DateTimeHelper()
    
    def register_handlers(self):
        """Регистрация обработчиков"""
        
        @self.bot.message_handler(func=lambda message: message.text == '💪 Привычки')
        @handle_errors
        def handle_habits_menu(message: Message):
            """Обработчик меню привычек"""
            instructions = (
                "💪 **Трекер привычек**\n\n"
                "Отслеживайте свои ежедневные привычки:\n\n"
                "• ➕ Создать новую привычку\n"
                "• 📊 Просмотреть прогресс\n"
                "• ✅ Отметить выполнение\n"
                "• 🗑️ Удалить привычку\n\n"
                "Выберите действие:"
            )
            self.bot.send_message(
                message.chat.id,
                instructions,
                reply_markup=self.keyboards.habits_menu()
            )
        
        @self.bot.message_handler(func=lambda message: message.text == '➕ Новая привычка')
        @handle_errors
        def handle_new_habit(message: Message):
            """Создание новой привычки"""
            self.bot.send_message(message.chat.id, "💪 Введите название привычки:")
            self.bot.register_next_step_handler(message, self.process_new_habit)
        
        @self.bot.message_handler(func=lambda message: message.text == '📊 Мои привычки')
        @handle_errors
        def handle_show_habits(message: Message):
            """Показать все привычки"""
            self.show_user_habits(message.chat.id)
        
        @self.bot.message_handler(func=lambda message: message.text == '✅ Отметить выполнение')
        @handle_errors
        def handle_track_habit(message: Message):
            """Отметить выполнение привычки"""
            self.show_habits_for_tracking(message.chat.id)
        
        @self.bot.message_handler(func=lambda message: message.text == '🗑️ Удалить привычку')
        @handle_errors
        def handle_delete_habit(message: Message):
            """Удаление привычки"""
            self.prompt_habit_deletion(message.chat.id)
    
    @handle_errors
    def process_new_habit(self, message: Message):
        """Обработка создания новой привычки"""
        habit_name = message.text.strip()
        
        if not habit_name:
            self.bot.send_message(
                message.chat.id,
                "❌ Название привычки не может быть пустым.",
                reply_markup=self.keyboards.habits_menu()
            )
            return
        
        # Создание привычки
        habit = Habit(
            id=0,
            user_id=message.chat.id,
            habit_name=habit_name,
            target_days=21,  # Стандартная цель - 21 день
            current_streak=0,
            created_at=datetime.now()
        )
        
        habit_id = self.db.add_habit(habit)
        
        response = (
            f"✅ **Привычка создана!**\n\n"
            f"💪 Название: {habit_name}\n"
            f"🎯 Цель: 21 день\n"
            f"🆔 ID: #{habit_id}\n\n"
            f"💡 *Теперь отмечайте выполнение каждый день!*"
        )
        
        self.bot.send_message(
            message.chat.id,
            response,
            parse_mode='Markdown',
            reply_markup=self.keyboards.habits_menu()
        )
    
    @handle_errors
    def show_user_habits(self, user_id: int):
        """Показать привычки пользователя с прогрессом"""
        habits = self.db.get_user_habits(user_id)
        
        if not habits:
            self.bot.send_message(
                user_id,
                "💪 У вас пока нет привычек.",
                reply_markup=self.keyboards.habits_menu()
            )
            return
        
        response = "📊 **Ваши привычки:**\n\n"
        
        for habit in habits:
            # Проверяем, выполнена ли привычка сегодня
            today_completed = self.db.is_habit_completed_today(habit.id)
            status_icon = "✅" if today_completed else "⏳"
            
            # Расчет прогресса
            progress_percent = min(100, (habit.current_streak / habit.target_days) * 100)
            progress_bar = self._create_progress_bar(progress_percent)
            
            response += (
                f"{status_icon} **{habit.habit_name}**\n"
                f"   🏃 Серия: {habit.current_streak} дней\n"
                f"   🎯 Цель: {habit.target_days} дней\n"
                f"   {progress_bar} {progress_percent:.0f}%\n\n"
            )
        
        # Статистика
        total_habits = len(habits)
        completed_today = sum(1 for habit in habits if self.db.is_habit_completed_today(habit.id))
        longest_streak = max((habit.current_streak for habit in habits), default=0)
        
        response += (
            f"📈 **Статистика:**\n"
            f"• Всего привычек: {total_habits}\n"
            f"• Выполнено сегодня: {completed_today}/{total_habits}\n"
            f"• Самая длинная серия: {longest_streak} дней\n\n"
            f"💡 *Продолжайте в том же духе!*"
        )
        
        # Клавиатура для быстрых действий
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("✅ Отметить выполнение", callback_data="habits:track"),
            InlineKeyboardButton("🗑️ Удалить привычку", callback_data="habits:delete_prompt")
        )
        markup.add(InlineKeyboardButton("↩️ В меню", callback_data="habits:back_to_menu"))
        
        self.bot.send_message(
            user_id,
            response,
            parse_mode='Markdown',
            reply_markup=markup
        )
    
    @handle_errors
    def show_habits_for_tracking(self, user_id: int):
        """Показать привычки для отметки выполнения"""
        habits = self.db.get_user_habits(user_id)
        
        if not habits:
            self.bot.send_message(
                user_id,
                "💪 У вас нет привычек для отметки.",
                reply_markup=self.keyboards.habits_menu()
            )
            return
        
        markup = InlineKeyboardMarkup()
        
        for habit in habits:
            # Проверяем текущий статус
            today_completed = self.db.is_habit_completed_today(habit.id)
            button_text = f"{'✅' if today_completed else '⬜'} {habit.habit_name} ({habit.current_streak} дн.)"
            callback_data = f"habits:track:{habit.id}"
            
            markup.add(InlineKeyboardButton(button_text, callback_data=callback_data))
        
        markup.add(InlineKeyboardButton("↩️ Назад", callback_data="habits:back_to_menu"))
        
        self.bot.send_message(
            user_id,
            "✅ **Отметьте выполненные привычки:**\n\n"
            "✅ - выполнено сегодня\n"
            "⬜ - не выполнено\n\n"
            "Нажмите на привычку, чтобы изменить статус:",
            reply_markup=markup
        )
    
    @handle_errors
    def prompt_habit_deletion(self, user_id: int):
        """Запрос на удаление привычки"""
        habits = self.db.get_user_habits(user_id)
        
        if not habits:
            self.bot.send_message(
                user_id,
                "💪 У вас нет привычек для удаления.",
                reply_markup=self.keyboards.habits_menu()
            )
            return
        
        markup = InlineKeyboardMarkup()
        
        for habit in habits:
            markup.add(
                InlineKeyboardButton(
                    f"🗑️ {habit.habit_name}",
                    callback_data=f"habits:delete:{habit.id}"
                )
            )
        
        markup.add(InlineKeyboardButton("❌ Отмена", callback_data="habits:cancel_delete"))
        
        self.bot.send_message(
            user_id,
            "🗑️ **Выберите привычку для удаления:**\n\n"
            "*Будут удалены все данные о привычке!*",
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    @handle_errors
    def handle_callback_query(self, call: CallbackQuery):
        """Обработка callback запросов для привычек"""
        chat_id = call.message.chat.id
        data = call.data
        
        try:
            # Используем более четкую структуру callback данных
            if data.startswith('habits:'):
                parts = data.split(':')
                action = parts[1] if len(parts) > 1 else None
                
                if action == 'track':
                    if len(parts) > 2 and parts[2].isdigit():
                        habit_id = int(parts[2])
                        self.toggle_habit_completion(chat_id, habit_id, call)
                    else:
                        # Показать список привычек для отметки
                        self.bot.delete_message(chat_id, call.message.message_id)
                        self.show_habits_for_tracking(chat_id)
                
                elif action == 'delete':
                    if len(parts) > 2 and parts[2].isdigit():
                        habit_id = int(parts[2])
                        self.confirm_habit_deletion(chat_id, habit_id, call)
                    else:
                        # Показать список привычек для удаления
                        self.bot.delete_message(chat_id, call.message.message_id)
                        self.prompt_habit_deletion(chat_id)
                
                elif action == 'confirm_delete':
                    if len(parts) > 2 and parts[2].isdigit():
                        habit_id = int(parts[2])
                        result_message = self.delete_habit(chat_id, habit_id)
                        
                        # Удаляем сообщение с подтверждением
                        self.bot.delete_message(chat_id, call.message.message_id)
                        
                        # Показываем результат удаления
                        self.bot.send_message(
                            chat_id,
                            result_message,
                            reply_markup=self.keyboards.habits_menu()
                        )
                
                elif action == 'delete_prompt':
                    self.bot.delete_message(chat_id, call.message.message_id)
                    self.prompt_habit_deletion(chat_id)
                
                elif action == 'cancel_delete':
                    self.bot.delete_message(chat_id, call.message.message_id)
                    self.bot.send_message(
                        chat_id,
                        "❌ Удаление отменено.",
                        reply_markup=self.keyboards.habits_menu()
                    )
                
                elif action == 'back_to_menu':
                    self.bot.delete_message(chat_id, call.message.message_id)
                    self.bot.send_message(
                        chat_id,
                        "Возвращаю в меню привычек...",
                        reply_markup=self.keyboards.habits_menu()
                    )
            
            # Обработка старых callback форматов для обратной совместимости
            elif data.startswith('track_habit_'):
                habit_id = int(data.split('_')[2])
                self.toggle_habit_completion(chat_id, habit_id, call)
            
            elif data == 'track_habits':
                self.bot.delete_message(chat_id, call.message.message_id)
                self.show_habits_for_tracking(chat_id)
            
            elif data == 'delete_habit_prompt':
                self.bot.delete_message(chat_id, call.message.message_id)
                self.prompt_habit_deletion(chat_id)
            
            elif data in ['back_to_habits_menu', 'back_to_habits']:
                self.bot.delete_message(chat_id, call.message.message_id)
                self.bot.send_message(
                    chat_id,
                    "Возвращаю в меню привычек...",
                    reply_markup=self.keyboards.habits_menu()
                )
            
            elif data == 'back_to_main_menu':
                self.bot.delete_message(chat_id, call.message.message_id)
                self.bot.send_message(
                    chat_id,
                    "Возвращаю в главное меню...",
                    reply_markup=self.keyboards.main_menu()
                )
        
        except Exception as e:
            logger.error(f"Callback error in habits: {e}")
            self.bot.answer_callback_query(call.id, "❌ Произошла ошибка")
    
    @handle_errors
    def toggle_habit_completion(self, user_id: int, habit_id: int, call: CallbackQuery = None):
        """Переключение статуса выполнения привычки"""
        habit = self.db.get_habit_by_id(habit_id)
        
        if not habit or habit.user_id != user_id:
            if call:
                self.bot.answer_callback_query(call.id, "❌ Привычка не найдена")
            return
        
        # Переключаем статус выполнения
        completed = self.db.toggle_habit_completion(habit_id)
        
        # Обновляем серию
        self.db.update_habit_streak(habit_id)
        
        # Обновляем привычку
        habit = self.db.get_habit_by_id(habit_id)
        
        if call:
            if completed:
                message = f"✅ Привычка '{habit.habit_name}' отмечена как выполненная!"
                # Показываем мотивационное сообщение для длинных серий
                if habit.current_streak % 7 == 0:  # Каждую неделю
                    message += f"\n\n🎉 Поздравляем! Вы сохраняете серию уже {habit.current_streak} дней!"
                elif habit.current_streak == habit.target_days:
                    message += f"\n\n🏆 Ура! Вы достигли цели в {habit.target_days} дней!"
            else:
                message = f"❌ Отметка о выполнении привычки '{habit.habit_name}' снята."
            
            self.bot.answer_callback_query(call.id, message)
            
            # Обновляем сообщение с привычками
            self.bot.delete_message(user_id, call.message.message_id)
            self.show_habits_for_tracking(user_id)
    
    @handle_errors
    def confirm_habit_deletion(self, user_id: int, habit_id: int, call: CallbackQuery):
        """Подтверждение удаления привычки"""
        habit = self.db.get_habit_by_id(habit_id)
        
        if not habit or habit.user_id != user_id:
            self.bot.answer_callback_query(call.id, "❌ Привычка не найдена")
            return
        
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("✅ Да, удалить", callback_data=f"habits:confirm_delete:{habit_id}"),
            InlineKeyboardButton("❌ Отмена", callback_data="habits:cancel_delete")
        )
        
        self.bot.edit_message_text(
            f"⚠️ **Вы уверены, что хотите удалить привычку?**\n\n"
            f"💪 {habit.habit_name}\n"
            f"🏃 Текущая серия: {habit.current_streak} дней\n\n"
            f"*Это действие нельзя отменить!*",
            user_id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    @handle_errors
    def delete_habit(self, user_id: int, habit_id: int) -> str:
        """Удаление привычки"""
        try:
            # Проверяем, существует ли привычка и принадлежит ли пользователю
            habit = self.db.get_habit_by_id(habit_id)
            if not habit:
                return "❌ Привычка не найдена"
            
            if habit.user_id != user_id:
                return "❌ Вы не можете удалить эту привычку"
            
            # Сохраняем название привычки для сообщения
            habit_name = habit.habit_name
            
            # Удаляем привычку
            success = self.db.delete_habit(habit_id)
            
            if success:
                return f"✅ Привычка '{habit_name}' успешно удалена!"
            else:
                return "❌ Ошибка при удалении привычки из базы данных"
        
        except Exception as e:
            logger.error(f"Error deleting habit {habit_id}: {e}")
            return "❌ Произошла ошибка при удалении привычки"
    
    def _create_progress_bar(self, percentage: float, length: int = 10) -> str:
        """Создание текстового прогресс-бара"""
        filled = int(length * percentage / 100)
        empty = length - filled
        return "█" * filled + "░" * empty