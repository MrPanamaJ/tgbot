import sys
import os
import traceback

sys.path.append(os.path.dirname(__file__))

def debug_subscription():
    print("🔍 Отладка кнопки подписки...")
    
    try:
        # Имитируем нажатие кнопки подписки
        from database.operations import DatabaseManager
        from handlers.weather import WeatherHandler
        from services.weather_api import WeatherService
        from utils.keyboards import KeyboardManager
        
        # Создаем мок-объекты
        class MockBot:
            def send_message(self, chat_id, text, parse_mode=None, reply_markup=None):
                print(f"📤 Bot отправляет: {text}")
        
        class MockWeatherService:
            def get_weather(self, lat, lon, city):
                return {'city': 'Test', 'temperature': 20}
        
        class MockKeyboards:
            def weather_menu(self):
                return None
            def main_menu(self):
                return None
        
        # Создаем БД
        if os.path.exists('database.db'):
            os.remove('database.db')
        
        db = DatabaseManager('database.db')
        bot = MockBot()
        weather_service = MockWeatherService()
        keyboards = MockKeyboards()
        
        # Создаем хендлер
        weather_handler = WeatherHandler(bot, db, weather_service, keyboards)
        print("✅ WeatherHandler создан")
        
        # Имитируем сообщение подписки
        class MockMessage:
            def __init__(self):
                self.chat = type('Chat', (), {'id': 123})()
                self.text = '🔔 Подписка'
        
        message = MockMessage()
        
        print("🧪 Тестируем обработку подписки...")
        # Вызываем ПРАВИЛЬНЫЙ метод
        weather_handler._handle_subscription(message)  # ← ИСПРАВЛЕНО!
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("🔍 Полный traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_subscription()