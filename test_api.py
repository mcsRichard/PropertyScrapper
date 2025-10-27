# -*- coding: utf-8 -*-
import requests
import json
import sys

def test():
    url = "http://localhost:5000/api/properties/1"
    print(f"Testing: {url}")
    
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        
        print(f"Status: {r.status_code}")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        if 'data' in data and 'image_url' in data['data']:
            img = data['data']['image_url']
            print(f"\nimage_url: {img[:80]}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test()

