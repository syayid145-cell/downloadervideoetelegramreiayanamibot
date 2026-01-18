import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot Token dari @BotFather
    BOT_TOKEN = os.getenv("BOT_TOKEN", "7804332417:AAE489rz4S274OauJT3NEbFLddEZx6HV3Zc")
    
    # ID Admin untuk notifikasi error
    ADMIN_ID = os.getenv("ADMIN_ID", "7291292815")
    
    # Config untuk logging
    LOG_LEVEL = "INFO"
    
    # Max file size untuk Telegram (50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024
    
    # Timeout download
    DOWNLOAD_TIMEOUT = 300
    
    # Iklan (bisa diubah)
    ADS_MESSAGE = """
    ⚡ *Download Selesai!*
    
    🔥 *Support Rei Assistant:*
    - Follow: @your_channel
    - Join: @your_channel
    
    ⚠️ Jangan lupa rate bot ini 5⭐
    """
    
    # Pesan welcome
    WELCOME_MESSAGE = """
    🤖 *REI ASSISTANT - VIDEO DOWNLOADER*
    
    👋 Halo! Saya adalah Rei Assistant, bot downloader video multi-platform!
    
    📥 *Fitur Unggulan:*
    • YouTube & YouTube Shorts
    • TikTok
    • Instagram Reels
    • Facebook
    • Twitter
    
    ⚡ *Cara Pakai:*
    Cukup kirim link video!
    
    ⚠️ *Note:* 
    • Gratis 100%
    • Max size: 50MB
    • No watermark (jika tersedia)
    
    🎬 *Powered by:* Rei Assistant Technology
    """