# -*- coding: utf-8 -*-
"""Test API"""
import requests
import json

def test_api():
    url = "http://localhost:5000/api/properties/1"
    print(f"Testing: {url}")
    
    try:
        response = requests.get(url, timeout=5)
        print(f"Status: {response.status_code}")
        
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # 检查image_url
        if 'data' in data and 'image_url' in data['data']:
            img_url = data['data']['image_url']
            print(f"\n✅ image_url: {img_url[:100]}...")
            if img_url and 'https://' in img_url:
                print("✅ 图片URL有效！")
            else:
                print("❌ 图片URL无效或为空")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()

