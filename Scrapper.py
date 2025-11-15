
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
)
from bs4 import BeautifulSoup
import urllib.parse
import csv
import requests
import json
import time
import random
import re
from datetime import datetime
import sys
import os
from typing import Dict, List, Any, Optional, Tuple

# 添加backend目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# 强制标准输出使用UTF-8，兼容Windows控制台
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

# 导入COS上传器和配置
try:
    from backend.utils.cos_uploader import create_cos_uploader
    from backend.config import Config
    from backend.models.database import DatabaseManager, Property
    from backend.utils.database import PropertyService
    COS_ENABLED = True
    print("[INFO] COS uploader enabled")
except ImportError as e:
    print(f"[WARNING] COS uploader not available: {e}")
    print("[WARNING] Please install: pip install cos-python-sdk-v5")
    COS_ENABLED = False

def translate_to_chinese(text):
    """Translate English text to Chinese using Google Translate API"""
    if not text or not text.strip():
        return ""
    
    try:
        # Using Google Translate API (free tier)
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            'client': 'gtx',
            'sl': 'en',  # source language (English)
            'tl': 'zh',  # target language (Chinese)
            'dt': 't',
            'q': text
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        if result and len(result) > 0 and len(result[0]) > 0:
            translated_text = ''.join([item[0] for item in result[0] if item[0]])
            return translated_text.strip()
        else:
            return text  # Return original if translation fails
            
    except Exception as e:
        print(f"[WARNING] Translation failed for text: {text[:50]}... Error: {e}")
        return text  # Return original text if translation fails


def is_detail_url(url: str) -> bool:
    """判断是否为详情页URL"""
    if not url:
        return False
    return '/details/' in url


def format_price(price_numeric: Optional[int], listing_type: str) -> Optional[str]:
    """格式化价格字符串"""
    if price_numeric is None:
        return None
    price_str = f"£{price_numeric:,.0f}"
    if listing_type == 'for_rent':
        price_str += " pcm"
    return price_str


def safe_int(value: Any) -> Optional[int]:
    """安全地将值转换为整数"""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        text = str(value)
        match = re.search(r'\d+', text)
        if match:
            return int(match.group())
        return int(float(text))
    except Exception:
        return None

def fetch_property_html(url, max_retries=3, click_full_description=False):
    """Fetch property HTML with retry mechanism and optional 'Read full description' interaction"""
    for attempt in range(max_retries):
        driver = None
        try:
            print(f"[INFO] Fetching URL (attempt {attempt + 1}/{max_retries}): {url}")
            
            # Set up Selenium Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Run in headless mode
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('window-size=1920x1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Random user agent to avoid detection
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
            chrome_options.add_argument(f'user-agent={random.choice(user_agents)}')

            service = Service('./chromedriver.exe')
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            driver.get(url)
            wait = WebDriverWait(driver, 15)
            try:
                wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            except TimeoutException:
                print("[WARNING] Page readyState wait timed out, continuing...")

            # 等待页面加载，特别是图片
            time.sleep(random.uniform(3, 6))  # 增加等待时间确保图片加载
            
            # 可选：点击“Read full description”按钮
            if click_full_description:
                _click_read_full_description(driver, wait)
            
            # 尝试滚动页面以触发懒加载图片
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
            except Exception:
                pass
            
            html = driver.page_source
            
            print(f"[SUCCESS] Successfully fetched HTML ({len(html)} characters)")
            return html
            
        except Exception as e:
            print(f"[ERROR] Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = random.uniform(5, 10)
                print(f"[INFO] Waiting {wait_time:.1f} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"[ERROR] All {max_retries} attempts failed for URL: {url}")
                return None
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass


def _click_read_full_description(driver, wait):
    """尝试点击详情页中的 'Read full description' 或类似按钮"""
    keywords = [
        "read full description",
        "read description",
        "full description",
        "read more",
        "show more",
    ]
    clicked = False
    
    # 一些常见的按钮选择器
    candidate_selectors = [
        '[data-testid*="read-more"]',
        '[data-testid*="toggle-description"]',
        'button[aria-expanded="false"]',
        'button[aria-controls*="description"]',
        'button',
        'a[role="button"]',
    ]
    
    try:
        # 先尝试使用特定选择器
        for selector in candidate_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
            except Exception:
                continue
            for el in elements:
                try:
                    text = (el.text or "").strip().lower()
                    aria_label = (el.get_attribute("aria-label") or "").lower()
                    if not text and aria_label:
                        text = aria_label
                    if text and any(keyword in text for keyword in keywords):
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                        time.sleep(0.5)
                        wait.until(lambda d, element=el: element.is_displayed() and element.is_enabled())
                        driver.execute_script("arguments[0].click();", el)
                        clicked = True
                        print("[INFO] Clicked full description button via CSS selector")
                        break
                except (StaleElementReferenceException, ElementClickInterceptedException):
                    continue
                except TimeoutException:
                    continue
                except Exception as click_err:
                    print(f"[WARNING] Failed to click selector {selector}: {click_err}")
            if clicked:
                break
        
        # 如果上述方法失败，再尝试根据文本匹配按钮
        if not clicked:
            buttons = driver.find_elements(By.XPATH, "//button|//a[@role='button']")
            for btn in buttons:
                try:
                    text = (btn.text or "").strip().lower()
                    aria_label = (btn.get_attribute("aria-label") or "").lower()
                    if not text and aria_label:
                        text = aria_label
                    if text and any(keyword in text for keyword in keywords):
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                        time.sleep(0.5)
                        wait.until(lambda d, element=btn: element.is_displayed() and element.is_enabled())
                        driver.execute_script("arguments[0].click();", btn)
                        clicked = True
                        print("[INFO] Clicked full description button via text search")
                        break
                except (StaleElementReferenceException, ElementClickInterceptedException):
                    continue
                except Exception as click_err:
                    print(f"[WARNING] Failed to click button by text: {click_err}")
    except Exception as e:
        print(f"[WARNING] Encountered error while attempting to click full description button: {e}")
    
    if clicked:
        # 等待展开动画完成
        time.sleep(1.5)
    else:
        print("[INFO] No 'Read full description' button was clicked (not found or already expanded)")


def extract_full_description(html: str) -> str:
    """从详情页HTML中提取完整描述文本"""
    if not html:
        return ""
    
    soup = BeautifulSoup(html, "html.parser")
    
    # 删除脚本和样式，避免干扰
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    
    # 1. 优先使用带有明显属性的容器
    description_selectors = [
        '#detailed-desc',
        '[id*="detailed-desc"]',
        '[data-testid*="listing-description"]',
        '[data-testid*="property-description"]',
        '[data-testid*="full-description"]',
        'section[aria-label*="description"]',
        '[class*="description"]',
    ]
    
    for selector in description_selectors:
        el = soup.select_one(selector)
        if el:
            text = el.get_text(" ", strip=True)
            if text and len(text) > 40:
                print(f"[SCRAPPER] Extracted description via selector: {selector}")
                return text
    
    # 2. 查找包含“Full description”或“Property description”的标题
    heading_keywords = ["full description", "property description", "description"]
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'span', 'button'])
    for heading in headings:
        heading_text = (heading.get_text(strip=True) or "").lower()
        if any(keyword in heading_text for keyword in heading_keywords):
            description_parts = []
            for sibling in heading.next_siblings:
                if getattr(sibling, "name", None) in ['h1', 'h2', 'h3', 'h4']:
                    break
                if hasattr(sibling, "get_text"):
                    text = sibling.get_text(" ", strip=True)
                else:
                    text = str(sibling).strip()
                if text:
                    description_parts.append(text)
            if description_parts:
                description = " ".join(description_parts).strip()
                if description:
                    print("[SCRAPPER] Extracted description via heading siblings")
                    return description
    
    # 3. 尝试从结构化数据（ld+json）中提取
    ldjson_scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
    
    def _extract_from_json(data):
        if isinstance(data, dict):
            if data.get("description"):
                return data["description"]
            if "@graph" in data:
                for item in data["@graph"]:
                    result = _extract_from_json(item)
                    if result:
                        return result
        elif isinstance(data, list):
            for item in data:
                result = _extract_from_json(item)
                if result:
                    return result
        return None
    
    for script in ldjson_scripts:
        try:
            data = json.loads(script.string)
            description = _extract_from_json(data)
            if description:
                description = BeautifulSoup(description, "html.parser").get_text(" ", strip=True)
                if description:
                    print("[SCRAPPER] Extracted description via ld+json")
                    return description
        except Exception:
            continue
    
    # 4. 最后尝试全局搜索包含关键字的段落
    paragraphs = soup.find_all(['p', 'div'])
    for p in paragraphs:
        text = (p.get_text(" ", strip=True) or "")
        if len(text) > 120 and ('apartment' in text.lower() or 'property' in text.lower()):
            print("[SCRAPPER] Extracted description via fallback paragraph search")
            return text
    
    print("[SCRAPPER] Full description not found in detail page")
    return ""


def extract_listings_from_search_html(html: str) -> List[Dict[str, Any]]:
    """从搜索结果页的ld+json结构中提取房源列表"""
    results: List[Dict[str, Any]] = []
    if not html:
        return results
    
    soup = BeautifulSoup(html, "html.parser")
    ldjson_scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
    for script in ldjson_scripts:
        try:
            data = json.loads(script.string)
        except Exception:
            continue
        if isinstance(data, dict) and data.get("@type") == "SearchResultsPage":
            item_list = data.get("mainEntity", {}).get("itemListElement", [])
            for item in item_list:
                product = item.get("item", {})
                url = product.get("url")
                if not url:
                    continue
                if url.startswith("/"):
                    url = urllib.parse.urljoin("https://www.zoopla.co.uk", url)
                description_html = product.get("description", "")
                description_text = BeautifulSoup(description_html, "html.parser").get_text(" ", strip=True)
                price_value = product.get("offers", {}).get("price")
                price_numeric = safe_int(price_value)
                results.append({
                    "title": product.get("name"),
                    "description": description_text,
                    "price_numeric": price_numeric,
                    "url": url,
                    "image": product.get("image")
                })
            break
    return results


def extract_listing_ldjson(html: str) -> Optional[Dict[str, Any]]:
    """从详情页HTML中提取RealEstateListing的ld+json数据"""
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(script.string)
        except Exception:
            continue
        if isinstance(data, dict) and data.get("@type") == "RealEstateListing":
            return data
    return None


def scrape_detail_page(detail_url: str, listing_type: str) -> Optional[Dict[str, Any]]:
    """抓取单个详情页数据"""
    print(f"[INFO] Scraping detail page: {detail_url}")
    detail_html = fetch_property_html(detail_url, click_full_description=True)
    if not detail_html:
        detail_html = fetch_property_html_fast(detail_url)
    if not detail_html:
        print(f"[ERROR] Failed to fetch detail page: {detail_url}")
        return None
    
    listing_ldjson = extract_listing_ldjson(detail_html) or {}
    description = extract_full_description(detail_html)
    if not description:
        description_html = listing_ldjson.get("description", "")
        description = BeautifulSoup(description_html, "html.parser").get_text(" ", strip=True)
    
    price_numeric = safe_int(listing_ldjson.get("offers", {}).get("price"))
    price = format_price(price_numeric, listing_type) if price_numeric else None
    
    title = None
    soup = BeautifulSoup(detail_html, "html.parser")
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)
    if not title:
        title = listing_ldjson.get("name")
    
    image_urls = extract_image_urls_from_detail_html(detail_html, base_url=detail_url)
    main_image = listing_ldjson.get("image")
    if image_urls:
        main_image = image_urls[0]
    
    bedrooms = None
    bathrooms = None
    for prop in listing_ldjson.get("additionalProperty", []) or []:
        name = (prop.get("name") or "").lower()
        if "bed" in name:
            bedrooms = safe_int(prop.get("value"))
        elif "bath" in name:
            bathrooms = safe_int(prop.get("value"))
    
    location, postcode = extract_location_and_postcode(detail_html, detail_url, title)
    
    property_data: Dict[str, Any] = {
        "title": title,
        "price": price,
        "price_numeric": price_numeric,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "property_type": None,  # 交由PropertyService自动推断
        "listing_type": listing_type,
        "location": location,
        "postcode": postcode,
        "description": description,
        "description_chinese": translate_to_chinese(description) if description else None,
        "url": detail_url,
        "image": main_image,
        "image_url": main_image,
        "image_urls": image_urls,
    }
    
    return property_data


def extract_location_and_postcode(html, url=None, title=None):
    """
    从详情页HTML中提取location和postcode
    优先级：标题 > URL > 页面内容
    
    Args:
        html: 详情页HTML内容
        url: 房产URL（可选，用于备用提取）
        title: 房产标题（可选，最准确的来源）
    
    Returns:
        tuple: (location, postcode)
    """
    soup = BeautifulSoup(html, "html.parser")
    location = None
    postcode = None
    
    # 方法0: 从HTML页面结构中提取地址（优先级最高）
    # Zoopla页面中，标题通常是"2 bed flat for sale"，地址在标题旁边/下方
    # 例如："Printworks House, Tottenham Lane, Crouch End, London N8"
    
    # 0.1: 优先从h1标题附近的元素提取地址（避免提取Zoopla注册地址）
    address_text = None
    h1_elements = soup.find_all('h1', limit=5)
    for h1 in h1_elements:
        # 查找h1的兄弟节点
        for sibling in h1.next_siblings:
            if hasattr(sibling, 'get_text'):
                text = sibling.get_text(strip=True)
                # 检查是否包含邮编前缀模式（只匹配前缀，不匹配完整邮编）
                if text and re.search(r'\b[A-Z]{1,2}\d{1,2}[A-Z]?\b', text.upper()):
                    # 排除可能包含Zoopla注册地址的文本（通常包含"SE1"等完整邮编）
                    if not re.search(r'\bSE1\s+\d[A-Z]{2}\b', text.upper()):
                        address_text = text
                        print(f"[SCRAPPER] 从h1兄弟节点提取地址: {address_text[:100]}")
                        break
            elif isinstance(sibling, str) and sibling.strip():
                text = sibling.strip()
                if re.search(r'\b[A-Z]{1,2}\d{1,2}[A-Z]?\b', text.upper()):
                    if not re.search(r'\bSE1\s+\d[A-Z]{2}\b', text.upper()):
                        address_text = text
                        print(f"[SCRAPPER] 从h1文本兄弟节点提取地址: {address_text[:100]}")
                        break
        if address_text:
            break
            
        # 查找h1的父节点的其他子节点
        if not address_text:
            parent = h1.parent
            if parent:
                for child in parent.children:
                    if child != h1 and hasattr(child, 'get_text'):
                        text = child.get_text(strip=True)
                        if text and re.search(r'\b[A-Z]{1,2}\d{1,2}[A-Z]?\b', text.upper()):
                            if not re.search(r'\bSE1\s+\d[A-Z]{2}\b', text.upper()):
                                address_text = text
                                print(f"[SCRAPPER] 从h1父节点子元素提取地址: {address_text[:100]}")
                                break
        if address_text:
            break
    
    # 0.2: 如果h1附近没找到，再查找常见的地址选择器（但要排除footer等区域）
    if not address_text:
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
        
        for selector in address_selectors:
            elements = soup.select(selector)
            for el in elements:
                # 排除footer、copyright等区域
                try:
                    parent_classes = []
                    for p in el.parents:
                        if hasattr(p, 'get'):
                            classes = p.get('class', []) or []
                            if isinstance(classes, list):
                                parent_classes.extend(classes)
                            elif isinstance(classes, str):
                                parent_classes.append(classes)
                    parent_classes_str = ' '.join(parent_classes).lower()
                    if 'footer' in parent_classes_str or 'copyright' in parent_classes_str:
                        continue
                except Exception:
                    pass  # 如果检查失败，继续处理
                    
                text = el.get_text(strip=True)
                # 只匹配邮编前缀，不匹配完整邮编（避免匹配Zoopla注册地址）
                if text and re.search(r'\b[A-Z]{1,2}\d{1,2}[A-Z]?\b', text.upper()):
                    # 排除包含完整邮编的文本（可能是Zoopla注册地址）
                    if not re.search(r'\b[A-Z]{1,2}\d{1,2}\s+\d[A-Z]{2}\b', text.upper()):
                        address_text = text
                        print(f"[SCRAPPER] 从选择器提取地址: {selector} -> {address_text[:100]}")
                        break
            if address_text:
                break
    
    # 0.3: 从提取的地址文本中解析邮编和location（只提取邮编前缀，不提取完整邮编）
    if address_text:
        address_upper = address_text.upper()
        
        # 只提取邮编前缀（如WC1E, N8, SW7等），不提取完整邮编（避免Zoopla注册地址）
        # 邮编前缀格式：1-2个字母 + 1-2个数字 + 可选的1个字母（如WC1E）
        postcode_patterns = [
            r'LONDON\s+([A-Z]{1,2}\d{1,2}[A-Z]?)\b',     # "London N8" 或 "London WC1E"
            r',\s+([A-Z]{1,2}\d{1,2}[A-Z]?)\s*$',        # ", N8" 或 ", WC1E" 在末尾
            r'\s+([A-Z]{1,2}\d{1,2}[A-Z]?)\s*$',         # 末尾的 " N8" 或 " WC1E"
            r'\b([A-Z]{1,2}\d{1,2}[A-Z]?)\b',            # 任何位置的邮编前缀
        ]
        for pattern in postcode_patterns:
            match = re.search(pattern, address_upper)
            if match:
                candidate = match.group(1).strip().upper()
                # 验证格式：1-2个字母 + 1-2个数字 + 可选的1个字母
                if re.match(r'^[A-Z]{1,2}\d{1,2}[A-Z]?$', candidate) and len(candidate) >= 2:
                    # 排除完整邮编（如SE1 2LH会被匹配为SE1，但我们要避免这种情况）
                    # 如果候选邮编后面紧跟着空格和数字+字母，说明是完整邮编，跳过
                    candidate_pos = match.end()
                    if candidate_pos < len(address_upper):
                        next_text = address_upper[candidate_pos:candidate_pos+5].strip()
                        # 如果后面是空格+数字+字母，说明是完整邮编，跳过
                        if re.match(r'^\s+\d[A-Z]{2}', next_text):
                            continue
                    postcode = candidate
                    print(f"[SCRAPPER] 从地址文本提取邮编前缀: {postcode}")
                    break
        
        # 从地址文本提取location
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
                print(f"[SCRAPPER] 从地址文本提取地点: {location}")
                break
    
    # 0.4: 如果地址文本中没有，尝试从标题中提取（备选）
    if not postcode and title:
        title_upper = title.upper()
        postcode_patterns = [
            r'LONDON\s+([A-Z]{1,2}\d{1,2}[A-Z]?)\b',     # "London N8" 或 "London WC1E"
            r',\s+([A-Z]{1,2}\d{1,2}[A-Z]?)\s*$',        # ", N8" 或 ", WC1E" 在末尾
            r'\s+([A-Z]{1,2}\d{1,2}[A-Z]?)\s*$',         # 末尾的 " N8" 或 " WC1E"
        ]
        for pattern in postcode_patterns:
            match = re.search(pattern, title_upper)
            if match:
                candidate = match.group(1).strip().upper()
                if re.match(r'^[A-Z]{1,2}\d{1,2}[A-Z]?$', candidate):
                    postcode = candidate
                    print(f"[SCRAPPER] 从标题提取邮编前缀: {postcode}")
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
                    print(f"[SCRAPPER] 从标题提取地点: {location}")
                    break
    
    # 方法1: 从ld+json中提取（备选，优先使用HTML结构提取的邮编）
    if not postcode or not location:
        ldjson = soup.find("script", attrs={"type": "application/ld+json"})
        if ldjson:
            try:
                data = json.loads(ldjson.string)
                
                def extract_postcode_from_ldjson(address_dict):
                    """从ld+json地址中提取邮编前缀"""
                    if not address_dict:
                        return None
                    postal_code = address_dict.get("postalCode") or address_dict.get("postcode")
                    if not postal_code:
                        return None
                    postal_code = str(postal_code).strip().upper()
                    # 如果是完整邮编（如"SE1 2LH"），只提取前缀部分
                    if ' ' in postal_code:
                        parts = postal_code.split()
                        if len(parts) > 0:
                            prefix = parts[0]
                            # 排除Zoopla注册地址邮编
                            if prefix == 'SE1':
                                return None
                            # 验证格式
                            if re.match(r'^[A-Z]{1,2}\d{1,2}[A-Z]?$', prefix):
                                return prefix
                    # 如果已经是前缀格式，直接返回（但要排除SE1）
                    if postal_code == 'SE1':
                        return None
                    if re.match(r'^[A-Z]{1,2}\d{1,2}[A-Z]?$', postal_code):
                        return postal_code
                    return None
                
                # 处理@graph数组
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("@type") in ["Place", "PostalAddress", "RealEstateListing"]:
                            # 跳过RealEstateAgent（可能是Zoopla的注册地址）
                            if item.get("@type") == "RealEstateAgent":
                                continue
                            address = item.get("address") or item
                            if isinstance(address, dict):
                                if not postcode:
                                    extracted = extract_postcode_from_ldjson(address)
                                    if extracted:
                                        postcode = extracted
                                        print(f"[SCRAPPER] 从ld+json提取邮编前缀: {postcode}")
                                if not location:
                                    location = address.get("addressLocality") or address.get("locality")
                                    if not location:
                                        # 尝试从streetAddress中提取
                                        street = address.get("streetAddress", "")
                                        if street:
                                            parts = street.split(',')
                                            if len(parts) > 1:
                                                location = parts[-1].strip()
                elif isinstance(data, dict):
                    # 检查是否有address字段
                    address = data.get("address", {})
                    if isinstance(address, dict):
                        if not postcode:
                            extracted = extract_postcode_from_ldjson(address)
                            if extracted:
                                postcode = extracted
                                print(f"[SCRAPPER] 从ld+json提取邮编前缀: {postcode}")
                        if not location:
                            location = address.get("addressLocality") or address.get("locality")
            except Exception as e:
                print(f"[DEBUG] Failed to parse ld+json for location/postcode: {e}")
    
    # 方法2: 从URL中提取邮编（备用）
    if not postcode and url:
        postcode_pattern = r'[\/\-]([A-Z]{1,2}\d{1,2}[A-Z]?)[\/\-]'
        match = re.search(postcode_pattern, url.upper())
        if match:
            postcode = match.group(1)
            print(f"[SCRAPPER] 从URL提取邮编前缀: {postcode}")
    
    # 方法3: 从页面文本中提取邮编前缀（最后尝试，避免提取完整邮编）
    if not postcode:
        text = soup.get_text()
        # 只提取邮编前缀（如WC1E, N8, SW7等），不提取完整邮编
        # 优先从h1附近的文本区域提取，避免从footer等区域提取
        postcode_prefix_patterns = [
            r'\b([A-Z]{1,2}\d{1,2}[A-Z]?)\b',  # 匹配邮编前缀格式
        ]
        # 先尝试从h1附近的文本中提取
        h1_elements = soup.find_all('h1', limit=3)
        for h1 in h1_elements:
            # 获取h1及其周围500字符的文本
            h1_text = ""
            if h1.parent:
                h1_text = h1.parent.get_text()[:500]
            else:
                h1_text = h1.get_text()
            
            for pattern in postcode_prefix_patterns:
                matches = re.finditer(pattern, h1_text.upper())
                for match in matches:
                    candidate = match.group(1).strip().upper()
                    if re.match(r'^[A-Z]{1,2}\d{1,2}[A-Z]?$', candidate) and len(candidate) >= 2:
                        # 检查后面是否跟着完整邮编的后半部分
                        candidate_pos = match.end()
                        if candidate_pos < len(h1_text):
                            next_text = h1_text[candidate_pos:candidate_pos+5].strip()
                            if re.match(r'^\s+\d[A-Z]{2}', next_text):
                                continue  # 跳过完整邮编
                        postcode = candidate
                        print(f"[SCRAPPER] 从h1附近文本提取邮编前缀: {postcode}")
                        break
                if postcode:
                    break
            if postcode:
                break
        
        # 如果h1附近没找到，再从整个页面文本中提取（但要排除完整邮编）
        if not postcode:
            for pattern in postcode_prefix_patterns:
                matches = re.finditer(pattern, text.upper())
                for match in matches:
                    candidate = match.group(1).strip().upper()
                    if re.match(r'^[A-Z]{1,2}\d{1,2}[A-Z]?$', candidate) and len(candidate) >= 2:
                        # 检查后面是否跟着完整邮编的后半部分
                        candidate_pos = match.end()
                        if candidate_pos < len(text):
                            next_text = text[candidate_pos:candidate_pos+5].strip()
                            if re.match(r'^\s+\d[A-Z]{2}', next_text):
                                continue  # 跳过完整邮编
                        # 排除常见的Zoopla注册地址邮编（如SE1）
                        if candidate == 'SE1':
                            continue
                        postcode = candidate
                        print(f"[SCRAPPER] 从页面文本提取邮编前缀: {postcode}")
                        break
                if postcode:
                    break
    
    # 方法4: 从地址区域提取location（最后尝试）
    if not location:
        # 查找包含"London"或地区名的元素
        address_selectors = [
            '[data-testid*="address"]',
            '.address',
            '[class*="address"]',
            '[itemprop="address"]',
            'h1[class*="title"]',  # 标题可能包含地址
        ]
        for selector in address_selectors:
            elements = soup.select(selector)
            for el in elements:
                text = el.get_text(strip=True)
                # 常见伦敦地区
                london_areas = [
                    'Muswell Hill', 'Hampstead', 'Camden', 'Greenwich',
                    'Shoreditch', 'Battersea', 'Clapham', 'Fulham',
                    'Notting Hill', 'Paddington', 'Marylebone', 'Kensington',
                    'Chelsea', 'Westminster', 'Islington', 'Covent Garden',
                    'Canary Wharf', 'Docklands'
                ]
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

def parse_property_block(block):
    data = {}
    # 1. price
    price_el = block.find(string=lambda t: t and "£" in t)
    if price_el:
        data['price'] = price_el.strip()

    # 2. title
    title_el = block.select_one("h1, .listing-title, .property-title")
    if title_el:
        data['title'] = title_el.get_text(strip=True)

    # 3. room info
    info_block = block.find(string=lambda t: t and "bath" in t.lower())
    if info_block:
        txt = info_block.strip()
        tokens = txt.split()
        for tok in tokens:
            if tok.endswith("bed"):
                data['beds'] = tok
            elif tok.endswith("baths") or tok.endswith("bath"):
                data['baths'] = tok
            elif tok.endswith("receptions"):
                data['receptions'] = tok

    # 4. epc rating
    epc = block.find(string=lambda t: t and "EPC Rating" in t)
    if epc:
        data['epc_rating'] = epc.strip().split(":")[-1].strip()

    # 5. tenure and chain free
    features = block.select("ul li, li")
    for li in features:
        text = li.get_text(strip=True)
        if "Freehold" in text:
            data['tenure'] = text
        if "Chain Free" in text:
            data['chain_free'] = text

    # 6. description
    desc_title = block.find("h2", string="About this property")
    desc_text = ""
    if desc_title:
        for sib in desc_title.find_next_siblings():
            if sib.name in ["h2", "h3"]:
                break
            desc_text += sib.get_text(" ", strip=True) + " "
        data['description'] = desc_text.strip()
        data['description_chinese'] = translate_to_chinese(desc_text.strip())

    return data

def parse_properties(html):
    soup = BeautifulSoup(html, "html.parser")
    properties = []
    # Try to find all property blocks (update selector as needed for Zoopla)
    blocks = soup.select(".listing-results-wrapper, .property-listing, .css-1e28vvi")
    print(f"[DEBUG] Found {len(blocks)} property blocks.")
    if not blocks:
        # Try to extract from ld+json script
        ldjson = soup.find("script", attrs={"type": "application/ld+json"})
        if ldjson:
            import json
            try:
                data = json.loads(ldjson.string)
                # Find SearchResultsPage with ItemList
                for g in data.get("@graph", []):
                    if g.get("@type") == "SearchResultsPage" and "mainEntity" in g:
                        items = g["mainEntity"].get("itemListElement", [])
                        for item in items:
                            prop = {}
                            prod = item.get("item", {})
                            prop["title"] = prod.get("name")
                            prop["description"] = prod.get("description")
                            prop["description_chinese"] = translate_to_chinese(prod.get("description", ""))
                            prop["price"] = "£" + prod.get("offers", {}).get("price", "")
                            prop["url"] = prod.get("url")
                            prop["image"] = prod.get("image")
                            
                            # 提取location和postcode
                            address = prod.get("address", {})
                            if isinstance(address, dict):
                                prop["postcode"] = address.get("postalCode") or address.get("postcode")
                                prop["location"] = address.get("addressLocality") or address.get("locality")
                            
                            properties.append(prop)
                print(f"[DEBUG] Extracted {len(properties)} properties from ld+json.")
            except Exception as e:
                print(f"[DEBUG] Failed to parse ld+json: {e}")
        else:
            print("[DEBUG] No blocks or ld+json found, treating whole page as one property.")
            blocks = [soup]
    if blocks:
        for idx, block in enumerate(blocks):
            print(f"[DEBUG] Block {idx+1} HTML snippet:")
            print(block.prettify()[:500])  # Print first 500 chars for brevity
            prop = parse_property_block(block)
            print(f"[DEBUG] Parsed property {idx+1}: {prop}")
            # Only add if price/title found (avoid empty dicts)
            if prop.get('price') or prop.get('title'):
                properties.append(prop)
    return properties

def fetch_property_html_fast(url, timeout=12):
    """优先用 requests 抓取详情页，失败再由上层回退到 Selenium"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
            'Referer': 'https://www.zoopla.co.uk/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9'
        }
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code == 200 and resp.text:
            return resp.text
        return None
    except Exception:
        return None

def extract_image_urls_from_detail_html(html, base_url: str = ""):
    """从详情页HTML提取所有图片URL"""
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    
    # 方法1: 从所有img和source标签提取
    for el in soup.select('img,source'):
        # 尝试多个属性
        src = (el.get('src') or el.get('data-src') or 
               el.get('data-lazy-src') or el.get('data-original') or
               el.get('srcset') or el.get('data-srcset'))
        if not src:
            continue
        # srcset 取第一个（可能有多个尺寸，如：url1 1x, url2 2x）
        if ' ' in src:
            # 如果是srcset格式，取第一个URL
            parts = src.split(',')
            src = parts[0].strip().split(' ')[0]
        # 相对路径转绝对
        if base_url and src and src.startswith('/'):
            try:
                src = urllib.parse.urljoin(base_url, src)
            except Exception:
                pass
        if src and src.startswith('http') and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
            urls.append(src)
    
    # 方法2: 查找Zoopla特定的图片容器（gallery、carousel等）
    gallery_selectors = [
        '.property-gallery img',
        '.gallery img',
        '.photo-gallery img',
        '.carousel img',
        '[class*="gallery"] img',
        '[class*="photo"] img',
        '[class*="image"] img',
        'picture source',
        'picture img'
    ]
    for selector in gallery_selectors:
        for el in soup.select(selector):
            src = (el.get('src') or el.get('data-src') or 
                   el.get('data-lazy-src') or el.get('data-original') or
                   el.get('srcset') or el.get('data-srcset'))
            if src and ' ' in src:
                src = src.split(' ')[0]
            if src and src.startswith('http') and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                if base_url and src.startswith('/'):
                    src = urllib.parse.urljoin(base_url, src)
                urls.append(src)
    
    # 方法3: 从JavaScript数据中提取（Zoopla可能将图片数据嵌入在JS变量中）
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string:
            js_content = script.string
            # 匹配JSON中的图片URL数组或单个URL
            # 模式1: "image": "https://..."
            # 模式2: "images": ["https://...", "https://..."]
            # 模式3: imageUrl: 'https://...'
            patterns = [
                r'(?:image|photo|src|url)["\']?\s*[:=]\s*["\'](https?://[^"\']+\.(?:jpg|jpeg|png|webp))',
                r'(?:images|photos|gallery)\s*[:=]\s*\[([^\]]+)\]',
                r'["\'](https?://[^"\']*zoocdn[^"\']*\.(?:jpg|jpeg|png|webp))["\']'
            ]
            for pattern in patterns:
                matches = re.findall(pattern, js_content, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]
                    if match and isinstance(match, str) and match.startswith('http'):
                        urls.append(match)
                    elif isinstance(match, str) and ',' in match:
                        # 可能是数组字符串，分割提取
                        for url in match.split(','):
                            url = url.strip().strip('"\'')
                            if url.startswith('http'):
                                urls.append(url)

    # 从 ld+json 中解析 image 字段
    ldjson = soup.find_all("script", attrs={"type": "application/ld+json"})
    for tag in ldjson:
        try:
            data = json.loads(tag.string or '{}')
            if isinstance(data, dict):
                images = data.get('image')
                if isinstance(images, list):
                    for u in images:
                        if isinstance(u, str) and u.startswith('http'):
                            urls.append(u)
                elif isinstance(images, str) and images.startswith('http'):
                    urls.append(images)
        except Exception:
            pass

    # 初始去重（简单字符串去重）
    temp_urls = []
    seen_temp = set()
    for u in urls:
        if u not in seen_temp:
            seen_temp.add(u)
            temp_urls.append(u)
    urls = temp_urls
    
    print(f"[DEBUG] 提取到 {len(urls)} 个图片URL（初始）")
    
    # 智能去重：合并同一图片的不同尺寸版本（Zoopla常见）
    def extract_image_key(url):
        """提取图片的唯一标识（去掉尺寸参数）"""
        # Zoopla格式：https://lid.zoocdn.com/u/480/360/xxxxx.jpg
        # 提取尺寸部分（如480/360）和文件名
        # 匹配 zoocdn.com/u/WIDTH/HEIGHT/ 格式
        match = re.search(r'/(\d+)/(\d+)/([^/]+\.(jpg|jpeg|png|webp))', url.lower())
        if match:
            width, height, filename = int(match.group(1)), int(match.group(2)), match.group(3)
            # 返回（文件名，尺寸）用于排序和去重
            return (filename, width * height)
        # 如果不能匹配，返回完整URL的哈希
        return (url.split('/')[-1] if '/' in url else url, 0)
    
    # 按图片唯一标识分组，每组保留最大尺寸版本
    image_groups = {}
    for url in urls:
        key, size = extract_image_key(url)
        # 如果还没记录，或者当前URL尺寸更大，则更新
        if key not in image_groups or size > image_groups[key][1]:
            image_groups[key] = (url, size)
    
    # 转换为列表并保持顺序（按首次出现的顺序）
    seen_keys = set()
    uniq = []
    for url in urls:
        key, _ = extract_image_key(url)
        if key not in seen_keys:
            seen_keys.add(key)
            # 使用该key组中最大尺寸的URL
            uniq.append(image_groups[key][0])
    
    print(f"[DEBUG] 智能去重后剩余 {len(uniq)} 个唯一图片URL")
    if len(uniq) > 0:
        print(f"[DEBUG] 前3个图片URL示例:")
        for i, url in enumerate(uniq[:3], 1):
            print(f"  {i}. {url[:100]}...")
    
    return uniq

def fetch_all_images_for_property(detail_url):
    """抓取详情页所有图片URL"""
    html = fetch_property_html_fast(detail_url)
    if not html:
        html = fetch_property_html(detail_url)
    if not html:
        return []
    return extract_image_urls_from_detail_html(html, base_url=detail_url)

def validate_property_data(property_data):
    """Validate property data quality"""
    required_fields = ['title', 'url']
    for field in required_fields:
        if not property_data.get(field):
            return False, f"Missing required field: {field}"
    
    # Validate price format
    price = property_data.get('price', '')
    if price:
        numeric_part = price.replace('£', '').replace('pcm', '').replace('pw', '').replace('per week', '')
        numeric_part = numeric_part.replace(',', '').strip()
        if numeric_part and not numeric_part.isdigit():
            return False, f"Invalid price format: {price}"
    
    return True, "Valid"

def deduplicate_properties(properties):
    """Remove duplicate properties based on URL"""
    seen_urls = set()
    unique_properties = []
    
    for prop in properties:
        url = prop.get('url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_properties.append(prop)
    
    return unique_properties

def upload_image_to_cos(property_data):
    """
    上传图片到腾讯云COS
    
    Args:
        property_data: 房产数据字典
        
    Returns:
        更新后的房产数据（包含COS图片URL）
    """
    if not COS_ENABLED:
        print("[INFO] COS uploader not enabled, skipping image upload")
        return property_data
    
    original_image_url = property_data.get('image')
    
    if not original_image_url or not original_image_url.startswith('http'):
        print(f"[INFO] No valid image URL, skipping upload")
        return property_data
    
    try:
        # 创建COS上传器
        cos_uploader = create_cos_uploader(Config())
        
        # 上传图片到COS
        print(f"[COS] Uploading image from {original_image_url}")
        cos_image_url = cos_uploader.upload_image_from_url(original_image_url)
        
        if cos_image_url:
            # 更新房产数据中的图片URL为COS URL
            property_data['image_url'] = cos_image_url
            property_data['original_image_url'] = original_image_url  # 保留原始URL
            print(f"[COS] Image uploaded successfully: {cos_image_url}")
        else:
            print(f"[COS] Failed to upload image, using original URL")
            property_data['image_url'] = original_image_url
        
    except Exception as e:
        print(f"[COS] Error uploading image: {e}")
        # 如果上传失败，使用原始URL
        property_data['image_url'] = original_image_url
    
    return property_data

def save_to_csv_with_metadata(properties, filename="properties.csv", max_images_per_property: int = 0):
    """Save properties to CSV with metadata"""
    if not properties:
        print("[WARNING] No properties to save")
        return
    
    # Add metadata
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[INFO] Saving {len(properties)} properties to {filename} at {timestamp}")
    
    # Validate and deduplicate
    valid_properties = []
    for prop in properties:
        is_valid, message = validate_property_data(prop)
        if is_valid:
            valid_properties.append(prop)
        else:
            print(f"[WARNING] Invalid property data: {message}")
    
    unique_properties = deduplicate_properties(valid_properties)
    print(f"[INFO] After validation and deduplication: {len(unique_properties)} properties")
    
    # 上传图片到COS（如果启用）
    if COS_ENABLED:
        print(f"[INFO] Starting image upload to COS...")
        uploaded_properties = []
        total_props = len(unique_properties)
        for prop_index, prop in enumerate(unique_properties, start=1):
            # 先处理单图（兼容旧逻辑）
            uploaded_prop = upload_image_to_cos(prop)

            # 若存在房源详情URL，则尝试抓取详情页所有图片
            detail_url = prop.get('url')
            if detail_url and detail_url.startswith('http'):
                all_imgs = prop.get('image_urls')
                if not all_imgs:
                    all_imgs = fetch_all_images_for_property(detail_url)
                total_imgs = len(all_imgs)
                uploaded_urls = []
                if all_imgs:
                    # 应用每套房产的最大图片数上限（>0 时生效）
                    if isinstance(max_images_per_property, int) and max_images_per_property and max_images_per_property > 0:
                        all_imgs = all_imgs[:max_images_per_property]
                        total_imgs = len(all_imgs)
                    cos_uploader = create_cos_uploader(Config())
                    for img_index, img_url in enumerate(all_imgs, start=1):
                        print(f"[PROGRESS] Property {prop_index}/{total_props} - Image {img_index}/{total_imgs} downloading & uploading...")
                        # 使用稳定key前缀，便于后续与DB的 order_index 对齐
                        key_prefix = 'property-images'
                        # 传入详情页作为 Referer，提升成功率
                        cos_url = cos_uploader.upload_image_from_url(img_url, object_key=None, key_prefix=key_prefix, referer=detail_url)
                        if cos_url:
                            uploaded_urls.append(cos_url)
                            print(f"[PROGRESS] Property {prop_index}/{total_props} - Image {img_index}/{total_imgs} done")
                        else:
                            print(f"[PROGRESS] Property {prop_index}/{total_props} - Image {img_index}/{total_imgs} failed")
                        time.sleep(0.2)
                if uploaded_urls:
                    uploaded_prop['image_urls'] = uploaded_urls

            uploaded_properties.append(uploaded_prop)
            time.sleep(0.3)  # 避免请求过快
        unique_properties = uploaded_properties
        print(f"[INFO] Image upload completed")
    
    # Write to CSV
    keys = set()
    for prop in unique_properties:
        keys.update(prop.keys())
    keys = list(keys)
    
    with open(filename, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(unique_properties)
    
    print(f"[SUCCESS] Saved {len(unique_properties)} properties to {filename}")


def persist_property_to_db(
    property_service: PropertyService,
    property_data: Dict[str, Any],
    max_images_per_property: int = 0
) -> Tuple[Property, bool]:
    """将房产数据写入数据库，并同步图片"""
    property_payload = property_data.copy()
    image_urls = property_payload.pop("image_urls", []) or []
    
    # 处理主图
    if not property_payload.get("image_url") and image_urls:
        property_payload["image_url"] = image_urls[0]
    if property_payload.get("image"):
        property_payload.setdefault("image_url", property_payload["image"])
    
    property_obj, created = property_service.upsert_property(property_payload)
    print(f"[DB] {'Inserted' if created else 'Updated'} property #{property_obj.id}")
    
    if image_urls:
        if isinstance(max_images_per_property, int) and max_images_per_property > 0:
            image_urls = image_urls[:max_images_per_property]
        for idx, img_url in enumerate(image_urls):
            image_data = {
                "source_url": img_url,
                "image_url": img_url,
                "order_index": idx,
                "is_primary": idx == 0
            }
            property_service.upsert_property_image(property_obj.id, image_data)
    
    return property_obj, created


def detect_listing_type(url):
    """Detect if URL is for sale or for rent"""
    if 'to-rent' in url or '/rent/' in url:
        return 'for_rent'
    elif 'for-sale' in url or '/sale/' in url:
        return 'for_sale'
    else:
        # Default to for_sale for backwards compatibility
        return 'for_sale'

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape properties from Zoopla')
    parser.add_argument('--url', type=str, 
                        default='https://www.zoopla.co.uk/for-sale/property/n10/?q=N10&radius=1&search_source=for-sale',
                        help='URL to scrape from')
    parser.add_argument('--output', type=str, default='properties.csv',
                        help='Output CSV filename')
    parser.add_argument('--max-per-property', type=int, default=0,
                        help='Maximum number of images per property (0 means unlimited)')
    parser.add_argument('--skip-csv', action='store_true',
                        help='Skip exporting CSV after database update')
    
    args = parser.parse_args()
    
    url = args.url
    output_file = args.output
    max_per_property = args.max_per_property
    
    # Detect listing type from URL
    listing_type = detect_listing_type(url)
    print(f"[INFO] Detected listing type: {listing_type}")
    
    print(f"[INFO] Starting property scraping at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[INFO] URL: {url}")
    
    scraped_properties: List[Dict[str, Any]] = []
    
    if is_detail_url(url):
        detail_property = scrape_detail_page(url, listing_type)
        if detail_property:
            scraped_properties.append(detail_property)
    else:
        html = fetch_property_html(url)
        if not html:
            print("[ERROR] Failed to fetch HTML for search results, aborting")
        else:
            listings = extract_listings_from_search_html(html)
            if not listings:
                print("[WARNING] Failed to extract listings from search results, falling back to legacy parser")
                listings = []
                legacy_props = parse_properties(html)
                for legacy in legacy_props:
                    if legacy.get('url'):
                        listings.append({
                            "url": legacy.get('url'),
                            "title": legacy.get('title'),
                            "price_numeric": safe_int(legacy.get('price')),
                            "description": legacy.get('description'),
                            "image": legacy.get('image')
                        })
            print(f"[INFO] Found {len(listings)} listings in search results")
            for index, listing in enumerate(listings, start=1):
                detail_url = listing.get('url')
                if not detail_url:
                    continue
                print(f"[PIPELINE] Processing listing {index}/{len(listings)} -> {detail_url}")
                detail_property = scrape_detail_page(detail_url, listing_type)
                if not detail_property:
                    continue
                # 合并列表页信息作为兜底
                if not detail_property.get('title') and listing.get('title'):
                    detail_property['title'] = listing['title']
                if not detail_property.get('price_numeric') and listing.get('price_numeric') is not None:
                    detail_property['price_numeric'] = listing['price_numeric']
                if not detail_property.get('price'):
                    detail_property['price'] = format_price(listing.get('price_numeric'), listing_type)
                if not detail_property.get('image') and listing.get('image'):
                    detail_property['image'] = listing['image']
                    detail_property.setdefault('image_url', listing['image'])
                scraped_properties.append(detail_property)
    
    if not scraped_properties:
        print("[WARNING] No properties were scraped. Nothing to persist.")
        sys.exit(0)
    
    # 持久化到数据库
    db_manager = DatabaseManager()
    try:
        db_session = db_manager.get_session()
    except Exception as e:
        print(f"[ERROR] Failed to connect to database: {e}")
        sys.exit(1)
    property_service = PropertyService(db_session)
    inserted = 0
    updated = 0
    try:
        for prop_data in scraped_properties:
            prop_obj, created = persist_property_to_db(property_service, prop_data, max_images_per_property=max_per_property)
            if created:
                inserted += 1
            else:
                updated += 1
    except Exception as e:
        print(f"[ERROR] Failed while persisting properties: {e}")
        raise
    finally:
        db_manager.close_session(db_session)
    
    print(f"[DB] Completed persistence. Inserted: {inserted}, Updated: {updated}")
    
    if not args.skip_csv and scraped_properties:
        save_to_csv_with_metadata(scraped_properties, filename=output_file, max_images_per_property=max_per_property)
