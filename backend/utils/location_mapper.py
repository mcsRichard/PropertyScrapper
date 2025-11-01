# utils/location_mapper.py
# -*- coding: utf-8 -*-
"""
英国地名到邮编映射工具
支持动态查询（使用Nominatim API）和静态字典两种方式
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
    
    # 常见英国大学和地标及其邮编映射（静态备用方案）
    # 格式: {地名: [邮编列表或邮编前缀列表]}
    LOCATION_TO_POSTCODE: Dict[str, List[str]] = {
        # 伦敦地区的大学
        '帝国理工大学': ['SW7', 'SW3'],  # Imperial College London
        'imperial college': ['SW7', 'SW3'],
        'imperial college london': ['SW7', 'SW3'],
        'ic': ['SW7', 'SW3'],
        
        '伦敦大学学院': ['WC1', 'WC2'],  # UCL
        'ucl': ['WC1', 'WC2'],
        'university college london': ['WC1', 'WC2'],
        
        '伦敦政治经济学院': ['WC2'],  # LSE
        'lse': ['WC2'],
        'london school of economics': ['WC2'],
        
        '伦敦国王学院': ['WC2', 'SE1'],  # KCL
        'kcl': ['WC2', 'SE1'],
        'king\'s college london': ['WC2', 'SE1'],
        'kings college london': ['WC2', 'SE1'],
        
        '伦敦大学': ['WC1', 'WC2', 'SE1'],  # 通用
        'london university': ['WC1', 'WC2', 'SE1'],
        
        # 其他城市的大学
        '牛津大学': ['OX1', 'OX2', 'OX3', 'OX4'],  # Oxford University
        'oxford': ['OX1', 'OX2', 'OX3', 'OX4'],
        'oxford university': ['OX1', 'OX2', 'OX3', 'OX4'],
        
        '剑桥大学': ['CB1', 'CB2', 'CB3'],  # Cambridge University
        'cambridge': ['CB1', 'CB2', 'CB3'],
        'cambridge university': ['CB1', 'CB2', 'CB3'],
        
        '曼彻斯特大学': ['M1', 'M13', 'M14'],  # University of Manchester
        'manchester university': ['M1', 'M13', 'M14'],
        'university of manchester': ['M1', 'M13', 'M14'],
        'manchester': ['M1', 'M13', 'M14'],
        
        '伯明翰大学': ['B15', 'B29'],  # University of Birmingham
        'birmingham university': ['B15', 'B29'],
        'university of birmingham': ['B15', 'B29'],
        'birmingham': ['B15', 'B29'],
        
        '爱丁堡大学': ['EH8', 'EH9'],  # University of Edinburgh
        'edinburgh university': ['EH8', 'EH9'],
        'university of edinburgh': ['EH8', 'EH9'],
        'edinburgh': ['EH8', 'EH9'],
        
        # 伦敦地区（通用）
        '伦敦': ['SW', 'SE', 'NW', 'NE', 'E', 'W', 'N', 'WC', 'EC'],
        'london': ['SW', 'SE', 'NW', 'NE', 'E', 'W', 'N', 'WC', 'EC'],
        
        # 伦敦市中心
        '伦敦市中心': ['WC1', 'WC2', 'EC1', 'EC2', 'EC3', 'EC4'],
        'central london': ['WC1', 'WC2', 'EC1', 'EC2', 'EC3', 'EC4'],
        
        # 伦敦各区（部分主要区域）
        '肯辛顿': ['SW7', 'SW5', 'W8'],
        'kensington': ['SW7', 'SW5', 'W8'],
        
        '切尔西': ['SW3', 'SW10'],
        'chelsea': ['SW3', 'SW10'],
        
        '威斯敏斯特': ['SW1', 'W1'],
        'westminster': ['SW1', 'W1'],
        
        '伊斯灵顿': ['N1', 'N7'],
        'islington': ['N1', 'N7'],
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
        优先使用静态字典，如果未找到且启用API，则使用Nominatim API查询
        
        Args:
            location: 地名（如"帝国理工大学"）
            use_api: 是否使用API动态查询（默认True）
        
        Returns:
            邮编列表，如果找不到则返回None
        """
        if not location:
            return None
        
        location_lower = location.lower().strip()
        
        # 首先尝试静态字典
        # 直接匹配
        if location_lower in cls.LOCATION_TO_POSTCODE:
            print(f"[LOCATION-MAPPER] 从静态字典获取: {location} -> {cls.LOCATION_TO_POSTCODE[location_lower]}")
            return cls.LOCATION_TO_POSTCODE[location_lower]
        
        # 模糊匹配（包含关系）
        for key, postcodes in cls.LOCATION_TO_POSTCODE.items():
            if key in location_lower or location_lower in key:
                print(f"[LOCATION-MAPPER] 从静态字典（模糊匹配）获取: {location} -> {postcodes}")
                return postcodes
        
        # 静态字典未找到，尝试API查询
        if use_api:
            return cls._get_postcode_from_nominatim(location)
        
        return None
    
    @classmethod
    def location_to_search_term(cls, location: str, use_api: bool = True) -> str:
        """
        将地名转换为搜索词
        如果找到对应的邮编，返回邮编前缀列表（用逗号分隔）
        否则返回原location
        
        Args:
            location: 地名
            use_api: 是否使用API动态查询（默认True）
        
        Returns:
            搜索词（可能是邮编前缀或多个邮编前缀）
        """
        if not location:
            return location
        
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
        
        # 英国邮编前缀格式通常是：字母+数字，如 SW7, WC1, M1, OX1 等
        import re
        pattern = r'^[A-Z]{1,2}\d{1,2}$'
        return bool(re.match(pattern, term.upper()))

