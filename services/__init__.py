# Инициализация пакета services
from .weather_api import WeatherService
from .qr_generator import QRCodeService
from .scheduler import start_scheduler
from .image_processor import ImageProcessor
from .voice_recognizer import VoiceRecognizer

__all__ = [
    'WeatherService',
    'QRCodeService', 
    'start_scheduler',
    'ImageProcessor',
    'VoiceRecognizer'
]