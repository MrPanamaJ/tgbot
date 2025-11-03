import logging

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Заглушка обработчика изображений"""
    
    def __init__(self):
        logger.warning("⚠️ Используется заглушка ImageProcessor")
    
    def process_image(self, image_path: str) -> str:
        """Заглушка для обработки изображения"""
        return image_path  # Возвращаем исходный путь без изменений