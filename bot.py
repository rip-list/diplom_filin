import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, InlineQueryHandler
from config import BOT_TOKEN
from database.db import init_db
from nlp.search import search_engine  # инициализация индекса
from handlers.common import start, help_command, show_category
from handlers.message import handle_message
from handlers.inline import inline_query
from handlers.admin import admin_conv_handler

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.INFO)

def main():
    # Инициализация БД
    init_db()
    # Перестраиваем индекс при старте (можно перенести в search_engine.init)
    search_engine.rebuild_index()

    # Создаём приложение
    app = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    # Админка (conversation handler)
    app.add_handler(admin_conv_handler)

    # Обработка текстовых сообщений (не команд)
    # Важно: чтобы кнопки меню не путались с командами, добавим фильтр
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Inline-режим
    app.add_handler(InlineQueryHandler(inline_query))

    # Запуск
    logger.info("Бот запущен и готов к работе!")
    app.run_polling(allowed_updates=["message", "inline_query"])

if __name__ == "__main__":
    main()