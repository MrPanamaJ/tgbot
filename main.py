import sys
import logging
import signal
import time
from pathlib import Path
from typing import List, Optional

# Настраиваем логирование до импорта других модулей
from utils.logging_config import setup_logging

# Добавляем корневую директорию в путь Python
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

setup_logging()

logger = logging.getLogger(__name__)

# Версия бота
BOT_VERSION = "1.0.0"


def import_with_fallback(module_name, class_name, fallback_value=None):
    """Импорт с обработкой ошибок"""
    try:
        module = __import__(module_name, fromlist=[class_name])
        return getattr(module, class_name)
    except ImportError as e:
        logger.warning(
            f"⚠️ Не удалось импортировать {class_name} из {module_name}: {e}"
        )
        return fallback_value


# Попытка импорта основных модулей
try:
    from telebot import TeleBot
    from config import config
    from database.operations import DatabaseManager
    from services.weather_api import WeatherService
    from services.scheduler import start_scheduler
    from utils.keyboards import KeyboardManager

    # Импортируем обработчики с обработкой ошибок
    from handlers.base import StartHandler, HelpHandler
    from handlers.weather import WeatherHandler
    from handlers.finance import FinanceHandler
    from handlers.notes import NotesHandler
    from handlers.habits import HabitsHandler
    from handlers.utilities import UtilitiesHandler
    from handlers.services import ServicesHandler

    # VoicePhotoHandler может быть опциональным
    try:
        from handlers.voice_photo import VoicePhotoHandler

        VOICE_PHOTO_AVAILABLE = True
    except ImportError as e:
        logger.warning(f"⚠️ VoicePhotoHandler недоступен: {e}")
        VOICE_PHOTO_AVAILABLE = False

except ImportError as e:
    logger.error(f"❌ Ошибка импорта: {e}")
    print(f"❌ Ошибка импорта: {e}")
    print("📦 Убедитесь, что все зависимости установлены:")
    print("   pip install -r requirements.txt")
    sys.exit(1)


class BotManager:
    """Менеджер для управления ботом и всеми компонентами"""

    def __init__(self):
        self.bot: Optional[TeleBot] = None
        self.db: Optional[DatabaseManager] = None
        self.keyboards: Optional[KeyboardManager] = None
        self.weather_service: Optional[WeatherService] = None
        self.handlers: List = []
        self.scheduler = None
        self._shutdown_requested = False

    def _signal_handler(self, signum, frame):
        """Обработчик сигналов завершения"""
        logger.info(
            f"📥 Получен сигнал {signum}, запрашиваю завершение работы..."
        )
        self._shutdown_requested = True
        self.shutdown()

    def _setup_signal_handlers(self):
        """Настройка обработчиков сигналов"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        logger.info("✅ Обработчики сигналов настроены")

    def _validate_config(self) -> bool:
        """Проверка конфигурации перед запуском"""
        try:
            # Проверка токена бота
            if not config.BOT_TOKEN or config.BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
                logger.error("❌ Не установлен токен бота в конфигурации")
                return False

            # Проверка URL API погоды
            if not config.WEATHER_API_URL:
                logger.error("❌ Не установлен URL API погоды в конфигурации")
                return False

            # Проверка конфигурации базы данных
            if not config.DATABASE_CONFIG or 'database' not in config.DATABASE_CONFIG:
                logger.error("❌ Некорректная конфигурация базы данных")
                return False

            logger.info("✅ Конфигурация проверена успешно")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка проверки конфигурации: {e}")
            return False

    def initialize(self):
        """Инициализация всех компонентов бота"""
        try:
            logger.info(
                f"🔄 Инициализация бота (версия {BOT_VERSION})..."
            )

            # Проверка конфигурации
            if not self._validate_config():
                raise ValueError("Ошибка конфигурации")

            # Настройка обработчиков сигналов
            self._setup_signal_handlers()

            # Инициализация основных компонентов
            self.bot = TeleBot(config.BOT_TOKEN)
            self.db = DatabaseManager(config.DATABASE_CONFIG['database'])
            self.keyboards = KeyboardManager()
            self.weather_service = WeatherService(config.WEATHER_API_URL)

            logger.info("✅ Основные компоненты инициализированы")

            # Инициализация обработчиков
            self._initialize_handlers()

            # Запуск планировщика
            self.scheduler = start_scheduler(self.bot, self.db, self.weather_service)

            logger.info("✅ Все компоненты бота успешно инициализированы")

        except Exception as e:
            logger.error(f"❌ Ошибка инициализации бота: {e}")
            raise

    def _initialize_handlers(self):
        """Инициализация всех обработчиков"""
        try:
            # Базовые обработчики (обязательные)
            self.handlers = [
                StartHandler(self.bot, self.db, self.keyboards),
                HelpHandler(self.bot, self.db, self.keyboards),
                WeatherHandler(
                    self.bot, self.db, self.weather_service, self.keyboards
                ),
                FinanceHandler(self.bot, self.db, self.keyboards),
                NotesHandler(self.bot, self.db, self.keyboards),
                HabitsHandler(self.bot, self.db, self.keyboards),
                UtilitiesHandler(self.bot, self.db, self.keyboards),
                ServicesHandler(self.bot, self.db, self.keyboards),
            ]

            # Опциональные обработчики
            if VOICE_PHOTO_AVAILABLE:
                self.handlers.append(
                    VoicePhotoHandler(self.bot, self.db, self.keyboards)
                )
                logger.info("✅ VoicePhotoHandler загружен")
            else:
                logger.info("⚠️ VoicePhotoHandler пропущен (недоступен)")

            # Регистрация обработчиков
            for handler in self.handlers:
                handler.register_handlers()

            # Регистрация callback обработчиков
            self._register_callback_handlers()

            logger.info(
                f"✅ Зарегистрировано {len(self.handlers)} обработчиков"
            )

        except Exception as e:
            logger.error(f"❌ Ошибка инициализации обработчиков: {e}")
            raise

    def _register_callback_handlers(self):
        """Регистрация обработчиков callback запросов"""

        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_all_callbacks(call):
            """Централизованный обработчик callback запросов"""
            try:
                # Перенаправляем callback в соответствующий обработчик
                for handler in self.handlers:
                    if hasattr(handler, 'handle_callback_query'):
                        handler.handle_callback_query(call)

            except Exception as e:
                logger.error(f"Callback handling error: {e}")
                try:
                    error_msg = "❌ Произошла ошибка"
                    self.bot.answer_callback_query(call.id, error_msg)
                except Exception:
                    pass

    def start(self):
        """Запуск бота"""
        try:
            logger.info("🤖 Запуск бота...")

            # Информация о запуске
            logger.info("📊 Загруженные модули:")
            logger.info(f"   🎯 Обработчиков: {len(self.handlers)}")
            logger.info("   🌤️ Погодный сервис")
            logger.info("   📅 Планировщик уведомлений")
            logger.info("   💾 База данных")
            logger.info(f"   📦 Версия: {BOT_VERSION}")

            # Запуск опроса
            while not self._shutdown_requested:
                try:
                    self.bot.polling(none_stop=True, interval=0, timeout=60)
                except Exception as e:
                    if not self._shutdown_requested:
                        logger.error(f"❌ Ошибка во время работы бота: {e}")
                        logger.info("🔄 Переподключение через 10 секунд...")
                        time.sleep(10)
                    else:
                        break

        except KeyboardInterrupt:
            logger.info("🛑 Бот остановлен пользователем")
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
            raise
        finally:
            self.shutdown()

    def shutdown(self):
        """Корректное завершение работы бота"""
        try:
            logger.info("🔄 Начинаю корректное завершение работы...")

            if self.scheduler:
                self.scheduler.stop()
                logger.info("✅ Планировщик остановлен")

            if self.bot:
                # Останавливаем polling в отдельном потоке, чтобы избежать блокировки
                import threading

                def stop_polling():
                    try:
                        self.bot.stop_polling()
                    except Exception:
                        pass

                stop_thread = threading.Thread(target=stop_polling, daemon=True)
                stop_thread.start()
                stop_thread.join(timeout=5)  # Ждем максимум 5 секунд
                logger.info("✅ Бот остановлен")

            if self.db:
                self.db.close()
                logger.info("✅ База данных закрыта")

            logger.info("✅ Бот корректно завершил работу")

        except Exception as e:
            logger.error(f"Ошибка при завершении работы: {e}")


def main():
    """Главная функция запуска"""
    logger.info(
        "🚀 Запуск многофункционального Telegram бота "
        f"(версия {BOT_VERSION})"
    )

    bot_manager = BotManager()

    try:
        bot_manager.initialize()
        bot_manager.start()

    except Exception as e:
        logger.critical(f"❌ Критическая ошибка при запуске бота: {e}")

        # Попытка перезапуска с экспоненциальной задержкой
        retry_count = 0
        max_retries = 5
        while retry_count < max_retries:
            retry_count += 1
            delay = min(
                30 * (2 ** (retry_count - 1)), 300
            )  # Максимум 5 минут
            logger.info(
                f"🔄 Попытка перезапуска #{retry_count}/{max_retries} "
                f"через {delay} секунд..."
            )
            time.sleep(delay)

            try:
                main()
                break
            except Exception as retry_error:
                logger.error(
                    f"❌ Ошибка при перезапуске #{retry_count}: {retry_error}"
                )
                if retry_count >= max_retries:
                    logger.critical(
                        "❌ Достигнуто максимальное количество "
                        "попыток перезапуска. Завершение работы."
                    )
                    sys.exit(1)


if __name__ == "__main__":
    main()
