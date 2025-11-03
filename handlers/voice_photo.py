import os
import tempfile
import logging
from telebot import TeleBot
from telebot.types import Message
from database.operations import DatabaseManager
from utils.keyboards import KeyboardManager
from utils.error_handling import handle_errors
from pathlib import Path

# Инициализация логгера должна быть в начале файла
logger = logging.getLogger(__name__)

class VoicePhotoHandler:
    """Обработчик голосовых сообщений и фотографий"""
    
    def __init__(self, bot: TeleBot, db: DatabaseManager, keyboards: KeyboardManager):
        self.bot = bot
        self.db = db
        self.keyboards = keyboards
        self.temp_dir = Path(tempfile.gettempdir()) / "telegram_bot"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Пытаемся импортировать реальные процессоры, иначе используем заглушки
        try:
            from services.image_processor import ImageProcessor
            self.image_processor = ImageProcessor()
            logger.info("✅ ImageProcessor загружен")
        except ImportError:
            from services.image_processor import ImageProcessor
            self.image_processor = ImageProcessor()
            logger.warning
        
        try:
            from services.voice_recognizer import VoiceRecognizer
            self.voice_recognizer = VoiceRecognizer()
            logger.info("✅ VoiceRecognizer загружен")
        except ImportError:
            from services.voice_recognizer_stub import VoiceRecognizer
            self.voice_recognizer = VoiceRecognizer()
            logger.warning
    
    def register_handlers(self):
        """Регистрация обработчиков"""
        
        @self.bot.message_handler(func=lambda message: message.text == '🎤 Распознать голос')
        @handle_errors
        def handle_voice_button(message: Message):
            """Обработчик кнопки распознавания голоса"""
            self.bot.send_message(
                message.chat.id,
                "🎤 Отправьте голосовое сообщение для распознавания\n\n"
                "💡 *Поддерживаются форматы: OGG, WAV, M4A*\n"
                "⚠️ *Для работы функции требуется установка дополнительных библиотек*",
                parse_mode='Markdown'
            )
        
        @self.bot.message_handler(func=lambda message: message.text == '🖼 Обработать фото')
        @handle_errors
        def handle_photo_button(message: Message):
            """Обработчик кнопки обработки фото"""
            self.bot.send_message(
                message.chat.id,
                "🖼 Отправьте фото для обработки\n\n"
                "💡 *Доступные улучшения: контраст, резкость, цветокоррекция*\n"
                "⚠️ *Для работы функции требуется установка библиотеки Pillow*",
                parse_mode='Markdown'
            )
        
        @self.bot.message_handler(content_types=['voice'])
        @handle_errors
        def handle_voice_message(message: Message):
            """Обработчик голосовых сообщений"""
            self.process_voice_message(message)
        
        @self.bot.message_handler(content_types=['audio'])
        @handle_errors
        def handle_audio_message(message: Message):
            """Обработчик аудио сообщений"""
            self.process_audio_message(message)
        
        @self.bot.message_handler(content_types=['photo'])
        @handle_errors
        def handle_photo_message(message: Message):
            """Обработчик фотографий"""
            self.process_photo_message(message)
    
    @handle_errors
    def process_voice_message(self, message: Message):
        """Обработка голосовых сообщений"""
        try:
            self.bot.send_message(message.chat.id, "🎤 Обрабатываю голосовое сообщение...")
        
            # Скачивание файла
            file_info = self.bot.get_file(message.voice.file_id)
            downloaded_file = self.bot.download_file(file_info.file_path)
        
            # Сохранение во временный файл
            temp_file = self.temp_dir / f"voice_{message.message_id}.oga"
            with open(temp_file, 'wb') as f:
                f.write(downloaded_file)
        
            # Распознавание речи
            text = self.voice_recognizer.recognize_speech(str(temp_file))
        
            # Очистка временного файла
            temp_file.unlink(missing_ok=True)
        
            # Форматирование ответа в зависимости от результата
            if "Ошибка" in text or "не удалось" in text.lower() or "установите" in text.lower():
                # Если это сообщение от заглушки или ошибка
                response = text
            else:
                # Если распознавание успешно
                response = f"🎤 **Распознанный текст:**\n\n{text}"
        
            self.bot.send_message(
                message.chat.id,
                response,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Voice processing error: {e}")
            self.bot.send_message(
                message.chat.id,
                "❌ Ошибка обработки голосового сообщения. Попробуйте еще раз.",
                reply_markup=self.keyboards.main_menu()
            )
    
    @handle_errors
    def process_audio_message(self, message: Message):
        """Обработка аудио файлов"""
        try:
            self.bot.send_message(message.chat.id, "🎵 Обрабатываю аудио файл...")
            
            # Скачивание файла
            file_info = self.bot.get_file(message.audio.file_id)
            downloaded_file = self.bot.download_file(file_info.file_path)
            
            # Сохранение во временный файл
            temp_file = self.temp_dir / f"audio_{message.message_id}.mp3"
            with open(temp_file, 'wb') as f:
                f.write(downloaded_file)
            
            # Распознавание речи
            text = self.voice_recognizer.recognize_speech(str(temp_file))
            
            # Очистка временного файла
            temp_file.unlink(missing_ok=True)
            
            # Отправка результата
            self.bot.send_message(
                message.chat.id,
                text,
                parse_mode='Markdown'
            )
                
        except Exception as e:
            logger.error(f"Audio processing error: {e}")
            self.bot.send_message(
                message.chat.id,
                "❌ Ошибка обработки аудио файла.",
                reply_markup=self.keyboards.main_menu()
            )
    
    @handle_errors
    def process_photo_message(self, message: Message):
        """Обработка фотографий"""
        try:
            self.bot.send_message(message.chat.id, "🖼 Обрабатываю фото...")
        
            # Получаем фото наивысшего качества
            file_id = message.photo[-1].file_id
            file_info = self.bot.get_file(file_id)
            downloaded_file = self.bot.download_file(file_info.file_path)
            
            # Сохранение во временный файл
            temp_file = self.temp_dir / f"photo_{message.message_id}.jpg"
            with open(temp_file, 'wb') as f:
                f.write(downloaded_file)
            
            # Получаем информацию об изображении до обработки
            original_info = self.image_processor.get_image_info(str(temp_file))
            
            # Обработка изображения
            processed_image_path = self.image_processor.process_image(str(temp_file))
            
            if processed_image_path and processed_image_path != str(temp_file):
                # Получаем информацию об обработанном изображении
                processed_info = self.image_processor.get_image_info(processed_image_path)
                
                # Формируем информативное сообщение
                caption = (
                    "✅ **Фото обработано!**\n\n"
                    f"📐 **Размер:** {original_info.get('width', '?')}×{original_info.get('height', '?')} → "
                    f"{processed_info.get('width', '?')}×{processed_info.get('height', '?')}\n"
                    "✨ **Улучшения:**\n"
                    "• Повышена резкость\n"
                    "• Улучшен контраст\n"
                    "• Оптимизирована яркость\n"
                    "• Усилена цветопередача\n"
                    "• Уменьшены шумы\n\n"
                    "💡 *Изображение оптимизировано для лучшего качества*"
                )
                
                # Отправка обработанного фото
                with open(processed_image_path, 'rb') as photo:
                    self.bot.send_photo(
                        message.chat.id,
                        photo,
                        caption=caption,
                        parse_mode='Markdown'
                    )
                
                # Очистка временных файлов
                try:
                    if Path(processed_image_path).exists():
                        Path(processed_image_path).unlink()
                except Exception as e:
                    logger.warning(f"Could not delete processed image: {e}")
                
            else:
                # Если обработка не удалась, отправляем исходное фото
                with open(temp_file, 'rb') as photo:
                    self.bot.send_photo(
                        message.chat.id,
                        photo,
                        caption="📸 **Фото получено!**\n\n"
                               "❌ *Не удалось обработать изображение*\n"
                               "💡 *Попробуйте отправить другое фото*",
                        parse_mode='Markdown'
                    )
            
            # Очистка исходного файла
            try:
                temp_file.unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Could not delete temp file: {e}")
        
        except Exception as e:
            logger.error(f"Photo processing error: {e}")
            self.bot.send_message(
                message.chat.id,
                "❌ Ошибка обработки фото. Попробуйте еще раз.",
                reply_markup=self.keyboards.main_menu()
            )