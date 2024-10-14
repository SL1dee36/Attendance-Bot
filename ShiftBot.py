import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import datetime
import random

TOKEN = "YOUR-TOKEN"  # **Replace with your actual bot token**

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# Global variables
people = []
last_assigned = {}
zones = ["Переговорка", "Коридор, умывальник", "Зона отдыха, сан. Узлы"]
schedule_days = 7  # Default schedule days


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Здравствуйте! Пожалуйста, отправьте мне файл со списком людей в формате txt.")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global people
    try:
        file = await context.bot.get_file(update.message.document.file_id)
        file_content = (await file.download_as_bytearray()).decode("utf-8")
        people = [line.strip() for line in file_content.splitlines() if line.strip()]

        if people:
            await update.message.reply_text(
                "Файл получен и обработан. Выберите количество дней для составления расписания:",
                reply_markup=ReplyKeyboardMarkup([
                    ["3 дня", "7 дней", "9 дней"],
                    ["14 дней", "21 день", "30 дней"]
                ], resize_keyboard=True, one_time_keyboard=True)
            )
        else:
            await update.message.reply_text("Файл пустой. Пожалуйста, отправьте файл со списком людей.")

    except Exception as e:
        await update.message.reply_text(f"Ошибка при обработке файла: {e}")


async def handle_schedule_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global schedule_days
    user_choice = update.message.text

    if "дня" in user_choice or "день" in user_choice or "дней" in user_choice:
        days_str = user_choice.split()[0]
        try:
            schedule_days = int(days_str)
            await update.message.reply_text(
                f"Выбрано расписание на {schedule_days} дней.", reply_markup=ReplyKeyboardRemove()
            )
            await generate_schedule(update, context, schedule_days)
        except ValueError:
            await update.message.reply_text("Неверный формат. Выберите количество дней, используя кнопки.")
    else:
        await update.message.reply_text("Неверный формат.")


async def generate_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE, days=7):
    global last_assigned
    available_people = people[:] 

    for day_offset in range(1, days + 1):
        current_date = datetime.date.today() + datetime.timedelta(days=day_offset)
        current_date_str = current_date.strftime("%d.%m.%Y")
        current_weekday = current_date.weekday()

        daily_available_people = [p for p in available_people if last_assigned.get(p, datetime.date.min) < current_date]
        if not daily_available_people:
            await update.message.reply_text(f"На {current_date_str} не хватает людей для составления расписания.")
            continue

        random.shuffle(daily_available_people)

        schedule_message = f"📢 Уважаемые коллеги, добрый день, напоминаю на {current_date_str} дежурят:\n\n"

        if current_weekday == 1 or current_weekday == 3:  # Tuesday or Thursday
            if daily_available_people:
                duty_person = daily_available_people.pop()
                schedule_message += f"Переговорка:\n{duty_person}\n\n"
                last_assigned[duty_person] = current_date
            else:
                schedule_message += "Переговорка: Некому дежурить\n\n"
        else:  # Other days (No Переговорка)
            for zone in zones[1:]:  # Exclude "Переговорка"
                duty_people = []
                for _ in range(min(2, len(daily_available_people))):
                    duty_person = daily_available_people.pop()
                    duty_people.append(duty_person)
                    last_assigned[duty_person] = current_date
                schedule_message += f"{zone}:\n{', '.join(duty_people) or 'Некому дежурить'}\n\n"

        schedule_message += "Коллеги, просьба отдежурить качественно, об уборке доложить. Как принято?\n\n"
        await update.message.reply_text(schedule_message)



def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.TEXT, handle_document))
    application.add_handler(MessageHandler(filters.TEXT, handle_schedule_days))

    application.run_polling()


if __name__ == '__main__':
    main()