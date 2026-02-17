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
    SECRET_KEY = os.getenv('SECRET_KEY', 'property-scrapper-secret')
    
    # 分页配置
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # 腾讯云COS配置
    COS_SECRET_ID = os.getenv('COS_SECRET_ID', '')
    COS_SECRET_KEY = os.getenv('COS_SECRET_KEY', '')
    COS_REGION = os.getenv('COS_REGION', 'ap-shanghai')
    COS_BUCKET = os.getenv('COS_BUCKET', 'your-bucket-name')
    COS_DOMAIN = os.getenv('COS_DOMAIN', '')  # 可选：自定义域名
    
    # AI搜索功能配置（默认使用DeepSeek，国内更稳定）
    AI_API_TYPE = os.getenv('AI_API_TYPE', 'deepseek')  # 'deepseek' 或 'openai'
    
    # DeepSeek API配置（推荐，国内用户更稳定）
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')  # DeepSeek API密钥
    DEEPSEEK_API_BASE = os.getenv('DEEPSEEK_API_BASE', 'https://api.deepseek.com')  # DeepSeek API地址
    DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')  # DeepSeek模型名称
    
    # OpenAI API配置（可选，如果使用OpenAI）
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')  # OpenAI API密钥
    OPENAI_API_BASE = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')  # OpenAI API地址
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')  # OpenAI模型名称

    WECHAT_APP_ID = os.getenv('WECHAT_APP_ID', 'wx626ba8df3b4edb7b')
    WECHAT_APP_SECRET = os.getenv('WECHAT_APP_SECRET', '2d5eaccaf4a6f28ec7c254ce608825c3')
    AUTH_TOKEN_EXPIRES = int(os.getenv('AUTH_TOKEN_EXPIRES', 86400))

    # 用户功能配置
    DAILY_CONTACT_LIMIT = int(os.getenv('DAILY_CONTACT_LIMIT', 5))
    _developer_openids = os.getenv('DEVELOPER_OPENIDS', '').strip()
    DEVELOPER_OPENIDS = [x.strip() for x in _developer_openids.split(',') if x.strip()]