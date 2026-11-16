from abc import ABC, abstractmethod
from collections.abc import Sequence
import copy


razdelitel = '__'

# Базовые кнопки
class BaseButton(ABC):
    def __init__(
            self,
            key: str,                       # Ключ, по которому можно идентифицировать кнопку
            caption: str,                   # Отображаемое пользователю название кнопки
            text: str | None = None,               # Отображаемый пользователю текст вместе с кнопками
            can_back: bool | None = None,          # Необходимость добавления кнопки "Назад", в список кнопок
            parse_mode: str | None = None,         # Действие кнопки выводит определенный тип содержимого
            analyze = None,                 # lambda функция для захода в кнопку при нажатии на неё
            visible = None,                 # lambda функция для отображения кнопки пользователю
            row_width: int = 1,
            get_first_if_one: bool = False, # Сразу переходить внутрь кнопки, если внутри текущей всего одна кнопка
            **kwargs
    ):
        if text is None:
            text = caption

        self.key = key
        self.caption = caption
        self.text = text
        self.is_back = key == 'back'
        self.parse_mode = parse_mode
        self.can_back = can_back
        self.analyze = analyze if analyze is not None else lambda *args: None
        self.visible = visible if visible is not None else lambda *args: True
        self.prev_button: BaseButton | None = None
        self.keys_search = key
        self.row_width = row_width
        self.get_first_if_one = get_first_if_one

    @abstractmethod
    def get_keys(self, *args):
        pass

    @abstractmethod
    def update_children_button(self):
        pass

    def get_prev_button(self, chat_id, two_up: bool = False, first=False):
        def check_btn(bt):
            keys = bt.prev_button.get_keys(chat_id)
            if len(keys) <= (2 if bt.can_back else 1):
                bt = bt.prev_button
                return check_btn(bt)
            return bt
        if first:
            btn = self
            while btn.prev_button is not None:
                btn = btn.prev_button
            return btn

        btn = self
        if btn.is_back:
            btn = btn.prev_button
        btn = check_btn(btn)
        if two_up and btn.prev_button is not None:
            btn = check_btn(btn.prev_button)
        if btn.prev_button is not None:
            btn = btn.prev_button
        return btn

    @staticmethod
    def get_buttons(btns: "BaseButton", chat_id: int, search_key: str, *args):
        def get_button(btn: "BaseButton"):
            if not search_key.startswith(btn.keys_search):
                return None
            if not btn.visible(chat_id):
                return btn.prev_button
            if btn.keys_search == search_key:
                return btn
            for el in btn.get_keys(chat_id, *args):
                sb = get_button(el)
                if not sb is None:
                    return sb
            return btn

        btn = get_button(btns)
        if btn is None:
            btn = btns

        if btn.is_back:
            btn = btn.get_prev_button(chat_id=chat_id)
        return btn

    @staticmethod
    def get_refresh_button(btn: "BaseButton", chat_id: int, *args):
        first = btn.get_prev_button(chat_id=chat_id, first=True)
        btn = BaseButton.get_buttons(first, chat_id, btn.keys_search, *args)
        return btn


class ButtonWork(BaseButton):
    def __init__(
            self,
            work_def,
            **kwargs
    ):
        super().__init__(**kwargs)
        self.work_def = work_def

    def get_keys(self, *args):
        if self.can_back:
            back = copy.copy(BackButton)
            back.keys_search = f"{self.keys_search}{razdelitel}{back.key}"
            back.prev_button = self
            back.update_children_button()
            return [back]
        return []

    def update_children_button(self):
        pass





# Неисполняемые кнопки
class ButtonCustoms(BaseButton):
    def __init__(
            self,
            def_for_buttons,
            **kwargs
    ):
        super().__init__(**kwargs)
        self.def_for_buttons = def_for_buttons

    def get_keys(self, *args):
        btns: list[BaseButton] = self.def_for_buttons(self, *args)
        if self.can_back:
            btns.append(copy.copy(BackButton))
        for btn in btns:
            btn.prev_button = self
            btn.keys_search = f"{self.keys_search}{razdelitel}{btn.key}"
            btn.update_children_button()
        return btns

    def update_children_button(self):
        pass



class ButtonFixed(BaseButton):
    def __init__(
            self,
            buttons: Sequence[BaseButton] | None = None,
            **kwargs
    ):
        super().__init__(**kwargs)
        if buttons is None:
            buttons = []
        self.buttons = buttons
        self.update_children_button()

    def get_keys(self, *args):
        if self.can_back:
            back = copy.copy(BackButton)
            back.keys_search = f"{self.keys_search}{razdelitel}{back.key}"
            back.prev_button = self
            back.update_children_button()
            return [*self.buttons, back]
        return self.buttons

    def update_children_button(self):
        for btn in self.buttons:
            btn.keys_search = f"{self.keys_search}{razdelitel}{btn.key}"
            btn.prev_button = self
            btn.update_children_button()



BackButton = ButtonFixed(key='back', caption='Назад')