import logging

logger = logging.getLogger(__name__)

class VoiceRecognizer:
    """Заглушка распознавателя речи"""
    
    def __init__(self):
        logger.warning("⚠️ Используется заглушка VoiceRecognizer")
    
    def recognize_speech(self, audio_path: str, language: str = 'ru-RU') -> str:
        """Заглушка для распознавания речи"""
        return (
            "🎤 Голосовое сообщение получено!\n\n"
            "💡 *Текст распознавания:*\n"
            "Здесь был бы распознанный текст\n\n"
            "⚠️ *Для полного распознавания установите:*\n"
            "• `pydub`\n"
            "• `speechrecognition`\n"
            "• `PyAudio`\n\n"
            "💡 *Команда для установки:*\n"
            "`pip install pydub speechrecognition pyaudio`"
        )
    
    def recognize_from_url(self, audio_url: str, language: str = 'ru-RU') -> str:
        return self.recognize_speech("")
    
    def get_supported_formats(self) -> list:
        return ['.oga', '.ogg', '.wav', '.mp3', '.m4a', '.flac']
    
    def set_language(self, language: str):
        pass
    
    def get_audio_duration(self, audio_path: str):
        return None