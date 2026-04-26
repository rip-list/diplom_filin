from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class Question(Base):
    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=False, unique=True)
    answer = Column(String, nullable=False)
    category = Column(String, default='general')   # math, prog, general ...
    subcategory = Column(String, nullable=True)

class Log(Base):
    __tablename__ = 'logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    username = Column(String, nullable=True)
    user_question = Column(String)
    found_answer = Column(String, nullable=True)
    similarity = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)

class AdminLog(Base):
    """Чтобы видеть, когда админ что-то менял"""
    __tablename__ = 'admin_logs'

    id = Column(Integer, primary_key=True)
    action = Column(String)
    details = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)