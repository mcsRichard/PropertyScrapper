# api/properties.py
# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from models.database import get_db
from utils.database import PropertyService
from utils.ai_parser import AISearchParser
from utils.location_mapper import LocationMapper
# 导入OPENAI_SDK_AVAILABLE用于测试
try:
    from utils.ai_parser import OPENAI_SDK_AVAILABLE
except ImportError:
    OPENAI_SDK_AVAILABLE = False
from config import Config
from typing import Dict, Any
import sys
import io
import logging
import traceback

# 设置标准输出编码为UTF-8（解决Windows控制台编码问题）
if sys.platform == 'win32':
    try:
        # 只在需要时设置，避免重复设置导致的问题
        if not hasattr(sys.stdout, '_wrapped'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stdout._wrapped = True
        if not hasattr(sys.stderr, '_wrapped'):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
            sys.stderr._wrapped = True
    except (AttributeError, ValueError, TypeError):
        # 如果已经设置过或设置失败，忽略错误
        pass

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
        sort_by = request.args.get('sort_by')  # 排序字段: 'price', 'created_at', 'updated_at'
        sort_order = request.args.get('sort_order', 'desc')  # 排序方向: 'asc' 或 'desc'
        
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
            listing_type=listing_type,
            sort_by=sort_by,
            sort_order=sort_order
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

@properties_bp.route('/ai-test', methods=['GET'])
def test_ai_config():
    """测试AI API配置（用于验证是否真的调用DeepSeek API）"""
    try:
        parser = AISearchParser()
        
        result = {
            'ai_available': parser.use_ai,
            'api_type': parser.api_type,
            'api_base': parser.api_base if parser.use_ai else None,
            'model': parser.model if parser.use_ai else None,
            'api_key_configured': bool(parser.api_key) if hasattr(parser, 'api_key') else False,
            'sdk_available': OPENAI_SDK_AVAILABLE if parser.api_type == 'openai' else True
        }
        
        # 如果AI可用，尝试一个简单的测试查询
        if parser.use_ai:
            try:
                test_query = "帝国理工附近2室"
                print(f"[AI-TEST] 执行测试查询: {test_query}")
                test_result = parser.parse_query(test_query, 'for_rent')
                result['test_query'] = test_query
                result['test_result'] = test_result
                result['test_success'] = True
            except Exception as e:
                result['test_success'] = False
                result['test_error'] = str(e)
                print(f"[AI-TEST] ❌ 测试查询失败: {e}")
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@properties_bp.route('/ai-search', methods=['POST'])
def ai_search_properties():
    """AI对话式搜索房产。支持 extra_filters（筛选条件）与 AI 解析结果 AND 合并。"""
    try:
        data = request.get_json() or {}
        query = data.get('query', '').strip()
        default_listing_type = data.get('listing_type', 'for_rent')  # 默认出租
        extra_filters = data.get('extra_filters') or {}  # 前端四个筛选条件，与 AI 结果 AND
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        # ========== 调试信息：记录输入参数 ==========
        print("=" * 60)
        print("[AI-SEARCH] 收到搜索请求")
        print(f"[AI-SEARCH] 原始查询: {query}")
        print(f"[AI-SEARCH] 默认listing_type: {default_listing_type}")
        print(f"[AI-SEARCH] extra_filters(AND): {extra_filters}")
        print(f"[AI-SEARCH] 分页参数: page={page}, limit={limit}")
        print("=" * 60)
        
        if not query:
            print("[AI-SEARCH] 错误: 查询为空")
            return jsonify({
                'success': False,
                'error': 'Query is required'
            }), 400
        
        # 限制每页最大数量
        limit = min(limit, 100)
        
        # 使用AI解析器解析查询
        print("[AI-SEARCH] 开始AI解析查询...")
        print(f"[AI-SEARCH] 原始查询: {query}")
        parser = AISearchParser()
        print(f"[AI-SEARCH] AI解析器状态: use_ai={parser.use_ai}, api_type={parser.api_type}")
        if parser.use_ai:
            print(f"[AI-SEARCH] ✅ 将使用 {parser.api_type.upper()} API 进行解析")
        else:
            print(f"[AI-SEARCH] ⚠️ 将使用正则表达式降级解析（AI API不可用）")
        filters = parser.parse_query(query, default_listing_type)
        
        # 检查AI是否提取了location
        if not filters.get('location'):
            print("[AI-SEARCH] ⚠️ 警告: AI解析器未提取到location，原始查询可能是纯邮编")
            # 如果查询看起来像邮编，直接使用
            cleaned_query = query.strip().upper().replace(',', '').replace('.', '')
            if LocationMapper.is_postcode_prefix(cleaned_query):
                print(f"[AI-SEARCH] ✅ 检测到查询本身是邮编格式，使用: {cleaned_query}")
                filters['location'] = cleaned_query
        
        # ========== 调试信息：显示AI解析结果 ==========
        radius_meters = filters.get('radius_meters')
        if radius_meters is not None:
            try:
                radius_meters = int(radius_meters)
            except (TypeError, ValueError):
                radius_meters = None
        print("[AI-SEARCH] AI解析结果:")
        print(f"  - listing_type: {filters.get('listing_type')}")
        print(f"  - bedrooms: {filters.get('bedrooms')}")
        print(f"  - property_type: {filters.get('property_type')}")
        print(f"  - min_price: {filters.get('min_price')}")
        print(f"  - max_price: {filters.get('max_price')}")
        print(f"  - location (原始): {filters.get('location')}")
        print(f"  - radius_meters: {radius_meters}")
        
        # 处理location：将地名转换为邮编（支持动态API查询）。若有 radius_meters，优先用更窄邮编（如 UCL+500m -> WC1E）
        original_location = filters.get('location')
        if original_location:
            print(f"[AI-SEARCH] 尝试将地名转换为邮编: {original_location}" + (f"（半径 {radius_meters}m）" if radius_meters else ""))
            
            cleaned_location = original_location.strip().replace(',', '').replace('.', '')
            
            if LocationMapper.is_postcode_prefix(cleaned_location):
                print(f"[AI-SEARCH] ✅ 检测到邮编格式，直接使用: {cleaned_location}")
                filters['location'] = cleaned_location
            else:
                print(f"[AI-SEARCH] 尝试映射地名: {original_location}")
                mapped_location = LocationMapper.location_to_search_term(
                    original_location, use_api=True, radius_meters=radius_meters
                )
                
                if mapped_location != original_location:
                    print(f"[AI-SEARCH] ✅ 地名映射成功: {original_location} -> {mapped_location}")
                    filters['location'] = mapped_location
                    filters['original_location'] = original_location
                else:
                    print(f"[AI-SEARCH] ⚠️ 未找到邮编映射，使用原始location进行模糊搜索: {original_location}")
                    filters['location'] = original_location
        
        if radius_meters is not None:
            filters['radius_meters'] = radius_meters
        print(f"  - location (最终): {filters.get('location')}")
        print("-" * 60)
        
        # 与 extra_filters（四个筛选条件）AND 合并：有则覆盖 AI 结果
        if extra_filters:
            if 'min_price' in extra_filters and (extra_filters.get('min_price') is not None and extra_filters.get('min_price') != ''):
                filters['min_price'] = int(extra_filters['min_price'])
            if 'max_price' in extra_filters and (extra_filters.get('max_price') is not None and extra_filters.get('max_price') != ''):
                filters['max_price'] = int(extra_filters['max_price'])
            if extra_filters.get('property_type'):
                filters['property_type'] = extra_filters['property_type']
            if extra_filters.get('bedrooms') is not None and extra_filters.get('bedrooms') != '':
                b = extra_filters['bedrooms']
                filters['bedrooms'] = int(b) if isinstance(b, (int, float)) else b
            if extra_filters.get('listing_type'):
                filters['listing_type'] = extra_filters['listing_type']
        sort_by = extra_filters.get('sort_by')
        sort_order = (extra_filters.get('sort_order') or 'desc')
        
        # 获取数据库会话
        db: Session = next(get_db())
        property_service = PropertyService(db)
        
        # ========== 调试信息：显示数据库查询参数 ==========
        print("[AI-SEARCH] 执行数据库查询（AI + extra_filters AND），参数:")
        print(f"  - page: {page}, limit: {limit}")
        print(f"  - min_price: {filters.get('min_price')}")
        print(f"  - max_price: {filters.get('max_price')}")
        print(f"  - property_type: {filters.get('property_type')}")
        print(f"  - bedrooms: {filters.get('bedrooms')}")
        print(f"  - location: {filters.get('location')}")
        location_type = '邮编格式' if filters.get('location') and LocationMapper.is_postcode_prefix(filters.get('location')) else '地名格式'
        print(f"  - location类型: {location_type}")
        print(f"  - listing_type: {filters.get('listing_type')}")
        print(f"  - sort_by: {sort_by}, sort_order: {sort_order}")
        
        # 使用解析出的筛选条件（已与 extra_filters 合并）获取房产列表
        result = property_service.get_properties(
            page=page,
            limit=limit,
            min_price=filters.get('min_price'),
            max_price=filters.get('max_price'),
            property_type=filters.get('property_type'),
            bedrooms=filters.get('bedrooms'),
            location=filters.get('location'),
            listing_type=filters.get('listing_type'),
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # ========== 调试信息：显示查询结果 ==========
        print("[AI-SEARCH] 数据库查询结果:")
        print(f"  - 找到房产数量: {result['total']}")
        print(f"  - 当前页: {result['page']}/{result['pages']}")
        print(f"  - 本页返回: {len(result['properties'])} 条")
        
        # 如果找不到结果，进行数据库诊断
        if result['total'] == 0 and filters.get('location'):
            print("[AI-SEARCH] 🔍 开始数据库诊断...")
            from backend.models.database import Property
            
            # 诊断1: 检查是否有该location的房产（不限listing_type）
            location_diagnosis = db.query(Property).filter(
                Property.postcode.ilike(f"{filters.get('location').upper()}%")
            ).count()
            print(f"[AI-SEARCH] 📊 诊断1 - 数据库中postcode以'{filters.get('location').upper()}'开头的房产总数（不限listing_type）: {location_diagnosis}")
            
            # 诊断2: 检查是否有该listing_type的房产（不限location）
            listing_diagnosis = db.query(Property).filter(
                Property.listing_type == filters.get('listing_type')
            ).count()
            print(f"[AI-SEARCH] 📊 诊断2 - 数据库中listing_type='{filters.get('listing_type')}'的房产总数（不限location）: {listing_diagnosis}")
            
            # 诊断3: 检查是否有同时满足两个条件的房产
            combined_diagnosis = db.query(Property).filter(
                Property.postcode.ilike(f"{filters.get('location').upper()}%"),
                Property.listing_type == filters.get('listing_type')
            ).count()
            print(f"[AI-SEARCH] 📊 诊断3 - 同时满足location和listing_type的房产数: {combined_diagnosis}")
            
            # 诊断4: 显示几个实际的postcode示例（如果存在）
            if location_diagnosis > 0:
                sample_postcodes = db.query(Property.postcode).filter(
                    Property.postcode.ilike(f"{filters.get('location').upper()}%")
                ).limit(5).all()
                print(f"[AI-SEARCH] 📋 示例postcode（前5个）: {[p[0] for p in sample_postcodes]}")
            
            # 诊断5: 检查listing_type分布
            if location_diagnosis > 0:
                listing_types = db.query(Property.listing_type, db.func.count(Property.id)).filter(
                    Property.postcode.ilike(f"{filters.get('location').upper()}%")
                ).group_by(Property.listing_type).all()
                print(f"[AI-SEARCH] 📊 该location的listing_type分布: {dict(listing_types)}")
        
        if result['total'] == 0:
            print("[AI-SEARCH] ⚠️ 警告: 未找到匹配的房产，可能的原因:")
            print("  1. 筛选条件过于严格")
            print("  2. 数据库中确实没有符合条件的房产")
            print("  3. location/邮编映射可能不准确")
            print("  4. 邮编格式可能不正确（应使用前缀如'N10'而不是完整邮编）")
            # 显示实际使用的筛选条件
            print("[AI-SEARCH] 实际使用的筛选条件:")
            active_filters = {k: v for k, v in filters.items() if v is not None}
            
            # 如果使用了邮编格式的location，显示查询SQL提示
            if filters.get('location') and LocationMapper.is_postcode_prefix(filters.get('location')):
                print(f"[AI-SEARCH] 📍 邮编查询: 搜索 postcode LIKE '{filters.get('location').upper()}%'")
                print(f"[AI-SEARCH] 💡 提示: 数据库中应存在以'{filters.get('location').upper()}'开头的邮编")
            for key, value in active_filters.items():
                print(f"    {key}: {value}")
        else:
            print("[AI-SEARCH] ✅ 成功找到房产")
        
        print("=" * 60)
        
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
                'description_chinese': prop.description_chinese,
                'url': prop.url,
                'image_url': prop.image_url,
                'created_at': prop.created_at.isoformat() if prop.created_at else None,
                'updated_at': prop.updated_at.isoformat() if prop.updated_at else None
            })
        
        # 准备返回的filters（用于前端显示）
        display_filters = filters.copy()
        # 如果location被映射了，返回时使用原始location以便显示
        if 'original_location' in filters:
            display_filters['location'] = filters['original_location']
            display_filters['postcode_prefixes'] = filters['location']  # 保留邮编前缀供调试
        
        # 构建详细的调试信息
        loc = filters.get('location')
        is_pc = loc and LocationMapper.is_postcode_prefix(loc)
        debug_info = {
            'total_found': result['total'],
            'search_location': loc,
            'original_location': filters.get('original_location') or loc,
            'location_type': '邮编格式' if is_pc else '地名格式',
            'radius_meters': filters.get('radius_meters'),
            'all_filters': filters,
            'query_params': {
                'page': page,
                'limit': limit,
                'min_price': filters.get('min_price'),
                'max_price': filters.get('max_price'),
                'property_type': filters.get('property_type'),
                'bedrooms': filters.get('bedrooms'),
                'listing_type': filters.get('listing_type'),
            },
            'sql_hint': None,
            'diagnosis': {}
        }
        
        # 如果使用了邮编格式，添加SQL提示（含 radius 时可能为紧邻邮编如 WC1E）
        if loc and (is_pc or (filters.get('radius_meters') and ',' not in loc)):
            debug_info['sql_hint'] = f"查询: postcode ILIKE '{loc.upper()}%'"
            if filters.get('radius_meters'):
                debug_info['sql_hint'] += f"（已按 周围{filters['radius_meters']}米 使用更窄邮编）"
            
            # 添加诊断信息到debug_info
            if result['total'] == 0:
                from backend.models.database import Property
                location_count = db.query(Property).filter(
                    Property.postcode.ilike(f"{filters.get('location').upper()}%")
                ).count()
                listing_count = db.query(Property).filter(
                    Property.listing_type == filters.get('listing_type')
                ).count()
                combined_count = db.query(Property).filter(
                    Property.postcode.ilike(f"{filters.get('location').upper()}%"),
                    Property.listing_type == filters.get('listing_type')
                ).count()
                
                debug_info['diagnosis'] = {
                    'location_count_all_types': location_count,
                    'listing_type_count_all_locations': listing_count,
                    'combined_count': combined_count,
                    'suggestion': f"数据库中有{location_count}条N10的房产，{listing_count}条{filters.get('listing_type')}类型的房产，但组合查询结果为0"
                }
        
        return jsonify({
            'success': True,
            'data': {
                'properties': properties_data,
                'pagination': {
                    'page': result['page'],
                    'limit': result['limit'],
                    'total': result['total'],
                    'pages': result['pages']
                },
                'filters': display_filters,  # 返回解析出的筛选条件，供前端显示
                'query': query,  # 返回原始查询
                'debug_info': debug_info  # 详细的调试信息
            }
        })
        
    except Exception as e:
        print("[AI-SEARCH] ❌ 发生错误:")
        print(f"[AI-SEARCH] 错误类型: {type(e).__name__}")
        print(f"[AI-SEARCH] 错误信息: {str(e)}")
        print("[AI-SEARCH] 错误堆栈:")
        traceback.print_exc()
        print("=" * 60)
        return jsonify({
            'success': False,
            'error': str(e),
            'debug_info': {
                'error_type': type(e).__name__,
                'traceback': traceback.format_exc() if Config.DEBUG else None
            }
        }), 500
