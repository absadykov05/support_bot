import logging
from datetime import datetime, timedelta, time
import pytz
import re
import threading
import time as time_module
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# ========== НАСТРОЙКИ ==========
TELEGRAM_TOKEN = 'ТВОЙ_НОВЫЙ_ТОКЕН_ЗДЕСЬ'   # <-- Вставь новый актуальный токен!
USER_USERNAME = '@absadykov4'
USER_ID = None

TIMEZONE = pytz.timezone("Asia/Almaty")  # Твой часовой пояс

# ========== ДАННЫЕ В ПАМЯТИ ==========
events = []
shopping_list = []
todo_list = []
birthdays = []

# ========== РАСПИСАНИЕ ==========
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

# Дзюдо: вт, чт, сб, напоминание в 17:00
JUDO_DAYS = ["tuesday", "thursday", "saturday"]
JUDO_REMINDER_TIME = time(17, 0)

# Время напоминания лечь спать
SLEEP_REMINDER_HOUR = 23
SLEEP_REMINDER_MIN = 0

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_msg(bot: Bot, chat_id, text):
    try:
        bot.send_message(chat_id=chat_id, text=text)
    except Exception as e:
        logger.error(f"Send error: {e}")

# ========== EVENTS ==========
def parse_event(text):
    match = re.match(r"ивент (\d{2})\.(\d{2}) (\d{2}):(\d{2}) (.+)", text, re.IGNORECASE)
    if not match:
        return None
    day, month, hour, minute, desc = match.groups()
    now = datetime.now(TIMEZONE)
    year = now.year
    try:
        event_time = datetime(year, int(month), int(day), int(hour), int(minute), tzinfo=TIMEZONE)
        if event_time < now:
            event_time = datetime(year+1, int(month), int(day), int(hour), int(minute), tzinfo=TIMEZONE)
        return event_time, desc
    except:
        return None

def check_events(bot, chat_id):
    now = datetime.now(TIMEZONE)
    for event in events[:]:
        event_time, desc = event
        reminder_time = event_time - timedelta(minutes=10)
        if reminder_time <= now < reminder_time + timedelta(minutes=1):
            send_msg(bot, chat_id, f"Через 10 минут: {desc} ({event_time.strftime('%d.%m %H:%M')})")
            events.remove(event)

# ========== СПИСОК ПОКУПОК ==========
def add_shopping_item(text):
    item = text.replace("добавь в список", "").strip()
    if item:
        shopping_list.append(item)
        return f"Добавил в покупки: {item}"
    return "Что добавить в покупки?"

def get_shopping_list():
    if not shopping_list:
        return "Список покупок пуст."
    return "Список покупок:\n" + "\n".join(f"{i+1}. {item}" for i, item in enumerate(shopping_list))

def clear_shopping_list():
    shopping_list.clear()
    return "Список покупок очищен."

# ========== TO-DO LIST ==========
def add_todo(text):
    task = text.replace("дело", "").strip()
    if task:
        todo_list.append(task)
        return f"Дело добавлено: {task}"
    return "Что добавить в дела?"

def get_todos():
    if not todo_list:
        return "Дел пока нет."
    return "Твои дела:\n" + "\n".join(f"{i+1}. {task}" for i, task in enumerate(todo_list))

def clear_todos():
    todo_list.clear()
    return "Все дела очищены."

# ========== ДНИ РОЖДЕНИЯ ==========
def parse_birthday(text):
    match = re.match(r"деньр (\d{2})\.(\d{2}) (.+)", text, re.IGNORECASE)
    if not match:
        return None
    day, month, name = match.groups()
    return int(day), int(month), name.strip()

def check_birthdays(bot, chat_id):
    now = datetime.now(TIMEZONE)
    for bday in birthdays[:]:
        day, month, name = bday
        if now.day == day and now.month == month:
            send_msg(bot, chat_id, f"Сегодня день рождения у {name}! Не забудь поздравить 🎉")

# ========== РАСПИСАНИЕ ==========
def today_schedule():
    now = datetime.now(TIMEZONE)
    weekday = now.strftime('%A').lower()
    if weekday not in SCHEDULE:
        return "Сегодня пар нет!"
    lessons = SCHEDULE[weekday]
    text = f"Расписание на сегодня ({weekday.title()}):\n"
    for start, end, subject, room in lessons:
        text += f"{start.strftime('%H:%M')}–{end.strftime('%H:%M')} — {subject} ({room})\n"
    return text.strip()

# ========== ОБРАБОТКА СООБЩЕНИЙ ==========
def on_message(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    user = update.message.from_user
    chat_id = update.effective_chat.id

    # Если не определён USER_ID, просим написать /start
    global USER_ID
    if USER_ID is None:
        update.message.reply_text("⚠️ Напиши /start для активации напоминаний!")
        return

    if user.username and ("@" + user.username) == USER_USERNAME:
        if text.lower().startswith("добавь в список"):
            update.message.reply_text(add_shopping_item(text))
            return
        if text.lower() in ["список", "покупки"]:
            update.message.reply_text(get_shopping_list())
            return
        if text.lower() == "я в магазине":
            update.message.reply_text("В магазине купи всё из списка:\n" + get_shopping_list())
            return
        if text.lower() in ["очистить покупки", "очистить список"]:
            update.message.reply_text(clear_shopping_list())
            return

        if text.lower().startswith("дело"):
            update.message.reply_text(add_todo(text))
            return
        if text.lower() == "мои дела":
            update.message.reply_text(get_todos())
            return
        if text.lower() == "очистить дела":
            update.message.reply_text(clear_todos())
            return

        if text.lower().startswith("ивент"):
            result = parse_event(text)
            if result:
                event_time, desc = result
                events.append((event_time, desc))
                update.message.reply_text(f"Событие добавлено: {desc} ({event_time.strftime('%d.%m %H:%M')})")
            else:
                update.message.reply_text("Не понял формат. Пример: ивент 28.05 10:00 джим с Дидаром")
            return

        if text.lower().startswith("деньр"):
            result = parse_birthday(text)
            if result:
                birthdays.append(result)
                day, month, name = result
                update.message.reply_text(f"Добавлен день рождения: {name}, {day:02}.{month:02}")
            else:
                update.message.reply_text("Формат: деньр 11.06 Аружан")
            return

        if text.lower() in ["расписание", "schedule"]:
            update.message.reply_text(today_schedule())
            return

        update.message.reply_text("Я тебя понял! Напомни, если надо что-то добавить в список, дело, событие или расписание.")

    else:
        update.message.reply_text("Извини, этот бот только для хозяина :)")

# ========== КОМАНДЫ ==========
def start(update, context):
    user = update.message.from_user
    global USER_ID
    if user.username and ("@" + user.username) == USER_USERNAME:
        USER_ID = user.id
        update.message.reply_text("SupportBuddy готов напоминать тебе о событиях, списках, делах, расписании и сне!")
    else:
        update.message.reply_text("Извини, этот бот только для хозяина :)")

def schedule(update, context):
    update.message.reply_text(today_schedule())

# ========== НАПОМИНАНИЯ ==========
def schedule_loop(bot: Bot, chat_id):
    sleep_reminded = False
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

        # События, дни рождения
        check_events(bot, chat_id)
        check_birthdays(bot, chat_id)

        # Напоминание лечь спать
        if now.hour == SLEEP_REMINDER_HOUR and now.minute == SLEEP_REMINDER_MIN:
            if not sleep_reminded:
                send_msg(bot, chat_id, "Пора ложиться спать! Завтра продуктивный день.")
                sleep_reminded = True
        else:
            sleep_reminded = False  # Сброс после часа

        time_module.sleep(60)

# ========== MAIN ==========
def main():
    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('schedule', schedule))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, on_message))

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
