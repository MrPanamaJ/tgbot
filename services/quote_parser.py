import requests
from bs4 import BeautifulSoup
import random
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class QuoteParser:
    """Парсер цитат с сайта citaty.info"""
    
    def __init__(self):
        self.base_url = "https://citaty.info"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_random_quote(self) -> Dict[str, str]:
        """Получение случайной цитаты"""
        try:
            # Получаем страницу со списком цитат
            url = f"{self.base_url}/selection/citaty-so-smyslom-podborka-mudryh-citat"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Ищем цитаты
            quotes = self._parse_quotes(soup)
            
            if not quotes:
                return self._get_fallback_quote()
            
            # Выбираем случайную цитату
            quote = random.choice(quotes)
            return quote
            
        except Exception as e:
            logger.error(f"Error parsing quote: {e}")
            return self._get_fallback_quote()
    
    def _parse_quotes(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Парсинг цитат со страницы"""
        quotes = []
        
        try:
            # Ищем блоки с цитатами (может потребоваться адаптация под структуру сайта)
            quote_blocks = soup.find_all('div', class_='node__content')  # Возможно, нужно уточнить класс
            
            for block in quote_blocks:
                # Ищем текст цитаты
                text_elem = block.find('div', class_='field-type-text-with-summary') or block.find('p')
                if not text_elem:
                    continue
                
                quote_text = text_elem.get_text(strip=True)
                
                # Ищем автора
                author_elem = block.find('div', class_='field-type-taxonomy-term-reference') or block.find('cite')
                author = author_elem.get_text(strip=True) if author_elem else "Неизвестный автор"
                
                if quote_text and len(quote_text) > 10:  # Минимальная длина цитаты
                    quotes.append({
                        'text': quote_text,
                        'author': author,
                        'full': f"«{quote_text}»\n\n— {author}"
                    })
            
            # Если не нашли по первому селектору, пробуем другой
            if not quotes:
                quote_elems = soup.find_all('blockquote') or soup.find_all('q')
                for elem in quote_elems:
                    quote_text = elem.get_text(strip=True)
                    if quote_text and len(quote_text) > 10:
                        # Пытаемся найти автора рядом
                        author_elem = elem.find_next('cite') or elem.find_next('footer')
                        author = author_elem.get_text(strip=True) if author_elem else "Неизвестный автор"
                        
                        quotes.append({
                            'text': quote_text,
                            'author': author,
                            'full': f"«{quote_text}»\n\n— {author}"
                        })
            
        except Exception as e:
            logger.error(f"Error in quote parsing: {e}")
        
        return quotes
    
    def _get_fallback_quote(self) -> Dict[str, str]:
        """Резервные цитаты на случай ошибки парсинга"""
        fallback_quotes = [
            {
                'text': 'Мы сами должны стать теми переменами, которые хотим увидеть в мире.',
                'author': 'Махатма Ганди',
                'full': '«Мы сами должны стать теми переменами, которые хотим увидеть в мире.»\n\n— Махатма Ганди'
            },
            {
                'text': 'Жизнь — это то, что происходит с тобой, пока ты строишь другие планы.',
                'author': 'Джон Леннон',
                'full': '«Жизнь — это то, что происходит с тобой, пока ты строишь другие планы.»\n\n— Джон Леннон'
            },
            {
                'text': 'Единственный способ делать великие дела — это любить то, что ты делаешь.',
                'author': 'Стив Джобс',
                'full': '«Единственный способ делать великие дела — это любить то, что ты делаешь.»\n\n— Стив Джобс'
            },
            {
                'text': 'Успех — это способность идти от неудачи к неудаче, не теряя энтузиазма.',
                'author': 'Уинстон Черчилль',
                'full': '«Успех — это способность идти от неудачи к неудаче, не теряя энтузиазма.»\n\n— Уинстон Черчилль'
            },
            {
                'text': 'Будьте изменением, которое вы хотите видеть в мире.',
                'author': 'Махатма Ганди', 
                'full': '«Будьте изменением, которое вы хотите видеть в мире.»\n\n— Махатма Ганди'
            }
        ]
        
        return random.choice(fallback_quotes)