# import html2text
# import requests
# import hashlib
# import re
# from pathlib import Path
# from urllib.parse import urlparse
# from src.utils.log_utils import logger
# from src.utils.file_utils import get_output_path
# from src.config import IMAGE_OUTPUT_DIR, IMAGE_DOWNLOAD_CONFIG

# def download_image(url: str, image_dir: Path = IMAGE_OUTPUT_DIR) -> str:
#     """下载远程图片到本地（优化错误处理）"""
#     try:
#         image_dir.mkdir(parents=True, exist_ok=True)
        
#         # 生成唯一文件名
#         url_hash = hashlib.md5(url.encode()).hexdigest()
#         ext = Path(urlparse(url).path).suffix or '.jpg'
#         local_path = image_dir / f"{url_hash}{ext}"
        
#         # 跳过已下载的图片
#         if local_path.exists():
#             logger.debug(f"图片已存在，跳过下载: {local_path}")
#             return str(local_path)
        
#         # 下载图片
#         response = requests.get(
#             url,
#             headers={'User-Agent': IMAGE_DOWNLOAD_CONFIG['user_agent']},
#             timeout=IMAGE_DOWNLOAD_CONFIG['timeout'],
#             stream=True
#         )
#         response.raise_for_status()
        
#         # 保存图片
#         with open(local_path, 'wb') as f:
#             for chunk in response.iter_content(chunk_size=8192):
#                 f.write(chunk)
        
#         logger.debug(f"图片下载成功: {url} -> {local_path}")
#         return str(local_path)
    
#     except Exception as e:
#         logger.warning(f"图片下载失败: {url} - {str(e)}")
#         return url

# def replace_images_with_local(markdown_content: str, html_file_path: Path) -> str:
#     """替换Markdown中的远程图片为本地路径"""
#     # 正则匹配Markdown图片格式
#     pattern = r'!\[(.*?)\]\((https?://[^\s)]+)\)'
    
#     def replace_match(match):
#         alt_text = match.group(1)
#         image_url = match.group(2)
        
#         # 下载图片
#         local_path = download_image(image_url)
        
#         # 转换为相对路径（相对于Markdown文件）
#         if not local_path.startswith('http'):
#             md_dir = html_file_path.parent
#             local_path = str(Path(local_path).relative_to(md_dir))
        
#         return f'![{alt_text}]({local_path})'
    
#     return re.sub(pattern, replace_match, markdown_content)

# def convert_html_to_md(
#     html_file: str | Path,
#     output_md_file: str | Path | None = None,
#     download_images: bool = True
# ) -> Path | None:
#     """
#     HTML转Markdown（支持下载远程图片）
#     :param html_file: HTML文件路径
#     :param output_md_file: 输出Markdown路径（None时自动生成）
#     :param download_images: 是否下载远程图片
#     :return: 输出Markdown路径
#     """
#     html_file = Path(html_file)
#     if not html_file.exists():
#         logger.error(f"HTML文件不存在: {html_file}")
#         return None
    
#     # 自动生成输出路径
#     if output_md_file is None:
#         from src.config import MD_OUTPUT_DIR
#         output_md_file = get_output_path(html_file, MD_OUTPUT_DIR, ".md")
#     else:
#         output_md_file = Path(output_md_file)
    
#     try:
#         # 初始化HTML转Markdown转换器
#         converter = html2text.HTML2Text()
#         converter.ignore_links = False
#         converter.ignore_images = False
#         converter.body_width = 0
#         converter.skip_internal_links = True
        
#         # 读取HTML内容
#         with open(html_file, 'r', encoding='utf-8') as f:
#             html_content = f.read()
        
#         # 转换为Markdown
#         markdown_content = converter.handle(html_content)
        
#         # 下载并替换远程图片
#         if download_images:
#             markdown_content = replace_images_with_local(markdown_content, html_file)
        
#         # 保存Markdown
#         with open(output_md_file, 'w', encoding='utf-8') as f:
#             f.write(markdown_content)
        
#         logger.success(f"HTML转Markdown成功: {html_file} -> {output_md_file}")
#         return output_md_file
    
#     except Exception as e:
#         logger.error(f"HTML转Markdown失败: {str(e)}", exc_info=True)
#         return None

import html2text
import requests
import hashlib
import re
from pathlib import Path
from urllib.parse import urlparse
from src.utils.log_utils import logger
from src.utils.file_utils import get_output_path
# 修复：在顶部导入，避免循环依赖
from src.config import IMAGE_OUTPUT_DIR, IMAGE_DOWNLOAD_CONFIG

def download_image(url: str, image_dir: Path = IMAGE_OUTPUT_DIR) -> str:
    """下载远程图片到本地（优化错误处理）"""
    try:
        image_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成唯一文件名
        url_hash = hashlib.md5(url.encode()).hexdigest()
        ext = Path(urlparse(url).path).suffix or '.jpg'
        local_path = image_dir / f"{url_hash}{ext}"
        
        # 跳过已下载的图片
        if local_path.exists():
            logger.debug(f"图片已存在，跳过下载: {local_path}")
            return str(local_path)
        
        # 下载图片
        response = requests.get(
            url,
            headers={'User-Agent': IMAGE_DOWNLOAD_CONFIG['user_agent']},
            timeout=IMAGE_DOWNLOAD_CONFIG['timeout'],
            stream=True
        )
        response.raise_for_status()
        
        # 保存图片
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.debug(f"图片下载成功: {url} -> {local_path}")
        return str(local_path)
    
    except Exception as e:
        logger.warning(f"图片下载失败: {url} - {str(e)}")
        return url

def replace_images_with_local(markdown_content: str, html_file_path: Path) -> str:
    """替换Markdown中的远程图片为本地路径"""
    # 正则匹配Markdown图片格式
    pattern = r'!\[(.*?)\]\((https?://[^\s)]+)\)'
    
    def replace_match(match):
        alt_text = match.group(1)
        image_url = match.group(2)
        
        # 下载图片
        local_path = download_image(image_url)
        
        # 转换为相对路径（相对于Markdown文件）
        if not local_path.startswith('http'):
            md_dir = html_file_path.parent
            try:
                local_path = str(Path(local_path).relative_to(md_dir))
            except ValueError:
                # 如果不在同一目录，使用绝对路径
                pass
        
        return f'![{alt_text}]({local_path})'
    
    return re.sub(pattern, replace_match, markdown_content)

# def convert_html_to_md(
#     html_file: str | Path,
#     output_md_file: str | Path | None = None,
#     download_images: bool = True
# ) -> Path | None:
#     """
#     HTML转Markdown（支持下载远程图片）
#     :param html_file: HTML文件路径
#     :param output_md_file: 输出Markdown路径（None时自动生成）
#     :param download_images: 是否下载远程图片
#     :return: 输出Markdown路径
#     """
#     html_file = Path(html_file)
#     if not html_file.exists():
#         logger.error(f"HTML文件不存在: {html_file}")
#         return None
    
#     # 自动生成输出路径
#     if output_md_file is None:
#         from src.config import MD_OUTPUT_DIR
#         output_md_file = get_output_path(html_file, MD_OUTPUT_DIR, ".md")
#     else:
#         output_md_file = Path(output_md_file)
    
#     try:
#         # 初始化HTML转Markdown转换器
#         converter = html2text.HTML2Text()
#         converter.ignore_links = False
#         converter.ignore_images = False
#         converter.body_width = 0
#         converter.skip_internal_links = True
        
#         # 读取HTML内容
#         with open(html_file, 'r', encoding='utf-8') as f:
#             html_content = f.read()
        
#         # 转换为Markdown
#         markdown_content = converter.handle(html_content)
        
#         # 下载并替换远程图片
#         if download_images:
#             markdown_content = replace_images_with_local(markdown_content, html_file)
        
#         # 保存Markdown
#         with open(output_md_file, 'w', encoding='utf-8') as f:
#             f.write(markdown_content)
        
#         logger.success(f"HTML转Markdown成功: {html_file} -> {output_md_file}")
#         return output_md_file
    
#     except Exception as e:
#         logger.error(f"HTML转Markdown失败: {str(e)}", exc_info=True)
#         return None

# def convert_html_to_md(
#     html_file: str | Path,
#     output_md_file: str | Path | None = None,
#     download_images: bool = True
# ) -> Path | None:
#     html_file = Path(html_file)
#     if not html_file.exists():
#         logger.error(f"HTML文件不存在: {html_file}")
#         return None
    
#     if output_md_file is None:
#         from src.config import MD_OUTPUT_DIR
#         output_md_file = get_output_path(html_file, MD_OUTPUT_DIR, ".md")
#     else:
#         output_md_file = Path(output_md_file)
    
#     try:
#         # 优化html2text配置
#         converter = html2text.HTML2Text()
#         converter.ignore_links = False
#         converter.ignore_images = False
#         converter.body_width = 0  # 禁用自动换行
#         converter.skip_internal_links = True
#         converter.bypass_tables = False
#         converter.mark_code = True
#         converter.single_line_break = True
        
#         # 读取HTML内容
#         with open(html_file, 'r', encoding='utf-8') as f:
#             html_content = f.read()
        
#         # 直接转换，避免额外处理
#         markdown_content = converter.handle(html_content)
        
#         # 仅在需要时处理图片
#         if download_images:
#             markdown_content = replace_images_with_local(markdown_content, html_file)
        
#         # 保存Markdown
#         output_md_file.parent.mkdir(parents=True, exist_ok=True)
#         with open(output_md_file, 'w', encoding='utf-8') as f:
#             f.write(markdown_content)
        
#         logger.success(f"HTML转Markdown成功: {html_file} -> {output_md_file}")
#         return output_md_file
    
#     except Exception as e:
#         logger.error(f"HTML转Markdown失败: {str(e)}", exc_info=True)
#         return None

def convert_html_to_md(
    html_file: str | Path,
    output_md_file: str | Path | None = None,
    download_images: bool = True
) -> Path | None:
    
    html_file = Path(html_file)
    if not html_file.exists():
        logger.error(f"HTML文件不存在: {html_file}")
        return None
    
    if output_md_file is None:
        from src.config import MD_OUTPUT_DIR
        output_md_file = get_output_path(html_file, MD_OUTPUT_DIR, ".md")
    else:
        output_md_file = Path(output_md_file)
    
    try:
        # 优化的转换器配置
        converter = html2text.HTML2Text()
        converter.ignore_links = False
        converter.ignore_images = False
        converter.ignore_emphasis = False  # 新增
        converter.ignore_tables = False    # 新增
        converter.body_width = 0
        converter.skip_internal_links = True
        converter.single_line_break = False  # 重要：避免单行换行问题
        converter.mark_code = True          # 代码标记
        
        # 读取HTML内容
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 可选：预处理HTML，移除可能的重复内容
        html_content = preprocess_html(html_content)
        
        # 转换为Markdown
        markdown_content = converter.handle(html_content)
        
        # 后处理：移除可能的重复内容
        markdown_content = postprocess_markdown(markdown_content)
        
        # 下载并替换远程图片
        if download_images:
            markdown_content = replace_images_with_local(markdown_content, html_file)
        
        # 保存Markdown
        output_md_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_md_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.success(f"HTML转Markdown成功: {html_file} -> {output_md_file}")
        return output_md_file
    
    except Exception as e:
        logger.error(f"HTML转Markdown失败: {str(e)}", exc_info=True)
        return None

def preprocess_html(html_content: str) -> str:
    """预处理HTML，移除可能导致重复的元素"""
    # 移除常见的重复容器（根据实际情况调整）
    patterns_to_remove = [
        r'<script[^>]*>.*?</script>',  # 脚本
        r'<style[^>]*>.*?</style>',    # 样式
        r'<!--.*?-->',                 # 注释
    ]
    
    for pattern in patterns_to_remove:
        html_content = re.sub(pattern, '', html_content, flags=re.DOTALL)
    
    return html_content

def postprocess_markdown(markdown_content: str) -> str:
    """后处理Markdown，移除重复内容"""
    lines = markdown_content.split('\n')
    seen_lines = set()
    unique_lines = []
    
    for line in lines:
        # 跳过空行和重复行
        line_stripped = line.strip()
        if line_stripped and line_stripped not in seen_lines:
            seen_lines.add(line_stripped)
            unique_lines.append(line)
        elif not line_stripped:
            # 保留空行但避免连续多个空行
            if not unique_lines or unique_lines[-1].strip():
                unique_lines.append(line)
    
    return '\n'.join(unique_lines)