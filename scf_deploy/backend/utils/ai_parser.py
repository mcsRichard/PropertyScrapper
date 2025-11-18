# utils/ai_parser.py
# -*- coding: utf-8 -*-
"""
AI自然语言查询解析器
将用户输入的自然语言转换为具体的搜索筛选参数
支持DeepSeek API（推荐，国内更稳定）和OpenAI API（可选）
"""
import os
import json
import re
import sys
import io
from typing import Dict, Any, Optional

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
try:
    from openai import OpenAI
    OPENAI_SDK_AVAILABLE = True
except ImportError:
    OPENAI_SDK_AVAILABLE = False

class AISearchParser:
    """AI搜索解析器"""
    
    def __init__(self, api_key: Optional[str] = None, api_type: Optional[str] = None):
        """
        初始化AI解析器
        Args:
            api_key: API密钥，如果为None则从环境变量获取
            api_type: API类型，'deepseek'（默认）或'openai'，如果为None则从环境变量获取
        """
        self.api_type = (api_type or os.getenv('AI_API_TYPE', 'deepseek')).lower()
        
        # 优先使用DeepSeek（国内更稳定）
        if self.api_type == 'deepseek':
            self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
            # DeepSeek API base_url（OpenAI SDK 会自动添加 /v1 路径）
            default_base = os.getenv('DEEPSEEK_API_BASE', 'https://api.deepseek.com')
            # 移除末尾的 /v1（如果存在），因为 OpenAI SDK 会自动添加
            if default_base.endswith('/v1'):
                self.api_base = default_base[:-3]
            elif default_base.endswith('/v1/'):
                self.api_base = default_base[:-4]
            else:
                self.api_base = default_base.rstrip('/')
            self.model = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
        else:  # OpenAI
            self.api_key = api_key or os.getenv('OPENAI_API_KEY')
            default_base = os.getenv('OPENAI_API_BASE', 'https://api.openai.com')
            # 移除末尾的 /v1（如果存在），因为 OpenAI SDK 会自动添加
            if default_base.endswith('/v1'):
                self.api_base = default_base[:-3]
            elif default_base.endswith('/v1/'):
                self.api_base = default_base[:-4]
            else:
                self.api_base = default_base.rstrip('/')
            self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        
        if OPENAI_SDK_AVAILABLE and self.api_key:
            # DeepSeek API与OpenAI API完全兼容，使用相同的SDK
            # OpenAI SDK 会自动在 base_url 后添加 /v1，所以这里不需要包含 /v1
            try:
                # 直接使用显式创建的 http_client，避免 httpx 版本兼容性问题
                import httpx
                # 创建 httpx 客户端（不传递 proxies 参数，避免兼容性问题）
                http_client = httpx.Client(
                    timeout=60.0,
                    follow_redirects=True
                )
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.api_base,
                    http_client=http_client
                )
            except Exception as e:
                # 如果显式创建 http_client 失败，尝试默认方式
                print(f"[AI-PARSER] ⚠️ 显式创建 http_client 失败: {e}，尝试默认方式")
                try:
                    self.client = OpenAI(
                        api_key=self.api_key,
                        base_url=self.api_base
                    )
                except Exception as e2:
                    print(f"[AI-PARSER] ❌ 默认方式初始化也失败: {e2}")
                    raise e2
            self.use_ai = True
            print(f"[INFO] Using {self.api_type.upper()} API for AI parsing")
        else:
            self.client = None
            self.use_ai = False
            print("[WARNING] AI API not available, using fallback regex parser")
    
    def parse_query(self, query: str, default_listing_type: str = 'for_rent') -> Dict[str, Any]:
        """
        解析自然语言查询为筛选参数
        
        Args:
            query: 用户输入的自然语言查询，例如："帝国理工大学附近2室一厅公寓4000镑以下"
            default_listing_type: 默认的listing_type（for_sale或for_rent）
        
        Returns:
            包含筛选参数的字典
        """
        if self.use_ai:
            return self._parse_with_ai(query, default_listing_type)
        else:
            return self._parse_with_regex(query, default_listing_type)
    
    def _parse_with_ai(self, query: str, default_listing_type: str) -> Dict[str, Any]:
        """使用AI API（DeepSeek或OpenAI）解析查询"""
        try:
            print(f"[AI-PARSER] 使用 {self.api_type.upper()} API 解析查询")
            prompt = f"""你是一个房产搜索助手。用户输入了一段自然语言查询，请将其转换为JSON格式的筛选参数。

可用的筛选参数包括：
- listing_type: "for_sale"（出售）或 "for_rent"（出租）
- bedrooms: 卧室数量（整数，如1、2、3）
  * 注意：用户可能用"2室"、"2居室"、"两室"、"两居室"等表达方式，都要识别为bedrooms=2
  * 常见表达：1室/一室、2室/两室/2居室/两居室、3室/三室/3居室/三居室等
- property_type: "flat"（公寓）、"house"（别墅）、"studio"（单间）、"other"（其他）
- max_price: 最高价格（整数，英镑）
- min_price: 最低价格（整数，英镑）
- location: 位置关键词（字符串，可以是地名如"帝国理工大学"、"伦敦"，也可以是英国邮编如"N10"、"SW7"、"WC1"等）

用户查询：{query}

请分析查询内容，提取出相应的筛选条件。如果查询中没有明确提到某个条件，则不要包含该字段。
对于位置信息：
- 如果提到"附近"、"周边"等，保留地点名称作为location参数
- 常见地点包括：
  * 帝国理工大学（Imperial College London）、帝国理工、帝国大学 -> "imperial college" 或 "imperial college london"
  * 剑桥三一学院、三一学院 -> "trinity college cambridge" 或 "trinity college"
  * 剑桥大学、剑桥 -> "cambridge university" 或 "cambridge"
  * 牛津大学、牛津 -> "oxford university" 或 "oxford"
  * 伦敦大学（UCL/LSE/KCL）-> "ucl"、"lse"、"kcl" 或完整名称
- 如果输入的是英国邮编格式（如"N10"、"SW7"、"WC1"等），直接作为location参数
- 邮编格式通常是：1-2个字母+1-2个数字，或纯字母（如"N10"、"SW7"、"N"、"SW"等）
- 地点简称也要识别，如"帝国理工"应理解为"帝国理工大学"或"Imperial College London"
- 特别注意：如果用户提到"剑桥三一学院附近"，应提取为"trinity college cambridge"或"cambridge"，而不是只提取"cambridge"

只返回JSON格式，不要包含任何其他文字说明。格式示例：
{{"listing_type": "for_rent", "bedrooms": 2, "property_type": "flat", "max_price": 4000, "location": "imperial college"}}
或
{{"location": "N10"}}
或
{{"location": "imperial college", "bedrooms": 2}}

如果无法确定listing_type，使用默认值：{default_listing_type}"""

            print(f"[AI-PARSER] 调用AI API，模型: {self.model}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的房产搜索助手，擅长将自然语言转换为结构化的搜索参数。只返回JSON格式，不包含任何解释文字。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            # 检查响应是否有效
            if not response or not hasattr(response, 'choices') or not response.choices:
                raise ValueError("API响应中没有choices字段或choices为空")
            
            if not response.choices[0].message or not hasattr(response.choices[0].message, 'content'):
                raise ValueError("API响应中没有message.content字段")
            
            result_text = response.choices[0].message.content
            if not result_text:
                raise ValueError("API响应中的content为空")
            
            result_text = result_text.strip()
            print(f"[AI-PARSER] AI API原始响应: {result_text[:200]}...")  # 只显示前200个字符
            
            # 尝试提取JSON（可能包含markdown代码块）
            # 先尝试去掉markdown代码块标记
            if result_text.startswith('```'):
                # 去掉 ```json 或 ``` 标记
                lines = result_text.split('\n')
                result_text = '\n'.join(lines[1:-1]) if lines[-1].strip() == '```' else '\n'.join(lines[1:])
            
            # 尝试直接解析JSON
            try:
                filters = json.loads(result_text)
            except json.JSONDecodeError:
                # 如果直接解析失败，尝试正则提取JSON对象
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result_text = json_match.group(0)
                    try:
                        filters = json.loads(result_text)
                    except json.JSONDecodeError:
                        # 如果正则提取的JSON也无法解析，抛出异常让外层处理
                        raise
                else:
                    # 如果没有找到JSON对象，抛出JSONDecodeError
                    # JSONDecodeError(msg, doc, pos) 格式
                    raise json.JSONDecodeError("No JSON found in response", result_text, 0)
            
            print(f"[AI-PARSER] 提取的JSON: {result_text}")
            print(f"[AI-PARSER] 解析成功，得到筛选条件: {filters}")
            
            # 确保listing_type有默认值
            if 'listing_type' not in filters:
                filters['listing_type'] = default_listing_type
                print(f"[AI-PARSER] 使用默认listing_type: {default_listing_type}")
            
            return filters
            
        except json.JSONDecodeError as e:
            result_text_str = result_text if 'result_text' in locals() else "无法获取"
            print(f"[AI-PARSER] ❌ JSON解析失败: {e}")
            print(f"[AI-PARSER] 原始响应: {result_text_str}")
            print(f"[AI-PARSER] 降级到正则表达式解析")
            return self._parse_with_regex(query, default_listing_type)
        except Exception as e:
            print(f"[AI-PARSER] ❌ AI解析失败: {e}")
            print(f"[AI-PARSER] 错误类型: {type(e).__name__}")
            if 'result_text' in locals():
                print(f"[AI-PARSER] 原始响应: {result_text[:200] if len(result_text) > 200 else result_text}")
            print(f"[AI-PARSER] 降级到正则表达式解析")
            return self._parse_with_regex(query, default_listing_type)
    
    def _parse_with_regex(self, query: str, default_listing_type: str) -> Dict[str, Any]:
        """使用正则表达式作为备用方案解析查询"""
        filters: Dict[str, Any] = {
            'listing_type': default_listing_type
        }
        
        query_lower = query.lower()
        
        # 解析listing_type
        if '出售' in query or 'for_sale' in query_lower or 'sale' in query_lower:
            filters['listing_type'] = 'for_sale'
        elif '出租' in query or 'rent' in query_lower or '租' in query:
            filters['listing_type'] = 'for_rent'
        
        # 解析卧室数量（支持中文和英文）
        bedroom_patterns = [
            r'(\d+)\s*居室',  # 匹配"2居室"、"3居室"等
            r'(\d+)\s*室',
            r'(\d+)\s*bed',
            r'(\d+)\s*bedroom',
            r'(\d+)\s*间',
            r'一室一厅',
            r'两室',
            r'三室',
            r'四室',
            r'五室',
            r'两居室',  # 中文数字+居室
            r'三居室',
            r'四居室',
            r'五居室'
        ]
        
        for pattern in bedroom_patterns:
            match = re.search(pattern, query_lower)
            if match:
                if '一室一厅' in query or '1室' in query or '一居室' in query:
                    filters['bedrooms'] = 1
                elif '两室' in query or '2室' in query or '两居室' in query or '2居室' in query:
                    filters['bedrooms'] = 2
                elif '三室' in query or '3室' in query or '三居室' in query or '3居室' in query:
                    filters['bedrooms'] = 3
                elif '四室' in query or '4室' in query or '四居室' in query or '4居室' in query:
                    filters['bedrooms'] = 4
                elif '五室' in query or '5室' in query or '五居室' in query or '5居室' in query:
                    filters['bedrooms'] = 5
                else:
                    filters['bedrooms'] = int(match.group(1))
                break
        
        # 解析房产类型
        if '公寓' in query or 'flat' in query_lower or 'apartment' in query_lower:
            filters['property_type'] = 'flat'
        elif '别墅' in query or 'house' in query_lower:
            filters['property_type'] = 'house'
        elif '单间' in query or 'studio' in query_lower:
            filters['property_type'] = 'studio'
        
        # 解析价格
        # 查找价格数字（支持英镑符号和"镑"字）
        price_patterns = [
            r'£?\s*(\d+)\s*[万亿]?[镑磅]?\s*以下',
            r'少于\s*£?\s*(\d+)\s*[万亿]?[镑磅]?',
            r'低于\s*£?\s*(\d+)\s*[万亿]?[镑磅]?',
            r'最多\s*£?\s*(\d+)\s*[万亿]?[镑磅]?',
            r'£?\s*(\d+)\s*-\s*£?\s*(\d+)\s*[万亿]?[镑磅]?',
            r'£?\s*(\d+)\s*[万亿]?[镑磅]?\s*以上',
            r'超过\s*£?\s*(\d+)\s*[万亿]?[镑磅]?',
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                if '以下' in query or '少于' in query or '低于' in query or '最多' in query:
                    price_value = int(match.group(1))
                    # 处理"万"的情况
                    if '万' in query:
                        price_value = price_value * 10000
                    filters['max_price'] = price_value
                elif '以上' in query or '超过' in query:
                    price_value = int(match.group(1))
                    if '万' in query:
                        price_value = price_value * 10000
                    filters['min_price'] = price_value
                elif len(match.groups()) == 2:
                    min_val = int(match.group(1))
                    max_val = int(match.group(2))
                    if '万' in query:
                        min_val *= 10000
                        max_val *= 10000
                    filters['min_price'] = min_val
                    filters['max_price'] = max_val
                break
        
        # 解析位置信息（简单提取关键词）
        # 常见地标和区域（按优先级排序，更具体的在前）
        location_keywords = [
            ('剑桥三一学院', 'trinity college cambridge'),  # 剑桥三一学院
            ('三一学院', 'trinity college cambridge'),  # 三一学院（通常指剑桥的）
            ('trinity college cambridge', 'trinity college cambridge'),  # 英文完整名
            ('trinity college', 'trinity college cambridge'),  # 英文简称
            ('帝国理工大学', 'imperial college'),  # 完整名称
            ('帝国理工', 'imperial college'),  # 简称
            ('帝国', 'imperial college'),  # 超简称
            ('剑桥大学', 'cambridge'),  # 剑桥大学
            ('剑桥', 'cambridge'),  # 剑桥
            ('牛津大学', 'oxford'),
            ('牛津', 'oxford'),
            ('伦敦大学', 'ucl'),
            ('ucl', 'ucl'),
            ('lse', 'lse'),
            ('kcl', 'kcl'),
            ('伦敦', 'london'),
            ('曼彻斯特', 'manchester'),
            ('伯明翰', 'birmingham'),
            ('爱丁堡', 'edinburgh'),
            ('ic', 'imperial college')
        ]
        
        for keyword_pattern, mapped_location in location_keywords:
            if keyword_pattern in query or keyword_pattern.lower() in query_lower:
                filters['location'] = mapped_location
                break
        
        return filters

