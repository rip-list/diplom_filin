from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from database.models import Base

engine = create_engine(DATABASE_URL, echo=False)  # echo=True для дебага
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Создаёт таблицы, если их нет."""
    Base.metadata.create_all(engine)

def get_session():
    return SessionLocal()