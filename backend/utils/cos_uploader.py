# utils/cos_uploader.py
"""
腾讯云COS图片上传工具
"""
import os
import requests
import hashlib
from datetime import datetime
from typing import Optional
import urllib.parse
import re

try:
    from qcloud_cos import CosConfig
    from qcloud_cos import CosS3Client
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    print("[WARNING] qcloud_cos SDK not available")

class COSUploader:
    """腾讯云COS上传器"""
    
    def __init__(self, secret_id: str, secret_key: str, region: str, bucket: str, domain: str = ''):
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.region = region
        self.bucket = bucket
        self.domain = domain
        self.base_url = f"https://{bucket}.cos.{region}.myqcloud.com"
        
    def _generate_signature(self, method: str, path: str, headers: dict) -> str:
        """生成签名"""
        # 构建签名key
        key_list = []
        for k in sorted(headers.keys()):
            k_lower = k.lower()
            if k_lower.startswith('x-cos-'):
                key_list.append(f"{k_lower}:{headers[k]}")
        
        string_to_sign = f"{method}\n{path}\n\n"
        if key_list:
            string_to_sign += "\n".join(key_list)
        
        signature_string = f"{method}\n{path}\n\n{'\n'.join(key_list)}\n"
        
        # 生成HMAC-SHA1签名
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            signature_string.encode('utf-8'),
            hashlib.sha1
        ).digest()
        
        return signature.hexdigest()
    
    def upload_image_from_url(self, image_url: str, object_key: Optional[str] = None) -> Optional[str]:
        """
        从URL下载图片并上传到COS
        
        Args:
            image_url: 图片URL
            object_key: COS对象key（可选，自动生成）
            
        Returns:
            上传成功后的图片URL
        """
        try:
            # 下载图片
            print(f"[COS] 正在下载图片: {image_url}")
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            image_data = response.content
            
            # 生成对象key
            if not object_key:
                # 从URL提取文件名
                filename = os.path.basename(urllib.parse.urlparse(image_url).path)
                if not filename or '.' not in filename:
                    filename = f"property_{hashlib.md5(image_url.encode()).hexdigest()[:12]}.jpg"
                
                # 添加日期目录
                date_dir = datetime.now().strftime('%Y/%m/%d')
                object_key = f"property-images/{date_dir}/{filename}"
            
            # 上传到COS
            print(f"[COS] 正在上传到: {object_key}")
            result = self._upload_to_cos(image_data, object_key, 'image/jpeg')
            
            if result:
                # 返回图片URL
                if self.domain:
                    image_url = f"https://{self.domain}/{object_key}"
                else:
                    image_url = f"{self.base_url}/{object_key}"
                print(f"[COS] 上传成功: {image_url}")
                return image_url
            else:
                print(f"[COS] 上传失败")
                return None
                
        except Exception as e:
            print(f"[COS] 上传图片失败: {e}")
            return None
    
    def _upload_to_cos(self, data: bytes, object_key: str, content_type: str) -> bool:
        """
        上传数据到COS
        
        Args:
            data: 要上传的数据
            object_key: COS对象key
            content_type: 内容类型
            
        Returns:
            是否成功
        """
        try:
            url = f"{self.base_url}/{object_key}"
            
            headers = {
                'Content-Type': content_type,
                'Content-Length': str(len(data)),
                'x-cos-storage-class': 'STANDARD'
            }
            
            # 使用简单的方式上传（适用于小文件）
            response = requests.put(url, data=data, headers=headers)
            
            if response.status_code in [200, 201]:
                return True
            else:
                print(f"[COS] 上传失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"[COS] 上传异常: {e}")
            return False
    
    def upload_image_from_file(self, file_path: str, object_key: Optional[str] = None) -> Optional[str]:
        """
        从本地文件上传图片到COS
        
        Args:
            file_path: 本地文件路径
            object_key: COS对象key（可选）
            
        Returns:
            上传成功后的图片URL
        """
        try:
            with open(file_path, 'rb') as f:
                image_data = f.read()
            
            if not object_key:
                filename = os.path.basename(file_path)
                date_dir = datetime.now().strftime('%Y/%m/%d')
                object_key = f"property-images/{date_dir}/{filename}"
            
            result = self._upload_to_cos(image_data, object_key, 'image/jpeg')
            
            if result:
                if self.domain:
                    return f"https://{self.domain}/{object_key}"
                else:
                    return f"{self.base_url}/{object_key}"
            return None
            
        except Exception as e:
            print(f"[COS] 上传本地文件失败: {e}")
            return None


class SimpleCOSUploader:
    """使用腾讯云官方SDK的上传器"""
    
    def __init__(self, secret_id: str, secret_key: str, region: str, bucket: str, domain: str = ''):
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.region = region
        self.bucket = bucket
        # 清理domain：去掉注释、空格，验证是否为有效域名格式
        domain_clean = domain.strip() if domain else ''
        # 如果包含注释标记、空格或不是有效域名格式，则清空使用默认COS域名
        if not domain_clean or '#' in domain_clean or '可选' in domain_clean or ' ' in domain_clean or (not domain_clean.startswith(('http://', 'https://')) and '.' not in domain_clean):
            self.domain = ''
        else:
            # 去掉http://或https://前缀（返回URL时再加）
            self.domain = domain_clean.replace('https://', '').replace('http://', '').strip('/')
        
        # 初始化COS客户端
        if SDK_AVAILABLE:
            config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
            self.client = CosS3Client(config)
        else:
            self.client = None
    
    def _get_image_url(self, object_key: str) -> str:
        """生成图片访问URL（统一处理域名逻辑）"""
        if self.domain and self.domain.strip():
            return f"https://{self.domain}/{object_key}"
        else:
            # 使用默认COS域名
            return f"https://{self.bucket}.cos.{self.region}.myqcloud.com/{object_key}"
    
    def _object_exists(self, object_key: str) -> bool:
        """检查对象是否已存在（HEAD）"""
        try:
            if SDK_AVAILABLE and self.client:
                self.client.head_object(Bucket=self.bucket, Key=object_key)
                return True
            # fallback
            url = f"https://{self.bucket}.cos.{self.region}.myqcloud.com/{object_key}"
            resp = requests.head(url, timeout=10)
            return resp.status_code == 200
        except Exception:
            return False

    def _stable_key_from_bytes(self, data: bytes, suggested_ext: str = ".jpg", key_prefix: str = "property-images") -> str:
        """基于内容MD5生成稳定cos_key，避免重复上传"""
        md5_hex = hashlib.md5(data).hexdigest()
        shard = md5_hex[:2]
        ext = suggested_ext if suggested_ext.startswith('.') else f".{suggested_ext}"
        return f"{key_prefix}/{shard}/{md5_hex}{ext}"

    def _normalize_image_url(self, url: str) -> str:
        """清理图片URL，如去掉 .jpg:p 这类后缀和多余参数"""
        if not url:
            return url
        u = url.strip()
        # 去掉以 :p 等后缀（常见于缩略样式）
        # 如 ...jpg:p 或 ...webp:p
        u = re.sub(r"\.(jpg|jpeg|png|webp):[a-z]$", r".\1", u, flags=re.IGNORECASE)
        # 一些 srcset 可能带逗号或空格后的描述，之前已切割，这里兜底
        if ' ' in u:
            u = u.split(' ')[0]
        return u

    def upload_image_from_url(self, image_url: str, object_key: Optional[str] = None, key_prefix: str = "property-images", referer: Optional[str] = None) -> Optional[str]:
        """从URL上传图片到COS（幂等：基于内容MD5 生成key 并先做HEAD检查）"""
        if not SDK_AVAILABLE or not self.client:
            print("[COS] SDK not available, fallback to requests")
            return self._upload_with_requests(image_url, object_key, key_prefix)
        
        try:
            # 下载图片（带UA与Referer，重试）
            image_url = self._normalize_image_url(image_url)
            print(f"[COS] 正在下载: {image_url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
                'Referer': referer or 'https://www.zoopla.co.uk/'
            }
            image_data = None
            last_resp = None
            for _ in range(3):
                try:
                    response = requests.get(image_url, headers=headers, timeout=20)
                    last_resp = response
                    if response.status_code == 200:
                        image_data = response.content
                        break
                except Exception:
                    time.sleep(0.3)
            if image_data is None:
                status = getattr(last_resp, 'status_code', 'NA')
                print(f"[COS] 下载失败 status={status} url={image_url} referer={headers.get('Referer')} 跳过")
                return None

            # 生成稳定对象key（优先用内容MD5）
            if not object_key:
                # 从Content-Type推断扩展名
                content_type = last_resp.headers.get('Content-Type', 'image/jpeg') if last_resp else 'image/jpeg'
                ext = '.jpg'
                if 'png' in content_type:
                    ext = '.png'
                elif 'webp' in content_type:
                    ext = '.webp'
                elif 'jpeg' in content_type or 'jpg' in content_type:
                    ext = '.jpg'
                object_key = self._stable_key_from_bytes(image_data, ext, key_prefix)

            # 存在性检查
            if self._object_exists(object_key):
                return self._get_image_url(object_key)
            
            # 使用SDK上传
            print(f"[COS] 正在上传到: {object_key}")
            response = self.client.put_object(
                Bucket=self.bucket,
                Body=image_data,
                Key=object_key,
                ContentType='image/jpeg'
            )
            
            # 返回图片URL
            result_url = self._get_image_url(object_key)
            print(f"[COS] 上传成功: {result_url}")
            return result_url
                
        except Exception as e:
            print(f"[COS] 上传失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _upload_with_requests(self, image_url: str, object_key: Optional[str] = None, key_prefix: str = "property-images", referer: Optional[str] = None) -> Optional[str]:
        """使用requests上传（备用方案）"""
        try:
            # 下载图片（带UA与Referer，重试）
            image_url = self._normalize_image_url(image_url)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
                'Referer': referer or 'https://www.zoopla.co.uk/'
            }
            image_data = None
            last_resp = None
            for _ in range(3):
                try:
                    response = requests.get(image_url, headers=headers, timeout=20)
                    last_resp = response
                    if response.status_code == 200:
                        image_data = response.content
                        break
                except Exception:
                    time.sleep(0.3)
            if image_data is None:
                status = getattr(last_resp, 'status_code', 'NA')
                print(f"[COS] 下载失败 status={status} url={image_url} referer={headers.get('Referer')} 跳过")
                return None
            
            # 生成稳定对象key
            if not object_key:
                content_type = last_resp.headers.get('Content-Type', 'image/jpeg') if last_resp else 'image/jpeg'
                ext = '.jpg'
                if 'png' in content_type:
                    ext = '.png'
                elif 'webp' in content_type:
                    ext = '.webp'
                elif 'jpeg' in content_type or 'jpg' in content_type:
                    ext = '.jpg'
                object_key = self._stable_key_from_bytes(image_data, ext, key_prefix)

            # 存在性检查
            if self._object_exists(object_key):
                return self._get_image_url(object_key)
            
            # 简单的PUT请求上传（使用默认COS域名进行上传，但返回URL通过_get_image_url生成）
            upload_url = f"https://{self.bucket}.cos.{self.region}.myqcloud.com/{object_key}"
            put_response = requests.put(upload_url, data=image_data)
            
            if put_response.status_code in [200, 201]:
                result_url = self._get_image_url(object_key)
                print(f"[COS] 上传成功: {result_url}")
                return result_url
            else:
                print(f"[COS] 上传失败: {put_response.status_code}")
                return None
                
        except Exception as e:
            print(f"[COS] 上传失败: {e}")
            return None


# 工厂函数
def create_cos_uploader(config) -> SimpleCOSUploader:
    """创建COS上传器实例"""
    return SimpleCOSUploader(
        secret_id=config.COS_SECRET_ID,
        secret_key=config.COS_SECRET_KEY,
        region=config.COS_REGION,
        bucket=config.COS_BUCKET,
        domain=config.COS_DOMAIN
    )

