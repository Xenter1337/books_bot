from aiogram import types, Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.filters.callback_data import CallbackData

from keyboards.client import ClientKeyboards, SearchPagination, BookSearch
from utils.states import AddStates, SearchByStyle, SearchBByRequest
from database.core import db

router = Router()


# Хендлер /start
@router.message(CommandStart())
async def start_command(message: types.Message, state: FSMContext, text="Добро пожаловать"):
    await state.clear()
    await message.answer(text=text,
                         reply_markup=await ClientKeyboards.start_keyboard())


# Отмена добавления книги
@router.message(F.text == "Отмена")
async def cancel_add(message: types.Message, state: FSMContext):
    await state.clear()
    await start_command(message, state)


# Добавление книги
@router.callback_query(F.data == "add_book")
async def adding_book(callback: types.CallbackQuery, state: FSMContext):
    # Используем message.delete() потому что
    # Нельзя методом edit_text изменять Inline клавиатуру
    # На клавиатуру ReplyMarkup
    await callback.message.delete()
    await callback.message.answer(text="Отправьте название книги", reply_markup=await ClientKeyboards.cancel_keyboard())
    await state.set_state(AddStates.get_tittle)


# Запрашиваем название
@router.message(F.text, AddStates.get_tittle)
async def getting_tittle(message: types.Message, state: FSMContext):
    if len(message.text) > 32:
        await message.answer("Максимальная длинна 32 символа!")
        return

    await state.update_data(tittle=message.text)

    await message.answer(text="Отправьте автора")
    await state.set_state(AddStates.get_author)


# Запрашиваем автора
@router.message(F.text, AddStates.get_author)
async def getting_author(message: types.Message, state: FSMContext):
    if len(message.text) > 32:
        await message.answer("Максимальная длинна 32 символа!")
        return
    date = await state.get_data()

    # Проверяем есть ли книга с таким же названием и автором в базе данных
    book_check = await db.get_book(tittle=date["tittle"], author=message.text)
    if book_check:
        await message.answer(text="Такая книга уже есть в библиотеке",
                             reply_markup=await ClientKeyboards.start_keyboard())
        await state.clear()
        return

    await message.answer(text="Введите описание")

    await state.update_data(author=message.text)
    await state.set_state(AddStates.get_description)


# Запрашиваем описание
@router.message(F.text, AddStates.get_description)
async def getting_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer(text="Выберите или введите свой жанр",
                         reply_markup=await ClientKeyboards.styles_keyboard())
    await state.set_state(AddStates.get_style)


# Отрабатывает на стандартные жанры
@router.callback_query(AddStates.get_style)
async def getting_style(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text="Книга добавлена",
                                     reply_markup=await ClientKeyboards.start_keyboard())
    data = await state.get_data()
    await db.add_book(tittle=data["tittle"],
                      author=data["author"],
                      description=data["description"],
                      style=callback.data)
    await state.clear()


# Отрабатывает на ввод своего жанраа
@router.message(F.text, AddStates.get_style)
async def getting_custom_style(message: types.Message, state: FSMContext):
    await message.answer(text="Книга добавлена",
                         reply_markup=await ClientKeyboards.start_keyboard())
    data = await state.get_data()

    await db.add_book(tittle=data["tittle"],
                      author=data["author"],
                      description=data["description"],
                      style=message.text)


# Поиск книг
@router.callback_query(F.data.in_(["books_list", "back_search"]))
async def books_list(callback: types.CallbackQuery):
    await callback.message.edit_text("<b>Сделайте выбор</b>", parse_mode="HTML", reply_markup=await ClientKeyboards.search_keyboard())


# Поиск по всем книгам
@router.callback_query(F.data == "all_books")
async def all_books(callback: types.CallbackQuery):
    books = await db.get_books()
    if len(books) == 0:
        await callback.message.edit_text("Книг не найдено", reply_markup=await ClientKeyboards.search_pagination(books, 1, "normal"))
        return

    await callback.message.edit_text("Выберите книгу:", reply_markup=await ClientKeyboards.search_pagination(books, 1, "normal"))


# Выбор жанра
@router.callback_query(F.data == "by_style")
async def by_style(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text="Выберите или введите свой жанр",
                                     reply_markup=await ClientKeyboards.styles_keyboard())
    await state.set_state(SearchByStyle.search)


# Поиск по жанру из списка
@router.callback_query(F.data.in_(["comedy", "drama", "tragedy"]),
                       SearchByStyle.search)
async def searching_by_style(callback: types.CallbackQuery, state: FSMContext):
    books = await db.get_books_by_style(callback.data)
    if len(books) == 0:
        await callback.message.edit_text("Книг не найдено", reply_markup=await ClientKeyboards.search_pagination(books, 1, callback.data))
        await state.clear()
        return

    await callback.message.edit_text("Выберите книгу:", reply_markup=await ClientKeyboards.search_pagination(books, 1, callback.data))

    await state.clear()


# Поиск по введённому жанру
@router.message(SearchByStyle.search)
async def searching_custom_style(message: types.Message, state: FSMContext):
    books = await db.get_books_by_style(message.text)
    if len(books) == 0:
        await message.answer("Книг не найдено", reply_markup=await ClientKeyboards.search_pagination(books, 1, message.text))
        await state.clear()
        return

    await message.answer("Выберите книгу:", reply_markup=await ClientKeyboards.search_pagination(books, 1, message.text))


# Основной вывод найденных книг с пагинацией.
# Отвечает за вывод как при поиске по всем книгам, так и по жанру
# Отрабатывает при нажатии кнопки ➡️
@router.callback_query(SearchPagination.filter(F.action == "next"))
async def all_books_next(callback: types.CallbackQuery, callback_data: SearchPagination):

    # Для понимания прочитай комментарий в классе SearchPagination
    if callback_data.search_type == "normal":
        books = await db.get_books()
    elif callback_data.search_type.startswith("byRequest"):
        books = await db.search_by_request(callback_data.search_type.replace("byRequest|", ""))
    else:
        books = await db.get_books_by_style(callback_data.search_type)

    page = callback_data.page

    await callback.message.edit_text("Выберите книгу:", reply_markup=await ClientKeyboards.search_pagination(books, page, callback_data.search_type))


# Отрабатывает при нажатии кнопки ◀️
@router.callback_query(SearchPagination.filter(F.action == "prev"), F.text)
async def all_books_prev(callback: types.CallbackQuery, callback_data: SearchPagination):

    # Для понимания прочитай комментарий в классе SearchPagination
    if callback_data.search_type == "normal":
        books = await db.get_books()
    elif callback_data.search_type.startswith("byRequest"):
        books = await db.search_by_request(callback_data.search_type.replace("byRequest|", ""))
    else:
        books = await db.get_books_by_style(callback_data.search_type)

    await callback.message.edit_text("Выберите книгу:", reply_markup=await ClientKeyboards.search_pagination(books, callback_data.page, callback_data.search_type))


# Нажатие inline кнопки назад
@router.callback_query(F.data == "back")
async def back_keyboard(callback: types.CallbackQuery):
    await callback.message.edit_text(text="Добро пожаловать",
                                     reply_markup=await ClientKeyboards.start_keyboard())


# Отрабатывает при нажатии на кнопку с книгой
@router.callback_query(BookSearch.filter(F.action == "output"))
async def book_output(callback: types.CallbackQuery, callback_data: BookSearch):
    book_info = await db.get_by_rowid(callback_data.rowid)

    text = f"""
<strong>Название:</strong> <code>{book_info[0]}</code>
<strong>Автор:</strong> <code>{book_info[1]}</code>

<b>Жанр:</b> <em>{book_info[3]}</em>

{book_info[2]}"""

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=await ClientKeyboards.searched_keyboard(callback_data.page,
                                                                                                                   search_type=callback_data.search_type,
                                                                                                                   rowid=callback_data.rowid))


@router.callback_query(BookSearch.filter(F.action == "back"))
async def books_back(callback: types.CallbackQuery, callback_data: BookSearch):
    await all_books_next(callback, callback_data)


# Удаление из меню книги
@router.callback_query(BookSearch.filter(F.action == "delete"))
async def books_back(callback: types.CallbackQuery, callback_data: BookSearch, state: FSMContext):

    await db.delete_by_rowid(callback_data.rowid)
    await callback.answer()
    await callback.message.delete()
    await start_command(callback.message, text="Книга удалена", state=state)


# Запрашиваем ввод для поиска книги
@router.callback_query(F.data == "search_book")
async def start_search(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("Введите название\автора книги")
    await state.set_state(SearchBByRequest.info)


# Вывод поиска по запросу
@router.message(SearchBByRequest.info)
async def searching_result(message: types.Message, state: FSMContext):
    result = await db.search_by_request(message.text)

    # такой странный search_type нужен для верного отображениия книиг при нажатии кнопки назад
    if len(result):
        await message.answer("Найденные книги", reply_markup=await ClientKeyboards.search_pagination(result, 1, f"byRequest|{message.text}"))
    else:
        await message.answer("Книг не найдено", reply_markup=await ClientKeyboards.search_pagination(result, 1, f"byRequest|{message.text}"))

    # request_search_keybboard
