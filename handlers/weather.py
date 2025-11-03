from telebot import TeleBot
from telebot.types import Message
from database.operations import DatabaseManager
from services.weather_api import WeatherService
from utils.keyboards import KeyboardManager
from database.models import WeatherSubscription
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class WeatherHandler:
    """Обработчик погоды"""
    def __init__(self, bot: TeleBot, db: DatabaseManager, weather_service: WeatherService, keyboards: KeyboardManager):
        self.bot = bot
        self.db = db
        self.weather_service = weather_service
        self.keyboards = keyboards
    
    def register_handlers(self):
        """Регистрация всех обработчиков"""
        
        @self.bot.message_handler(func=lambda message: message.text == '🌤️ Прогноз погоды')
        def handle_weather_request(message: Message):
            """Обработчик кнопки прогноза погоды"""
            instructions = (
                "🌤️ **Чтобы получить точный прогноз погоды:**\n\n"
                "1. 📍 Нажмите кнопку **'Поделиться местоположением'** ниже\n"
                "2. 📱 Разрешите доступ к вашей геолокации\n"
                "3. ⏳ Подождите несколько секунд\n\n"
                "📍 *Нажмите кнопку ниже:*"
            )
            self.bot.send_message(
                message.chat.id, 
                instructions, 
                reply_markup=self.keyboards.weather_menu(),
                parse_mode='Markdown'
            )
        
        @self.bot.message_handler(func=lambda message: message.text == '💾 Сохранить локацию')
        def handle_save_location(message: Message):
            """Обработчик кнопки сохранения локации"""
            instructions = (
                "💾 **Сохранение локации**\n\n"
                "Сохраните ваше местоположение для:\n"
                "• 🌤️ Быстрого доступа к прогнозу погоды\n"
                "• 🔔 Точных уведомлений о погоде\n"
                "• 📍 Быстрого получения прогноза\n\n"
                "📍 *Нажмите кнопку ниже, чтобы поделиться местоположением:*"
            )
            self.bot.send_message(
                message.chat.id,
                instructions,
                reply_markup=self.keyboards.weather_menu(),
                parse_mode='Markdown'
            )
        
        @self.bot.message_handler(content_types=['location'])
        def handle_location(message: Message):
            """Обработчик геолокации"""
            if not message.location:
                self.bot.send_message(message.chat.id, "❌ Не удалось получить ваше местоположение.")
                return
            
            self.bot.send_message(message.chat.id, "📍 Получил ваше местоположение! Обрабатываю...")
            
            try:
                lat = message.location.latitude
                lon = message.location.longitude
                
                # Получение названия города
                city_name = self._get_city_name(lat, lon)
                
                # Сохранение подписки с локацией
                subscription = WeatherSubscription(
                    user_id=message.chat.id,
                    latitude=lat,
                    longitude=lon,
                    city_name=city_name,
                    updated_at=datetime.now()
                )
                self.db.save_weather_subscription(subscription)
                
                # Определяем тип запроса по тексту сообщения
                if hasattr(message, 'text') and message.text == '💾 Сохранить локацию':
                    # Если это сохранение локации, просто подтверждаем
                    response = (
                        f"✅ **Локация сохранена!**\n\n"
                        f"📍 Город: {city_name}\n"
                        f"📏 Координаты: {lat:.4f}, {lon:.4f}\n\n"
                        f"💡 Теперь вы можете быстро получать прогноз погоды "
                        f"и точные уведомления!"
                    )
                else:
                    # Если это запрос погоды, получаем и показываем погоду
                    weather_data = self.weather_service.get_weather(lat, lon, city_name)
                    response = self._format_weather_response(weather_data)
                
                self.bot.send_message(message.chat.id, response, parse_mode='Markdown')
                
            except Exception as e:
                logger.error(f"Location handling error: {e}")
                self.bot.send_message(
                    message.chat.id, 
                    "❌ Не удалось обработать ваше местоположение. Попробуйте еще раз."
                )
        
        @self.bot.message_handler(func=lambda message: message.text == '🔔 Подписка')
        def handle_subscription(message: Message):
            """Обработчик подписки на уведомления"""
            self._handle_subscription(message)
    def _handle_subscription(self, message: Message):
        """Обработчик подписки на уведомления (отдельный метод)"""
        try:
            print(f"🔔 Обработка подписки для пользователя {message.chat.id}")
            
            # Простая логика без проверки существующей подписки
            subscription = WeatherSubscription(
                user_id=message.chat.id,
                latitude=None,
                longitude=None,
                city_name=None,
                updated_at=datetime.now()
            )
            self.db.save_weather_subscription(subscription)
            
            self.bot.send_message(
                message.chat.id,
                "✅ Вы подписались на уведомления о погоде!\n\n"
                "📅 Я буду присылать вам прогноз погоды:\n"
                "• 🌅 В 8:00 - утренний прогноз\n" 
                "• 🌆 В 20:00 - вечерний прогноз\n\n"
                "💡 *Для точных прогнозов сохраните вашу локацию*",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Subscription error: {e}")
            self.bot.send_message(
                message.chat.id,
                "❌ Ошибка при обработке подписки. Попробуйте позже."
            )
    
    def _get_city_name(self, lat: float, lon: float) -> str:
        """Получение названия города по координатам"""
        # Реализация через OpenStreetMap
        return "Вашем городе"  # Упрощенная реализация
    
    def _format_weather_response(self, weather_data: dict) -> str:
        """Форматирование данных о погоде в текст"""
        try:
            # Получаем значения из словаря с защитой от отсутствующих ключей
            city = weather_data.get('city', 'Неизвестно')
            temperature = weather_data.get('temperature', 'N/A')
            feels_like = weather_data.get('feels_like', 'N/A')
            humidity = weather_data.get('humidity', 'N/A')
            pressure = weather_data.get('pressure', 'N/A')
            wind_speed = weather_data.get('wind_speed', 'N/A')
            description = weather_data.get('description', 'Нет описания')
            
            # Извлекаем эмодзи из описания или используем по умолчанию
            icon = '🌤️'  # Эмодзи по умолчанию
            if description and ' ' in description:
                icon = description.split(' ')[0]  # Берем первый эмодзи из описания
            
            return (
                f"{icon} **Погода в {city}:**\n\n"
                f"• 🌡 **Температура:** {temperature}°C\n"
                f"• 💭 **Ощущается как:** {feels_like}°C\n"
                f"• 💧 **Влажность:** {humidity}%\n"
                f"• 📈 **Давление:** {pressure} гПа\n"
                f"• 🌬 **Ветер:** {wind_speed} м/с\n"
                f"• 📝 **Описание:** {description}\n\n"
                f"💡 *Локация сохранена для уведомлений!*"
            )
            
        except Exception as e:
            logger.error(f"Error formatting weather response: {e}")
            return "❌ Ошибка при форматировании данных о погоде"
    
    def _weather_icons(self) -> dict:
        """Словарь для конвертации кодов погоды в эмодзи"""
        return {
            '01d': '☀️',  # ясно (день)
            '01n': '🌙',  # ясно (ночь)
            '02d': '⛅',  # малооблачно (день)
            '02n': '☁️',  # малооблачно (ночь)
            '03d': '☁️',  # облачно
            '03n': '☁️',
            '04d': '☁️',  # пасмурно
            '04n': '☁️',
            '09d': '🌧️',  # ливень
            '09n': '🌧️',
            '10d': '🌦️',  # дождь
            '10n': '🌦️',
            '11d': '⛈️',  # гроза
            '11n': '⛈️',
            '13d': '❄️',  # снег
            '13n': '❄️',
            '50d': '🌫️',  # туман
            '50n': '🌫️'
        }
        