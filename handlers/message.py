# handlers/message.py

import logging
from telegram import Update
from telegram.ext import ContextTypes
from nlp.search import search_engine
from database.db import get_session
from database.models import Log
from handlers.common import show_category

logger = logging.getLogger(__name__)

# Кнопки, которые считаются навигационными (меню)
MENU_BUTTONS = {
    "📘 Математика", "💻 Программирование", "🌐 Общие вопросы", "❓ Помощь",
    "Линейная алгебра", "Матанализ", "Python", "Java", "Алгоритмы",
    "Wi-Fi", "Расписание", "Назад", "Назад в главное меню"
}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Получаем текст сообщения один раз в начале
    if update.message and update.message.text:
        user_text = update.message.text.strip()
    else:
        return

    # Игнорируем сообщения, если активен админ-режим (дублирующая защита)
    # Проверяем по context.user_data флаг, который будет установлен в админке
    if context.user_data.get("admin_mode"):
        return

    # Если это навигационная кнопка из меню – передаём в show_category
    if user_text in MENU_BUTTONS:
        await show_category(update, context)
        return

    # Попытка семантического поиска
    answer, similarity = search_engine.search(user_text)

    # Запись в лог БД
    user = update.effective_user
    session = get_session()
    try:
        log_entry = Log(
            user_id=user.id,
            username=user.username,
            user_question=user_text,
            found_answer=answer,
            similarity=round(float(similarity), 4)
        )
        session.add(log_entry)
        session.commit()
        logger.info(f"Вопрос от @{user.username}: '{user_text}' | Ответ найден: {bool(answer)} | sim={similarity:.3f}")
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка записи лога: {e}")
    finally:
        session.close()

    # Отправка ответа пользователю
    if answer:
        await update.message.reply_text(answer)
    else:
        await update.message.reply_text(
            "Извините, я не нашёл точного ответа на ваш вопрос.\n"
            "Попробуйте переформулировать или выберите раздел в меню."
        )