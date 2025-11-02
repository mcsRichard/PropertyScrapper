#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新抓取房产详情页，提取location和postcode，更新数据库
不会插入新记录，只更新postcode为空的记录
如果数据库已有postcode，会跳过不重新抓取

使用方法:
    python update_location_postcode.py                    # 从头开始处理所有记录
    python update_location_postcode.py --start 50         # 从第50条记录开始
    python update_location_postcode.py -s 100             # 从第100条记录开始
"""

import sys
import os
import re
import time
import random
import argparse

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加backend目录到路径
backend_path = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, backend_path)

# 设置工作目录到backend
os.chdir(backend_path)

# 导入Scrapper中的提取函数
project_root = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, os.path.abspath(project_root))

# 创建全局session以提高请求成功率
_session = None

def get_session():
    """获取或创建requests session"""
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
        })
    return _session

# 实现抓取函数（优先使用requests，不依赖Selenium）
def fetch_property_html_fast(url, timeout=20):
    """快速抓取房产详情页（使用requests）"""
    try:
        session = get_session()
        session.headers['Referer'] = 'https://www.zoopla.co.uk/'
        
        # 先访问首页获取cookies
        session.get('https://www.zoopla.co.uk/', timeout=10)
        time.sleep(0.5)  # 短暂延迟
        
        # 再访问目标页面
        resp = session.get(url, timeout=timeout, allow_redirects=True)
        
        if resp.status_code == 200:
            html = resp.text
            if html and len(html) > 1000:  # 确保有足够内容
                return html
            else:
                print(f"  ⚠️ 响应内容过短 ({len(html) if html else 0} 字符)")
                return None
        elif resp.status_code == 403:
            print(f"  ⚠️ 请求被拒绝 (403)，可能需要使用Selenium")
            return None
        elif resp.status_code == 404:
            print(f"  ⚠️ 页面不存在 (404)")
            return None
        else:
            print(f"  ⚠️ HTTP错误: {resp.status_code}")
            return None
    except requests.exceptions.Timeout:
        print(f"  ⚠️ 请求超时")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  ⚠️ 请求异常: {e}")
        return None
    except Exception as e:
        print(f"  ⚠️ 未知错误: {e}")
        return None

def fetch_property_html_selenium(url, max_retries=3):
    """使用Selenium抓取（需要selenium和chromedriver）"""
    for attempt in range(max_retries):
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('window-size=1920x1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 随机User-Agent
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
            chrome_options.add_argument(f'user-agent={random.choice(user_agents)}')
            
            # 尝试多个可能的chromedriver路径
            driver_paths = [
                './chromedriver.exe',
                '../chromedriver.exe',
                '../../chromedriver.exe',
                os.path.join(os.path.dirname(__file__), '../chromedriver.exe'),
                os.path.join(os.path.dirname(__file__), '../../chromedriver.exe')
            ]
            service = None
            for path in driver_paths:
                abs_path = os.path.abspath(path)
                if os.path.exists(abs_path):
                    service = Service(abs_path)
                    print(f"    [DEBUG] 使用ChromeDriver: {abs_path}")
                    break
            
            if not service:
                print(f"  ❌ 未找到ChromeDriver，尝试路径: {driver_paths}")
                return None
            
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            driver.get(url)
            # 等待页面加载，特别是动态内容
            time.sleep(random.uniform(3, 5))
            
            # 尝试滚动页面以触发懒加载
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
            except:
                pass
            
            html = driver.page_source
            driver.quit()
            
            if html and len(html) > 1000:
                return html
            else:
                raise Exception(f"获取的HTML内容过短: {len(html) if html else 0} 字符")
                
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = random.uniform(2, 5)
                print(f"  ⚠️ 尝试 {attempt + 1}/{max_retries} 失败: {e}")
                print(f"  ⏳ 等待 {wait_time:.1f} 秒后重试...")
                time.sleep(wait_time)
            else:
                print(f"  ❌ 所有尝试都失败: {e}")
                return None
    
    return None

from models.database import Property, DatabaseManager
from sqlalchemy import or_, text
from bs4 import BeautifulSoup
import json
import requests

def extract_location_and_postcode_from_db_html(html, url=None, title=None):
    """
    从详情页HTML中提取location和postcode
    优先级：标题 > URL > 页面内容
    """
    soup = BeautifulSoup(html, "html.parser")
    location = None
    postcode = None
    
    # 方法0: 从HTML页面结构中提取地址（优先级最高）
    # Zoopla页面中，标题通常是"2 bed flat for sale"，地址在标题旁边/下方
    # 例如："Printworks House, Tottenham Lane, Crouch End, London N8"
    
    # 0.1: 查找常见的地址选择器
    address_selectors = [
        '[data-testid*="address"]',
        '[data-testid*="location"]',
        '[itemprop="address"]',
        'address',
        '[class*="address"]',
        '[class*="location"]',
        '[class*="Address"]',
        '[class*="Location"]',
        'p[class*="address"]',
        'div[class*="address"]',
        'span[class*="address"]',
    ]
    
    address_text = None
    for selector in address_selectors:
        elements = soup.select(selector)
        for el in elements:
            text = el.get_text(strip=True)
            # 检查是否包含邮编模式（通常地址会包含"London N8"这样的格式）
            if re.search(r'\b[A-Z]{1,2}\d{1,2}(?:\s\d[A-Z]{2})?\b', text.upper()):
                address_text = text
                print(f"    🏠 从选择器提取地址: {selector} -> {address_text[:100]}")
                break
        if address_text:
            break
    
    # 0.2: 如果没找到，查找h1标题附近的元素（兄弟节点或父节点的其他子节点）
    if not address_text:
        h1_elements = soup.find_all('h1', limit=5)
        for h1 in h1_elements:
            h1_text = h1.get_text(strip=True)
            print(f"    [DEBUG] 找到h1: {h1_text[:50]}")
            
            # 查找h1的兄弟节点（next_sibling和previous_sibling）
            for sibling in list(h1.next_siblings) + list(h1.previous_siblings):
                if hasattr(sibling, 'get_text'):
                    text = sibling.get_text(strip=True)
                    if text and len(text) > 10 and re.search(r'\b[A-Z]{1,2}\d{1,2}(?:\s\d[A-Z]{2})?\b', text.upper()):
                        address_text = text
                        print(f"    🏠 从h1兄弟节点提取地址: {address_text[:100]}")
                        break
                elif isinstance(sibling, str) and sibling.strip():
                    text = sibling.strip()
                    if len(text) > 10 and re.search(r'\b[A-Z]{1,2}\d{1,2}(?:\s\d[A-Z]{2})?\b', text.upper()):
                        address_text = text
                        print(f"    🏠 从h1文本兄弟节点提取地址: {address_text[:100]}")
                        break
            if address_text:
                break
            
            # 查找h1的父节点的其他子节点
            parent = h1.parent
            if parent:
                for child in parent.children:
                    if child != h1 and hasattr(child, 'get_text'):
                        text = child.get_text(strip=True)
                        if text and len(text) > 10 and re.search(r'\b[A-Z]{1,2}\d{1,2}(?:\s\d[A-Z]{2})?\b', text.upper()):
                            address_text = text
                            print(f"    🏠 从h1父节点子元素提取地址: {address_text[:100]}")
                            break
            if address_text:
                break
            
            # 查找h1附近的其他元素（通过查找包含地址关键词的相邻元素）
            if not address_text:
                # 查找h1所在容器的其他部分
                container = parent if parent else soup
                # 查找包含"London"或其他地址关键词的元素
                for elem in container.find_all(['p', 'div', 'span', 'h2', 'h3'], limit=10):
                    if elem != h1:
                        text = elem.get_text(strip=True)
                        # 检查是否包含完整的地址模式（包含逗号和邮编）
                        if text and ',' in text and re.search(r'\b[A-Z]{1,2}\d{1,2}(?:\s\d[A-Z]{2})?\b', text.upper()):
                            address_text = text
                            print(f"    🏠 从附近元素提取地址: {address_text[:100]}")
                            break
                if address_text:
                    break
    
    # 0.3: 从提取的地址文本中解析邮编和location
    if address_text:
        address_upper = address_text.upper()
        
        # 提取完整邮编
        postcode_pattern_full = r'\b([A-Z]{1,2}\d{1,2}\s\d[A-Z]{2})\b'
        match = re.search(postcode_pattern_full, address_upper)
        if match:
            postcode = match.group(1).strip()
            print(f"    📋 从地址文本提取完整邮编: {postcode}")
        else:
            # 提取邮编前缀（如N8, SW7）
            postcode_patterns = [
                r'LONDON\s+([A-Z]{1,2}\d{1,2})\b',     # "London N8"
                r',\s+([A-Z]{1,2}\d{1,2})\s*$',        # ", N8" 在末尾
                r'\s+([A-Z]{1,2}\d{1,2})\s*$',         # 末尾的 " N8"
                r'\b([A-Z]{1,2}\d{1,2})\b',            # 任何位置的邮编前缀（更宽松）
            ]
            for pattern in postcode_patterns:
                match = re.search(pattern, address_upper)
                if match:
                    candidate = match.group(1).strip().upper()
                    if re.match(r'^[A-Z]{1,2}\d{1,2}$', candidate) and len(candidate) >= 2:
                        postcode = candidate
                        print(f"    📋 从地址文本提取邮编前缀: {postcode}")
                        break
        
        # 从地址文本提取location（常见伦敦地区）
        london_areas = [
            'Muswell Hill', 'Crouch End', 'South Kensington', 'Hampstead', 
            'Camden', 'Greenwich', 'Shoreditch', 'Battersea', 'Clapham', 
            'Fulham', 'Notting Hill', 'Paddington', 'Marylebone', 'Kensington',
            'Chelsea', 'Westminster', 'Islington', 'Covent Garden',
            'Canary Wharf', 'Docklands', 'Tottenham'
        ]
        address_lower = address_text.lower()
        for area in london_areas:
            if area.lower() in address_lower:
                location = area
                print(f"    📋 从地址文本提取地点: {location}")
                break
    
    # 方法0.4: 如果地址文本中没有，尝试从标题中提取（备选）
    if not postcode and title:
        title_upper = title.upper()
        # 检查标题是否包含邮编（有些情况下标题可能包含地址）
        postcode_patterns = [
            r'LONDON\s+([A-Z]{1,2}\d{1,2})\b',
            r',\s+([A-Z]{1,2}\d{1,2})\s*$',
            r'\s+([A-Z]{1,2}\d{1,2})\s*$',
        ]
        for pattern in postcode_patterns:
            match = re.search(pattern, title_upper)
            if match:
                candidate = match.group(1).strip().upper()
                if re.match(r'^[A-Z]{1,2}\d{1,2}$', candidate):
                    postcode = candidate
                    print(f"    📋 从标题提取邮编前缀: {postcode}")
                    break
        
        # 从标题提取location（如果地址文本中没有）
        if not location:
            london_areas = [
                'Muswell Hill', 'Crouch End', 'South Kensington', 'Hampstead', 
                'Camden', 'Greenwich', 'Shoreditch', 'Battersea', 'Clapham', 
                'Fulham', 'Notting Hill', 'Paddington', 'Marylebone', 'Kensington',
                'Chelsea', 'Westminster', 'Islington', 'Covent Garden',
                'Canary Wharf', 'Docklands', 'Tottenham'
            ]
            title_lower = title.lower()
            for area in london_areas:
                if area.lower() in title_lower:
                    location = area
                    print(f"    📋 从标题提取地点: {location}")
                    break
    
    if postcode or location:
        print(f"    ✅ 提取结果: postcode={postcode}, location={location}")
    else:
        print(f"    ⚠️ 未找到邮编和地点")
    
    # 方法1: 从URL中提取邮编（优先级高于页面内容）
    if not postcode and url:
        # URL可能包含邮编，如 /details/71626136/ 或 /property/n10/
        # 更常见的是在URL路径中
        url_patterns = [
            r'[\/\-]n([0-9]{1,2})[\/\-]',  # /n10/ 或 -n10-
            r'[\/\-]([A-Z]{1,2}\d{1,2})[\/\-]',  # 通用邮编前缀
            r'(?:london|property)[\/\-]([A-Z]{1,2}\d{1,2})',  # london/n10 或 property/sw7
        ]
        for pattern in url_patterns:
            match = re.search(pattern, url.upper())
            if match:
                extracted = match.group(1)
                # 如果是n开头，补全为N10格式
                if extracted.startswith('N') and extracted[1:].isdigit():
                    postcode = extracted.upper()
                elif re.match(r'^[A-Z]{1,2}\d{1,2}$', extracted):
                    postcode = extracted.upper()
                if postcode:
                    print(f"    🔗 从URL提取: {postcode}")
                    break
    
    # 方法2: 从ld+json中提取（需要验证是否属于当前房产）
    # 注意：ld+json可能包含多个地址，需要严格验证URL匹配
    if not postcode or not location:
        ldjson = soup.find("script", attrs={"type": "application/ld+json"})
        if ldjson:
            try:
                data = json.loads(ldjson.string)
                # 处理@graph数组
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("@type") in ["Product", "Offer", "RealEstateListing"]:
                            # 优先从Product/Offer中提取，这些更可能是当前房产的信息
                            item_url = item.get("url") or item.get("item", {}).get("url")
                            # 严格验证URL匹配（必须包含当前房产的URL）
                            if url and item_url and url.replace('https://', '').replace('http://', '') in item_url.replace('https://', '').replace('http://', ''):
                                address = item.get("address") or item.get("item", {}).get("address")
                                if isinstance(address, dict):
                                    if not postcode:
                                        postcode_from_json = address.get("postalCode") or address.get("postcode")
                                        if postcode_from_json:
                                            postcode = postcode_from_json.strip()
                                            print(f"    📦 从ld+json(Product)提取邮编: {postcode}")
                                    if not location:
                                        location_from_json = address.get("addressLocality") or address.get("locality")
                                        if location_from_json:
                                            location = location_from_json.strip()
                                            print(f"    📦 从ld+json(Product)提取地点: {location}")
                elif isinstance(data, dict):
                    # 对于单个dict，检查URL是否匹配
                    item_url = data.get("url")
                    if not url or not item_url or url in item_url:
                        address = data.get("address", {})
                        if isinstance(address, dict):
                            if not postcode:
                                postcode_from_json = address.get("postalCode") or address.get("postcode")
                                if postcode_from_json:
                                    postcode = postcode_from_json.strip()
                                    print(f"    📦 从ld+json提取邮编: {postcode}")
                            if not location:
                                location_from_json = address.get("addressLocality") or address.get("locality")
                                if location_from_json:
                                    location = location_from_json.strip()
                                    print(f"    📦 从ld+json提取地点: {location}")
            except Exception as e:
                print(f"    [DEBUG] Failed to parse ld+json: {e}")
    
    # 方法3: 从页面文本中提取邮编（最后尝试，需要更严格的匹配）
    if not postcode:
        # 优先从h1标题中提取（最可能包含正确的地址）
        h1_elements = soup.find_all('h1', limit=3)
        for h1 in h1_elements:
            h1_text = h1.get_text()
            # 在h1中查找邮编
            postcode_pattern_full = r'\b([A-Z]{1,2}\d{1,2}\s\d[A-Z]{2})\b'
            match = re.search(postcode_pattern_full, h1_text.upper())
            if match:
                postcode = match.group(1).strip()
                print(f"    📄 从h1标题提取完整邮编: {postcode}")
                break
            else:
                # 尝试邮编前缀
                postcode_pattern_prefix = r'London\s+([A-Z]{1,2}\d{1,2})\b'
                match = re.search(postcode_pattern_prefix, h1_text.upper())
                if match:
                    postcode = match.group(1).strip().upper()
                    print(f"    📄 从h1标题提取邮编前缀: {postcode}")
                    break
        
        # 如果h1中没有，再尝试页面头部文本（前1000字符）
        if not postcode:
            page_text = soup.get_text()[:1000]
            # 查找完整邮编（更严格）
            postcode_pattern_full = r'\b([A-Z]{1,2}\d{1,2}\s\d[A-Z]{2})\b'
            match = re.search(postcode_pattern_full, page_text.upper())
            if match:
                postcode = match.group(1).strip()
                print(f"    📄 从页面头部提取完整邮编: {postcode}")
    
    # 方法4: 从地址区域提取location（如果还没找到）
    if not location:
        address_selectors = [
            '[data-testid*="address"]',
            '.address',
            '[class*="address"]',
            '[itemprop="address"]',
            'h1[class*="title"]',
        ]
        london_areas = [
            'Muswell Hill', 'Hampstead', 'Camden', 'Greenwich',
            'Shoreditch', 'Battersea', 'Clapham', 'Fulham',
            'Notting Hill', 'Paddington', 'Marylebone', 'Kensington',
            'Chelsea', 'Westminster', 'Islington', 'Covent Garden',
            'Canary Wharf', 'Docklands'
        ]
        for selector in address_selectors:
            elements = soup.select(selector)
            for el in elements:
                text = el.get_text(strip=True)
                for area in london_areas:
                    if area.lower() in text.lower():
                        location = area
                        break
                if location:
                    break
            if location:
                break
    
    # 方法4: 从URL中提取（备用）
    if not postcode and url:
        postcode_pattern = r'[\/\-]([A-Z]{1,2}\d{1,2})[\/\-]'
        match = re.search(postcode_pattern, url.upper())
        if match:
            postcode = match.group(1)
    
    return location, postcode

def update_property_location_postcode(property_obj, db):
    """更新单个房产的location和postcode"""
    if not property_obj.url or not property_obj.url.startswith('http'):
        print(f"  ⚠️ 跳过：URL无效或不存在")
        return False, None, None
    
    print(f"  📥 抓取: {property_obj.url}")
    
    # 获取标题（可能包含邮编信息）
    title = property_obj.title or ''
    
    # 直接使用Selenium抓取
    html = fetch_property_html_selenium(property_obj.url)
    
    if not html:
        print(f"  ❌ Selenium抓取失败")
        return False, None, None
    
    print(f"  ✅ 抓取成功 ({len(html)} 字符)")
    
    # 提取location和postcode（传入标题和URL，优先使用）
    location, postcode = extract_location_and_postcode_from_db_html(html, property_obj.url, title)
    
    updated = False
    old_location = property_obj.location
    old_postcode = property_obj.postcode
    
    extracted_location = None
    extracted_postcode = None
    
    # 更新location
    if location and (not property_obj.location or property_obj.location == ''):
        property_obj.location = location
        extracted_location = location
        updated = True
        print(f"  ✅ Location: {old_location or 'None'} -> {location}")
    elif location and property_obj.location and property_obj.location != location:
        # 如果已有location但与提取的不同，可以选择更新（这里保持原值）
        print(f"  ℹ️ Location已有值: {property_obj.location}（提取到: {location}，保持原值）")
    
    # 更新postcode
    if postcode and (not property_obj.postcode or property_obj.postcode == ''):
        property_obj.postcode = postcode
        extracted_postcode = postcode
        updated = True
        print(f"  ✅ Postcode: {old_postcode or 'None'} -> {postcode}")
    elif postcode and property_obj.postcode and property_obj.postcode != postcode:
        # 如果已有postcode但与提取的不同，可以选择更新（这里保持原值）
        print(f"  ℹ️ Postcode已有值: {property_obj.postcode}（提取到: {postcode}，保持原值）")
    elif not postcode:
        print(f"  ⚠️ 未提取到postcode")
        if title:
            print(f"  💡 提示: 标题是 '{title[:80]}'，请检查提取逻辑")
    
    if not updated:
        print(f"  ℹ️ 未找到新的location或postcode，或已有值")
    
    # 返回更新状态和提取的值（即使未更新也返回，以便重试时使用）
    return updated, extracted_location, extracted_postcode

def refresh_db_session(db_manager, db):
    """刷新数据库会话，解决连接超时问题"""
    try:
        db.rollback()  # 先回滚任何未提交的事务
        db.close()
    except Exception as e:
        print(f"    [DEBUG] 关闭旧会话时出错: {e}")
        pass
    time.sleep(0.5)  # 短暂延迟，确保连接完全关闭
    return db_manager.get_session()

def main():
    """主函数：更新所有postcode为空的房产的location和postcode"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='Re-scrape property detail pages and update location/postcode in database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python update_location_postcode.py                    # Process all records from beginning
  python update_location_postcode.py --start 50         # Start from record 50
  python update_location_postcode.py -s 100             # Start from record 100
        """
    )
    parser.add_argument(
        '-s', '--start',
        type=int,
        default=1,
        metavar='N',
        help='Start from record N (default: 1)'
    )
    
    args = parser.parse_args()
    start_idx = args.start
    
    db_manager = DatabaseManager()
    db = db_manager.get_session()
    
    try:
        # 获取所有postcode为空的房产
        # 注意：脚本是幂等的，可以安全地重复运行，只更新postcode为空的记录
        properties = db.query(Property).filter(
            or_(
                Property.postcode.is_(None),
                Property.postcode == ''
            )
        ).order_by(Property.id).all()  # 按ID排序，确保处理顺序一致
        
        total_to_update = len(properties)
        
        # 统计已有postcode的记录
        already_have_postcode = db.query(Property).filter(
            Property.postcode.isnot(None),
            Property.postcode != ''
        ).count()
        
        print(f"[INFO] 数据库状态:")
        print(f"  - 需要更新的记录: {total_to_update}")
        print(f"  - 已有postcode的记录: {already_have_postcode}")
        print(f"[INFO] 将重新抓取详情页提取location和postcode")
        print(f"[INFO] 起始位置: 第 {start_idx} 条记录")
        print(f"[INFO] ⚠️ 注意：脚本是幂等的，如果数据库已有postcode，会跳过不重新抓取\n")
        
        # 如果没有需要更新的记录，直接返回
        if total_to_update == 0:
            print(f"[INFO] 所有记录都已包含postcode，无需更新")
            return
        
        # 如果起始位置超出范围，给出提示
        if start_idx > total_to_update:
            print(f"[ERROR] 起始位置 {start_idx} 超出记录总数 {total_to_update}")
            return
        
        updated_count = 0
        postcode_count = 0
        location_count = 0
        failed_count = 0
        skipped_count = 0  # 已有点击但跳过抓取的记录
        
        # 从指定位置开始处理
        for idx, prop in enumerate(properties, 1):
            # 如果索引小于起始位置，跳过
            if idx < start_idx:
                skipped_count += 1
                continue
            # 在处理前再次检查（可能在之前的运行中已经更新）
            current_prop = db.query(Property).filter(Property.id == prop.id).first()
            if not current_prop:
                print(f"\n[处理 {idx}/{total_to_update}] ID: {prop.id}")
                print(f"  ⚠️ 记录不存在，跳过")
                skipped_count += 1
                continue
            
            # 如果已有postcode，跳过（不重新抓取）
            if current_prop.postcode and current_prop.postcode != '':
                print(f"\n[处理 {idx}/{total_to_update}] ID: {current_prop.id}")
                print(f"  ⏭️ 已有postcode，跳过: location={current_prop.location or 'None'}, postcode={current_prop.postcode}")
                skipped_count += 1
                continue
            
            # 使用当前查询到的对象
            prop = current_prop
            print(f"\n[处理 {idx}/{len(properties)}] ID: {prop.id}")
            print(f"  Title: {prop.title[:60] if prop.title else 'N/A'}...")
            
            try:
                # 检查数据库连接，如果断开则重新连接
                try:
                    db.execute(text("SELECT 1"))
                except Exception as conn_err:
                    print(f"  🔄 数据库连接断开，重新连接... ({conn_err})")
                    try:
                        db.rollback()
                    except:
                        pass
                    db = refresh_db_session(db_manager, db)
                    # 重新加载对象
                    prop = db.query(Property).filter(Property.id == prop.id).first()
                    if not prop:
                        print(f"  ⚠️ 无法重新加载房产记录，跳过")
                        failed_count += 1
                        continue
                
                updated, extracted_location, extracted_postcode = update_property_location_postcode(prop, db)
                
                if updated:
                    updated_count += 1
                    postcode_updated = extracted_postcode is not None
                    location_updated = extracted_location is not None
                    
                    if postcode_updated:
                        postcode_count += 1
                    if location_updated:
                        location_count += 1
                    
                    # 每条记录立即提交，避免连接超时
                    try:
                        db.commit()
                    except Exception as commit_error:
                        print(f"  ⚠️ 提交失败: {commit_error}，尝试重新连接...")
                        try:
                            db.rollback()
                        except:
                            pass
                        db = refresh_db_session(db_manager, db)
                        # 重新加载对象并再次尝试更新
                        prop = db.query(Property).filter(Property.id == prop.id).first()
                        if prop:
                            # 再次设置提取的值
                            need_update = False
                            if extracted_location and (not prop.location or prop.location == ''):
                                prop.location = extracted_location
                                need_update = True
                            if extracted_postcode and (not prop.postcode or prop.postcode == ''):
                                prop.postcode = extracted_postcode
                                need_update = True
                            
                            if need_update:
                                try:
                                    db.commit()
                                    print(f"  ✅ 重试提交成功")
                                except Exception as retry_error:
                                    print(f"  ❌ 重试提交也失败: {retry_error}")
                                    db.rollback()
                                    updated_count -= 1  # 回退计数
                            else:
                                print(f"  ℹ️ 值已存在，无需更新")
                else:
                    failed_count += 1
                
                # 避免请求过快，随机延迟
                time.sleep(random.uniform(1, 3))
                
                # 每50条记录刷新一次数据库连接，防止连接超时
                if idx % 50 == 0:
                    print(f"\n[维护] 刷新数据库连接...")
                    db = refresh_db_session(db_manager, db)
                
            except Exception as e:
                print(f"  ❌ 处理失败: {e}")
                failed_count += 1
                try:
                    db.rollback()
                    db = refresh_db_session(db_manager, db)
                except:
                    pass
                continue
        
        processed_count = (total_to_update - skipped_count + (start_idx - 1))
        print(f"\n{'='*60}")
        print(f"[SUCCESS] 处理完成！")
        print(f"  - 总共需要处理: {total_to_update} 条")
        print(f"  - 实际处理: {processed_count} 条（从第{start_idx}条开始）")
        print(f"  - 成功更新: {updated_count} 条")
        print(f"  - Postcode更新: {postcode_count} 条")
        print(f"  - Location更新: {location_count} 条")
        print(f"  - 跳过（已有数据）: {skipped_count - (start_idx - 1)} 条")
        print(f"  - 失败: {failed_count} 条")
        print(f"{'='*60}")
        print(f"  - 剩余待处理: {total_to_update - updated_count - skipped_count - failed_count}")
        
        # 统计更新后的数据（使用新会话）
        db = refresh_db_session(db_manager, db)
        total_properties = db.query(Property).count()
        properties_with_postcode = db.query(Property).filter(
            Property.postcode.isnot(None),
            Property.postcode != ''
        ).count()
        properties_with_location = db.query(Property).filter(
            Property.location.isnot(None),
            Property.location != ''
        ).count()
        
        print(f"\n[统计] 更新后的数据:")
        print(f"  - 总房产数: {total_properties}")
        if total_properties > 0:
            print(f"  - 有postcode的: {properties_with_postcode} ({properties_with_postcode*100/total_properties:.1f}%)")
            print(f"  - 有location的: {properties_with_location} ({properties_with_location*100/total_properties:.1f}%)")
        
    except Exception as e:
        print(f"[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        try:
            db.rollback()
        except:
            pass
    finally:
        try:
            db.close()
        except:
            pass

if __name__ == "__main__":
    main()

