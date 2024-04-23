from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types
from aiogram.filters.callback_data import CallbackData

from database.core import db


# Callback Data Factory для пагинации
class SearchPagination(CallbackData, prefix="search"):
    page: int

    # Это параметр будет = normal в случае вывода всех книг
    # И будет равен названию жанра в случае поиска по жанрам
    search_type: str


# Нужен для правильной работы кнопки "Назад" при нажатии на книгу.
# Чтобы правильно возвращать на нужную страницу поиска
class BookSearch(CallbackData, prefix="output"):
    action: str
    page: int
    search_type: str

    rowid: str


class ClientKeyboards:

    async def start_keyboard():
        ikb = InlineKeyboardBuilder()

        ikb.button(text="📖Добавить книгу", callback_data="add_book")
        ikb.button(text="📚Список книг", callback_data="books_list")
        ikb.button(text="🔎Поиск книг", callback_data="search_book")

        ikb.adjust(1)

        return ikb.as_markup()

    # Клавиатура жанров
    async def styles_keyboard():
        # Получаем жанры из бд и собираем клавиатуру - i[0] Название жанра - i[1] строка для callback_data
        styles = await db.get_styles()
        keyboard = [types.InlineKeyboardButton(
            text=i[0], callback_data=i[1]) for i in styles]

        # Делаем список списков клавиатур по 2 элемента для правильного отображения [[клавиатура, клавиатура],
        #                                                                           [клавиатура, клавиатура]]
        keyboard = [keyboard[i:i+2] for i in range(0, len(keyboard), 2)]

        return types.InlineKeyboardMarkup(inline_keyboard=keyboard)

    # Клавиатура поиска
    async def search_keyboard():
        ikb = InlineKeyboardBuilder()

        ikb.button(text="Все книги", callback_data="all_books")
        ikb.button(text="По жанру", callback_data="by_style")
        ikb.button(text="Назад❌", callback_data="back")

        return ikb.adjust(1).as_markup()

    # Клавиатура с пагинацией для выводаа результатов поиска
    async def search_pagination(books, page, search_type):
        second_page = ""

        # Для того чтобы при поиске по запросу нас не возвращало
        # в меню выбора поиска(по жанру, или всем книгам
        # В случае поиска по запросу search_type начинается с byRequest
        if not search_type.startswith("byRequest"):
            back_text = "back_search"
        else:
            back_text = "back"

        ikb = InlineKeyboardBuilder()

        # На одной страницее будет отображаться 9 книг
        if len(books) > 0:
            if page > 1:

                # Делаем срез следующей страницы чтобы понять
                # Будут ли там элементы
                second_page = books[(page)*9:(page+1)*9]

                # получаем список книг с текущей страници.
                # 2 страница = первые 9 книг уже отобразились.
                # По итогу и получаем page - 1 * 9 = 2 - 1 * 9 = 9.
                # И делаем срез с 9:18
                books = books[(page-1)*9:(page)*9]

            else:
                second_page = books[9:18]
                books = books[:9]

            print(books)

            for i in books:
                # callback_data == book rowid
                ikb.button(text=f"{i[1]} {i[2]}", callback_data=BookSearch(
                    page=page, search_type=search_type, rowid=str(i[0]), action="output").pack())

            ikb.adjust(1)

        keyboard = ikb.export()

        last_buttons = []

        if page > 1:
            last_buttons.append(types.InlineKeyboardButton(text="◀️", callback_data=SearchPagination(
                page=page-1, action="prev", search_type=search_type).pack()))

        if len(second_page) > 0:
            last_buttons.append(types.InlineKeyboardButton(text="➡️", callback_data=SearchPagination(
                page=page+1, action="next", search_type=search_type).pack()))

        keyboard.append(last_buttons)
        keyboard.append([types.InlineKeyboardButton(
            text="Назад❌", callback_data=back_text)])

        return types.InlineKeyboardMarkup(inline_keyboard=keyboard)

    async def back_keyboard():
        ikb = InlineKeyboardBuilder()

        ikb.button(text="Назад❌", callback_data="back")

        return ikb.as_markup()

    # Клавиатура при нажатии на определённую книгу
    async def searched_keyboard(page, search_type, rowid):
        ikb = InlineKeyboardBuilder()

        ikb.button(text="Удалить", callback_data=BookSearch(
            page=page, search_type=search_type, rowid=rowid, action="delete").pack())
        ikb.button(text="Назад❌", callback_data=BookSearch(
            page=page, search_type=search_type, rowid=rowid, action="back").pack())

        return ikb.as_markup()

    # Отмена добавления книги
    async def cancel_keyboard():

        return types.ReplyKeyboardMarkup(keyboard=[
            [types.KeyboardButton(text="Отмена")]
        ],
            resize_keyboard=True,
            one_time_keyboard=True)

    # async def request_search_keybboard(rowid, text):
    #     return types.InlineKeyboardMarkup(inline_keyboard=[
    #         [types.InlineKeyboardButton(text=text, callback_data=BookSearch(
    #             page=0, search_type="search_type", rowid=str(rowid), action="request_search"))]
    #     ])
