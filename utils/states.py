from aiogram.fsm.state import State, StatesGroup


# Состояния добавления книги
class AddStates(StatesGroup):
    get_tittle = State()
    get_author = State()
    get_description = State()
    get_style = State()


# Состояние нужно для избежания дублирования кода ClientKeyboards.styles_keyboard
class SearchByStyle(StatesGroup):
    search = State()


# Состояние поиска книги по автору\названию
class SearchBByRequest(StatesGroup):
    info = State()
