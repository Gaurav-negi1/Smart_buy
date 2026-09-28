from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "smartbuy.db")
Base    = declarative_base()
engine  = create_engine(f"sqlite:///{DB_PATH}", echo=False)
Session = sessionmaker(bind=engine)

class SearchLog(Base):
    __tablename__ = "search_logs"
    id             = Column(Integer, primary_key=True)
    query          = Column(String)
    best_platform  = Column(String)
    best_score     = Column(Float)
    result_count   = Column(Integer)
    created_at     = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)
