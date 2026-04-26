# handlers/admin.py

import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
from config import ADMIN_PASSWORD
from database.db import get_session
from database.models import Question, Log, AdminLog
from nlp.search import search_engine

logger = logging.getLogger(__name__)

ADMIN_MENU, ADD_QUESTION, ADD_ANSWER, ADD_CATEGORY = range(4)

ADMIN_BUTTONS = ["➕ Добавить вопрос", "📋 Неотвеченные", "📊 Статистика", "🔄 Обновить индекс", "❌ Выйти"]

async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or context.args[0] != ADMIN_PASSWORD:
        await update.message.reply_text("Неверный пароль.")
        return ConversationHandler.END

    # Устанавливаем флаг админа
    context.user_data["admin_mode"] = True

    keyboard = [ADMIN_BUTTONS[:2], ADMIN_BUTTONS[2:4], [ADMIN_BUTTONS[4]]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Админ-панель активирована. Выберите действие:",
        reply_markup=reply_markup
    )
    return ADMIN_MENU

async def admin_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return ADMIN_MENU

    text = update.message.text.strip()
    logger.info(f"Админ-меню: получено '{text}'")

    if text == "➕ Добавить вопрос":
        await update.message.reply_text("Введите текст вопроса:", reply_markup=ReplyKeyboardRemove())
        return ADD_QUESTION
    elif text == "📋 Неотвеченные":
        session = get_session()
        logs = session.query(Log).filter(Log.found_answer == None).order_by(Log.timestamp.desc()).limit(10).all()
        session.close()
        if not logs:
            await update.message.reply_text("Нет неотвеченных вопросов.")
        else:
            msg = "Последние неотвеченные:\n" + "\n".join(
                f"{l.timestamp.strftime('%d.%m %H:%M')} – {l.user_question}" for l in logs
            )
            await update.message.reply_text(msg)
        return ADMIN_MENU
    elif text == "📊 Статистика":
        session = get_session()
        total_logs = session.query(Log).count()
        unique_users = session.query(Log.user_id).distinct().count()
        from sqlalchemy import func
        top = session.query(Log.user_question, func.count(Log.user_question).label('cnt')).group_by(Log.user_question).order_by(func.count(Log.user_question).desc()).limit(5).all()
        session.close()
        msg = f"📊 Статистика:\nВсего запросов: {total_logs}\nУникальных пользователей: {unique_users}\n\nТоп-5 вопросов:"
        for q, cnt in top:
            msg += f"\n- {q[:50]}... ({cnt})"
        await update.message.reply_text(msg)
        return ADMIN_MENU
    elif text == "🔄 Обновить индекс":
        search_engine.rebuild_index()
        await update.message.reply_text("Индекс поиска обновлён.")
        return ADMIN_MENU
    elif text == "❌ Выйти":
        context.user_data["admin_mode"] = False
    # Показываем главное меню после выхода
        keyboard = [
          ["📘 Математика", "💻 Программирование"],
            ["🌐 Общие вопросы", "❓ Помощь"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Выход из админ-панели. Вы снова в главном меню.", reply_markup=reply_markup)
        return ConversationHandler.END
    else:
        await update.message.reply_text("Используйте кнопки админ-панели.")
        return ADMIN_MENU

async def add_question_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_question'] = update.message.text
    await update.message.reply_text("Теперь введите ответ:")
    return ADD_ANSWER

async def add_question_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_answer'] = update.message.text
    await update.message.reply_text("Введите категорию (math, prog, general и т.п.):")
    return ADD_CATEGORY

async def add_question_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = update.message.text
    question_text = context.user_data['new_question']
    answer_text = context.user_data['new_answer']
    session = get_session()
    new_q = Question(text=question_text, answer=answer_text, category=category)
    session.add(new_q)
    admin_log = AdminLog(action="add_question", details=f"Q: {question_text}")
    session.add(admin_log)
    session.commit()
    session.close()
    search_engine.rebuild_index()
    await update.message.reply_text("Вопрос успешно добавлен!")
    keyboard = [ADMIN_BUTTONS[:2], ADMIN_BUTTONS[2:4], [ADMIN_BUTTONS[4]]]
    await update.message.reply_text("Дальнейшие действия?", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return ADMIN_MENU

admin_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("admin", admin_start)],
    states={
        ADMIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_menu_handler)],
        ADD_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_question_text)],
        ADD_ANSWER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_question_answer)],
        ADD_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_question_category)],
    },
    fallbacks=[MessageHandler(filters.TEXT & ~filters.COMMAND, admin_menu_handler)],
    allow_reentry=True
)