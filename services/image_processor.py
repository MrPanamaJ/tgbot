import logging
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from pathlib import Path
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Процессор для обработки изображений"""
    
    def __init__(self):
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
    
    def process_image(self, image_path: str) -> Optional[str]:
        """Основная обработка изображения"""
        try:
            # Проверка существования файла
            if not Path(image_path).exists():
                logger.error(f"Image file not found: {image_path}")
                return None
            
            # Открытие изображения
            with Image.open(image_path) as img:
                # Конвертация в RGB если нужно
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Применение улучшений
                enhanced_img = self._apply_enhancements(img)
                
                # Сохранение обработанного изображения
                output_path = self._get_output_path(image_path)
                enhanced_img.save(output_path, 'JPEG', quality=85)
                
                return output_path
                
        except Exception as e:
            logger.error(f"Image processing error: {e}")
            return None
    
    def _apply_enhancements(self, image: Image.Image) -> Image.Image:
        """Применение улучшений к изображению"""
        # 1. Увеличение резкости
        image = image.filter(ImageFilter.SHARPEN)
        
        # 2. Коррекция контраста
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)  # Увеличение контраста на 20%
        
        # 3. Коррекция яркости
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.1)  # Увеличение яркости на 10%
        
        # 4. Насыщенность цветов
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.15)  # Увеличение насыщенности на 15%
        
        # 5. Легкое размытие для уменьшения шума
        image = image.filter(ImageFilter.SMOOTH)
        
        return image
    
    def resize_image(self, image_path: str, max_size: tuple = (1024, 1024)) -> Optional[str]:
        """Изменение размера изображения"""
        try:
            with Image.open(image_path) as img:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                output_path = self._get_output_path(image_path, "_resized")
                img.save(output_path, 'JPEG', quality=85)
                
                return output_path
                
        except Exception as e:
            logger.error(f"Image resize error: {e}")
            return None
    
    def convert_to_grayscale(self, image_path: str) -> Optional[str]:
        """Конвертация в черно-белый формат"""
        try:
            with Image.open(image_path) as img:
                grayscale_img = ImageOps.grayscale(img)
                
                output_path = self._get_output_path(image_path, "_bw")
                grayscale_img.save(output_path, 'JPEG', quality=85)
                
                return output_path
                
        except Exception as e:
            logger.error(f"Grayscale conversion error: {e}")
            return None
    
    def add_watermark(self, image_path: str, watermark_text: str) -> Optional[str]:
        """Добавление водяного знака"""
        try:
            with Image.open(image_path) as img:
                from PIL import ImageDraw, ImageFont
                
                # Создание объекта для рисования
                draw = ImageDraw.Draw(img)
                
                # Попытка использования шрифта (запасной вариант если шрифт не найден)
                try:
                    font = ImageFont.truetype("arial.ttf", 36)
                except:
                    font = ImageFont.load_default()
                
                # Позиционирование водяного знака
                bbox = draw.textbbox((0, 0), watermark_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                width, height = img.size
                x = width - text_width - 10
                y = height - text_height - 10
                
                # Рисование текста с тенью
                shadow_color = (0, 0, 0, 128)
                text_color = (255, 255, 255, 128)
                
                # Тень
                draw.text((x+1, y+1), watermark_text, font=font, fill=shadow_color)
                # Основной текст
                draw.text((x, y), watermark_text, font=font, fill=text_color)
                
                output_path = self._get_output_path(image_path, "_watermark")
                img.save(output_path, 'JPEG', quality=85)
                
                return output_path
                
        except Exception as e:
            logger.error(f"Watermark error: {e}")
            return None
    
    def _get_output_path(self, original_path: str, suffix: str = "_processed") -> str:
        """Генерация пути для выходного файла"""
        original_path = Path(original_path)
        temp_dir = Path(tempfile.gettempdir()) / "telegram_bot"
        temp_dir.mkdir(exist_ok=True)
        
        output_filename = f"{original_path.stem}{suffix}.jpg"
        return str(temp_dir / output_filename)
    
    def get_image_info(self, image_path: str) -> dict:
        """Получение информации об изображении"""
        try:
            with Image.open(image_path) as img:
                return {
                    'format': img.format,
                    'size': img.size,
                    'mode': img.mode,
                    'width': img.width,
                    'height': img.height
                }
        except Exception as e:
            logger.error(f"Image info error: {e}")
            return {}