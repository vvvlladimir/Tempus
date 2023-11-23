# import log
# from main import send_or_edit_message
#
# # Настройка логирования
# logger = log.setup_logger("Error Handler", 1, 1)
#
#
# def handle_convert_dates_error(update, context):
#     user = update.effective_user.id
#
#     logger.error("// %s // Incorrect date data!", user)
#     send_or_edit_message(update, context, "Вы указали неверные данные!", ["new_schedule", "menu"])
