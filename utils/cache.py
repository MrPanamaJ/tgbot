# utils/cache.py
from functools import wraps
from typing import Any, Dict
import time

class SimpleCache:
    """Простой кэш для часто используемых данных"""
    
    def __init__(self, ttl: int = 300):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Any:
        if key in self._cache:
            data = self._cache[key]
            if time.time() - data['timestamp'] < self.ttl:
                return data['value']
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any):
        self._cache[key] = {
            'value': value,
            'timestamp': time.time()
        }

def cached(ttl: int = 300):
    """Декоратор для кэширования результатов функций"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            return result
        return wrapper
    return decorator

# Глобальный экземпляр кэша
cache = SimpleCache()