from flask import Flask, request
import telebot
from config import Config
import os

# Inisialisasi Flask app
app = Flask(__name__)

# Inisialisasi bot
bot = telebot.TeleBot(Config.BOT_TOKEN)

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/' + Config.BOT_TOKEN, methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return 'OK', 200

if __name__ == '__main__':
    # Untuk lokal testing
    bot.remove_webhook()
    bot.polling()