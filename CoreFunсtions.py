import asyncio
import calendar
from datetime import datetime

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, ConversationHandler

import DataBase as db
from ButtonsFactory import KeyboardManager
from utils import log

# Setting up logging for the Telegram bot
logger = log.setup_logger("Telegram", 1, 1)

# Help text dictionary for different scenarios
help_text = {
    404: "Unknown command",
    0: "You are in the project information section"
}

# Initialize keyboard manager for creating custom keyboards
config_keyboard = KeyboardManager().config_keyboard


async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    # TODO: add language preferences to user
    # language_code = user.language_code
    db_user = await db.get_user_data(user.id)

    # Greeting registered users with their name or asking new users to register
    if db_user:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Hello, {db_user.get('name')}!")
        await menu(update, context)
        logger.info("Registered user: %s", user.id)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Hello, {user.full_name}!"
                                            f"\nYou need to register...")
        await db.change_user_data(user.id, {"name": user.full_name})
        await settings(update, context)
        logger.info("New user: %s", user.id)


async def show_help(update: Update, context: CallbackContext, error=0) -> None:
    # Show help message or error message
    reply_markup = await config_keyboard(["menu"])
    if error != 0:
        logger.error("// %s // ERROR - %s", update.effective_chat.id, error)
    text = help_text[error]
    await send_or_edit_message(update, context, text, reply_markup)


async def menu(update: Update, context: CallbackContext):
    # Display the main menu
    text = "You are in the menu!"
    reply_markup = await config_keyboard(["now_stamp", "time_stamp", "schedule", "settings", "info"])
    await send_or_edit_message(update, context, text, reply_markup)

    return ConversationHandler.END


async def settings(update: Update, context: CallbackContext):
    # Display the settings menu
    reply_markup = await config_keyboard(["bio", "job_code", "menu"])
    text = "Settings"
    await send_or_edit_message(update, context, text, reply_markup)


async def cancel(update: Update, context: CallbackContext):
    # Cancels and ends the conversation
    await menu(update, context)

    logger.info("// %s // cancelled the conversation", update.effective_user.id)
    return ConversationHandler.END


async def send_or_edit_message(update: Update, context: CallbackContext, text: str, reply_markup: list = None,
                               send_priority: bool = False):
    # Send a new message or edit an existing one based on the callback query
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
        return await menu(update, context)


async def parse_date(day, hours, minutes):
    # Parse a date from day, hours, and minutes
    now = datetime.now()
    return datetime(now.year, now.month, day, hours, minutes)


async def convert_string_to_dates(date_dict):
    # Convert a string to a list of datetime objects
    try:
        days = map(int, date_dict["dates"].split(','))
        hours, minutes = map(int, date_dict["time"].split(':'))
        now = datetime.now()
        month_days = calendar.monthrange(now.year, now.month)[1]

        valid_dates = [await parse_date(day, hours, minutes) for day in days if
                       0 < day <= month_days and 0 <= hours < 24 and 0 <= minutes < 59]

        return sorted(valid_dates) if valid_dates else False

    except ValueError:
        return False


async def status_msg(update: Update, context: CallbackContext, status: bool = False, func=menu) -> None:
    # Display a status message and then proceed to the specified function
    text = "Success!" if status else "An error occurred!"
    message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        parse_mode=ParseMode.HTML
    )
    await asyncio.sleep(1)
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message.message_id)
    await func(update, context)
