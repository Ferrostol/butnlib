from telebot import TeleBot, types, apihelper
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from .buttons import BaseButton, ButtonWork


class LogicBot:
    def __init__(self, buttons: BaseButton, bot: TeleBot):
        self.buttons = buttons
        self.bot = bot

    def check_button_click(self, call: types.CallbackQuery):
        chat_id = call.message.chat.id
        self.bot.clear_step_handler(call.message)
        btn: BaseButton = BaseButton.get_buttons(self.buttons, chat_id, call.data)
        result: Result = btn.analyze(btn, chat_id)
        if result is not None:
            btn = result.btn
            text = result.text
            next = result.next_step
        elif isinstance(btn, ButtonWork):
            result: Result = btn.work_def(btn, chat_id, self.bot)
            btn: BaseButton = result.btn
            text = result.text
            next = result.next_step
        else:
            text = btn.text
            next = None
        btn: BaseButton = BaseButton.get_buttons(self.buttons, chat_id, btn.keys_search)
        try:
            self.bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=self.get_markup(btn, chat_id=chat_id),
                parse_mode=btn.parse_mode
            )
            if next is not None:
                self.bot.register_next_step_handler(call.message, self.next_step, next)
        except apihelper.ApiTelegramException as e:
            if "message is not modified" in e.description:
                pass
            else:
                print(e)
        except Exception as e:
            print(e)

    def next_step(self, message: types.Message, next=None, *args):
        if message.from_user.is_bot:
            self.bot.send_message(message.chat.id, "Доступ запрещен")
            return
        chat_id = message.chat.id
        result = next(message.text, chat_id, message, *args)
        msg = self.bot.send_message(
            message.chat.id,
            result.text,
            reply_markup=self.get_markup(result.btn, chat_id=chat_id),
            parse_mode=result.btn.parse_mode
        )
        if result.next_step is not None:
            self.bot.register_next_step_handler(msg, self.next_step, result.next_step)

    def get_markup(self, btn: BaseButton, chat_id: int = None):
        row = []
        for el in btn.get_keys(chat_id):
            if not el.visible(chat_id):
                continue
            row.append(InlineKeyboardButton(el.caption, callback_data=el.keys_search))
        markup = InlineKeyboardMarkup(row_width=btn.row_width)
        markup.add(*row)
        return markup



class Result:
    def __init__(self, btn: BaseButton, text: str, next_step=None):
        self.btn = btn
        self.text = text
        self.next_step = next_step

