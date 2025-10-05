

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import csv

def fetch_property_html(url):
    # Set up Selenium Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in headless mode
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('window-size=1920x1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    # Update the path to your chromedriver.exe if needed
    service = Service('C:/Projects/Scrapper/chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(url)
    html = driver.page_source
    driver.quit()
    return html


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

    return data

def parse_properties(html):
    soup = BeautifulSoup(html, "lxml")
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

if __name__ == "__main__":
    url = "https://www.zoopla.co.uk/for-sale/details/69607310/?search_identifier=a11e4602fdf1c0e865ef052e85635098b6810e25e0187a09d72eff9f95eee100&weekly_featured=1&utm_content=featured_listing"
    html = fetch_property_html(url)
    properties = parse_properties(html)
    print(properties)

    # Write to CSV
    if properties:
        keys = set()
        for prop in properties:
            keys.update(prop.keys())
        keys = list(keys)
        with open("properties.csv", "w", newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(properties)
        print(f"[INFO] Saved {len(properties)} properties to properties.csv")
