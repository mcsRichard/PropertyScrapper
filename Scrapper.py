

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import csv
import requests
import json
import time
import random
from datetime import datetime

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
            time.sleep(random.uniform(2, 5))  # Random delay to avoid detection
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

def save_to_csv_with_metadata(properties, filename="properties.csv"):
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

if __name__ == "__main__":
    url = "https://www.zoopla.co.uk/for-sale/property/n10/?q=N10&radius=1&search_source=for-sale"
    
    print(f"[INFO] Starting property scraping at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    html = fetch_property_html(url)
    if html:
        properties = parse_properties(html)
        print(f"[INFO] Successfully extracted {len(properties)} properties")
        print(f"[INFO] Translation completed for all descriptions")
        
        # Save with validation and deduplication
        save_to_csv_with_metadata(properties)
    else:
        print("[ERROR] Failed to fetch HTML, skipping data processing")
