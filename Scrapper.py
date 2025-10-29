
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
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

# 添加backend目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# 导入COS上传器和配置
try:
    from backend.utils.cos_uploader import create_cos_uploader
    from backend.config import Config
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

def fetch_property_html(url, max_retries=3):
    """Fetch property HTML with retry mechanism and error handling"""
    for attempt in range(max_retries):
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
            # 等待页面加载，特别是图片
            time.sleep(random.uniform(3, 6))  # 增加等待时间确保图片加载
            
            # 尝试滚动页面以触发懒加载图片
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
            except Exception:
                pass
            
            html = driver.page_source
            driver.quit()
            
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
    required_fields = ['title', 'price', 'url']
    for field in required_fields:
        if not property_data.get(field):
            return False, f"Missing required field: {field}"
    
    # Validate price format
    price = property_data.get('price', '')
    if not price.startswith('£') or not price[1:].replace(',', '').isdigit():
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
    
    args = parser.parse_args()
    
    url = args.url
    output_file = args.output
    max_per_property = args.max_per_property
    
    # Detect listing type from URL
    listing_type = detect_listing_type(url)
    print(f"[INFO] Detected listing type: {listing_type}")
    
    print(f"[INFO] Starting property scraping at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[INFO] URL: {url}")
    
    html = fetch_property_html(url)
    if html:
        properties = parse_properties(html)
        # Add listing_type to each property
        for prop in properties:
            prop['listing_type'] = listing_type
        
        print(f"[INFO] Successfully extracted {len(properties)} properties")
        print(f"[INFO] Translation completed for all descriptions")
        
        # Save with validation and deduplication
        save_to_csv_with_metadata(properties, filename=output_file, max_images_per_property=max_per_property)
    else:
        print("[ERROR] Failed to fetch HTML, skipping data processing")
