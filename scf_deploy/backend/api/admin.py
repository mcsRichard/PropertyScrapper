# api/admin.py
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from models.database import get_db
from utils.database import PropertyService
import csv
import io

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/import-properties', methods=['POST'])
def import_properties():
    """导入房产数据"""
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # 读取CSV文件
        if file.filename.endswith('.csv'):
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_input = csv.DictReader(stream)
            
            db: Session = next(get_db())
            property_service = PropertyService(db)
            
            imported_count = 0
            skipped_count = 0
            errors = []
            
            for row in csv_input:
                try:
                    # 检查是否已存在
                    existing = property_service.get_property_by_url(row.get('url', ''))
                    if existing:
                        skipped_count += 1
                        continue
                    
                    # 创建房产记录
                    property_service.create_property(row)
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {imported_count + skipped_count + 1}: {str(e)}")
                    skipped_count += 1
            
            return jsonify({
                'success': True,
                'data': {
                    'imported': imported_count,
                    'skipped': skipped_count,
                    'errors': errors
                }
            })
        
        else:
            return jsonify({
                'success': False,
                'error': 'Only CSV files are supported'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/properties/<int:property_id>', methods=['PUT'])
def update_property(property_id: int):
    """更新房产数据"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        db: Session = next(get_db())
        property_service = PropertyService(db)
        
        property_obj = property_service.get_property_by_id(property_id)
        if not property_obj:
            return jsonify({
                'success': False,
                'error': 'Property not found'
            }), 404
        
        # 更新字段
        for key, value in data.items():
            if hasattr(property_obj, key):
                setattr(property_obj, key, value)
        
        # 重新计算派生字段
        if 'price' in data:
            property_obj.price_numeric = property_service._extract_price_numeric(data['price'])
        if 'title' in data:
            property_obj.property_type = property_service._extract_property_type(data['title'])
            property_obj.bedrooms = property_service._extract_bedrooms(data['title'])
        
        db.commit()
        db.refresh(property_obj)
        
        return jsonify({
            'success': True,
            'data': {
                'id': property_obj.id,
                'title': property_obj.title,
                'price': property_obj.price,
                'updated_at': property_obj.updated_at.isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/properties/<int:property_id>', methods=['DELETE'])
def delete_property(property_id: int):
    """删除房产数据"""
    try:
        db: Session = next(get_db())
        property_service = PropertyService(db)
        
        property_obj = property_service.get_property_by_id(property_id)
        if not property_obj:
            return jsonify({
                'success': False,
                'error': 'Property not found'
            }), 404
        
        db.delete(property_obj)
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Property deleted successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/stats', methods=['GET'])
def get_stats():
    """获取统计信息"""
    try:
        db: Session = next(get_db())
        property_service = PropertyService(db)
        
        # 获取总数
        total_properties = db.query(Property).count()
        
        # 获取最新更新时间
        latest_property = db.query(Property).order_by(Property.updated_at.desc()).first()
        last_updated = latest_property.updated_at.isoformat() if latest_property else None
        
        # 获取筛选选项
        filters = property_service.get_filter_options()
        
        return jsonify({
            'success': True,
            'data': {
                'total_properties': total_properties,
                'last_updated': last_updated,
                'filters': filters
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
