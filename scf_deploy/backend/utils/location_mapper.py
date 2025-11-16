# utils/location_mapper.py
# -*- coding: utf-8 -*-
"""
英国地名到邮编映射工具
完全使用Nominatim API动态查询，支持全英国任何地区
"""
from typing import List, Optional, Dict
import requests
import time
import os

class LocationMapper:
    """地名到邮编映射器"""
    
    # Nominatim API配置（OpenStreetMap免费地理编码服务，国内可访问）
    NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org/search"
    NOMINATIM_TIMEOUT = 5  # 请求超时时间（秒）
    
    # 请求延迟（避免触发API限流）
    REQUEST_DELAY = 1.0  # 秒
    
    # 缓存文件路径
    CACHE_FILE = os.path.join(os.path.dirname(__file__), '..', 'location_cache.json')
    
    # 静态缓存（内存缓存）
    _memory_cache: Dict[str, Optional[List[str]]] = {}
    _last_request_time = 0
    
    # 常见地标到邮编的静态映射（优先使用，避免API调用延迟）
    # 格式: {地名关键词: [邮编前缀列表]}
    LANDMARK_POSTCODE_MAP = {
        # 剑桥大学及学院
        'trinity college cambridge': ['CB2'],
        'trinity college': ['CB2'],  # 剑桥三一学院
        '剑桥三一学院': ['CB2'],
        '三一学院': ['CB2'],
        'cambridge university': ['CB2', 'CB3'],
        'cambridge': ['CB2', 'CB3'],  # 剑桥市
        '剑桥大学': ['CB2', 'CB3'],
        '剑桥': ['CB2', 'CB3'],
        
        # 伦敦大学
        'imperial college london': ['SW7'],
        'imperial college': ['SW7'],
        '帝国理工大学': ['SW7'],
        '帝国理工': ['SW7'],
        '帝国': ['SW7'],
        'ic': ['SW7'],
        
        'ucl': ['WC1'],
        'london university college': ['WC1'],
        '伦敦大学': ['WC1'],
        
        'lse': ['WC2'],
        'london school of economics': ['WC2'],
        '伦敦政治经济学院': ['WC2'],
        
        'kcl': ['WC2'],
        "king's college london": ['WC2'],
        '国王学院': ['WC2'],
        
        # 牛津大学
        'oxford university': ['OX1', 'OX2'],
        'oxford': ['OX1', 'OX2'],
        '牛津大学': ['OX1', 'OX2'],
        '牛津': ['OX1', 'OX2'],
    }
    
    @classmethod
    def _get_postcode_from_nominatim(cls, location: str) -> Optional[List[str]]:
        """
        使用Nominatim API动态查询地名对应的邮编
        
        Args:
            location: 地名
        
        Returns:
            邮编前缀列表，如果查询失败则返回None
        """
        # 检查内存缓存
        cache_key = location.lower().strip()
        if cache_key in cls._memory_cache:
            print(f"[LOCATION-MAPPER] 从内存缓存获取: {location} -> {cls._memory_cache[cache_key]}")
            return cls._memory_cache[cache_key]
        
        # 控制请求频率（避免触发API限流）
        current_time = time.time()
        time_since_last = current_time - cls._last_request_time
        if time_since_last < cls.REQUEST_DELAY:
            sleep_time = cls.REQUEST_DELAY - time_since_last
            time.sleep(sleep_time)
        cls._last_request_time = time.time()
        
        try:
            print(f"[LOCATION-MAPPER] 使用Nominatim API查询: {location}")
            
            # 构建查询参数（添加"UK"或"London"提高准确性）
            query_text = f"{location}, UK" if 'london' not in location.lower() else f"{location}, London, UK"
            
            params = {
                'q': query_text,
                'format': 'json',
                'limit': 5,  # 限制返回结果数量
                'addressdetails': 1,  # 需要详细地址信息
                'countrycodes': 'gb',  # 限制在英国
                'accept-language': 'en'
            }
            
            headers = {
                'User-Agent': 'UKPropertySearch/1.0'  # Nominatim要求设置User-Agent
            }
            
            response = requests.get(
                cls.NOMINATIM_BASE_URL,
                params=params,
                headers=headers,
                timeout=cls.NOMINATIM_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data and len(data) > 0:
                    # 提取邮编
                    postcodes = []
                    for item in data:
                        address = item.get('address', {})
                        postcode = address.get('postcode', '')
                        
                        if postcode:
                            # 提取邮编前缀
                            # 英国邮编格式通常是：SW7 2AZ, WC1N 1AZ, M1 1AA 等
                            # 前缀通常是空格前的部分，或者前2-4个字符
                            if ' ' in postcode:
                                # 有空格，取空格前的部分（例如"SW7 2AZ" -> "SW7"）
                                postcode_prefix = postcode.split()[0]
                            elif len(postcode) >= 2:
                                # 没有空格，根据长度判断
                                # 如果长度>=4且第3个字符是数字，可能是"M1 1AA"这种格式
                                if len(postcode) >= 4 and postcode[2].isdigit():
                                    postcode_prefix = postcode[:3]  # 例如"M1 1" -> "M1"
                                elif len(postcode) >= 3 and postcode[2].isdigit():
                                    postcode_prefix = postcode[:3]  # 例如"SW7" -> "SW7"
                                else:
                                    postcode_prefix = postcode[:2]  # 例如"SW" -> "SW"
                            else:
                                postcode_prefix = postcode
                            
                            # 标准化邮编前缀并去重
                            postcode_prefix = postcode_prefix.upper().strip()
                            if postcode_prefix and postcode_prefix not in postcodes:
                                postcodes.append(postcode_prefix)
                    
                    if postcodes:
                        print(f"[LOCATION-MAPPER] ✅ 成功查询到邮编: {location} -> {postcodes}")
                        # 存入内存缓存
                        cls._memory_cache[cache_key] = postcodes
                        return postcodes
                    else:
                        print(f"[LOCATION-MAPPER] ⚠️ 未找到邮编: {location}")
                        cls._memory_cache[cache_key] = None
                        return None
                else:
                    print(f"[LOCATION-MAPPER] ⚠️ 未找到结果: {location}")
                    cls._memory_cache[cache_key] = None
                    return None
            else:
                print(f"[LOCATION-MAPPER] ❌ API请求失败: HTTP {response.status_code}")
                cls._memory_cache[cache_key] = None
                return None
                
        except requests.exceptions.Timeout:
            print(f"[LOCATION-MAPPER] ❌ 请求超时: {location}")
            cls._memory_cache[cache_key] = None
            return None
        except requests.exceptions.RequestException as e:
            print(f"[LOCATION-MAPPER] ❌ 请求异常: {e}")
            cls._memory_cache[cache_key] = None
            return None
        except Exception as e:
            print(f"[LOCATION-MAPPER] ❌ 未知错误: {e}")
            cls._memory_cache[cache_key] = None
            return None
    
    @classmethod
    def get_postcodes(cls, location: str, use_api: bool = True) -> Optional[List[str]]:
        """
        根据地名获取对应的邮编列表
        优先使用静态映射，如果找不到则使用Nominatim API动态查询
        
        Args:
            location: 地名（如"帝国理工大学"、"剑桥三一学院"）
            use_api: 是否使用API动态查询（默认True）
        
        Returns:
            邮编列表，如果找不到则返回None
        """
        if not location:
            return None
        
        # 清理location（去除空格、标点，转换为小写）
        location_clean = location.strip().lower().replace(',', '').replace('.', '').replace('附近', '').replace('周边', '').strip()
        
        # 首先检查静态映射（优先，快速）
        # 按关键词长度排序，优先匹配更具体的关键词（更长的在前）
        sorted_landmarks = sorted(cls.LANDMARK_POSTCODE_MAP.items(), key=lambda x: len(x[0]), reverse=True)
        
        for landmark, postcodes in sorted_landmarks:
            # 检查完整匹配或包含关系
            if landmark == location_clean or landmark in location_clean or location_clean in landmark:
                # 额外检查：如果是"cambridge"这样的通用词，只有在没有更具体的匹配时才使用
                if landmark == 'cambridge' and any('trinity' in location_clean or '三一' in location_clean):
                    continue  # 跳过通用词，继续查找更具体的匹配
                print(f"[LOCATION-MAPPER] ✅ 从静态映射找到: {location} -> {postcodes} (匹配关键词: {landmark})")
                return postcodes
        
        # 如果禁用API，返回None
        if not use_api:
            return None
        
        # 使用API查询
        return cls._get_postcode_from_nominatim(location)
    
    @classmethod
    def location_to_search_term(cls, location: str, use_api: bool = True) -> str:
        """
        将地名转换为搜索词
        使用API查询邮编，如果找到则返回邮编前缀列表（用逗号分隔）
        否则返回原location
        
        Args:
            location: 地名
            use_api: 是否使用API动态查询（默认True）
        
        Returns:
            搜索词（可能是邮编前缀或多个邮编前缀）
        """
        if not location:
            return location
        
        # 如果是邮编格式，直接返回
        if cls.is_postcode_prefix(location):
            return location
        
        # 使用API查询
        postcodes = cls.get_postcodes(location, use_api=use_api)
        
        if postcodes:
            # 返回邮编前缀列表，用逗号分隔，用于SQL LIKE查询
            # 例如: "SW7,SW3" 可以用来搜索 "SW7%" 或 "SW3%"
            return ','.join(postcodes)
        
        return location
    
    @classmethod
    def is_postcode_prefix(cls, term: str) -> bool:
        """
        判断一个字符串是否为邮编前缀格式
        
        Args:
            term: 待判断的字符串
        
        Returns:
            是否为邮编前缀
        """
        if not term:
            return False
        
        term = term.strip().upper()
        
        # 英国邮编前缀格式：
        # - 1-2个字母 + 1-2个数字，如: N10, SW7, WC1, M1, OX1, E14 等
        # - 或者纯字母（较少见），如: SW, SE, N, E, W 等
        import re
        
        # 标准格式：1-2字母 + 1-2数字（如 N10, SW7, E14）
        pattern1 = r'^[A-Z]{1,2}\d{1,2}$'
        if re.match(pattern1, term):
            return True
        
        # 纯字母格式：1-2个字母（如 N, SW, SE）
        pattern2 = r'^[A-Z]{1,2}$'
        if re.match(pattern2, term):
            return True
        
        return False

