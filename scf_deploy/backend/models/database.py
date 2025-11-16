# models/database.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import Config

# 创建数据库引擎，添加连接池配置以处理长时间运行的任务
engine = create_engine(
    Config.DATABASE_URL, 
    echo=Config.DEBUG,
    pool_pre_ping=True,  # 每次使用前ping数据库，自动重连断开的连接
    pool_recycle=3600,   # 1小时后回收连接，避免连接超时
    pool_size=5,         # 连接池大小
    max_overflow=10      # 允许的额外连接数
)
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
    listing_type = Column(String(20), index=True, default='for_sale')  # for_sale or for_rent
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
    property_id = Column(Integer, ForeignKey('properties.id'), index=True, nullable=False)
    # 原始来源URL（如Zoopla图片地址）
    source_url = Column(String(500))
    # COS访问URL（对外可访问）
    image_url = Column(String(500))
    # COS对象键（用于幂等与定位对象）
    cos_key = Column(String(500))
    # 可选：本地临时保存路径
    image_path = Column(String(500))
    # 在房源图片中的顺序（从0或1开始均可，前端按此排序显示）
    order_index = Column(Integer, default=0, index=True)
    # 主图标记
    is_primary = Column(Boolean, default=False, index=True)
    # 可选：图片尺寸
    width = Column(Integer)
    height = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 去重与查询优化：
    __table_args__ = (
        # 同一房源下的顺序唯一
        UniqueConstraint('property_id', 'order_index', name='uq_property_image_order'),
        # 同一COS对象键全局唯一（若使用内容哈希命名，可确保幂等）
        UniqueConstraint('cos_key', name='uq_property_image_cos_key'),
        # 常用查询索引
        Index('idx_property_id_created', 'property_id', 'created_at')
    )

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
