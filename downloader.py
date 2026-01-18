import os
import re
import subprocess
import yt_dlp
from pytube import YouTube
from utils import clean_filename, format_file_size
import logging

logger = logging.getLogger(__name__)

class VideoDownloader:
    def __init__(self, max_size=50*1024*1024):
        self.max_size = max_size
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'cookiefile': None,  # Tidak menggunakan cookie
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            'format': 'best[filesize<50M]',  # Max 50MB untuk Telegram
        }
    
    def get_platform(self, url):
        """Deteksi platform dari URL"""
        patterns = {
            'youtube': r'(youtube\.com|youtu\.be)',
            'tiktok': r'tiktok\.com',
            'instagram': r'instagram\.com',
            'facebook': r'facebook\.com|fb\.watch',
            'twitter': r'twitter\.com|x\.com',
        }
        
        for platform, pattern in patterns.items():
            if re.search(pattern, url, re.IGNORECASE):
                return platform
        return 'unknown'
    
    def download_video(self, url, platform=None):
        """Download video dari berbagai platform"""
        try:
            if not platform:
                platform = self.get_platform(url)
            
            logger.info(f"Downloading from {platform}: {url}")
            
            # Gunakan yt-dlp untuk semua platform
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Cek ukuran file
                if info.get('filesize') and info['filesize'] > self.max_size:
                    return None, "File terlalu besar (>50MB)"
                
                # Download video
                ydl.download([url])
                
                # Cari file yang baru didownload
                filename = f"{clean_filename(info['title'])}.mp4"
                
                return filename, "Success"
                
        except Exception as e:
            logger.error(f"Download error: {str(e)}")
            return None, str(e)
    
    def get_video_info(self, url):
        """Get video info tanpa download"""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'platform': self.get_platform(url)
                }
        except Exception as e:
            logger.error(f"Info error: {str(e)}")
            return None