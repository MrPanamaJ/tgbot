from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.operations import DatabaseManager
from database.models import Note
from utils.keyboards import KeyboardManager
from utils.error_handling import handle_errors
from utils.helpers import TextAnalyzer
import logging
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)

class NotesHandler:
    """Обработчик заметок"""
    
    def __init__(self, bot: TeleBot, db: DatabaseManager, keyboards: KeyboardManager):
        self.bot = bot
        self.db = db
        self.keyboards = keyboards
        self.text_analyzer = TextAnalyzer()
    
    def register_handlers(self):
        """Регистрация обработчиков"""
        
        @self.bot.message_handler(func=lambda message: message.text == '📝 Заметки')
        @handle_errors
        def handle_notes_menu(message: Message):
            """Обработчик меню заметок"""
            instructions = (
                "📝 **Управление заметками**\n\n"
                "Вы можете:\n"
                "• ➕ Создать новую заметку\n"
                "• 📋 Просмотреть все заметки\n"
                "• 🗑️ Удалить заметку\n\n"
                "Выберите действие:"
            )
            self.bot.send_message(
                message.chat.id,
                instructions,
                reply_markup=self.keyboards.notes_menu()
            )
        
        @self.bot.message_handler(func=lambda message: message.text == '➕ Новая заметка')
        @handle_errors
        def handle_new_note(message: Message):
            """Создание новой заметки"""
            self.bot.send_message(message.chat.id, "📝 Введите текст заметки:")
            self.bot.register_next_step_handler(message, self.process_new_note)
        
        @self.bot.message_handler(func=lambda message: message.text == '📋 Все заметки')
        @handle_errors
        def handle_show_notes(message: Message):
            """Показать все заметки"""
            self.show_user_notes(message.chat.id)
        
        @self.bot.message_handler(func=lambda message: message.text == '🗑️ Удалить заметку')
        @handle_errors
        def handle_delete_note(message: Message):
            """Удаление заметки"""
            self.prompt_note_deletion(message.chat.id)
    
    @handle_errors
    def process_new_note(self, message: Message):
        """Обработка создания новой заметки"""
        note_text = message.text.strip()
        
        if not note_text:
            self.bot.send_message(
                message.chat.id,
                "❌ Текст заметки не может быть пустым.",
                reply_markup=self.keyboards.notes_menu()
            )
            return
        
        # Анализ текста
        analysis = self.text_analyzer.analyze(note_text)
        
        # Создание заметки
        note = Note(
            id=0,
            user_id=message.chat.id,
            note_text=note_text,
            created_at=datetime.now()
        )
        
        note_id = self.db.add_note(note)
        
        response = (
            f"✅ **Заметка #{note_id} сохранена!**\n\n"
            f"📊 Статистика:\n"
            f"• 📝 Слов: {analysis['words']}\n"
            f"• 🔤 Символов: {analysis['characters']}\n"
            f"• 📄 Предложений: {analysis['sentences']}\n"
            f"• ⏱ Время чтения: ~{analysis['reading_time_minutes']} мин\n\n"
            f"💡 *Заметка доступна в списке ваших заметок*"
        )
        
        self.bot.send_message(
            message.chat.id,
            response,
            parse_mode='Markdown',
            reply_markup=self.keyboards.notes_menu()
        )
    
    @handle_errors
    def show_user_notes(self, user_id: int, page: int = 1, page_size: int = 5):
        """Показать заметки пользователя с пагинацией"""
        notes = self.db.get_user_notes(user_id)
        
        if not notes:
            self.bot.send_message(
                user_id,
                "📝 У вас пока нет заметок.",
                reply_markup=self.keyboards.notes_menu()
            )
            return
        
        # Пагинация
        total_notes = len(notes)
        total_pages = (total_notes + page_size - 1) // page_size
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_notes = notes[start_idx:end_idx]
        
        response = f"📋 **Ваши заметки (страница {page}/{total_pages}):**\n\n"
        
        for note in page_notes:
            # Обрезка длинного текста для предпросмотра
            preview = note.note_text[:100] + "..." if len(note.note_text) > 100 else note.note_text
            created_date = note.created_at.strftime('%d.%m.%Y %H:%M')
            response += f"🆔 #{note.id} - {created_date}\n{preview}\n\n"
        
        # Создание клавиатуры пагинации
        markup = InlineKeyboardMarkup()
        
        if page > 1:
            markup.add(InlineKeyboardButton("⬅️ Назад", callback_data=f"notes_page_{page-1}"))
        
        if page < total_pages:
            if page > 1:
                # Если есть обе кнопки, добавляем в один ряд
                markup.row(
                    InlineKeyboardButton("⬅️ Назад", callback_data=f"notes_page_{page-1}"),
                    InlineKeyboardButton("Вперед ➡️", callback_data=f"notes_page_{page+1}")
                )
            else:
                markup.add(InlineKeyboardButton("Вперед ➡️", callback_data=f"notes_page_{page+1}"))
        
        markup.add(InlineKeyboardButton("🗑️ Удалить заметку", callback_data="delete_note_prompt"))
        markup.add(InlineKeyboardButton("↩️ В меню", callback_data="back_to_notes_menu"))
        
        self.bot.send_message(
            user_id,
            response,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    @handle_errors
    def prompt_note_deletion(self, user_id: int):
        """Запрос на удаление заметки"""
        notes = self.db.get_user_notes(user_id)
        
        if not notes:
            self.bot.send_message(
                user_id,
                "📝 У вас нет заметок для удаления.",
                reply_markup=self.keyboards.notes_menu()
            )
            return
        
        response = "🗑️ **Введите ID заметки для удаления:**\n\n"
        
        # Показываем только последние 5 заметок для выбора
        for note in notes[:5]:
            preview = note.note_text[:50] + "..." if len(note.note_text) > 50 else note.note_text
            created_date = note.created_at.strftime('%d.%m.%Y')
            response += f"🆔 #{note.id} - {created_date}\n{preview}\n\n"
        
        self.bot.send_message(user_id, response)
        self.bot.register_next_step_handler_by_chat_id(user_id, self.process_note_deletion)
    
    @handle_errors
    def process_note_deletion(self, message: Message):
        """Обработка удаления заметки"""
        try:
            note_id = int(message.text.strip())
            
            # Проверка существования заметки и прав доступа
            note = self.db.get_note_by_id(note_id)
            
            if not note or note.user_id != message.chat.id:
                self.bot.send_message(
                    message.chat.id,
                    "❌ Заметка не найдена или у вас нет прав для её удаления.",
                    reply_markup=self.keyboards.notes_menu()
                )
                return
            
            # Подтверждение удаления
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_note_{note_id}"),
                InlineKeyboardButton("❌ Отмена", callback_data="cancel_delete_note")
            )
            
            preview = note.note_text[:100] + "..." if len(note.note_text) > 100 else note.note_text
            
            self.bot.send_message(
                message.chat.id,
                f"⚠️ **Вы уверены, что хотите удалить заметку?**\n\n"
                f"🆔 #{note_id}\n"
                f"📝 {preview}\n\n"
                f"*Это действие нельзя отменить!*",
                reply_markup=markup,
                parse_mode='Markdown'
            )
            
        except ValueError:
            self.bot.send_message(
                message.chat.id,
                "❌ Неверный формат ID. Введите число.",
                reply_markup=self.keyboards.notes_menu()
            )
    
    @handle_errors
    def handle_callback_query(self, call: CallbackQuery):
        """Обработка callback запросов для заметок"""
        chat_id = call.message.chat.id
        data = call.data
        
        try:
            if data.startswith('notes_page_'):
                page = int(data.split('_')[2])
                self.bot.delete_message(chat_id, call.message.message_id)
                self.show_user_notes(chat_id, page)
            
            elif data == 'delete_note_prompt':
                self.bot.delete_message(chat_id, call.message.message_id)
                self.prompt_note_deletion(chat_id)
            
            elif data.startswith('confirm_delete_note_'):
                note_id = int(data.split('_')[3])
                success = self.db.delete_note(note_id)
                
                if success:
                    self.bot.edit_message_text(
                        f"✅ Заметка #{note_id} удалена!",
                        chat_id,
                        call.message.message_id
                    )
                else:
                    self.bot.edit_message_text(
                        "❌ Ошибка при удалении заметки.",
                        chat_id,
                        call.message.message_id
                    )
            
            elif data == 'cancel_delete_note':
                self.bot.edit_message_text(
                    "❌ Удаление отменено.",
                    chat_id,
                    call.message.message_id
                )
            
            elif data == 'back_to_notes_menu':
                self.bot.delete_message(chat_id, call.message.message_id)
                self.bot.send_message(
                    chat_id,
                    "Возвращаю в меню заметок...",
                    reply_markup=self.keyboards.notes_menu()
                )
        
        except Exception as e:
            logger.error(f"Callback error in notes: {e}")
            self.bot.answer_callback_query(call.id, "❌ Произошла ошибка")