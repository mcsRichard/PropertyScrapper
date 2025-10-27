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
        self.domain = domain
        
        # 初始化COS客户端
        if SDK_AVAILABLE:
            config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
            self.client = CosS3Client(config)
        else:
            self.client = None
    
    def upload_image_from_url(self, image_url: str, object_key: Optional[str] = None) -> Optional[str]:
        """从URL上传图片到COS"""
        if not SDK_AVAILABLE or not self.client:
            print("[COS] SDK not available, fallback to requests")
            return self._upload_with_requests(image_url, object_key)
        
        try:
            # 下载图片
            print(f"[COS] 正在下载: {image_url}")
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            image_data = response.content
            
            # 生成对象key
            if not object_key:
                filename = os.path.basename(urllib.parse.urlparse(image_url).path)
                if not filename or '.' not in filename:
                    filename = f"property_{hashlib.md5(image_url.encode()).hexdigest()[:12]}.jpg"
                date_dir = datetime.now().strftime('%Y/%m/%d')
                object_key = f"property-images/{date_dir}/{filename}"
            
            # 使用SDK上传
            print(f"[COS] 正在上传到: {object_key}")
            response = self.client.put_object(
                Bucket=self.bucket,
                Body=image_data,
                Key=object_key,
                ContentType='image/jpeg'
            )
            
            # 返回图片URL
            if self.domain:
                result_url = f"https://{self.domain}/{object_key}"
            else:
                result_url = f"https://{self.bucket}.cos.{self.region}.myqcloud.com/{object_key}"
            
            print(f"[COS] 上传成功: {result_url}")
            return result_url
                
        except Exception as e:
            print(f"[COS] 上传失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _upload_with_requests(self, image_url: str, object_key: Optional[str] = None) -> Optional[str]:
        """使用requests上传（备用方案）"""
        try:
            # 下载图片
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            image_data = response.content
            
            # 生成对象key
            if not object_key:
                filename = os.path.basename(urllib.parse.urlparse(image_url).path)
                if not filename or '.' not in filename:
                    filename = f"property_{hashlib.md5(image_url.encode()).hexdigest()[:12]}.jpg"
                date_dir = datetime.now().strftime('%Y/%m/%d')
                object_key = f"property-images/{date_dir}/{filename}"
            
            # 简单的PUT请求上传
            url = f"https://{self.bucket}.cos.{self.region}.myqcloud.com/{object_key}"
            put_response = requests.put(url, data=image_data)
            
            if put_response.status_code in [200, 201]:
                result_url = f"https://{self.bucket}.cos.{self.region}.myqcloud.com/{object_key}"
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

