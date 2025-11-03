import requests
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class WeatherService:
    """Сервис для работы с погодой"""
    
    def __init__(self, api_url: str, timeout: int = 10):
        self.api_url = api_url
        self.timeout = timeout
    
    def get_weather(self, lat: float, lon: float, city_name: str = "Вашем городе") -> Dict[str, Any]:
        """Получение данных о погоде"""
        try:
            params = {
                'latitude': lat,
                'longitude': lon,
                'current': 'temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,pressure_msl',
                'timezone': 'auto'
            }

            response = requests.get(self.api_url, params=params, timeout=self.timeout)
            data = response.json()
            current = data.get('current', {})
            
            weather_desc = self._get_weather_description(current.get('weather_code', 0))
            
            return {
                'city': city_name,
                'temperature': round(current.get('temperature_2m', 0)),
                'feels_like': round(current.get('apparent_temperature', 0)),
                'humidity': round(current.get('relative_humidity_2m', 0)),
                'wind_speed': round(current.get('wind_speed_10m', 0)),
                'pressure': round(current.get('pressure_msl', 0)),
                'description': weather_desc
            }

        except Exception as e:
            logger.error(f"Ошибка получения погоды: {e}")
            return self._get_fallback_weather(city_name)

    def _get_weather_description(self, weather_code: int) -> str:
        """Преобразование кода погоды в текстовое описание"""
        weather_mapping = {
            0: "☀️ Ясно", 1: "🌤️ Преимущественно ясно", 2: "⛅ Переменная облачность",
            3: "☁️ Пасмурно", 45: "🌫️ Туман", 48: "🌫️ Гололедный туман",
            51: "🌧️ Легкая морось", 53: "🌧️ Умеренная морось", 55: "🌧️ Сильная морось",
            61: "🌧️ Небольшой дождь", 63: "🌧️ Умеренный дождь", 65: "🌧️ Сильный дождь",
            71: "❄️ Небольшой снег", 73: "❄️ Умеренный снег", 75: "❄️ Сильный снег",
            80: "🌦️ Небольшие ливни", 81: "🌦️ Умеренные ливни", 82: "🌦️ Сильные ливни",
            95: "⛈️ Гроза", 96: "⛈️ Гроза с градом", 99: "⛈️ Сильная гроза"
        }
        return weather_mapping.get(weather_code, "Неизвестно")

    def _get_fallback_weather(self, city_name: str) -> Dict[str, Any]:
        """Резервные данные погоды при ошибке API"""
        return {
            'city': city_name, 'temperature': 5, 'feels_like': 3, 'humidity': 75,
            'wind_speed': 3.0, 'pressure': 1015, 'description': '⛅ Переменная облачность'
        }