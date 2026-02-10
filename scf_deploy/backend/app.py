# app.py
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from config import Config
from models.database import create_tables
from api.properties import properties_bp
from api.admin import admin_bp
from api.auth import auth_bp
from api.user import users_bp

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 修复代理头，让 Flask 正确识别 HTTPS（解决云函数重定向到 HTTP 的问题）
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # 全局禁用尾部斜杠严格检查（解决 308 重定向问题）
    app.url_map.strict_slashes = False
    
    # 配置CORS
    CORS(app, origins=['*'])
    
    # 注册蓝图
    app.register_blueprint(properties_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    
    # 健康检查接口
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'message': 'Property API is running'
        })
    
    # 根路径
    @app.route('/', methods=['GET'])
    def root():
        return jsonify({
            'message': 'Property Scraper API',
            'version': '1.0.0',
            'endpoints': {
                'properties': '/api/properties',
                'admin': '/api/admin',
                'health': '/health'
            }
        })
    
    return app

def init_database():
    """初始化数据库"""
    try:
        create_tables()
        print("[SUCCESS] Database initialized successfully")
    except Exception as e:
        print(f"[ERROR] Database initialization failed: {e}")
        raise

if __name__ == '__main__':
    # 初始化数据库
    init_database()
    
    # 创建应用
    app = create_app()
    
    # 启动应用
    print(f"[INFO] Starting Property API server on {Config.API_HOST}:{Config.API_PORT}")
    app.run(host=Config.API_HOST, port=Config.API_PORT, debug=Config.DEBUG)
