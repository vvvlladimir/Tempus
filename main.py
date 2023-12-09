import calendar
import os
import re
from datetime import datetime

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import *
from utils import log, database as db

load_dotenv("./utils/.env")
TOKEN = os.getenv("TOKEN")

logger = log.setup_logger("Telegram", 1, 1)

JOB_CODE = 0
NAME, JOB, AGE = range(3)
NEW_SCHEDULE, TIME = range(2)
INPUT_TIME_STAMP = 0

help_text = {
    404: "Неизвестная команда",
    0: "Вы находитесь в разделе информации о проекте"
}


# --------------------------------------------------------------------------------------------------- #
# FUNCTIONS BLOCK

async def send_or_edit_message(update: Update, context: CallbackContext, text: str, reply_markup: list = None,
                               send_priority: bool = False):
    try:
        if not update.callback_query or send_priority:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            logger.info("// %s // Request: %s", update.effective_user.id, update.effective_message.text)
        else:
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            logger.info("// %s // Changing message due to: %s", update.effective_user.id, update.callback_query.data)

    except Exception as e:
        logger.error(f"Error sending message for {update.effective_user.id}: {e}")
        await show_menu(update, context)


async def convert_string_to_dates(date_dict):
    now = datetime.now()
    year, month = now.year, now.month
    num_days = calendar.monthrange(year, month)[1]

    days = date_dict["dates"].split(',')
    hours, minutes = map(int, date_dict["time"].split(':'))

    dates = []

    for day in days:
        # if int(day) > num_days or int(day) < 0:
        #     err.handle_convert_dates_error(update, context)
        date = datetime(year, month, int(day), hours, minutes)
        dates.append(date)
    return sorted(dates)


# --------------------------------------------------------------------------------------------------- #
# MAIN FUNCTIONS BLOCK

# class Main:
#     def __init__(self, update: Update, context: CallbackContext):
#         self.update = update
#

async def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""

    user = update.effective_user
    # TODO: add language preferences to user
    language_code = user.language_code
    db_user = await db.get_user_data(user.id)

    if db_user == 0:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Привет, {user.full_name}!"
                                            f"\nТебе надо зарегистрироваться...")
        await db.change_user_data(user.id, {"name": user.full_name})
        await settings(update, context)
        logger.info("New user: %s", user.id)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Привет, {db_user.get("name")}!")
        await show_menu(update, context)
        logger.info("Registered user: %s", user.id)


# TODO: change /help func with, error handling
async def help(update: Update, context: CallbackContext, error=0) -> None:
    """Send a message when the command /help is issued."""

    reply_markup = await config_keyboard(["menu"])
    if error != 0:
        logger.error("// %s // %s", update.effective_chat.id, help_text[error])
    text = help_text[error]
    await send_or_edit_message(update, context, text, reply_markup)


async def show_menu(update: Update, context: CallbackContext):
    text = "Вы в меню!"
    reply_markup = await config_keyboard(["now_stamp", "time_stamp", "schedule", "settings", "info"])
    await send_or_edit_message(update, context, text, reply_markup)

    return ConversationHandler.END


async def settings(update: Update, context: CallbackContext):
    reply_markup = await config_keyboard(["bio", "job_code", "menu"])
    text = "Настройки"
    await send_or_edit_message(update, context, text, reply_markup)


# TODO: change the cansel func
async def cancel(update: Update, context: CallbackContext) -> None:
    """Cancels and ends the conversation."""
    await show_menu(update, context)

    logger.info("// %s // cancelled the conversation", update.effective_user.id)
    return ConversationHandler.END


# --------------------------------------------------------------------------------------------------- #

# SCHEDULE BLOCK
async def now_stamp(update: Update, context: CallbackContext) -> None:
    text = "Вы уверены что хотите отметиться сейчас?"
    reply_markup = await   config_keyboard(["stamp_confirm", "menu"])
    await   send_or_edit_message(update, context, text, reply_markup)


async def stamp_confirm(update: Update, context: CallbackContext) -> None:
    user = update.effective_user.id
    status = await   db.make_schedule_time_stamp(user)
    if status:
        await   show_menu(update, context)
    else:
        reply_markup = await   config_keyboard(["schedule", "menu"])
        text = "Вам нужно сначала создать расписание!"
        await   send_or_edit_message(update, context, text, reply_markup)


async def time_stamp(update: Update, context: CallbackContext):
    text = "Отправте дату и время когда вы хотите отметиться"
    reply_markup = await   config_keyboard(["menu"])
    await   send_or_edit_message(update, context, text, reply_markup)
    return INPUT_TIME_STAMP


async def extract_datetimes(user_input):
    # Регулярное выражение для проверки формата "19.07 12:00-15:00"
    pattern = r"^(0[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[012]) ([01][0-9]|2[0-3]):([0-5][0-9])-([01][0-9]|2[0-3]):([0-5][0-9])$"
    try:
        match = re.match(pattern, user_input)
        year = datetime.now().year
        day, month, start_hour, start_minute, end_hour, end_minute = match.groups()
        # Формирование полных строковых представлений начальной и конечной даты и времени
        start_datetime_str = f"{year}-{month}-{day} {start_hour}:{start_minute}"
        end_datetime_str = f"{year}-{month}-{day} {end_hour}:{end_minute}"
        # Преобразование строк в объекты datetime
        start_datetime = datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M")
        end_datetime = datetime.strptime(end_datetime_str, "%Y-%m-%d %H:%M")

        return start_datetime, end_datetime
    except:
        return None, None


async def time_stamp_handler(update, context):
    user_text = update.message.text  # Получение текста от пользователя
    start_datetime, end_datetime = await extract_datetimes(user_text)
    print(start_datetime, end_datetime)
    if start_datetime is None or end_datetime is None:
        print("Fail!")
        return INPUT_TIME_STAMP
    await   send_or_edit_message(update, context, "Успех!", send_priority=True)
    await   show_menu(update, context)
    return ConversationHandler.END


async def schedule_show(update: Update, context: CallbackContext) -> None:
    user = update.effective_user.id

    reply_markup = await   config_keyboard(["new_schedule", "menu"])
    data = await   db.get_schedule_data(user)
    if data:
        text = (f"Вы находитесь в меню расписаний.\n\n"
                f"Последняя дата обновления: <b>{data.get("creation_date")}</b>\n\n"
                f"<b>Ваше расписание: </b>\n"
                f"{data.get("notifications")}")
    else:
        text = (f"Вы находитесь в меню расписаний.\n\n"
                f"<b>У вас еще нет расписаний!</b>\n\n")

    await   send_or_edit_message(update, context, text, reply_markup)


# TODO: add view of a schedule with old strike and new normal dates
async def schedule_new(update: Update, context: CallbackContext) -> None:
    text = "Отправьте даты когда вы работаете в формате 1,2,3,4"

    await   send_or_edit_message(update, context, text)
    # await context.bot.send_message(
    #     chat_id=update.effective_chat.id,
    #     text="text",
    #     reply_markup=generate_date_keyboard(),
    #     parse_mode=ParseMode.HTML
    # )
    logger.info("// %s // Defining a new    ..", update.effective_user.id)
    return NEW_SCHEDULE


async def schedule_handler(update: Update, context: CallbackContext) -> None:
    user = update.effective_user.id

    data = context.user_data
    data[user] = {"dates": update.message.text}

    text = "Укажите время уведомления"
    await   send_or_edit_message(update, context, text)

    logger.info("// %s // New date in schedule: %s", user, update.message.text)
    return TIME


async def time_handler(update: Update, context: CallbackContext) -> None:
    user = update.effective_user.id
    data = context.user_data

    logger.info("// %s // New notification time: %s", user, update.message.text)

    data[user]["time"] = update.message.text
    data[user] = await   convert_string_to_dates(data[user])
    await   db.add_new_schedule(user, data[user])

    await schedule_show(update, context)

    return ConversationHandler.END


# --------------------------------------------------------------------------------------------------- #
# BIOGRAPHY BLOCK

async def bio(update: Update, context: CallbackContext):
    user = update.effective_chat.id
    data = await db.get_user_data(user)

    reply_markup = await config_keyboard(["bio_change", "menu"])
    text = (f"Настройки пользователя\n\n"
            f"<b>Ваши данные:</b>\n"
            f"Имя: {data.get("name")}\n"
            f"Должность: {data.get("job")}\n"
            f"Возраст: {data.get("age")}")
    await send_or_edit_message(update, context, text, reply_markup)


async def bio_change(update: Update, context: CallbackContext):
    text = "Отправьте пожалуйста ваше полное имя..."
    await send_or_edit_message(update, context, text)

    logger.info("Defining a new user info...")
    return NAME


async def bio_change_name(update, context):
    user = update.effective_user.id
    context.user_data[user] = {"name": update.message.text}

    text = "Отправьте пожалуйста вашу должность..."
    await send_or_edit_message(update, context, text)

    logger.info("// %s // 1. User new name: %s", user, context.user_data[user]["name"])
    return JOB


async def bio_change_job(update, context):
    user = update.effective_user.id
    context.user_data[user]["job"] = update.message.text

    text = "Отправьте пожалуйста ваш возраст..."
    await send_or_edit_message(update, context, text)

    logger.info("// %s // 2. User new job: %s", user, context.user_data[user]["job"])
    return AGE


async def bio_change_handler(update: Update, context: CallbackContext):
    user = update.effective_user.id
    try:
        age = int(update.message.text)
        logger.info("// %s // 3. User new age: %s", user, age)

        changes = {
            "name": context.user_data[user]["name"],
            "job": context.user_data[user]["job"],
            "age": age,
        }

        feedback = await db.change_user_data(user, changes)
    except ValueError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Ошибка: введенные данные не являются числом. Пожалуйста, введите ваш возраст цифрами."
        )

        logger.error("// %s // 3. 'age' is not a number", user)
        return AGE  # Возвращаем пользователя обратно в состояние ввода возраста

    reply_markup = await config_keyboard(["menu"])
    text = f"{feedback}"
    await send_or_edit_message(update, context, text, reply_markup)

    logger.info("// %s // User info updated successfully!", user)
    return ConversationHandler.END


# --------------------------------------------------------------------------------------------------- #
# JOB BLOCK
async def job_code(update: Update, context: CallbackContext) -> None:
    user = update.effective_user.id
    data = await db.get_user_data(user)

    reply_markup = await config_keyboard(["job_code_change", "menu"])
    text = f"Ваш рабочий код: <b>{data.get("job_code")}</b>"

    await send_or_edit_message(update, context, text, reply_markup)


async def job_code_change(update, context):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(text="Ожидаю код...")

    logger.info("// %s // Defining a new 'job_code'", update.effective_user.id)
    return JOB_CODE


async def job_code_handler(update, context):
    user = update.effective_user.id
    await db.update_job_code(user, update.message.text)
    reply_markup = await config_keyboard(["menu"])

    await update.message.reply_text(
        "Код получен и обработан.\n"
        f"Ваш новый код - <b>{update.message.text}</b>",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

    logger.info("// %s // New 'job_code': %s", user, update.message.text)
    return ConversationHandler.END


# --------------------------------------------------------------------------------------------------- #
# BUTTONS BLOCK
all_buttons = {
    'menu': InlineKeyboardButton("Возврат в меню ⏪", callback_data='menu'),

    'now_stamp': InlineKeyboardButton("Отметиться сейчас", callback_data='now_stamp'),
    'time_stamp': InlineKeyboardButton("Отметиться по времени", callback_data='time_stamp'),
    'stamp_confirm': InlineKeyboardButton("Да", callback_data="stamp_confirm"),
    'schedule': InlineKeyboardButton("Ваше расписание", callback_data='schedule'),
    'new_schedule': InlineKeyboardButton("Задать новое расписание", callback_data='new_schedule'),

    'settings': InlineKeyboardButton("Настройки", callback_data='settings'),
    'info': InlineKeyboardButton("О проекте", callback_data='info'),

    'bio': InlineKeyboardButton("Информация о себе", callback_data='bio'),
    'bio_change': InlineKeyboardButton("Изменить информацию о себе", callback_data='bio_change'),
    'name': InlineKeyboardButton("Имя", callback_data='name'),

    'job_code': InlineKeyboardButton("Код работника", callback_data='job_code'),
    'job_code_change': InlineKeyboardButton("Изменить код", callback_data='job_code_change')
}

handlers = {
    'now_stamp': now_stamp,
    'time_stamp': time_stamp,
    'stamp_confirm': stamp_confirm,
    'schedule': schedule_show,
    'new_schedule': schedule_new,
    'settings': settings,
    'bio': bio,
    'bio_change': bio_change,
    'info': help,
    'job_code': job_code,
    'job_code_change': job_code_change,
    'menu': show_menu,
}


async def config_keyboard(button_ids):
    keyboard = [[all_buttons[button_id]] for button_id in button_ids if button_id in all_buttons]
    return InlineKeyboardMarkup(keyboard)


async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    # Обработка различных callback данных
    handler = handlers.get(query.data)
    if handler:
        await handler(update, context)
    else:
        await help(update, context, 404)


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))

    all_fallbacks = [
        CommandHandler("cancel", cancel),
        CallbackQueryHandler(show_menu, pattern='^menu')
    ]

    job_conv_handler = ConversationHandler(

        entry_points=[CallbackQueryHandler(job_code_change, pattern='^job_code_change')],
        states={
            JOB_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, job_code_handler)],
        },
        fallbacks=all_fallbacks
    )
    stamp_conv_handler = ConversationHandler(

        entry_points=[CallbackQueryHandler(time_stamp, pattern='^time_stamp')],
        states={
            JOB_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, time_stamp_handler)],
        },
        fallbacks=all_fallbacks
    )
    bio_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(bio_change, pattern='^bio_change')],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, bio_change_name)],
            JOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, bio_change_job)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bio_change_handler)],
        },
        fallbacks=all_fallbacks
    )
    schedule_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(schedule_new, pattern='^new_schedule')],
        states={
            NEW_SCHEDULE: [MessageHandler(filters.TEXT & ~filters.COMMAND, schedule_handler)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, time_handler)],
        },
        fallbacks=all_fallbacks
    )

    application.add_handler(job_conv_handler)
    application.add_handler(stamp_conv_handler)
    application.add_handler(bio_conv_handler)
    application.add_handler(schedule_conv_handler)
    application.add_handler(CallbackQueryHandler(button))
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
