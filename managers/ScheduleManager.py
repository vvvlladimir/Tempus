import re

from CoreFunсtions import *

INPUT_TIME_STAMP = 0
NEW_SCHEDULE, TIME = range(2)

config_keyboard = KeyboardManager().config_keyboard


# Prompt the user for a current time stamp
async def now_stamp(update: Update, context: CallbackContext) -> None:
    text = "Are you sure you want to mark your time now?"
    reply_markup = await config_keyboard(["stamp_confirm", "menu"])
    await send_or_edit_message(update, context, text, reply_markup)


# Confirm the time stamp
async def stamp_confirm(update: Update, context: CallbackContext) -> None:
    user = update.effective_user.id
    status = await db.make_schedule_time_stamp(user)
    await status_msg(update, context, status)


# Handle a custom time stamp
async def time_stamp(update: Update, context: CallbackContext):
    text = "Please send the date and time when you want to mark your time"
    reply_markup = await config_keyboard(["menu"])
    await send_or_edit_message(update, context, text, reply_markup)
    return INPUT_TIME_STAMP


# Extract and validate date and time from user input
async def extract_datetimes(user_input):
    # Regular expression to check the format "01.01-31.12 12:00-15:00"
    pattern = r"^(0[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[012])-(0[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[012]) ([01][0-9]|2[0-3]):([0-5][0-9])-([01][0-9]|2[0-3]):([0-5][0-9])$"
    try:
        match = re.match(pattern, user_input)
        # Extract and format the date and time
        # TODO: Handle different year scenarios or time zones
        year = datetime.now().year
        # Parsing the datetime components
        start_day, start_month, end_day, end_month, start_hour, start_minute, end_hour, end_minute = match.groups()
        # Constructing datetime strings
        start_datetime_str = f"{year}-{start_month}-{start_day} {start_hour}:{start_minute}"
        end_datetime_str = f"{year}-{end_month}-{end_day} {end_hour}:{end_minute}"
        # Converting strings to datetime objects
        start_datetime = datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M")
        end_datetime = datetime.strptime(end_datetime_str, "%Y-%m-%d %H:%M")

        return start_datetime, end_datetime
    except ValueError as e:
        return e


# Handle time stamp submission
async def time_stamp_handler(update, context):
    user = update.effective_user.id
    user_text = update.message.text

    start_datetime, end_datetime = await extract_datetimes(user_text)
    status = await db.make_schedule_time_stamp(user, start_datetime, end_datetime)
    await status_msg(update, context, status)

    return ConversationHandler.END


# Display current schedule
async def schedule_show(update: Update, context: CallbackContext) -> None:
    user = update.effective_user.id

    reply_markup = await config_keyboard(["new_schedule", "menu"])
    data = await db.get_user_data(user)

    if "notify_creation_date" and "notifications" in data:
        # Displaying the current schedule
        text = (f"You are in the schedule menu.\n\n"
                f"Last update date: <b>{data.get('notify_creation_date')}</b>\n\n"
                f"<b>Your schedule: </b>\n"
                f"{data.get('notifications')}")
    else:
        text = (f"You are in the schedule menu.\n\n"
                f"<b>You do not have any schedules yet!</b>\n\n")

    await send_or_edit_message(update, context, text, reply_markup)


# Create a new schedule
async def schedule_new(update: Update, context: CallbackContext):
    text = "Send the dates you work in the format 1,2,3,4"
    await send_or_edit_message(update, context, text)

    logger.info("// %s // Defining a new schedule...", update.effective_user.id)
    return NEW_SCHEDULE


# Handle new schedule submission
async def schedule_handler(update: Update, context: CallbackContext):
    user = update.effective_user.id

    data = context.user_data
    data[user] = {"dates": update.message.text}

    text = "Please specify the notification time"
    await send_or_edit_message(update, context, text)

    logger.info("// %s // New date in schedule: %s", user, update.message.text)
    return TIME


# Handle time submission for notifications
async def time_handler(update: Update, context: CallbackContext):
    user = update.effective_user.id
    data = context.user_data

    logger.info("// %s // New notification time: %s", user, update.message.text)

    data[user]["time"] = update.message.text
    data[user] = await convert_string_to_dates(data[user])
    if not data[user]:
        text = "An error occurred!\nPlease send the dates you work in the format 1,2,3,4"
        await send_or_edit_message(update, context, text)
        logger.error("// %s // Date error appear!", user)
        return NEW_SCHEDULE

    status = await db.add_new_notify_user(user, data[user])
    await status_msg(update, context, status, schedule_show)

    return ConversationHandler.END
