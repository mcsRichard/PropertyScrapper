# api/properties.py
# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from models.database import get_db
from utils.database import PropertyService
from typing import Dict, Any
import sys
import io

# 设置标准输出编码为UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

properties_bp = Blueprint('properties', __name__, url_prefix='/api/properties')

@properties_bp.route('/', methods=['GET'])
def get_properties():
    """获取房产列表"""
    try:
        # 获取查询参数
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        min_price = request.args.get('min_price', type=int)
        max_price = request.args.get('max_price', type=int)
        property_type = request.args.get('property_type')
        bedrooms = request.args.get('bedrooms', type=int)
        location = request.args.get('location')
        listing_type = request.args.get('listing_type')
        
        # 限制每页最大数量
        limit = min(limit, 100)
        
        # 获取数据库会话
        db: Session = next(get_db())
        property_service = PropertyService(db)
        
        # 获取房产列表
        result = property_service.get_properties(
            page=page,
            limit=limit,
            min_price=min_price,
            max_price=max_price,
            property_type=property_type,
            bedrooms=bedrooms,
            location=location,
            listing_type=listing_type
        )
        
        # 转换为字典格式
        properties_data = []
        for prop in result['properties']:
            properties_data.append({
                'id': prop.id,
                'title': prop.title,
                'price': prop.price,
                'price_numeric': prop.price_numeric,
                'area': prop.area,
                'bedrooms': prop.bedrooms,
                'bathrooms': prop.bathrooms,
                'property_type': prop.property_type,
                'listing_type': prop.listing_type,
                'location': prop.location,
                'postcode': prop.postcode,
                'description': prop.description,
                'description_chinese': prop.description_chinese,
                'url': prop.url,
                'image_url': prop.image_url,
                'created_at': prop.created_at.isoformat() if prop.created_at else None,
                'updated_at': prop.updated_at.isoformat() if prop.updated_at else None
            })
        
        return jsonify({
            'success': True,
            'data': {
                'properties': properties_data,
                'pagination': {
                    'page': result['page'],
                    'limit': result['limit'],
                    'total': result['total'],
                    'pages': result['pages']
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@properties_bp.route('/<int:property_id>', methods=['GET'])
def get_property_detail(property_id: int):
    """获取房产详情"""
    try:
        db: Session = next(get_db())
        property_service = PropertyService(db)
        
        property_obj = property_service.get_property_by_id(property_id)
        if not property_obj:
            return jsonify({
                'success': False,
                'error': 'Property not found'
            }), 404
        
        property_data = {
            'id': property_obj.id,
            'title': property_obj.title,
            'price': property_obj.price,
            'price_numeric': property_obj.price_numeric,
            'area': property_obj.area,
            'bedrooms': property_obj.bedrooms,
            'bathrooms': property_obj.bathrooms,
            'property_type': property_obj.property_type,
            'listing_type': property_obj.listing_type,
            'location': property_obj.location,
            'postcode': property_obj.postcode,
            'description': property_obj.description,
            'description_chinese': property_obj.description_chinese,
            'url': property_obj.url,
            'image_url': property_obj.image_url,
            'created_at': property_obj.created_at.isoformat() if property_obj.created_at else None,
            'updated_at': property_obj.updated_at.isoformat() if property_obj.updated_at else None
        }

        # 追加图片列表
        images = property_service.get_images_by_property_id(property_id)
        property_data['images'] = [{
            'id': img.id,
            'source_url': img.source_url,
            'image_url': img.image_url,
            'cos_key': img.cos_key,
            'order_index': img.order_index,
            'is_primary': img.is_primary,
            'width': img.width,
            'height': img.height,
            'created_at': img.created_at.isoformat() if img.created_at else None
        } for img in images]
        
        return jsonify({
            'success': True,
            'data': property_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@properties_bp.route('/search', methods=['GET'])
def search_properties():
    """搜索房产"""
    try:
        keyword = request.args.get('keyword', '')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        if not keyword:
            return jsonify({
                'success': False,
                'error': 'Keyword is required'
            }), 400
        
        db: Session = next(get_db())
        property_service = PropertyService(db)
        
        result = property_service.search_properties(keyword, page, limit)
        
        # 转换为字典格式
        properties_data = []
        for prop in result['properties']:
            properties_data.append({
                'id': prop.id,
                'title': prop.title,
                'price': prop.price,
                'price_numeric': prop.price_numeric,
                'area': prop.area,
                'bedrooms': prop.bedrooms,
                'bathrooms': prop.bathrooms,
                'property_type': prop.property_type,
                'listing_type': prop.listing_type,
                'location': prop.location,
                'postcode': prop.postcode,
                'description': prop.description,
                'description_chinese': prop.description_chinese,
                'url': prop.url,
                'image_url': prop.image_url,
                'created_at': prop.created_at.isoformat() if prop.created_at else None,
                'updated_at': prop.updated_at.isoformat() if prop.updated_at else None
            })
        
        return jsonify({
            'success': True,
            'data': {
                'properties': properties_data,
                'pagination': {
                    'page': result['page'],
                    'limit': result['limit'],
                    'total': result['total'],
                    'pages': result['pages']
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@properties_bp.route('/filters', methods=['GET'])
def get_filter_options():
    """获取筛选选项"""
    try:
        db: Session = next(get_db())
        property_service = PropertyService(db)
        
        filters = property_service.get_filter_options()
        
        return jsonify({
            'success': True,
            'data': filters
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
