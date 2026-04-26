import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from database.db import get_session
from database.models import Question
from config import TFIDF_THRESHOLD

logger = logging.getLogger(__name__)

class SearchEngine:
    def __init__(self):
        self.vectorizer = None
        self.matrix = None
        self.questions = []  # список Question ORM-объектов
        self.rebuild_index()

    def rebuild_index(self):
        """Перестраивает индекс TF-IDF по текущей базе."""
        session = get_session()
        try:
            self.questions = session.query(Question).all()
            corpus = [q.text for q in self.questions]
            if not corpus:
                self.vectorizer = None
                self.matrix = None
                logger.warning("База вопросов пуста, индекс не создан.")
                return
            self.vectorizer = TfidfVectorizer()
            self.matrix = self.vectorizer.fit_transform(corpus)
            logger.info(f"Индекс перестроен, вопросов: {len(self.questions)}")
        finally:
            session.close()

    def search(self, user_query: str) -> tuple:
        """
        Возвращает (answer_text, similarity) для лучшего совпадения,
        либо (None, 0.0), если ничего не найдено.
        """
        if not self.questions or not self.vectorizer:
            return None, 0.0
        try:
            query_vec = self.vectorizer.transform([user_query])
            sims = cosine_similarity(query_vec, self.matrix).flatten()
            best_idx = sims.argmax()
            best_sim = sims[best_idx]
            if best_sim >= TFIDF_THRESHOLD:
                return self.questions[best_idx].answer, best_sim
            else:
                return None, best_sim
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            return None, 0.0

# Глобальный экземпляр – инициализируется при старте бота
search_engine = SearchEngine()