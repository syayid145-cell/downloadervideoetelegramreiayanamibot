import os
import re
import logging
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes, CallbackQueryHandler
)
from config import Config
from downloader import VideoDownloader
from utils import setup_logger, format_file_size, log_rei_activity

# Setup logger
logger = setup_logger()

class ReiAssistantBot:
    def __init__(self):
        self.config = Config()
        self.downloader = VideoDownloader(max_size=Config.MAX_FILE_SIZE)
        self.user_stats = {}
        self.active_downloads = {}
        
        # Log startup
        logger.info("=" * 50)
        logger.info("REI ASSISTANT VIDEO DOWNLOADER BOT STARTING...")
        logger.info(f"Bot Token: [REDACTED]")
        logger.info(f"Admin ID: {self.config.ADMIN_ID}")
        logger.info("=" * 50)
    
    async def notify_admin(self, context: ContextTypes.DEFAULT_TYPE, message: str, user_info: dict = None):
        """Kirim notifikasi real-time ke admin"""
        try:
            if user_info:
                user_details = (
                    f"👤 *User Details:*\n"
                    f"• ID: `{user_info.get('id', 'N/A')}`\n"
                    f"• Username: @{user_info.get('username', 'N/A')}\n"
                    f"• Name: {user_info.get('full_name', 'N/A')}\n"
                    f"• Language: {user_info.get('language_code', 'N/A')}\n"
                )
                message = f"{message}\n\n{user_details}"
            
            await context.bot.send_message(
                chat_id=self.config.ADMIN_ID,
                text=message,
                parse_mode='Markdown'
            )
            logger.info(f"Notification sent to admin: {message[:50]}...")
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk command /start"""
        user = update.effective_user
        
        # Log user activity
        log_rei_activity(
            user_id=user.id,
            username=user.username or "no_username",
            action="START_COMMAND",
            platform="Telegram"
        )
        
        # Update user stats
        if user.id not in self.user_stats:
            self.user_stats[user.id] = {
                'username': user.username,
                'full_name': user.full_name,
                'downloads': 0,
                'first_seen': datetime.now(),
                'last_seen': datetime.now()
            }
        else:
            self.user_stats[user.id]['last_seen'] = datetime.now()
        
        # Send welcome message
        welcome_text = Config.WELCOME_MESSAGE
        
        # Tambahkan tombol quick start
        keyboard = [
            [InlineKeyboardButton("📥 Download Video", url="https://t.me/share/url?url=https://youtube.com")],
            [InlineKeyboardButton("ℹ️ Cara Pakai", callback_data="help_callback")],
            [InlineKeyboardButton("⭐ Rate Bot", url="https://t.me/bots")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        # Kirim notifikasi ke admin
        user_info = {
            'id': user.id,
            'username': user.username,
            'full_name': user.full_name,
            'language_code': user.language_code
        }
        
        notification_msg = (
            "🚀 *NEW USER STARTED BOT*\n"
            f"*Rei Assistant* mendapatkan pengguna baru!"
        )
        
        await self.notify_admin(context, notification_msg, user_info)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk command /help"""
        help_text = """
        📖 *REI ASSISTANT - Bantuan Penggunaan*
        
        *🤖 Tentang Rei Assistant:*
        Bot downloader video canggih dengan support multi-platform
        
        *⚡ Cara Menggunakan:*
        1. Kirim link video (YouTube, TikTok, Instagram, dll)
        2. Tunggu proses download
        3. Video akan dikirim otomatis
        
        *🌐 Platform yang Didukung:*
        • YouTube & YouTube Shorts
        • TikTok
        • Instagram Reels & IGTV
        • Facebook & Facebook Watch
        • Twitter Video
        
        *⚙️ Spesifikasi:*
        • Max file size: 50MB (batasan Telegram)
        • Auto detect platform
        • High quality download
        
        *⚠️ Perhatian:*
        • Jangan spam download
        • Untuk penggunaan pribadi
        • Pastikan punya izin konten
        
        *📊 Stats Pribadi:*
        Kirim /stats untuk melihat statistik download Anda
        
        *👨‍💻 Developer:* @your_username
        *🔧 Version:* 2.0.0
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Command untuk melihat statistics"""
        user = update.effective_user
        
        if user.id == int(self.config.ADMIN_ID):
            # Admin stats
            total_users = len(self.user_stats)
            total_downloads = sum(stats.get('downloads', 0) for stats in self.user_stats.values())
            active_today = len([u for u in self.user_stats.values() 
                               if (datetime.now() - u.get('last_seen', datetime.now())).days < 1])
            
            # Top users
            top_users = sorted(self.user_stats.items(), 
                              key=lambda x: x[1].get('downloads', 0), 
                              reverse=True)[:5]
            
            top_users_text = "\n".join([
                f"{i+1}. {data.get('username', 'N/A')}: {data.get('downloads', 0)} downloads"
                for i, (uid, data) in enumerate(top_users)
            ])
            
            stats_text = f"""
            📊 *REI ASSISTANT - Admin Statistics*
            
            👥 *Users:*
            • Total: {total_users}
            • Active Today: {active_today}
            • New Today: {len([u for u in self.user_stats.values() 
                              if (datetime.now() - u.get('first_seen', datetime.now())).days < 1])}
            
            📥 *Downloads:*
            • Total: {total_downloads}
            • Avg per User: {total_downloads/max(total_users, 1):.1f}
            
            🏆 *Top 5 Users:*
            {top_users_text}
            
            ⏰ *Last Updated:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            await update.message.reply_text(stats_text, parse_mode='Markdown')
        else:
            # User stats personal
            user_data = self.user_stats.get(user.id, {})
            downloads = user_data.get('downloads', 0)
            first_seen = user_data.get('first_seen', datetime.now())
            days_used = (datetime.now() - first_seen).days
            
            user_stats_text = f"""
            📊 *Statistik Anda*
            
            👤 *Info:*
            • Username: @{user.username or 'N/A'}
            • User ID: `{user.id}`
            
            📥 *Download Stats:*
            • Total Downloads: {downloads}
            • Pertama Bergabung: {first_seen.strftime('%Y-%m-%d')}
            • Hari Penggunaan: {days_used} hari
            
            🏆 *Ranking:* {self.get_user_rank(user.id)}
            
            *Terima kasih telah menggunakan Rei Assistant!* 🤖
            """
            
            await update.message.reply_text(user_stats_text, parse_mode='Markdown')
    
    def get_user_rank(self, user_id):
        """Get user ranking based on downloads"""
        if user_id not in self.user_stats:
            return "Belum ada aktivitas"
        
        user_downloads = self.user_stats[user_id].get('downloads', 0)
        all_users = [(uid, data.get('downloads', 0)) 
                     for uid, data in self.user_stats.items()]
        
        sorted_users = sorted(all_users, key=lambda x: x[1], reverse=True)
        
        for rank, (uid, downloads) in enumerate(sorted_users, 1):
            if uid == user_id:
                total_users = len(sorted_users)
                percentile = (rank / total_users) * 100 if total_users > 0 else 0
                
                if percentile <= 10:
                    return f"🏅 Top {rank}/{total_users} (Elite User)"
                elif percentile <= 30:
                    return f"🥈 Top {rank}/{total_users} (Power User)"
                elif percentile <= 60:
                    return f"🥉 Top {rank}/{total_users} (Active User)"
                else:
                    return f"📊 #{rank}/{total_users} (Regular User)"
        
        return "Unranked"
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk pesan berisi link"""
        user = update.effective_user
        message_text = update.message.text
        
        # Log activity
        log_rei_activity(
            user_id=user.id,
            username=user.username or "no_username",
            action="SEND_LINK",
            platform="Telegram",
            details=f"Link: {message_text[:50]}..."
        )
        
        # Update user stats
        if user.id not in self.user_stats:
            self.user_stats[user.id] = {
                'username': user.username,
                'full_name': user.full_name,
                'downloads': 0,
                'first_seen': datetime.now(),
                'last_seen': datetime.now()
            }
        else:
            self.user_stats[user.id]['last_seen'] = datetime.now()
        
        # Cek apakah pesan berisi URL
        url_patterns = [
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            r'www\.[^\s]+',
            r'[^\s]+\.[a-zA-Z]{2,}[^\s]*'
        ]
        
        is_url = any(re.search(pattern, message_text) for pattern in url_patterns)
        
        if not is_url:
            await update.message.reply_text(
                "❌ *Format tidak valid!*\n\n"
                "Silakan kirim link video yang valid dari:\n"
                "• YouTube\n• TikTok\n• Instagram\n• Facebook\n• Twitter\n\n"
                "Contoh: `https://youtube.com/watch?v=...`",
                parse_mode='Markdown'
            )
            return
        
        # Kirim notifikasi ke admin tentang download attempt
        user_info = {
            'id': user.id,
            'username': user.username,
            'full_name': user.full_name,
            'download_count': self.user_stats[user.id].get('downloads', 0)
        }
        
        download_notification = (
            "📥 *DOWNLOAD ATTEMPT DETECTED*\n"
            f"*User:* @{user.username or 'no_username'}\n"
            f"*Link:* `{message_text[:30]}...`\n"
            f"*Previous Downloads:* {user_info['download_count']}"
        )
        
        await self.notify_admin(context, download_notification, user_info)
        
        # Kirim pesan sedang memproses
        processing_msg = await update.message.reply_text(
            "⏳ *Rei Assistant sedang memproses...*\n"
            "🔍 Mendeteksi platform video...",
            parse_mode='Markdown'
        )
        
        try:
            # Get video info
            video_info = self.downloader.get_video_info(message_text)
            
            if not video_info:
                await processing_msg.edit_text(
                    "❌ *Tidak bisa mendapatkan info video!*\n"
                    "Pastikan link valid dan video tersedia."
                )
                return
            
            platform = video_info.get('platform', 'unknown').title()
            
            # Update processing message
            await processing_msg.edit_text(
                f"✅ *Platform Terdeteksi:* {platform}\n"
                f"📹 *Judul:* {video_info['title'][:60]}...\n"
                f"⏱️ *Durasi:* {video_info.get('duration', 0)} detik\n"
                f"⬇️ *Mendownload video...*"
            )
            
            # Kirim notifikasi platform detection ke admin
            platform_notification = (
                f"🌐 *PLATFORM DETECTED*\n"
                f"*Platform:* {platform}\n"
                f"*User:* @{user.username or 'no_username'}\n"
                f"*Video:* {video_info['title'][:50]}..."
            )
            await self.notify_admin(context, platform_notification, user_info)
            
            # Download video
            filename, status = self.downloader.download_video(message_text)
            
            if not filename:
                error_msg = f"❌ *Download Gagal!*\n\nError: {status}"
                await processing_msg.edit_text(error_msg)
                
                # Kirim notifikasi error ke admin
                error_notification = (
                    f"❌ *DOWNLOAD FAILED*\n"
                    f"*User:* @{user.username or 'no_username'}\n"
                    f"*Platform:* {platform}\n"
                    f"*Error:* {status}\n"
                    f"*Link:* `{message_text[:30]}...`"
                )
                await self.notify_admin(context, error_notification, user_info)
                return
            
            # Cek jika file ada
            if not os.path.exists(filename):
                # Cari file dengan ekstensi video
                video_files = [f for f in os.listdir('.') 
                             if f.endswith(('.mp4', '.mkv', '.webm', '.mov', '.avi'))]
                if video_files:
                    filename = video_files[0]
                else:
                    await processing_msg.edit_text("❌ File video tidak ditemukan setelah download!")
                    return
            
            # Get file size
            file_size = os.path.getsize(filename)
            
            # Update processing message
            await processing_msg.edit_text(
                f"✅ *Download Selesai!*\n"
                f"📁 *File Size:* {format_file_size(file_size)}\n"
                f"📤 *Mengupload ke Telegram...*"
            )
            
            # Kirim video
            with open(filename, 'rb') as video_file:
                sent_message = await update.message.reply_video(
                    video=video_file,
                    caption=(
                        f"✅ *REI ASSISTANT - DOWNLOAD SELESAI*\n\n"
                        f"📹 *{video_info['title']}*\n"
                        f"🌐 *Platform:* {platform}\n"
                        f"💾 *Size:* {format_file_size(file_size)}\n\n"
                        f"{Config.ADS_MESSAGE}"
                    ),
                    parse_mode='Markdown',
                    supports_streaming=True,
                    thumbnail=open('thumbnail.jpg', 'rb') if os.path.exists('thumbnail.jpg') else None
                )
            
            # Update stats
            self.user_stats[user.id]['downloads'] = self.user_stats[user.id].get('downloads', 0) + 1
            
            # Update processing message
            await processing_msg.delete()
            
            # Kirim notifikasi sukses ke admin dengan detail lengkap
            success_notification = (
                f"✅ *DOWNLOAD SUCCESS*\n"
                f"*User:* @{user.username or 'no_username'}\n"
                f"*Platform:* {platform}\n"
                f"*Video:* {video_info['title'][:50]}...\n"
                f"*Size:* {format_file_size(file_size)}\n"
                f"*Total User Downloads:* {self.user_stats[user.id]['downloads']}\n"
                f"*Link:* `{message_text[:30]}...`"
            )
            await self.notify_admin(context, success_notification, user_info)
            
            # Kirim follow-up message dengan tombol
            keyboard = [
                [
                    InlineKeyboardButton("📥 Download Lain", callback_data="download_another"),
                    InlineKeyboardButton("⭐ Rate Bot", url="https://t.me/bots")
                ],
                [
                    InlineKeyboardButton("👥 Join Channel", url="https://t.me/your_channel"),
                    InlineKeyboardButton("💬 Support", url="https://t.me/your_support")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "🎉 *Download Berhasil!*\n\n"
                "Ingin download video lain?\n"
                "Cukup kirim link baru!",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            # Cleanup file
            try:
                os.remove(filename)
            except Exception as e:
                logger.error(f"Failed to cleanup file: {e}")
            
        except Exception as e:
            logger.error(f"Error processing video: {str(e)}", exc_info=True)
            
            # Kirim error message
            error_text = (
                "❌ *Terjadi Error!*\n\n"
                "Rei Assistant mengalami masalah saat memproses video.\n"
                "Silakan coba lagi nanti atau gunakan link yang berbeda.\n\n"
                f"Error: `{str(e)[:100]}...`"
            )
            
            if 'processing_msg' in locals():
                await processing_msg.edit_text(error_text)
            else:
                await update.message.reply_text(error_text, parse_mode='Markdown')
            
            # Kirim notifikasi error ke admin
            error_notification = (
                f"🚨 *CRITICAL ERROR*\n"
                f"*User:* @{user.username or 'no_username'}\n"
                f"*Error:* ```{str(e)[:200]}```\n"
                f"*Link:* `{message_text[:30]}...`"
            )
            await self.notify_admin(context, error_notification, user_info)
    
    async def broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Command untuk broadcast message ke semua users (admin only)"""
        user = update.effective_user
        
        if str(user.id) != self.config.ADMIN_ID:
            await update.message.reply_text("❌ Command ini hanya untuk admin!")
            return
        
        # Get broadcast message from command arguments
        if not context.args:
            await update.message.reply_text(
                "Usage: /broadcast <message>\n"
                "Example: /broadcast Hello semua users!"
            )
            return
        
        broadcast_message = ' '.join(context.args)
        
        # Send confirmation
        confirm_keyboard = [
            [
                InlineKeyboardButton("✅ Ya, Broadcast", callback_data=f"confirm_broadcast_{hash(broadcast_message)}"),
                InlineKeyboardButton("❌ Batalkan", callback_data="cancel_broadcast")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(confirm_keyboard)
        
        await update.message.reply_text(
            f"📢 *Konfirmasi Broadcast*\n\n"
            f"Message: {broadcast_message}\n\n"
            f"*Akan dikirim ke:* {len(self.user_stats)} users\n"
            f"*Anda yakin?*",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "help_callback":
            await self.help_command(update, context)
        elif data == "download_another":
            await query.edit_message_text(
                "📥 *Download Video Lain*\n\n"
                "Silakan kirim link video baru yang ingin didownload!",
                parse_mode='Markdown'
            )
        elif data.startswith("confirm_broadcast_"):
            # Handle broadcast confirmation
            await query.edit_message_text("⏳ Broadcasting message...")
            success_count = 0
            fail_count = 0
            
            for user_id in self.user_stats.keys():
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"📢 *Broadcast dari Admin*\n\n{query.message.text.split('Message: ')[1].split('\\n\\n')[0]}",
                        parse_mode='Markdown'
                    )
                    success_count += 1
                    await asyncio.sleep(0.1)  # Rate limiting
                except Exception as e:
                    logger.error(f"Failed to send broadcast to {user_id}: {e}")
                    fail_count += 1
            
            await query.edit_message_text(
                f"✅ *Broadcast Selesai!*\n\n"
                f"✅ Berhasil: {success_count} users\n"
                f"❌ Gagal: {fail_count} users"
            )
        elif data == "cancel_broadcast":
            await query.edit_message_text("❌ Broadcast dibatalkan.")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Global error handler"""
        logger.error(f"Update {update} caused error {context.error}", exc_info=True)
        
        # Kirim notifikasi error ke admin
        error_notification = (
            f"🚨 *BOT ERROR*\n"
            f"*Error:* ```{str(context.error)[:300]}```\n"
            f"*Update:* `{str(update)[:100]}...`"
        )
        
        try:
            await self.notify_admin(context, error_notification)
        except:
            pass
        
        # Kirim pesan error ke user jika ada
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ *Terjadi kesalahan sistem!*\n"
                    "Silakan coba lagi nanti atau hubungi admin.",
                    parse_mode='Markdown'
                )
            except:
                pass
    
    def run(self):
        """Jalankan Rei Assistant Bot"""
        try:
            # Create application
            application = Application.builder().token(self.config.BOT_TOKEN).build()
            
            # Add handlers
            application.add_handler(CommandHandler("start", self.start))
            application.add_handler(CommandHandler("help", self.help_command))
            application.add_handler(CommandHandler("stats", self.stats_command))
            application.add_handler(CommandHandler("broadcast", self.broadcast_command))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            application.add_handler(CallbackQueryHandler(self.callback_handler))
            
            # Add error handler
            application.add_error_handler(self.error_handler)
            
            # Jalankan bot
            logger.info("🤖 Rei Assistant Bot starting...")
            
            # Kirim startup notification ke admin
            startup_message = (
                "🚀 *REI ASSISTANT STARTUP*\n"
                "Bot telah berhasil dijalankan!\n"
                "*Timestamp:* " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            
            # Note: We can't send notification here because we don't have context yet
            # This will be sent after bot starts
            
            application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
                close_loop=False
            )
            
        except Exception as e:
            logger.critical(f"Failed to start Rei Assistant Bot: {e}", exc_info=True)
            raise

if __name__ == "__main__":
    bot = ReiAssistantBot()
    bot.run()