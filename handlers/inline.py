from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ContextTypes
from nlp.search import search_engine
import hashlib

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    if not query:
        return
    # Для inline используем простой поиск по подстроке или TF-IDF
    results = []
    for q in search_engine.questions:
        if query.lower() in q.text.lower():
            results.append(
                InlineQueryResultArticle(
                    id=str(q.id),
                    title=q.text[:60],
                    description=q.answer[:100],
                    input_message_content=InputTextMessageContent(q.answer)
                )
            )
            if len(results) >= 10:
                break
    await update.inline_query.answer(results, cache_time=10)