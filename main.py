import calendar
import os
from datetime import datetime
from functools import partial

from dotenv import load_dotenv
from telegram import *
from telegram.constants import ParseMode
from telegram.ext import *

import database as db
import log
import error_handler as err

load_dotenv()
TOKEN = os.getenv("TOKEN")

logger = log.setup_logger("Telegram", 1, 1)

JOB_CODE, MENU = range(2)
NAME, JOB, AGE = range(3)
NEW_SCHEDULE, TIME = range(2)

all_buttons = {
    'menu': InlineKeyboardButton("Возврат в меню ⏪", callback_data='menu'),

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

help_text = {
    404: "Неизвестная команда",
    0: "Вы находитесь в разделе информации о проекте"
}


# --------------------------------------------------------------------------------------------------- #
# FUNCTIONS BLOCK

# TODO: make new date-keyboard only 1 time per mouth, not for every person
# def generate_date_keyboard():
#     now = datetime.now()
#     year, month, day = now.year, now.month, now.day
#     num_days = calendar.monthrange(year, month)[1]
#
#     keyboard = []
#     row = []
#
#     for day in range(1, num_days + 1):
#         row.append(KeyboardButton(f"{year}-{month}-{day}"))
#         if len(row) == 5:  # Разбиваем на ряды по 5 кнопок
#             keyboard.append(row)
#             row = []
#     if row:
#         keyboard.append(row)
#
#     row.append(KeyboardButton("❌ Exit"))
#     keyboard.append(row)
#
#     logger.info("Generating Date-keyboard with %s days", num_days)
#     return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
#
def config_keyboard(button_ids):
    keyboard = [[all_buttons[button_id]] for button_id in button_ids if button_id in all_buttons]
    return InlineKeyboardMarkup(keyboard)


async def send_or_edit_message(update: Update, context: CallbackContext, text: str, reply_markup=""):
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        logger.info("// %s // Changing message due to: %s", update.effective_user.id, update.callback_query.data)
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        logger.info("// %s // Request: %s", update.effective_user.id, update.effective_message.text)


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
    print(dates)
    return dates


# --------------------------------------------------------------------------------------------------- #
# MAIN FUNCTIONS BLOCK
async def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""

    user = update.effective_user
    language_code = user.language_code
    db_user = db.get_user_data(user.id)
    if db_user == 0:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Привет, {user.full_name}!"
                                            f"\nТебе надо зарегистрироваться...")
        await settings(update, context)
        logger.info("New user: %s", user.id)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Привет, {user.full_name}!")
        await show_menu(update, context)
        logger.info("Registered user: %s", user.id)


# TODO: change /help func with, error handling
async def help(update: Update, context: CallbackContext, error) -> None:
    """Send a message when the command /help is issued."""

    reply_markup = config_keyboard(["menu"])
    if error != 0:
        logger.error("// %s // %s", update.effective_chat.id, help_text[error])
    text = help_text[error]
    await send_or_edit_message(update, context, text, reply_markup)


async def show_menu(update: Update, context: CallbackContext):
    text = "Вы в меню!"
    reply_markup = config_keyboard(["schedule", "settings", "info"])

    await send_or_edit_message(update, context, text, reply_markup)


async def settings(update: Update, context: CallbackContext):
    reply_markup = config_keyboard(["bio", "job_code", "menu"])
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

async def schedule(update: Update, context: CallbackContext) -> None:
    user = update.effective_user.id

    reply_markup = config_keyboard(["new_schedule", "menu"])
    data = db.get_schedule_data(user)
    text = (f"Вы находитесь в меню расписаний.\n\n"
            f"Последняя дата обновления: <b>{data.get("creation_date")}</b>\n\n"
            f"<b>Ваше расписание: </b>\n"
            f"{data.get("dates")}")

    await send_or_edit_message(update, context, text, reply_markup)


# TODO: add view of a schedule with old strike and new normal dates
async def new_schedule(update: Update, context: CallbackContext) -> None:
    text = "Отправьте даты когда вы работаете в формате 1,2,3,4"

    await send_or_edit_message(update, context, text)
    # await context.bot.send_message(
    #     chat_id=update.effective_chat.id,
    #     text="text",
    #     reply_markup=generate_date_keyboard(),
    #     parse_mode=ParseMode.HTML
    # )
    logger.info("// %s // Defining a new schedule...", update.effective_user.id)
    return NEW_SCHEDULE


async def schedule_handler(update: Update, context: CallbackContext) -> None:
    user = update.effective_user.id

    date = context.user_data
    date[user] = {"dates": update.message.text}

    text = "Укажите время уведомления"
    await send_or_edit_message(update, context, text)

    logger.info("// %s // New date in schedule: %s", user, update.message.text)
    return TIME


async def time_handler(update: Update, context: CallbackContext) -> None:
    user = update.effective_user.id
    date = context.user_data

    logger.info("// %s // New notification time: %s", user, update.message.text)

    date[user]["time"] = update.message.text
    date[user] = await convert_string_to_dates(date[user])
    db.add_new_schedule(user, date[user])

    await schedule(update, context)

    return ConversationHandler.END


# --------------------------------------------------------------------------------------------------- #
# BIOGRAPHY BLOCK
async def bio(update: Update, context: CallbackContext):
    user = update.effective_chat.id
    data = db.get_user_data(user)

    reply_markup = config_keyboard(["bio_change", "menu"])
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
        context.user_data[user]["age"] = age
        logger.info("// %s // 3. User new age: %s", user, context.user_data[user]["age"])

        feedback = db.change_user_data(user, context.user_data[user])
    except ValueError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Ошибка: введенные данные не являются числом. Пожалуйста, введите ваш возраст цифрами."
        )

        logger.error("// %s // 3. 'age' is not a number", user)
        return AGE  # Возвращаем пользователя обратно в состояние ввода возраста

    reply_markup = config_keyboard(["menu"])
    text = f"{feedback}"
    await send_or_edit_message(update, context, text, reply_markup)

    logger.info("// %s // User info updated successfully!", user)
    return ConversationHandler.END


# --------------------------------------------------------------------------------------------------- #
# JOB BLOCK
async def job_code(update: Update, context: CallbackContext) -> None:
    user = update.effective_user.id
    jb = db.get_user_data(user)

    reply_markup = config_keyboard(["job_code_change", "menu"])
    text = f"Ваш рабочий код: <b>{jb.get("job_code")}</b>"

    await send_or_edit_message(update, context, text, reply_markup)


async def job_code_change(update, context):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(text="Ожидаю код...")

    logger.info("// %s // Defining a new 'job_code'", update.effective_user.id)
    return JOB_CODE


async def job_code_handler(update, context):
    user = update.effective_user.id
    db.update_job_code(user, update.message.text)
    reply_markup = config_keyboard(["menu"])

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
async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    # Обработка различных callback данных
    match query.data:
        case 'schedule':
            await schedule(update, context)
        case 'new_schedule':
            await new_schedule(update, context)
        case 'settings':
            await settings(update, context)
        case 'bio':
            await bio(update, context)
        case 'bio_change':
            await bio_change(update, context)
        case 'info':
            await help(update, context, 0)
        case 'job_code':
            await job_code(update, context)
        case 'job_code_change':
            await job_code_change(update, context)
        case 'menu':
            await show_menu(update, context)
        case _:
            await help(update, context, 404)


def main() -> None:
    """Run the bot."""

    part_help = partial(help, error=0)
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", part_help))

    job_conv_handler = ConversationHandler(

        entry_points=[CallbackQueryHandler(job_code_change, pattern='^job_code_change')],
        states={
            JOB_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, job_code_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    bio_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(bio_change, pattern='^bio_change')],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, bio_change_name)],
            JOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, bio_change_job)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bio_change_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    schedule_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(new_schedule, pattern='^new_schedule')],
        states={
            NEW_SCHEDULE: [MessageHandler(filters.TEXT & ~filters.COMMAND, schedule_handler)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, time_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    application.add_handler(job_conv_handler)
    application.add_handler(bio_conv_handler)
    application.add_handler(schedule_conv_handler)
    # application.add_handler(MessageHandler(filters.TEXT, messageHandler))
    application.add_handler(CallbackQueryHandler(button))
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
