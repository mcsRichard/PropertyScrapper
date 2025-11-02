# utils/database.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from models.database import Property, PropertyImage, Location, DatabaseManager
from typing import List, Optional, Dict, Any
import re

class PropertyService:
    """房产服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_property(self, property_data: Dict[str, Any]) -> Property:
        """创建房产记录"""
        # 提取数字价格用于排序
        price_numeric = self._extract_price_numeric(property_data.get('price', ''))
        
        # 提取房产类型
        property_type = self._extract_property_type(property_data.get('title', ''))
        
        # 提取卧室数量
        bedrooms = self._extract_bedrooms(property_data.get('title', ''))
        
        property_obj = Property(
            title=property_data.get('title'),
            price=property_data.get('price'),
            price_numeric=price_numeric,
            area=property_data.get('area'),
            bedrooms=bedrooms,
            bathrooms=property_data.get('bathrooms'),
            property_type=property_type,
            listing_type=property_data.get('listing_type', 'for_sale'),
            location=property_data.get('location'),
            postcode=property_data.get('postcode'),
            description=property_data.get('description'),
            description_chinese=property_data.get('description_chinese'),
            url=property_data.get('url'),
            image_url=property_data.get('image_url')
        )
        
        self.db.add(property_obj)
        self.db.commit()
        self.db.refresh(property_obj)
        return property_obj
    
    def get_properties(self, 
                      page: int = 1, 
                      limit: int = 20,
                      min_price: Optional[int] = None,
                      max_price: Optional[int] = None,
                      property_type: Optional[str] = None,
                      bedrooms: Optional[int] = None,
                      location: Optional[str] = None,
                      listing_type: Optional[str] = None) -> Dict[str, Any]:
        """获取房产列表"""
        query = self.db.query(Property)
        
        # 应用筛选条件
        if min_price:
            query = query.filter(Property.price_numeric >= min_price)
        if max_price:
            query = query.filter(Property.price_numeric <= max_price)
        if property_type:
            query = query.filter(Property.property_type.ilike(f"%{property_type}%"))
        if bedrooms:
            query = query.filter(Property.bedrooms == bedrooms)
        if location:
            # 检查是否是邮编格式
            from backend.utils.location_mapper import LocationMapper
            is_postcode = LocationMapper.is_postcode_prefix(location)
            
            # 如果location是邮编前缀列表（逗号分隔），分别搜索每个前缀
            if ',' in location:
                postcode_prefixes = [p.strip().upper() for p in location.split(',')]
                postcode_conditions = [Property.postcode.ilike(f"{prefix}%") for prefix in postcode_prefixes]
                query = query.filter(or_(
                    Property.location.ilike(f"%{location.split(',')[0]}%"),  # 保留地名搜索
                    *postcode_conditions
                ))
            elif is_postcode:
                # 邮编格式：使用前缀匹配（更精确）
                location_upper = location.upper().strip()
                print(f"[DATABASE] 邮编格式搜索: {location_upper}")
                query = query.filter(
                    Property.postcode.ilike(f"{location_upper}%")  # 前缀匹配，如"N10"匹配"N10 1AB"
                )
            else:
                # 地名格式：同时搜索location和postcode字段（模糊匹配）
                print(f"[DATABASE] 地名格式搜索: {location}")
                query = query.filter(or_(
                    Property.location.ilike(f"%{location}%"),  # 搜索location字段（地名）
                    Property.postcode.ilike(f"%{location}%")   # 搜索postcode字段（可能包含地名的邮编）
                ))
        if listing_type:
            query = query.filter(Property.listing_type == listing_type)
        
        # 获取总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * limit
        properties = query.order_by(desc(Property.created_at)).offset(offset).limit(limit).all()
        
        return {
            "properties": properties,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    
    def get_property_by_id(self, property_id: int) -> Optional[Property]:
        """根据ID获取房产详情"""
        return self.db.query(Property).filter(Property.id == property_id).first()
    
    def get_property_by_url(self, url: str) -> Optional[Property]:
        """根据URL获取房产"""
        return self.db.query(Property).filter(Property.url == url).first()

    def get_images_by_property_id(self, property_id: int) -> List[PropertyImage]:
        """获取房产所有图片，主图优先，其次按顺序"""
        return (
            self.db.query(PropertyImage)
            .filter(PropertyImage.property_id == property_id)
            .order_by(desc(PropertyImage.is_primary), asc(PropertyImage.order_index), asc(PropertyImage.id))
            .all()
        )

    def upsert_property_image(self, property_id: int, image_data: Dict[str, Any]) -> PropertyImage:
        """插入或更新房产图片（基于 cos_key 或 (property_id, order_index) 幂等）"""
        cos_key = image_data.get('cos_key')
        order_index = image_data.get('order_index', 0)

        query = self.db.query(PropertyImage).filter(PropertyImage.property_id == property_id)
        if cos_key:
            existing = query.filter(PropertyImage.cos_key == cos_key).first()
        else:
            existing = query.filter(PropertyImage.order_index == order_index).first()

        if existing:
            # 更新可变字段
            for k in ['source_url', 'image_url', 'image_path', 'is_primary', 'width', 'height', 'order_index', 'cos_key']:
                if k in image_data and image_data[k] is not None:
                    setattr(existing, k, image_data[k])
            self.db.add(existing)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        new_img = PropertyImage(
            property_id=property_id,
            source_url=image_data.get('source_url'),
            image_url=image_data.get('image_url'),
            image_path=image_data.get('image_path'),
            is_primary=bool(image_data.get('is_primary', False)),
            width=image_data.get('width'),
            height=image_data.get('height'),
            order_index=order_index,
            cos_key=image_data.get('cos_key'),
        )
        self.db.add(new_img)
        self.db.commit()
        self.db.refresh(new_img)
        return new_img
    
    def search_properties(self, keyword: str, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        """搜索房产"""
        query = self.db.query(Property).filter(or_(
            Property.title.ilike(f"%{keyword}%"),
            Property.description.ilike(f"%{keyword}%"),
            Property.description_chinese.ilike(f"%{keyword}%"),
            Property.location.ilike(f"%{keyword}%")
        ))
        
        total = query.count()
        offset = (page - 1) * limit
        properties = query.order_by(desc(Property.created_at)).offset(offset).limit(limit).all()
        
        return {
            "properties": properties,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    
    def get_filter_options(self) -> Dict[str, Any]:
        """获取筛选选项"""
        # 价格范围
        price_range = self.db.query(Property.price_numeric).filter(
            Property.price_numeric.isnot(None)
        ).all()
        prices = [p[0] for p in price_range if p[0]]
        
        # 房产类型
        property_types = self.db.query(Property.property_type).filter(
            Property.property_type.isnot(None)
        ).distinct().all()
        
        # 卧室数量
        bedrooms = self.db.query(Property.bedrooms).filter(
            Property.bedrooms.isnot(None)
        ).distinct().all()
        
        # 区域
        locations = self.db.query(Property.location).filter(
            Property.location.isnot(None)
        ).distinct().all()
        
        return {
            "price_range": {
                "min": min(prices) if prices else 0,
                "max": max(prices) if prices else 0
            },
            "property_types": [pt[0] for pt in property_types if pt[0]],
            "bedrooms": sorted([b[0] for b in bedrooms if b[0]]),
            "locations": [l[0] for l in locations if l[0]]
        }
    
    def _extract_price_numeric(self, price_str: str) -> Optional[int]:
        """提取价格数字"""
        if not price_str:
            return None
        # 移除£符号和逗号
        price_clean = re.sub(r'[£,\s]', '', price_str)
        try:
            return int(price_clean)
        except ValueError:
            return None
    
    def _extract_property_type(self, title: str) -> Optional[str]:
        """从标题中提取房产类型"""
        if not title:
            return None
        
        title_lower = title.lower()
        if 'flat' in title_lower or 'apartment' in title_lower:
            return 'flat'
        elif 'house' in title_lower:
            return 'house'
        elif 'maisonette' in title_lower:
            return 'maisonette'
        elif 'studio' in title_lower:
            return 'studio'
        else:
            return 'other'
    
    def _extract_bedrooms(self, title: str) -> Optional[int]:
        """从标题中提取卧室数量"""
        if not title:
            return None
        
        # 匹配 "X bed" 模式
        match = re.search(r'(\d+)\s*bed', title.lower())
        if match:
            return int(match.group(1))
        return None
