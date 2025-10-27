#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""简化的Flask API服务"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from config import Config
import pymysql

app = Flask(__name__)
CORS(app, origins=['*'])

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset='utf8mb4'
    )

@app.route('/', methods=['GET'])
def root():
    """根路径"""
    return jsonify({
        'message': 'Property Scraper API',
        'version': '1.0.0',
        'endpoints': {
            'properties': '/api/properties',
            'health': '/health'
        }
    })

@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    try:
        conn = get_db_connection()
        conn.close()
        return jsonify({'status': 'healthy'})
    except:
        return jsonify({'status': 'unhealthy'}), 500

@app.route('/api/properties', methods=['GET'])
def get_properties():
    """获取房产列表"""
    try:
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 20)), 100)
        min_price = request.args.get('min_price', type=int)
        max_price = request.args.get('max_price', type=int)
        property_type = request.args.get('property_type', type=str)
        bedrooms = request.args.get('bedrooms', type=int)
        
        print(f"[API] 请求参数: page={page}, limit={limit}, min_price={min_price}, max_price={max_price}, property_type={property_type}, bedrooms={bedrooms}")
        
        offset = (page - 1) * limit
        
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 构建查询条件
        where_clauses = []
        if min_price:
            where_clauses.append(f"price_numeric >= {min_price}")
        if max_price:
            where_clauses.append(f"price_numeric <= {max_price}")
        if property_type:
            where_clauses.append(f"property_type = '{property_type}'")
        if bedrooms:
            where_clauses.append(f"bedrooms = {bedrooms}")
        
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        print(f"[API] SQL查询: SELECT * FROM properties{where_sql}")
        
        # 获取总数
        cursor.execute(f"SELECT COUNT(*) as total FROM properties{where_sql}")
        total = cursor.fetchone()['total']
        
        # 获取数据
        query = f"SELECT * FROM properties{where_sql} ORDER BY created_at DESC LIMIT {limit} OFFSET {offset}"
        cursor.execute(query)
        properties = cursor.fetchall()
        
        # 转换datetime为字符串
        for prop in properties:
            if prop.get('created_at'):
                prop['created_at'] = prop['created_at'].isoformat()
            if prop.get('updated_at'):
                prop['updated_at'] = prop['updated_at'].isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'properties': properties,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'pages': (total + limit - 1) // limit
                }
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/properties/<int:property_id>', methods=['GET'])
def get_property_detail(property_id):
    """获取房产详情"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("SELECT * FROM properties WHERE id = %s", (property_id,))
        property_obj = cursor.fetchone()
        
        if not property_obj:
            return jsonify({'success': False, 'error': 'Property not found'}), 404
        
        if property_obj.get('created_at'):
            property_obj['created_at'] = property_obj['created_at'].isoformat()
        if property_obj.get('updated_at'):
            property_obj['updated_at'] = property_obj['updated_at'].isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': property_obj})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print(f"[INFO] Starting Property API server on {Config.API_HOST}:{Config.API_PORT}")
    app.run(host=Config.API_HOST, port=Config.API_PORT, debug=Config.DEBUG)
