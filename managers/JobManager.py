from CoreFunсtions import *

JOB_CODE = 0

config_keyboard = KeyboardManager().config_keyboard


# Retrieves the user's job code and displays it.
async def job_code(update: Update, context: CallbackContext) -> None:
    # Extract the user ID from the update object.
    user = update.effective_user.id
    # Fetch user data from the database.
    data = await db.get_user_data(user)

    reply_markup = await config_keyboard(["job_code_change", "menu"])
    text = f"Your work code:<b>{data.get('job_code')}</b>"

    await send_or_edit_message(update, context, text, reply_markup)


# Initiate changing the job code.
async def job_code_change(update, context):
    query = update.callback_query
    await query.edit_message_text(text="Waiting for the code...")

    # Log the event of defining a new job code.
    logger.info("// %s // Defining a new 'job_code'", update.effective_user.id)
    return JOB_CODE


# Handle the new job code input.
async def job_code_handler(update, context):
    user = update.effective_user.id
    # Update the job code in the database.
    status = await db.update_job_code(user, update.message.text)
    await status_msg(update, context, status, job_code)

    logger.info("// %s // New 'job_code': %s", user, update.message.text)
    return ConversationHandler.END
