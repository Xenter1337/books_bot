# Бот "Библиотека"

### - Инструкция по запуску

- **Установить** [Python.](https://www.python.org/) Версии 3.11...
- **Установить** библиотеки путём запуска файла **install.bat** или командой **pip install -r requirements.txt**. При использовании второго варианта необходимо перейти в директорию проекта.
- Создать **.env** файл с параметром **BOT_TOKEN = ""**. В ковычках должен находиться токен бота. Получить его можно [тут(кликабельно)](https://t.me/BotFather)


### - Добавление стандартных жанров

Для добавления стандартных жанров вам нужно скачать программу для работы с базой данных.
[DB Browser for  SQLite](https://sqlitebrowser.org/dl/) или [SQLite Studio](https://sqlitestudio.pl/)

- Открыть файл базы данных. Он находиться в папке database и имеет расширение **.db**
- Перейти в таблицу **styles**
- Добавить новую запись с двумя столбцами 
  - Название жанра
  - Любое уникальное в таблице слово/набор букв на латинице. Рекомендуется использовать название жанра переведённое на английский язык