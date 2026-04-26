# handlers/common.py

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from database.db import get_session
from database.models import Question

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    keyboard = [
        ["📘 Математика", "💻 Программирование"],
        ["🌐 Общие вопросы", "❓ Помощь"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"Привет, {user}! Я бот-помощник по учебной программе.\n"
        "Выбери категорию или задай вопрос текстом.",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Я понимаю вопросы на русском языке. Можешь спросить:\n"
        "- Когда сдавать курсовую?\n"
        "- Что такое рекурсия?\n"
        "- Расписание консультаций\n\n"
        "Используй меню для навигации по разделам."
    )

async def show_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # Главные категории
    if "математика" in text.lower():
        keyboard = [["Линейная алгебра", "Матанализ"], ["Назад в главное меню"]]
    elif "программирование" in text.lower():
        keyboard = [["Python", "Java"], ["Алгоритмы"], ["Назад в главное меню"]]
    elif "общие" in text.lower():
        keyboard = [["Wi-Fi", "Расписание"], ["Назад в главное меню"]]
    # Конечные темы – выдаём ответ
    elif text in ["Линейная алгебра", "Матанализ", "Python", "Java", "Алгоритмы", "Wi-Fi", "Расписание"]:
        session = get_session()
        q = session.query(Question).filter(
            (Question.subcategory == text) | (Question.text.contains(text))
        ).first()
        session.close()
        if q:
            await update.message.reply_text(q.answer)
        else:
            await update.message.reply_text(f"По теме «{text}» пока информации нет.")
        return  # не показываем меню
    elif text == "❓ Помощь":
        await help_command(update, context)
        return
    elif text == "Назад в главное меню" or text == "Назад":
        keyboard = [
            ["📘 Математика", "💻 Программирование"],
            ["🌐 Общие вопросы", "❓ Помощь"]
        ]
        await update.message.reply_text("Главное меню", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return
    else:
        # Неизвестная кнопка – ничего не делаем
        return

    # Отправляем клавиатуру с подменю
    await update.message.reply_text("Выбери тему:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))