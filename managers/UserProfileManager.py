from CoreFunсtions import *

NAME, JOB, AGE = range(3)

# Function to configure the keyboard layout for the bot
config_keyboard = KeyboardManager().config_keyboard


# Display user's current bio information
async def bio(update: Update, context: CallbackContext):
    user = update.effective_chat.id
    data = await db.get_user_data(user)

    # Creating a reply markup with options for the user
    reply_markup = await config_keyboard(["bio_change", "menu"])

    # Formatting the text to show user data
    text = (f"User settings\n\n"
            f"<b>Your data:</b>\n"
            f"Name: {data.get("name")}\n"
            f"Job: {data.get("job")}\n"
            f"Age: {data.get("age")}")

    # Sending or editing the bots message with user's bio
    await send_or_edit_message(update, context, text, reply_markup)


# Initiate bio change process
async def bio_change(update: Update, context: CallbackContext):
    text = "Please send your full name..."
    await send_or_edit_message(update, context, text)

    logger.info("Defining a new user info...")
    return NAME


# Handle name change
async def bio_change_name(update, context):
    user = update.effective_user.id
    context.user_data[user] = {"name": update.message.text}

    text = "Please post your job position...."
    await send_or_edit_message(update, context, text)

    logger.info("// %s // 1. User new name: %s", user, context.user_data[user]["name"])
    return JOB


# Handle job title change
async def bio_change_job(update, context):
    user = update.effective_user.id
    context.user_data[user]["job"] = update.message.text

    text = "Please send your age..."
    await send_or_edit_message(update, context, text)

    logger.info("// %s // 2. User new job: %s", user, context.user_data[user]["job"])
    return AGE


# Handle age change and update user data
async def bio_change_handler(update: Update, context: CallbackContext):
    user = update.effective_user.id
    try:
        age = int(update.message.text)
        if not (0 <= age <= 120):
            raise ValueError("Unacceptable age")
        changes = {
            "name": context.user_data[user]["name"],
            "job": context.user_data[user]["job"],
            "age": age
        }
        status = await db.change_user_data(user, changes)
    except Exception as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Unacceptable age!\n"
                 f"Enter again."
        )
        logger.error("// %s // 3. Age Error: %s", user, str(e))
        return AGE

    await status_msg(update, context, status)
    logger.info("// %s // User info updated successfully!", user)
    return ConversationHandler.END
