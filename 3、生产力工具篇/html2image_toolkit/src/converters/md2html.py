import markdown
from pathlib import Path
from bs4 import BeautifulSoup
from src.utils.log_utils import logger

def convert_md_to_html(
    md_file: str | Path,
    output_dir: Path,
    task_name: str = None,
    use_extensions: bool = True
) -> dict | None:
    """
    Markdown转HTML（支持任务目录）
    
    Args:
        md_file: Markdown文件路径
        output_dir: 输出目录（任务目录）
        task_name: 任务名称
        use_extensions: 是否启用Markdown扩展
    
    Returns:
        dict: 处理结果信息
    """
    md_file = Path(md_file)
    if not md_file.exists():
        logger.error(f"Markdown文件不存在: {md_file}")
        return None
    
    # 创建任务子目录
    task_dirs = {
        'html': output_dir / "html",
        'temp': output_dir / ".temp"
    }
    
    for dir_path in task_dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # 输出HTML路径
    output_html_file = task_dirs['html'] / f"{md_file.stem}.html"
    
    try:
        # 读取Markdown内容
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # 配置Markdown扩展
        extensions = []
        if use_extensions:
            extensions = [
                'markdown.extensions.extra',
                'markdown.extensions.codehilite',
                'markdown.extensions.toc',
                'markdown.extensions.sane_lists',
                'markdown.extensions.smarty',
                'markdown.extensions.fenced_code'
            ]
        
        # Markdown转HTML
        md_processor = markdown.Markdown(extensions=extensions)
        html_content = md_processor.convert(md_content)
        
        # 获取目录内容
        toc_content = md_processor.toc if hasattr(md_processor, 'toc') else ""
        
        # 创建完整的HTML文档
        soup = BeautifulSoup('', 'html.parser')
        
        # 创建HTML结构
        html_tag = soup.new_tag('html', lang='zh-CN')
        head_tag = soup.new_tag('head')
        body_tag = soup.new_tag('body')
        
        # 添加meta和title
        head_tag.append(soup.new_tag('meta', charset='utf-8'))
        title_tag = soup.new_tag('title')
        title_tag.string = md_file.stem
        head_tag.append(title_tag)
        
        # 优化CSS样式（保持原样）
        style_tag = soup.new_tag('style')
        style_content = """
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif; 
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            background: white;
        }
        /* ... 其他样式保持不变 ... */
        """
        style_tag.string = style_content
        head_tag.append(style_tag)
        
        # 处理HTML内容，替换[toc]标记
        content_soup = BeautifulSoup(html_content, 'html.parser')
        html_str = str(content_soup)
        
        # 处理目录
        if '<p>[toc]</p>' in html_str and toc_content:
            toc_html = f'''
            <div class="toc-container">
                <div class="toc-title">目录</div>
                {toc_content}
            </div>
            '''
            html_str = html_str.replace('<p>[toc]</p>', toc_html)
        
        # 重新解析为BeautifulSoup对象
        processed_soup = BeautifulSoup(html_str, 'html.parser')
        
        # 处理图片和表格居中
        for img in processed_soup.find_all('img'):
            img['style'] = 'display: block; margin: 15px auto; max-width: 100%; height: auto;'
        
        for table in processed_soup.find_all('table'):
            table['style'] = 'margin: 15px auto;'
        
        # 创建内容包装器
        content_wrapper = soup.new_tag('div', **{'class': 'content-wrapper'})
        for element in processed_soup.children:
            content_wrapper.append(element)
        
        # 组装完整HTML文档
        body_tag.append(content_wrapper)
        html_tag.append(head_tag)
        html_tag.append(body_tag)
        soup.append(html_tag)
        
        # 保存HTML
        with open(output_html_file, 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        
        logger.success(f"Markdown转HTML成功: {md_file} -> {output_html_file}")
        
        return {
            'input_file': str(md_file),
            'output_html': str(output_html_file),
            'html_dir': str(task_dirs['html']),
            'task_dir': str(output_dir),
            'has_toc': bool(toc_content)
        }
    
    except Exception as e:
        logger.error(f"Markdown转HTML失败: {str(e)}", exc_info=True)
        return None