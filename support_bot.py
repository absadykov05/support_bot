import logging
from datetime import datetime, timedelta, time
import pytz
from telegram import Bot
from telegram.ext import Updater, CommandHandler, CallbackContext
import threading
import time as time_module

TELEGRAM_TOKEN = '7808119794:AAHsdjR7IECQlR8zFHFsRTLIt5yAshYINDA'
USER_USERNAME = '@absadykov4'
USER_ID = None   

TIMEZONE = pytz.timezone("Asia/Almaty")  

SCHEDULE = {
    "monday": [
        (time(10, 0), time(10, 50), "Database Management Systems", "1.1.241"),
        (time(11, 0), time(12, 50), "Algorithms and Data Structures", "1.1.358"),
    ],
    "wednesday": [
        (time(10, 0), time(10, 50), "Algorithms and Data Structures", "1.1.358"),
        (time(11, 0), time(11, 50), "Psychology", "1.1.226"),
        (time(12, 0), time(13, 50), "Discrete Maths", "1.1.251"),
    ],
    "friday": [
        (time(8, 0), time(8, 50), "Political Science", "1.1.254"),
        (time(9, 0), time(9, 50), "Database Management Systems", "1.1.241"),
        (time(10, 0), time(11, 50), "Discrete Maths", "1.2.224"),
        (time(12, 0), time(13, 50), "Physical Education", "спортзал"),
    ],
}

JUDO_DAYS = ["tuesday", "thursday", "saturday"]
JUDO_REMINDER_TIME = time(17, 0)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_msg(bot: Bot, chat_id, text):
    try:
        bot.send_message(chat_id=chat_id, text=text)
    except Exception as e:
        logger.error(f"Send error: {e}")

def schedule_loop(bot: Bot, chat_id):
    while True:
        now = datetime.now(TIMEZONE)
        weekday = now.strftime('%A').lower()
        # Пары
        if weekday in SCHEDULE:
            for lesson in SCHEDULE[weekday]:
                lesson_start = datetime.combine(now.date(), lesson[0]).replace(tzinfo=TIMEZONE)
                reminder_time = lesson_start - timedelta(minutes=10)
                if now.hour == reminder_time.hour and now.minute == reminder_time.minute:
                    send_msg(bot, chat_id,
                        f"Через 10 минут пара: {lesson[2]} в кабинете {lesson[3]} ({lesson[0].strftime('%H:%M')}–{lesson[1].strftime('%H:%M')})"
                    )
        # Дзюдо
        if weekday in JUDO_DAYS:
            reminder = datetime.combine(now.date(), JUDO_REMINDER_TIME).replace(tzinfo=TIMEZONE)
            if now.hour == reminder.hour and now.minute == reminder.minute:
                send_msg(bot, chat_id,
                    "Серик, пора читать екінті намаз и собираться на тренировку по дзюдо! Пешком идти 35 минут, чтобы прийти к 18:00."
                )
        time_module.sleep(60)

def start(update, context):
    user = update.message.from_user
    update.message.reply_text(f"Я вижу тебя! Username: @{user.username}, ID: {user.id}")


def main():
    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    global USER_ID
    def wait_for_userid():
        while USER_ID is None:
            time_module.sleep(5)
        threading.Thread(target=schedule_loop, args=(updater.bot, USER_ID), daemon=True).start()
    threading.Thread(target=wait_for_userid, daemon=True).start()
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
