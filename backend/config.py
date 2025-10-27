# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """数据库配置"""
    # TDSQL-C Serverless 配置
    DB_HOST = os.getenv('DB_HOST', 'your-tdsql-endpoint')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'your-username')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'your-password')
    DB_NAME = os.getenv('DB_NAME', 'properties')
    
    # 数据库连接URL
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # API配置
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # 分页配置
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
