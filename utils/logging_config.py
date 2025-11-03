import logging
import sys
from pathlib import Path

def setup_logging(log_dir: str = "logs", level: str = "INFO"):
    """Настройка логирования"""
    # Создаем директорию для логов
    Path(log_dir).mkdir(exist_ok=True)
    
    # Настраиваем уровень логирования
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Форматтер для логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Обработчик для файла
    file_handler = logging.FileHandler(
        Path(log_dir) / 'bot.log', 
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # Обработчик для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Очищаем существующие обработчики
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Добавляем наши обработчики
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Логируем запуск
    logging.info("Логирование инициализировано")