import html2text
import requests
import hashlib
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse
from src.utils.log_utils import logger
from src.config import IMAGE_DOWNLOAD_CONFIG

def download_image(url: str, images_dir: Path) -> str:
    """
    下载远程图片到指定目录
    
    Args:
        url: 图片URL
        images_dir: 图片保存目录（相对于当前任务）
    
    Returns:
        str: 本地图片路径（相对路径）
    """
    try:
        images_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成唯一文件名
        url_hash = hashlib.md5(url.encode()).hexdigest()
        ext = Path(urlparse(url).path).suffix or '.jpg'
        filename = f"{url_hash}{ext}"
        local_path = images_dir / filename
        
        # 跳过已下载的图片
        if local_path.exists():
            logger.debug(f"图片已存在，跳过下载: {local_path}")
            return str(filename)  # 返回相对路径
        
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
        return str(filename)  # 返回相对路径
    
    except Exception as e:
        logger.warning(f"图片下载失败: {url} - {str(e)}")
        return url

def replace_images_with_local(markdown_content: str, images_dir: Path, md_file: Path = None) -> str:
    """
    替换Markdown中的远程图片为本地相对路径
    
    Args:
        markdown_content: Markdown内容
        images_dir: 图片保存目录
        md_file: Markdown文件路径（用于计算相对路径）
    
    Returns:
        str: 处理后的Markdown内容
    """
    # 正则匹配Markdown图片格式
    pattern = r'!\[(.*?)\]\((https?://[^\s)]+)\)'
    
    def replace_match(match):
        alt_text = match.group(1)
        image_url = match.group(2)
        
        # 下载图片
        local_filename = download_image(image_url, images_dir)
        
        # 如果下载成功（返回的是文件名而不是URL）
        if not local_filename.startswith('http'):
            # 构建相对于Markdown文件的图片路径
            if md_file and images_dir.is_relative_to(md_file.parent):
                # 计算相对路径
                relative_path = images_dir.relative_to(md_file.parent) / local_filename
                return f'![{alt_text}]({relative_path})'
            else:
                # 如果不在同一目录树，使用绝对路径（相对于images_dir）
                return f'![{alt_text}]({local_filename})'
        
        return match.group(0)  # 保持原样
    
    return re.sub(pattern, replace_match, markdown_content)

def convert_html_to_md(
    html_file: str | Path,
    output_dir: Path,
    download_images: bool = True,
    task_name: str = None
) -> dict | None:
    """
    HTML转换为Markdown（支持按任务保存）
    
    Args:
        html_file: HTML文件路径
        output_dir: 输出目录（任务目录）
        download_images: 是否下载图片
        task_name: 任务名称
    
    Returns:
        dict: 处理结果信息
    """
    html_file = Path(html_file)
    if not html_file.exists():
        logger.error(f"HTML文件不存在: {html_file}")
        return None
    
    # 创建任务子目录
    task_dirs = {
        'markdown': output_dir / "markdown",
        'images': output_dir / "markdown" / "images",
        'temp': output_dir / ".temp"
    }
    
    for dir_path in task_dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # 输出文件路径
    output_md_file = task_dirs['markdown'] / f"{html_file.stem}.md"
    
    try:
        # 优化的转换器配置
        converter = html2text.HTML2Text()
        converter.ignore_links = False
        converter.ignore_images = False
        converter.ignore_emphasis = False
        converter.ignore_tables = False
        converter.body_width = 0
        converter.skip_internal_links = True
        converter.single_line_break = False
        converter.mark_code = True
        
        # 读取HTML内容
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 预处理HTML
        html_content = preprocess_html(html_content)
        
        # 转换为Markdown
        markdown_content = converter.handle(html_content)
        
        # 后处理
        markdown_content = postprocess_markdown(markdown_content)
        
        # 下载并替换远程图片
        if download_images:
            markdown_content = replace_images_with_local(
                markdown_content, 
                task_dirs['images'],
                output_md_file
            )
        
        # 保存Markdown
        with open(output_md_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.success(f"HTML转Markdown成功: {html_file} -> {output_md_file}")
        
        return {
            'input_file': str(html_file),
            'output_md': str(output_md_file),
            'images_dir': str(task_dirs['images']),
            'markdown_dir': str(task_dirs['markdown']),
            'task_dir': str(output_dir)
        }
    
    except Exception as e:
        logger.error(f"HTML转Markdown失败: {str(e)}", exc_info=True)
        return None

def preprocess_html(html_content: str) -> str:
    """预处理HTML，移除可能导致重复的元素"""
    patterns_to_remove = [
        r'<script[^>]*>.*?</script>',
        r'<style[^>]*>.*?</style>',
        r'<!--.*?-->',
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
        line_stripped = line.strip()
        if line_stripped and line_stripped not in seen_lines:
            seen_lines.add(line_stripped)
            unique_lines.append(line)
        elif not line_stripped:
            if not unique_lines or unique_lines[-1].strip():
                unique_lines.append(line)
    
    return '\n'.join(unique_lines)