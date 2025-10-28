#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速启动GUI工具
"""
import sys
import os

def check_dependencies():
    """检查必要的依赖"""
    try:
        import tkinter
    except ImportError:
        print("错误: 未安装 tkinter，请安装 Python 的 GUI 支持")
        print("Ubuntu/Debian: sudo apt-get install python3-tk")
        print("Windows: tkinter 通常已包含在 Python 中")
        return False
    
    try:
        from PIL import Image
    except ImportError:
        print("错误: 未安装 Pillow")
        print("请运行: pip install Pillow")
        return False
    
    try:
        import requests
    except ImportError:
        print("错误: 未安装 requests")
        print("请运行: pip install requests")
        return False
    
    return True

def main():
    """主函数"""
    print("=" * 50)
    print("房产数据GUI工具")
    print("=" * 50)
    print()
    
    if not check_dependencies():
        print("\n请先安装必要的依赖后再运行")
        sys.exit(1)
    
    # 导入并启动GUI
    try:
        from property_gui import PropertyGUI
        import tkinter as tk
        
        print("正在启动GUI...")
        print()
        
        root = tk.Tk()
        app = PropertyGUI(root)
        
        print("GUI 已启动！")
        print("提示:")
        print("  - 点击'加载CSV'选择数据文件")
        print("  - 点击'下载所有图片'下载房产图片")
        print("  - 在左侧列表中选择房产查看详情")
        print()
        
        root.mainloop()
        
    except Exception as e:
        print(f"启动GUI时发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()


