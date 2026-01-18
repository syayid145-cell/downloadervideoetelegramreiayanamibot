import logging
import os
import sys
from datetime import datetime

class CustomFormatter(logging.Formatter):
    """Custom formatter untuk menyembunyikan informasi sensitif"""
    
    def format(self, record):
        # Sembunyikan API keys dari log
        msg = super().format(record)
        
        # Filter kata-kata sensitif
        sensitive_keywords = [
            'bot_token', 'api_key', 'token', 'secret', 
            'password', 'BOT_TOKEN', 'API_KEY'
        ]
        
        for keyword in sensitive_keywords:
            if keyword in msg.lower():
                msg = msg.replace(keyword, '[REDACTED]')
        
        return msg

def setup_logger():
    """Setup logger dengan custom formatter"""
    
    # Buat logs directory jika belum ada
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Setup logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Handler untuk file
    file_handler = logging.FileHandler(
        f'logs/bot_{datetime.now().strftime("%Y%m%d")}.log',
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    
    # Handler untuk console (tanpa info sensitif)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Custom formatter
    formatter = CustomFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def clean_filename(filename):
    """Membersihkan nama file dari karakter tidak valid"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename[:100]  # Batasi panjang nama file

def format_file_size(size_bytes):
    """Format ukuran file menjadi readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def log_rei_activity(user_id, username, action, platform=None, details=""):
    """Log khusus untuk Rei Assistant dengan format yang rapi"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    log_entry = (
        f"[REI_ASSISTANT] [{timestamp}] "
        f"USER:{user_id} (@{username}) | "
        f"ACTION:{action} | "
        f"PLATFORM:{platform or 'N/A'} | "
        f"DETAILS:{details[:100]}"
    )
    
    # Log ke file
    with open(f'logs/rei_activity_{datetime.now().strftime("%Y%m%d")}.log', 'a', encoding='utf-8') as f:
        f.write(log_entry + "\n")
    
    # Juga log ke console dengan level INFO
    logger.info(log_entry)