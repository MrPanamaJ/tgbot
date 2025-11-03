import logging
import functools
from typing import Callable, Any
from telebot.types import Message, CallbackQuery

logger = logging.getLogger(__name__)

def handle_errors(func: Callable) -> Callable:
    """Декоратор для обработки ошибок в обработчиках"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Логирование ошибки
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            
            # Попытка отправить сообщение об ошибке пользователю
            try:
                # Ищем объект сообщения в аргументах
                message = None
                for arg in args:
                    if isinstance(arg, (Message, CallbackQuery)):
                        if isinstance(arg, CallbackQuery):
                            message = arg.message
                        else:
                            message = arg
                        break
                
                if message:
                    chat_id = message.chat.id
                    error_message = (
                        "❌ Произошла непредвиденная ошибка.\n\n"
                        "💡 *Что можно сделать:*\n"
                        "• Попробуйте еще раз\n"
                        "• Проверьте введенные данные\n"
                        "• Если ошибка повторяется, обратитесь к администратору\n\n"
                        "⚡ *Мы уже работаем над исправлением!*"
                    )
                    
                    # Пытаемся отправить сообщение об ошибке
                    try:
                        if hasattr(args[0], 'bot'):
                            args[0].bot.send_message(
                                chat_id,
                                error_message,
                                parse_mode='Markdown'
                            )
                    except:
                        pass
                        
            except Exception as send_error:
                logger.error(f"Error sending error message: {send_error}")
            
            return None
    
    return wrapper

class ErrorHandler:
    """Класс для централизованной обработки ошибок"""
    
    @staticmethod
    def handle_database_error(error: Exception, context: str = "") -> str:
        """Обработка ошибок базы данных"""
        logger.error(f"Database error in {context}: {error}")
        
        if "UNIQUE constraint" in str(error):
            return "❌ Запись с такими данными уже существует"
        elif "FOREIGN KEY constraint" in str(error):
            return "❌ Ошибка связи данных"
        elif "no such table" in str(error):
            return "❌ Ошибка структуры базы данных"
        else:
            return "❌ Ошибка базы данных. Попробуйте позже."
    
    @staticmethod
    def handle_api_error(error: Exception, service: str = "") -> str:
        """Обработка ошибок API"""
        logger.error(f"API error from {service}: {error}")
        
        if "connection" in str(error).lower():
            return f"❌ Ошибка соединения с {service}. Проверьте интернет-соединение."
        elif "timeout" in str(error).lower():
            return f"❌ Превышено время ожидания ответа от {service}."
        elif "404" in str(error):
            return f"❌ Сервис {service} временно недоступен."
        else:
            return f"❌ Ошибка сервиса {service}. Попробуйте позже."
    
    @staticmethod
    def handle_validation_error(field: str, value: Any, rules: str = "") -> str:
        """Обработка ошибок валидации"""
        error_messages = {
            'empty': f"❌ Поле '{field}' не может быть пустым",
            'invalid_format': f"❌ Неверный формат для поля '{field}'",
            'too_short': f"❌ Поле '{field}' слишком короткое",
            'too_long': f"❌ Поле '{field}' слишком длинное",
            'invalid_range': f"❌ Значение поля '{field}' вне допустимого диапазона"
        }
        
        return error_messages.get(rules, f"❌ Ошибка валидации поля '{field}'")
    
    @staticmethod
    def handle_file_error(error: Exception, operation: str = "") -> str:
        """Обработка ошибок файлов"""
        logger.error(f"File error during {operation}: {error}")
        
        if "permission" in str(error).lower():
            return "❌ Ошибка доступа к файлу"
        elif "not found" in str(error).lower():
            return "❌ Файл не найден"
        elif "disk" in str(error).lower():
            return "❌ Недостаточно места на диске"
        else:
            return "❌ Ошибка при работе с файлом"

# Глобальный обработчик ошибок для бота
def setup_error_handling(bot):
    """Настройка глобальной обработки ошибок для бота"""
    
    @bot.callback_query_handler(func=lambda call: True)
    @handle_errors
    def handle_all_callbacks(call):
        """Глобальный обработчик callback запросов"""
        # Эта функция будет перехватывать все callback'и
        # и направлять их в соответствующие обработчики
        pass
    
    @bot.message_handler(content_types=['text', 'photo', 'voice', 'audio', 'document', 'location'])
    @handle_errors  
    def handle_all_messages(message):
        """Глобальный обработчик сообщений"""
        # Эта функция будет перехватывать все сообщения
        # и направлять их в соответствующие обработчики
        pass