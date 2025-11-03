import os
import tempfile
import logging
from pathlib import Path
from typing import Optional
import speech_recognition as sr
from pydub import AudioSegment
import requests

logger = logging.getLogger(__name__)

class VoiceRecognizer:
    """Распознаватель речи из аудио сообщений"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.supported_formats = ['.oga', '.ogg', '.wav', '.mp3', '.m4a', '.flac']
    
    def recognize_speech(self, audio_path: str, language: str = 'ru-RU') -> str:
        """Распознавание речи из аудио файла"""
        try:
            # Конвертация в WAV если нужно
            wav_path = self._convert_to_wav(audio_path)
            if not wav_path:
                return "Не удалось конвертировать аудио файл"
            
            # Распознавание речи
            text = self._recognize_from_wav(wav_path, language)
            
            # Очистка временных файлов
            if wav_path != audio_path:  # Удаляем только если создавали временный файл
                Path(wav_path).unlink(missing_ok=True)
            
            return text
            
        except Exception as e:
            logger.error(f"Speech recognition error: {e}")
            return "Ошибка распознавания речи"
    
    def _convert_to_wav(self, audio_path: str) -> Optional[str]:
        """Конвертация аудио файла в WAV формат"""
        try:
            audio_path = Path(audio_path)
            
            # Если файл уже в WAV формате, возвращаем исходный путь
            if audio_path.suffix.lower() == '.wav':
                return str(audio_path)
            
            # Проверка поддержки формата
            if audio_path.suffix.lower() not in [fmt.lower() for fmt in self.supported_formats]:
                logger.error(f"Unsupported audio format: {audio_path.suffix}")
                return None
            
            # Создание временного файла для WAV
            temp_dir = Path(tempfile.gettempdir()) / "telegram_bot"
            temp_dir.mkdir(exist_ok=True)
            wav_path = temp_dir / f"{audio_path.stem}.wav"
            
            # Конвертация с помощью pydub
            audio = AudioSegment.from_file(str(audio_path))
            audio = audio.set_frame_rate(16000)  # Стандартная частота для распознавания
            audio = audio.set_channels(1)  # Моно для лучшего распознавания
            
            # Экспорт в WAV
            audio.export(str(wav_path), format="wav")
            
            return str(wav_path)
            
        except Exception as e:
            logger.error(f"Audio conversion error: {e}")
            return None
    
    def _recognize_from_wav(self, wav_path: str, language: str = 'ru-RU') -> str:
        """Распознавание речи из WAV файла"""
        try:
            with sr.AudioFile(wav_path) as source:
                # Настройка для шумной среды
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Запись аудио данных
                audio_data = self.recognizer.record(source)
                
                # Попытка распознавания через Google Speech Recognition
                text = self.recognizer.recognize_google(
                    audio_data,
                    language=language,
                    show_all=False
                )
                
                return text
                
        except sr.UnknownValueError:
            return "Не удалось распознать речь. Возможно, речь нечеткая или слишком тихая."
        except sr.RequestError as e:
            logger.error(f"Speech recognition API error: {e}")
            return "Ошибка сервиса распознавания речи. Попробуйте позже."
        except Exception as e:
            logger.error(f"Recognition error: {e}")
            return "Ошибка при обработке аудио файла."
    
    def recognize_from_url(self, audio_url: str, language: str = 'ru-RU') -> str:
        """Распознавание речи из URL"""
        try:
            # Скачивание аудио файла
            response = requests.get(audio_url, timeout=30)
            response.raise_for_status()
            
            # Сохранение во временный файл
            temp_dir = Path(tempfile.gettempdir()) / "telegram_bot"
            temp_dir.mkdir(exist_ok=True)
            temp_file = temp_dir / "downloaded_audio"
            
            with open(temp_file, 'wb') as f:
                f.write(response.content)
            
            # Распознавание речи
            text = self.recognize_speech(str(temp_file), language)
            
            # Очистка
            temp_file.unlink(missing_ok=True)
            
            return text
            
        except Exception as e:
            logger.error(f"URL recognition error: {e}")
            return "Ошибка при загрузке аудио с URL"
    
    def get_supported_formats(self) -> list:
        """Получение списка поддерживаемых форматов"""
        return self.supported_formats
    
    def set_language(self, language: str):
        """Установка языка распознавания"""
        self.language = language
    
    def get_audio_duration(self, audio_path: str) -> Optional[float]:
        """Получение длительности аудио файла"""
        try:
            audio = AudioSegment.from_file(audio_path)
            return len(audio) / 1000.0  # Конвертация в секунды
        except Exception as e:
            logger.error(f"Audio duration error: {e}")
            return None