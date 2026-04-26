import os

BOT_TOKEN = "8277438956:AAG8G1ALN3JhWzIPSxCPaYWec_tMukizTeY"
ADMIN_PASSWORD = "supersecret123"  

# Путь к базе
DATABASE_URL = f'sqlite:///{os.path.join(os.path.dirname(__file__), "data", "bot.db")}'

# Параметры поиска
TFIDF_THRESHOLD = 0.3    # минимальный косинус для ответа