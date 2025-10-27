# models/database.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import Config

# 创建数据库引擎
engine = create_engine(Config.DATABASE_URL, echo=Config.DEBUG)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Property(Base):
    """房产模型"""
    __tablename__ = "properties"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    price = Column(String(50), nullable=False)
    price_numeric = Column(Integer, index=True)  # 用于排序和筛选
    area = Column(String(100))
    bedrooms = Column(Integer, index=True)
    bathrooms = Column(Integer)
    property_type = Column(String(100), index=True)  # flat, house, etc.
    location = Column(String(255), index=True)
    postcode = Column(String(20), index=True)
    description = Column(Text)
    description_chinese = Column(Text)
    url = Column(String(500), unique=True, index=True)
    image_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PropertyImage(Base):
    """房产图片模型"""
    __tablename__ = "property_images"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, index=True)
    image_url = Column(String(500))
    image_path = Column(String(500))  # 本地存储路径
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Location(Base):
    """区域模型"""
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    region = Column(String(100), index=True)
    postcode = Column(String(20), index=True)
    coordinates = Column(String(50))  # lat,lng

def create_tables():
    """创建所有表"""
    Base.metadata.create_all(bind=engine)
    print("[INFO] Database tables created successfully")

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 数据库操作类
class DatabaseManager:
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def get_session(self):
        return self.SessionLocal()
    
    def close_session(self, session):
        session.close()
