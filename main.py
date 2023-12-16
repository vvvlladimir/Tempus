import os

from dotenv import load_dotenv
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters
)

from CoreFunсtions import *
from managers import JobManager, ScheduleManager, UserProfileManager

# Load environment variables
load_dotenv("./utils/.env")
TOKEN = os.getenv("TOKEN")

# Fallback handlers
all_fallbacks = [
    CommandHandler("cancel", cancel),
    CallbackQueryHandler(menu, pattern='^menu')
]

# Handler dictionary for callback queries
handlers = {
    'menu': menu,
    'info': show_help,
    'settings': settings,

    'now_stamp': ScheduleManager.now_stamp,
    'time_stamp': ScheduleManager.time_stamp,
    'stamp_confirm': ScheduleManager.stamp_confirm,
    'schedule': ScheduleManager.schedule_show,
    'new_schedule': ScheduleManager.schedule_new,

    'bio': UserProfileManager.bio,
    'bio_change': UserProfileManager.bio_change,

    'job_code': JobManager.job_code,
    'job_code_change': JobManager.job_code_change,
}


async def buttons(update: Update, context: CallbackContext) -> None:
    # Handle button presses in Telegram
    try:
        query = update.callback_query
        handler = handlers.get(query.data)
        if handler:
            await handler(update, context)
        else:
            await show_help(update, context, 404)
    except Exception as e:
        logger.critical(f"Error in buttons handler: {e}")


def main() -> None:
    """Run the bot."""
    try:
        application = Application.builder().token(TOKEN).build()

        # on different commands - answer in Telegram
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", show_help))

        job_conv_handler = ConversationHandler(

            entry_points=[CallbackQueryHandler(JobManager.job_code_change, pattern='^job_code_change')],
            states={
                JobManager.JOB_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, JobManager.job_code_handler)],
            },
            fallbacks=all_fallbacks
        )
        stamp_conv_handler = ConversationHandler(

            entry_points=[CallbackQueryHandler(ScheduleManager.time_stamp, pattern='^time_stamp')],
            states={
                ScheduleManager.INPUT_TIME_STAMP: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, ScheduleManager.time_stamp_handler)],
            },
            fallbacks=all_fallbacks
        )
        bio_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(UserProfileManager.bio_change, pattern='^bio_change')],
            states={
                UserProfileManager.NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, UserProfileManager.bio_change_name)],
                UserProfileManager.JOB: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, UserProfileManager.bio_change_job)],
                UserProfileManager.AGE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, UserProfileManager.bio_change_handler)],
            },
            fallbacks=all_fallbacks
        )
        schedule_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(ScheduleManager.schedule_new, pattern='^new_schedule')],
            states={
                ScheduleManager.NEW_SCHEDULE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, ScheduleManager.schedule_handler)],
                ScheduleManager.TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ScheduleManager.time_handler)],
            },
            fallbacks=all_fallbacks
        )

        application.add_handler(job_conv_handler)
        application.add_handler(stamp_conv_handler)
        application.add_handler(bio_conv_handler)
        application.add_handler(schedule_conv_handler)
        application.add_handler(CallbackQueryHandler(buttons))

        # Run the bot until the user presses Ctrl-C
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.critical(f"Error in main function: {e}")


if __name__ == "__main__":
    main()
