import schedule
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import List
from database.operations import DatabaseManager
from services.weather_api import WeatherService
from utils.helpers import QuoteGenerator

logger = logging.getLogger(__name__)

class NotificationScheduler:
    """Планировщик уведомлений"""
    
    def __init__(self, bot, db: DatabaseManager, weather_service: WeatherService):
        self.bot = bot
        self.db = db
        self.weather_service = weather_service
        self.quote_generator = QuoteGenerator()
        self.is_running = False
        self.thread = None
    
    def start(self):
        """Запуск планировщика"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        self._setup_schedule()
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("🚀 Планировщик уведомлений запущен")
    
    def stop(self):
        """Остановка планировщика"""
        self.is_running = False
        logger.info("🛑 Планировщик уведомлений остановлен")
    
    def _setup_schedule(self):
        """Настройка расписания"""
        # Утренние уведомления о погоде
        schedule.every().day.at("08:00").do(self._send_morning_weather)
        
        # Вечерние уведомления о погоде  
        schedule.every().day.at("20:00").do(self._send_evening_weather)
        
        # Ежедневные цитаты
        schedule.every().day.at("09:00").do(self._send_daily_quote)
        
        # Проверка напоминаний каждые 5 минут
        schedule.every(5).minutes.do(self._check_reminders)
    
    def _run_scheduler(self):
        """Основной цикл планировщика"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)
    
    def _send_morning_weather(self):
        """Отправка утреннего прогноза погоды"""
        try:
            subscriptions = self.db.get_weather_subscriptions()
            
            for subscription in subscriptions:
                try:
                    if subscription.latitude and subscription.longitude:
                        weather_data = self.weather_service.get_weather(
                            subscription.latitude, 
                            subscription.longitude,
                            subscription.city_name or "Вашем городе"
                        )
                        
                        message = (
                            f"🌅 **Доброе утро!**\n\n"
                            f"Погода в {weather_data['city']}:\n"
                            f"• 🌡 {weather_data['temperature']}°C (ощущается как {weather_data['feels_like']}°C)\n"
                            f"• 💧 Влажность: {weather_data['humidity']}%\n"
                            f"• 🌬 Ветер: {weather_data['wind_speed']} м/с\n"
                            f"• 📝 {weather_data['description']}\n\n"
                            f"Хорошего дня! ☀️"
                        )
                        
                        self.bot.send_message(subscription.user_id, message, parse_mode='Markdown')
                        
                except Exception as e:
                    logger.error(f"Error sending weather to {subscription.user_id}: {e}")
            
            logger.info("✅ Утренние уведомления о погоде отправлены")
            
        except Exception as e:
            logger.error(f"Morning weather error: {e}")
    
    def _send_evening_weather(self):
        """Отправка вечернего прогноза погоды"""
        try:
            subscriptions = self.db.get_weather_subscriptions()
            
            for subscription in subscriptions:
                try:
                    if subscription.latitude and subscription.longitude:
                        weather_data = self.weather_service.get_weather(
                            subscription.latitude,
                            subscription.longitude, 
                            subscription.city_name or "Вашем городе"
                        )
                        
                        message = (
                            f"🌆 **Добрый вечер!**\n\n"
                            f"Погода в {weather_data['city']}:\n"
                            f"• 🌡 {weather_data['temperature']}°C (ощущается как {weather_data['feels_like']}°C)\n"
                            f"• 💧 Влажность: {weather_data['humidity']}%\n"
                            f"• 🌬 Ветер: {weather_data['wind_speed']} м/с\n"
                            f"• 📝 {weather_data['description']}\n\n"
                            f"Спокойной ночи! 🌙"
                        )
                        
                        self.bot.send_message(subscription.user_id, message, parse_mode='Markdown')
                        
                except Exception as e:
                    logger.error(f"Error sending evening weather to {subscription.user_id}: {e}")
            
            logger.info("✅ Вечерние уведомления о погоде отправлены")
            
        except Exception as e:
            logger.error(f"Evening weather error: {e}")
    
    def _send_daily_quote(self):
        """Отправка ежедневной цитаты"""
        try:
            users = self.db.get_active_users()
            quote = self.quote_generator.get_daily_quote()
            
            for user in users:
                try:
                    message = f"💬 **Цитата дня:**\n\n{quote['full']}"
                    self.bot.send_message(user.user_id, message, parse_mode='Markdown')
                    
                except Exception as e:
                    logger.error(f"Error sending quote to {user.user_id}: {e}")
            
            logger.info("✅ Ежедневные цитаты отправлены")
            
        except Exception as e:
            logger.error(f"Daily quote error: {e}")
    
    def _check_reminders(self):
        """Проверка и отправка напоминаний"""
        try:
            reminders = self.db.get_pending_reminders()
            
            for reminder in reminders:
                try:
                    message = f"🔔 **Напоминание!**\n\n{reminder.reminder_text}"
                    self.bot.send_message(reminder.user_id, message, parse_mode='Markdown')
                    
                    # Отмечаем как выполненное
                    self.db.complete_reminder(reminder.id)
                    
                except Exception as e:
                    logger.error(f"Error sending reminder to {reminder.user_id}: {e}")
            
            if reminders:
                logger.info(f"✅ Отправлено {len(reminders)} напоминаний")
                
        except Exception as e:
            logger.error(f"Reminders check error: {e}")

def start_scheduler(bot, db: DatabaseManager, weather_service: WeatherService):
    """Запуск планировщика"""
    scheduler = NotificationScheduler(bot, db, weather_service)
    scheduler.start()
    return scheduler