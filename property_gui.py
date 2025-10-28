#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
房产数据GUI显示工具
支持图片存储和本地展示
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import os
import requests
from PIL import Image, ImageTk
from io import BytesIO
import threading
import time

class PropertyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("房产数据浏览器")
        self.root.geometry("1200x800")
        
        self.properties = []
        self.current_index = 0
        self.loaded_images = {}  # 缓存加载的图片
        self.image_dir = "property_images"  # 图片存储目录
        
        # 创建图片目录
        if not os.path.exists(self.image_dir):
            os.makedirs(self.image_dir)
        
        # 创建GUI界面
        self.create_widgets()
        
        # 加载数据
        self.load_data()
    
    def create_widgets(self):
        """创建GUI组件"""
        
        # 顶部工具栏
        toolbar = tk.Frame(self.root, bg='#f0f0f0', padx=10, pady=5)
        toolbar.pack(fill=tk.X)
        
        tk.Button(toolbar, text="加载CSV", command=self.load_csv_file).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="下载所有图片", command=self.download_all_images).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="清除图片缓存", command=self.clear_image_cache).pack(side=tk.LEFT, padx=5)
        
        # 主内容区域
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧：房产列表
        left_frame = tk.Frame(main_frame, width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        
        tk.Label(left_frame, text="房产列表", font=('Arial', 12, 'bold')).pack(pady=5)
        
        # 搜索框
        search_frame = tk.Frame(left_frame)
        search_frame.pack(fill=tk.X, pady=5)
        tk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)
        tk.Entry(search_frame, textvariable=self.search_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 列表框和滚动条
        scrollbar = tk.Scrollbar(left_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(left_frame, yscrollcommand=scrollbar.set, font=('Arial', 10))
        self.listbox.pack(fill=tk.BOTH, expand=True)
        self.listbox.bind('<<ListboxSelect>>', self.on_select_property)
        scrollbar.config(command=self.listbox.yview)
        
        # 右侧：房产详情
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 图片区域
        self.image_frame = tk.Frame(right_frame, bg='white', relief=tk.SUNKEN, bd=2)
        self.image_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.image_label = tk.Label(self.image_frame, text="选择房产查看图片", 
                                     bg='white', font=('Arial', 14))
        self.image_label.pack(expand=True)
        
        # 详细信息区域
        info_frame = tk.Frame(right_frame)
        info_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建文本框和滚动条
        info_scroll = tk.Scrollbar(info_frame)
        info_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.info_text = tk.Text(info_frame, yscrollcommand=info_scroll.set, 
                                 font=('Arial', 10), wrap=tk.WORD, bg='#f9f9f9')
        self.info_text.pack(fill=tk.BOTH, expand=True)
        info_scroll.config(command=self.info_text.yview)
        
        # 底部导航按钮
        nav_frame = tk.Frame(self.root, bg='#f0f0f0')
        nav_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
        
        tk.Button(nav_frame, text="上一个", command=self.previous_property).pack(side=tk.LEFT, padx=5)
        tk.Button(nav_frame, text="下一个", command=self.next_property).pack(side=tk.LEFT, padx=5)
        self.index_label = tk.Label(nav_frame, text="0 / 0", font=('Arial', 10))
        self.index_label.pack(side=tk.LEFT, padx=10)
    
    def load_csv_file(self):
        """加载CSV文件"""
        filename = filedialog.askopenfilename(
            title="选择CSV文件",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            self.load_data(filename)
    
    def load_data(self, csv_file="properties.csv"):
        """加载房产数据"""
        if not os.path.exists(csv_file):
            messagebox.showerror("错误", f"文件不存在: {csv_file}")
            return
        
        self.properties = []
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.properties.append(row)
            
            # 更新列表
            self.update_listbox()
            
            # 显示第一个房产
            if self.properties:
                self.current_index = 0
                self.show_property_details()
            
            messagebox.showinfo("成功", f"已加载 {len(self.properties)} 条房产数据")
        except Exception as e:
            messagebox.showerror("错误", f"加载数据失败: {str(e)}")
    
    def update_listbox(self):
        """更新列表框"""
        self.listbox.delete(0, tk.END)
        search_text = self.search_var.get().lower()
        
        for i, prop in enumerate(self.properties):
            display_text = f"{i+1}. {prop.get('title', 'N/A')} - {prop.get('price', 'N/A')}"
            if search_text == "" or search_text in display_text.lower():
                self.listbox.insert(tk.END, display_text)
    
    def on_search_change(self, *args):
        """搜索框内容改变"""
        self.update_listbox()
    
    def on_select_property(self, event):
        """选择房产"""
        selection = self.listbox.curselection()
        if selection:
            self.current_index = selection[0]
            # 调整索引以匹配实际数据
            listbox_items = [i for i in range(len(self.properties)) if self.should_display(i)]
            if self.current_index < len(listbox_items):
                self.current_index = listbox_items[self.current_index]
            self.show_property_details()
    
    def should_display(self, index):
        """判断房产是否应该显示"""
        search_text = self.search_var.get().lower()
        if not search_text:
            return True
        prop = self.properties[index]
        display_text = f"{index+1}. {prop.get('title', 'N/A')} - {prop.get('price', 'N/A')}"
        return search_text in display_text.lower()
    
    def next_property(self):
        """下一个房产"""
        if self.current_index < len(self.properties) - 1:
            self.current_index += 1
            self.show_property_details()
            self.update_listbox_selection()
    
    def previous_property(self):
        """上一个房产"""
        if self.current_index > 0:
            self.current_index -= 1
            self.show_property_details()
            self.update_listbox_selection()
    
    def update_listbox_selection(self):
        """更新列表选择"""
        for i in range(self.listbox.size()):
            self.listbox.selection_clear(i)
        self.listbox.selection_set(self.current_index)
        self.listbox.see(self.current_index)
    
    def show_property_details(self):
        """显示房产详细信息"""
        if not self.properties:
            return
        
        prop = self.properties[self.current_index]
        
        # 更新索引标签
        self.index_label.config(text=f"{self.current_index + 1} / {len(self.properties)}")
        
        # 显示图片
        self.load_image(prop.get('image', ''))
        
        # 显示详细信息
        info = f"""
═══════════════════════════════════════════
房产详细信息
═══════════════════════════════════════════

标题: {prop.get('title', 'N/A')}
价格: {prop.get('price', 'N/A')}

描述（中文）:
{prop.get('description_chinese', 'N/A')}

描述（英文）:
{prop.get('description', 'N/A')}

图片URL: {prop.get('image', 'N/A')}
详情链接: {prop.get('url', 'N/A')}

═══════════════════════════════════════════
"""
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info)
    
    def load_image(self, image_url):
        """加载并显示图片"""
        if not image_url or image_url == '':
            self.image_label.config(image='', text="无图片")
            return
        
        # 尝试从缓存加载
        if image_url in self.loaded_images:
            self.image_label.config(image=self.loaded_images[image_url], text='')
            return
        
        # 尝试从本地加载
        image_path = self.get_local_image_path(image_url)
        if os.path.exists(image_path):
            try:
                img = Image.open(image_path)
                img = self.resize_image(img)
                photo = ImageTk.PhotoImage(img)
                self.loaded_images[image_url] = photo
                self.image_label.config(image=photo, text='')
                return
            except Exception as e:
                print(f"加载本地图片失败: {e}")
        
        # 显示占位符
        self.image_label.config(image='', text="点击'下载所有图片'以加载图片")
    
    def resize_image(self, img, max_size=(600, 400)):
        """调整图片大小"""
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        return img
    
    def get_local_image_path(self, image_url):
        """获取本地图片路径"""
        # 使用URL的文件名
        filename = image_url.split('/')[-1].split('?')[0]
        if not filename or '.' not in filename:
            filename = f"image_{hash(image_url)}.jpg"
        return os.path.join(self.image_dir, filename)
    
    def download_all_images(self):
        """下载所有图片"""
        if not self.properties:
            messagebox.showwarning("警告", "请先加载数据")
            return
        
        # 询问确认
        result = messagebox.askyesno("确认", 
                                     f"将下载 {len(self.properties)} 张图片，确定继续？")
        if not result:
            return
        
        # 在新线程中下载
        thread = threading.Thread(target=self._download_images_thread)
        thread.daemon = True
        thread.start()
    
    def _download_images_thread(self):
        """下载图片线程"""
        total = len(self.properties)
        success = 0
        failed = 0
        
        for i, prop in enumerate(self.properties):
            image_url = prop.get('image', '')
            if image_url and image_url.startswith('http'):
                try:
                    self.download_image(image_url)
                    success += 1
                except Exception as e:
                    print(f"下载失败 {image_url}: {e}")
                    failed += 1
                
                # 更新进度
                progress = (i + 1) / total * 100
                self.root.after(0, lambda p=progress, s=success, f=failed: 
                               self.update_download_status(p, s, f))
        
        self.root.after(0, lambda: messagebox.showinfo("完成", 
                                  f"下载完成！\n成功: {success}\n失败: {failed}"))
    
    def download_image(self, image_url):
        """下载单个图片"""
        local_path = self.get_local_image_path(image_url)
        
        # 如果已存在，跳过
        if os.path.exists(local_path):
            return
        
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            # 保存图片
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            # 如果有图片url，立即显示当前图片
            if self.current_index < len(self.properties):
                current_prop = self.properties[self.current_index]
                if current_prop.get('image') == image_url:
                    self.root.after(0, lambda: self.show_property_details())
        except Exception as e:
            raise Exception(f"下载图片失败: {e}")
    
    def update_download_status(self, progress, success, failed):
        """更新下载状态"""
        self.root.title(f"房产数据浏览器 - 下载中 {progress:.1f}% (成功:{success} 失败:{failed})")
    
    def clear_image_cache(self):
        """清除图片缓存"""
        self.loaded_images = {}
        result = messagebox.askyesno("确认", 
                                    "确定清除所有下载的图片？")
        if result:
            import shutil
            if os.path.exists(self.image_dir):
                shutil.rmtree(self.image_dir)
                os.makedirs(self.image_dir)
                messagebox.showinfo("成功", "图片缓存已清除")
            self.root.title("房产数据浏览器")


def main():
    root = tk.Tk()
    app = PropertyGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()


