from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class KeyboardManager:
    def __init__(self):
        # Dictionary to store all the buttons used in the Telegram bot interface.
        self.all_buttons = {
            'menu': InlineKeyboardButton("Return to menu ⏪", callback_data='menu'),

            'now_stamp': InlineKeyboardButton("Check-in now", callback_data='now_stamp'),
            'time_stamp': InlineKeyboardButton("Check-in by time", callback_data='time_stamp'),
            'stamp_confirm': InlineKeyboardButton("Yes", callback_data="stamp_confirm"),
            'schedule': InlineKeyboardButton("Your schedule", callback_data='schedule'),
            'new_schedule': InlineKeyboardButton("Set new schedule", callback_data='new_schedule'),

            'settings': InlineKeyboardButton("Settings", callback_data='settings'),
            'info': InlineKeyboardButton("About the project", callback_data='info'),

            'bio': InlineKeyboardButton("About yourself", callback_data='bio'),
            'bio_change': InlineKeyboardButton("Change about yourself", callback_data='bio_change'),
            'name': InlineKeyboardButton("Name", callback_data='name'),

            'job_code': InlineKeyboardButton("Employee code", callback_data='job_code'),
            'job_code_change': InlineKeyboardButton("Change code", callback_data='job_code_change')
        }

    async def config_keyboard(self, button_ids):
        # Generates a keyboard layout based on the provided button IDs.
        # Ensures that only valid button IDs specified in the all_buttons dictionary are used.
        keyboard = [[self.all_buttons[button_id]] for button_id in button_ids if button_id in self.all_buttons]
        return InlineKeyboardMarkup(keyboard)
