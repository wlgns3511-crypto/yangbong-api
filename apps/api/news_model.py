from sqlalchemy import Column, Integer, String, DateTime, Text, create_engine, desc
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()

class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True)
    title = Column(String(300))
    link = Column(String(500), unique=True, index=True)
    source = Column(String(100))
    summary = Column(Text)
    thumbnail = Column(String(500))
    category = Column(String(20), index=True)
    published_at = Column(DateTime, default=datetime.utcnow)
    views = Column(Integer, default=0)
    score = Column(Integer, default=0)

DB_URL = "sqlite:///./news.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)

