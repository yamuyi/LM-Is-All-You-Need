# import html2text
# from pathlib import Path

# def convert_html_to_markdown(html_file, markdown_file=None):
#     """
#     简化的HTML文件转Markdown文件函数
    
#     Args:
#         html_file (str): HTML文件路径
#         markdown_file (str): 输出的Markdown文件路径
#     """
#     try:
#         # 设置转换器
#         converter = html2text.HTML2Text()
#         converter.ignore_links = False
#         converter.ignore_images = False
#         converter.body_width = 0
        
#         # 读取HTML
#         with open(html_file, 'r', encoding='utf-8') as f:
#             html_content = f.read()
        
#         # 转换
#         markdown_content = converter.handle(html_content)
        
#         # 确定输出路径
#         if markdown_file is None:
#             markdown_file = Path(html_file).with_suffix('.md')
        
#         # 写入Markdown
#         with open(markdown_file, 'w', encoding='utf-8') as f:
#             f.write(markdown_content)
        
#         print(f"成功转换: {html_file} -> {markdown_file}")
#         return True
        
#     except Exception as e:
#         print(f"转换失败: {e}")
#         return False

# # 使用示例
# if __name__ == "__main__":
#     # 最简单的使用方式
#     convert_html_to_markdown("output.html", "output.md")
    
#     # 或者自动生成输出文件名
#     # convert_html_to_markdown("input.html")


import html2text
from pathlib import Path
import requests
import os
import re
from urllib.parse import urlparse
import hashlib

def download_image(url, image_dir):
    """
    下载远程图片到本地
    
    Args:
        url (str): 图片URL
        image_dir (Path): 图片保存目录
    
    Returns:
        str: 本地图片路径（如果下载失败则返回原URL）
    """
    try:
        # 创建图片目录
        image_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取图片扩展名
        parsed_url = urlparse(url)
        ext = Path(parsed_url.path).suffix
        if not ext:
            ext = '.jpg'  # 默认扩展名
        
        # 生成唯一文件名（使用URL的MD5值）
        url_hash = hashlib.md5(url.encode()).hexdigest()
        filename = f"{url_hash}{ext}"
        local_path = image_dir / filename
        
        # 下载图片
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # 保存图片
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        return str(local_path)
        
    except Exception as e:
        print(f"下载图片失败 {url}: {e}")
        return url

def replace_images_with_local(markdown_content, html_file_path, image_dir_name="images"):
    """
    将markdown中的远程图片链接替换为本地路径
    
    Args:
        markdown_content (str): markdown内容
        html_file_path (str): 原始HTML文件路径
        image_dir_name (str): 图片保存目录名
    
    Returns:
        str: 替换后的markdown内容
    """
    # 获取HTML文件所在目录
    html_dir = Path(html_file_path).parent
    image_dir = html_dir / image_dir_name
    
    # 正则匹配markdown中的图片链接
    pattern = r'!\[(.*?)\]\((https?://[^\s)]+)\)'
    
    def replace_match(match):
        alt_text = match.group(1)
        image_url = match.group(2)
        
        # 下载图片并获取本地路径
        local_path = download_image(image_url, image_dir)
        
        # 如果是本地路径，转换为相对路径
        if local_path.startswith('http'):
            return match.group(0)  # 下载失败，返回原内容
        
        # 计算相对于markdown文件的相对路径
        relative_path = Path(local_path).relative_to(html_dir)
        return f'![{alt_text}]({relative_path})'
    
    # 替换所有图片链接
    return re.sub(pattern, replace_match, markdown_content)

def convert_html_to_markdown(html_file, markdown_file=None, download_images=True):
    """
    增强的HTML文件转Markdown文件函数，支持下载远程图片
    
    Args:
        html_file (str): HTML文件路径
        markdown_file (str): 输出的Markdown文件路径
        download_images (bool): 是否下载远程图片到本地
    """
    try:
        # 设置转换器
        converter = html2text.HTML2Text()
        converter.ignore_links = False
        converter.ignore_images = False
        converter.body_width = 0
        
        # 读取HTML
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 转换
        markdown_content = converter.handle(html_content)
        
        # 下载并替换远程图片
        if download_images:
            markdown_content = replace_images_with_local(markdown_content, html_file)
        
        # 确定输出路径
        if markdown_file is None:
            markdown_file = Path(html_file).with_suffix('.md')
        
        # 写入Markdown
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"成功转换: {html_file} -> {markdown_file}")
        return True
        
    except Exception as e:
        print(f"转换失败: {e}")
        return False

# 使用示例
if __name__ == "__main__":
    # 最简单的使用方式
    convert_html_to_markdown("output.html", "output.md")
    
    # 如果不希望下载图片，可以这样调用：
    # convert_html_to_markdown("output.html", "output.md", download_images=False)