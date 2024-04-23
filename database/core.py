import aiosqlite


# Своя функция которая приводит строку в нижний регистр
# Для поиска в sqlite. Потому что встроенная работает только с ASCII
def my_lower(string):
    return string.lower()


class Database:

    async def startup(self):
        try:
            self.con = await aiosqlite.connect("./database/libriary_database.db")
            self.cur = await self.con.cursor()

            await self.cur.execute("""CREATE TABLE IF NOT EXISTS books(tittle TEXT,
                                                author TEXT COLLATE NOCASE,
                                                description TEXT COLLATE NOCASE,
                                                style TEXT)""")
            await self.cur.execute("""CREATE TABLE IF NOT EXISTS styles(name TEXT,
                                callback_data TEXT)""")
            await self.con.create_function("my_lower", 1, my_lower)
            await self.con.commit()
            print("Подключение к базе данных прошло успешно")
        except Exception as e:
            print(f"Ошибка подключения к базе данных: {e}")

    async def shutdown(self):
        await self.cur.close()
        await self.con.close()
        print("Подключение к базе данных открыто")

# Поиск книги для проверки при добавлении
    async def get_book(self, tittle, author):
        query = "SELECT * FROM books WHERE tittle LIKE ? and author LIKE ?"
        await self.cur.execute(query, (tittle, author))

        return await self.cur.fetchone()

# Добавление книги
    async def add_book(self, tittle, author, description, style):

        # Получаем жанр на русском языке из бд
        style_name = await db.get_style_name(style)

        if style_name is None:
            style_name = style
        else:
            # [0] ибо при запросе возвращается список
            style_name = style_name[0]

        query = """INSERT INTO books(tittle, author, description, style)
        VALUES(?, ?, ?, ?)"""

        await self.cur.execute(query, (tittle, author, description, style_name))
        await self.con.commit()

# Получение информации о книге(без описания)
    async def get_books(self):
        await self.cur.execute("SELECT rowid, tittle, author FROM books")
        return await self.cur.fetchall()

# Получение жанров и базы данных
    async def get_styles(self):
        await self.cur.execute("SELECT * FROM styles")
        return await self.cur.fetchall()

# Получение названия жанра по callback_data
    async def get_style_name(self, callback_data):
        query = """SELECT name FROM styles WHERE callback_data = ?"""

        await self.cur.execute(query, (callback_data,))
        return await self.cur.fetchone()

# Получение списка книг по жанру
    async def get_books_by_style(self, style):
        style_name = await db.get_style_name(style)

        # Если style_name == None --> жанр введён пользователем
        if style_name is None:
            style_name = style
        else:
            style_name = style_name[0]

        query = "SELECT rowid, tittle, author FROM books WHERE style = ?"

        await self.cur.execute(query, (style_name,))
        return await self.cur.fetchall()

# Получение полной информации по книге по rowid
# Используется для вывода информации по книге при нажатии на неё после поиска
    async def get_by_rowid(self, rowid):
        query = "SELECT * FROM books WHERE rowid = ?"

        await self.cur.execute(query, (rowid,))
        return await self.cur.fetchone()

# Удаление по rowid
    async def delete_by_rowid(self, rowid):
        query = "DELETE FROM books WHERE rowid = ?"

        await self.cur.execute(query, (rowid,))
        await self.con.commit()

# Поиск книги по запросу
    async def search_by_request(self, request):
        query = "SELECT rowid, tittle, author FROM books WHERE my_lower(author) LIKE $1 or my_lower(tittle) LIKE $1"

        await self.cur.execute(query, (f"%{request}%",))
        return await self.cur.fetchall()


db = Database()
