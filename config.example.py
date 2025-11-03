"""
Пример конфигурационного файла для Telegram бота.
Создайте копию этого файла с именем config.py и заполните своими данными.
"""

class Config:
    # Токен вашего Telegram бота (получить через @BotFather)
    BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
    
    # URL API для получения погоды (Open-Meteo API)
    WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
    
    # Конфигурация базы данных
    DATABASE_CONFIG = {
        'database': 'database.db'  # Путь к файлу базы данных SQLite
    }

# Создаем экземпляр конфигурации
config = Config()