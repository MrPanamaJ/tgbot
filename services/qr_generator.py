import qrcode
from io import BytesIO
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class QRCodeService:
    """Сервис для генерации QR-кодов"""
    
    def __init__(self):
        self.version = 1
        self.box_size = 10
        self.border = 4
        self.error_correction = qrcode.constants.ERROR_CORRECT_L
    
    def generate_qr(self, data: str, **kwargs) -> Optional[BytesIO]:
        """Генерация QR-кода"""
        try:
            qr = qrcode.QRCode(
                version=kwargs.get('version', self.version),
                error_correction=kwargs.get('error_correction', self.error_correction),
                box_size=kwargs.get('box_size', self.box_size),
                border=kwargs.get('border', self.border)
            )
            
            qr.add_data(data)
            qr.make(fit=True)
            
            # Настройки цвета
            fill_color = kwargs.get('fill_color', 'black')
            back_color = kwargs.get('back_color', 'white')
            
            img = qr.make_image(fill_color=fill_color, back_color=back_color)
            
            bio = BytesIO()
            img.save(bio, 'PNG')
            bio.seek(0)
            
            return bio
            
        except Exception as e:
            logger.error(f"QR generation error: {e}")
            return None