# -*- coding: utf-8 -*-
"""Test API after server restart"""
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import requests
import json

print("=" * 80)
print("测试API服务器是否正常工作")
print("=" * 80)

# Test for_sale
print("\n测试 for_sale 查询...")
r = requests.get('http://localhost:5000/api/properties?listing_type=for_sale&limit=3')
data = r.json()
print(f"  总数: {data['data']['pagination']['total']}")
print(f"  返回: {len(data['data']['properties'])} 条")
for prop in data['data']['properties']:
    print(f"  - Type: {prop['listing_type']}, Title: {prop['title'][:40]}...")

# Test for_rent
print("\n测试 for_rent 查询...")
r = requests.get('http://localhost:5000/api/properties?listing_type=for_rent&limit=3')
data = r.json()
print(f"  总数: {data['data']['pagination']['total']}")
print(f"  返回: {len(data['data']['properties'])} 条")
for prop in data['data']['properties']:
    print(f"  - Type: {prop['listing_type']}, Title: {prop['title'][:40]}...")

print("\n" + "=" * 80)
print("测试完成!")
print("=" * 80)

# 验证结果
print("\n验证:")
if r.status_code == 200:
    sale_data = requests.get('http://localhost:5000/api/properties?listing_type=for_sale&limit=1').json()
    rent_data = requests.get('http://localhost:5000/api/properties?listing_type=for_rent&limit=1').json()
    
    sale_correct = sale_data['data']['pagination']['total'] == 28
    rent_correct = rent_data['data']['pagination']['total'] == 27
    
    if sale_correct and rent_correct:
        print("✅ API工作正常! 数据类型和数量都正确")
    else:
        print("❌ API仍然有问题")
        print(f"   for_sale total: {sale_data['data']['pagination']['total']} (应该是28)")
        print(f"   for_rent total: {rent_data['data']['pagination']['total']} (应该是27)")
        print("\n请确认已重启API服务器")
else:
    print(f"❌ API请求失败: {r.status_code}")

