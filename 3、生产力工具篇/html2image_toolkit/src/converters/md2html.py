import markdown
from pathlib import Path
from bs4 import BeautifulSoup
import shutil
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
        'images': output_dir / "html" / "images",  # 专门存放HTML中的图片
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
        html_tag = soup.new_tag('html')
        html_tag['lang'] = 'zh-CN'
        
        head_tag = soup.new_tag('head')
        body_tag = soup.new_tag('body')
        
        # 添加meta和title
        meta_charset = soup.new_tag('meta')
        meta_charset['charset'] = 'utf-8'
        head_tag.append(meta_charset)
        
        title_tag = soup.new_tag('title')
        title_tag.string = md_file.stem
        head_tag.append(title_tag)
        
        # 添加viewport标签，确保移动端适配
        viewport_tag = soup.new_tag('meta')
        viewport_tag['name'] = 'viewport'
        viewport_tag['content'] = 'width=device-width, initial-scale=1.0'
        head_tag.append(viewport_tag)
        
        # 优化CSS样式 - 增加字体大小以便在图片中清晰显示
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
            padding: 40px;
            line-height: 1.8;
            background: white;
            font-size: 18px;  /* 增加基础字体大小 */
            color: #333;
        }
        
        h1 {
            font-size: 32px;  /* 增加h1字体大小 */
            margin: 30px 0 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #eaeaea;
            font-weight: 700;
            color: #222;
        }
        
        h2 {
            font-size: 28px;  /* 增加h2字体大小 */
            margin: 28px 0 18px;
            padding-bottom: 8px;
            border-bottom: 2px solid #f0f0f0;
            font-weight: 600;
            color: #333;
        }
        
        h3 {
            font-size: 24px;  /* 增加h3字体大小 */
            margin: 24px 0 16px;
            font-weight: 600;
            color: #444;
        }
        
        h4 {
            font-size: 20px;  /* 增加h4字体大小 */
            margin: 20px 0 14px;
            font-weight: 600;
            color: #555;
        }
        
        h5, h6 {
            font-size: 18px;  /* 增加h5,h6字体大小 */
            margin: 18px 0 12px;
            font-weight: 600;
            color: #666;
        }
        
        p {
            margin: 16px 0;
            text-align: justify;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        
        a {
            color: #0070f3;
            text-decoration: none;
            border-bottom: 1px solid transparent;
            transition: border-color 0.2s;
        }
        
        a:hover {
            border-bottom-color: #0070f3;
        }
        
        /* 代码块样式 */
        pre {
            background: #f8f8f8;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            overflow-x: auto;
            border: 1px solid #eaeaea;
            font-size: 16px;  /* 代码字体大小 */
        }
        
        code {
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
            background: #f5f5f5;
            padding: 3px 6px;
            border-radius: 4px;
            font-size: 16px;  /* 行内代码字体大小 */
            color: #d63384;
        }
        
        pre code {
            background: transparent;
            padding: 0;
            color: #333;
            font-size: 16px;  /* 代码块内代码字体大小 */
        }
        
        /* 表格样式 */
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            font-size: 17px;  /* 表格字体大小 */
        }
        
        th, td {
            border: 1px solid #ddd;
            padding: 12px 15px;
            text-align: left;
        }
        
        th {
            background-color: #f8f9fa;
            font-weight: 600;
        }
        
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        
        /* 列表样式 */
        ul, ol {
            margin: 16px 0;
            padding-left: 30px;
        }
        
        li {
            margin: 8px 0;
            line-height: 1.8;
        }
        
        /* 引用块样式 */
        blockquote {
            border-left: 4px solid #0070f3;
            margin: 20px 0;
            padding: 15px 20px;
            background-color: #f9f9f9;
            border-radius: 0 4px 4px 0;
            font-size: 17px;  /* 引用块字体大小 */
        }
        
        blockquote p {
            margin: 0;
        }
        
        /* 图片样式 */
        img {
            display: block;
            margin: 25px auto;
            max-width: 100%;
            height: auto;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        /* 目录样式 */
        .toc-container {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 25px 0;
            border: 1px solid #eaeaea;
        }
        
        .toc-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 10px;
            color: #333;
        }
        
        .toc ul {
            list-style-type: none;
            padding-left: 0;
        }
        
        .toc ul ul {
            padding-left: 20px;
        }
        
        .toc li {
            margin: 6px 0;
        }
        
        .toc a {
            color: #555;
            text-decoration: none;
        }
        
        .toc a:hover {
            color: #0070f3;
        }
        
        /* 分割线 */
        hr {
            border: none;
            border-top: 2px solid #eaeaea;
            margin: 30px 0;
        }
        
        /* 脚注 */
        .footnote {
            font-size: 14px;
            color: #666;
        }
        
        /* 内容包装器 */
        .content-wrapper {
            max-width: 100%;
            overflow-wrap: break-word;
        }
        
        /* 打印优化 */
        @media print {
            body {
                padding: 0;
                font-size: 16pt;
            }
            
            h1 { font-size: 28pt; }
            h2 { font-size: 24pt; }
            h3 { font-size: 20pt; }
            h4 { font-size: 18pt; }
            
            pre, code {
                font-size: 14pt;
            }
            
            table {
                font-size: 15pt;
            }
        }
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
                <div class="toc">
                    {toc_content}
                </div>
            </div>
            '''
            html_str = html_str.replace('<p>[toc]</p>', toc_html)
        
        # 重新解析为BeautifulSoup对象
        processed_soup = BeautifulSoup(html_str, 'html.parser')
        
        # 查找并处理所有图片标签
        for img in processed_soup.find_all('img'):
            img_src = img.get('src', '')
            
            if img_src:
                # 尝试解析图片路径
                img_path = Path(img_src)
                
                # 如果是相对路径，尝试基于Markdown文件位置查找
                if not img_path.is_absolute():
                    # 尝试几种可能的路径
                    possible_paths = []
                    
                    # 1. 相对于Markdown文件本身
                    possible_paths.append(md_file.parent / img_src)
                    
                    # 2. 如果Markdown文件在markdown目录中，尝试相对于markdown目录
                    if "markdown" in str(md_file.parent):
                        # 相对于markdown目录
                        possible_paths.append(md_file.parent / img_src)
                        # 相对于markdown的父目录
                        possible_paths.append(md_file.parent.parent / img_src)
                    
                    # 3. 尝试从images目录查找
                    if md_file.parent.name == "markdown":
                        # 在markdown目录中查找images子目录
                        images_dir = md_file.parent / "images"
                        if images_dir.exists():
                            possible_paths.append(images_dir / Path(img_src).name)
                    
                    # 查找存在的图片文件
                    found = False
                    for possible_path in possible_paths:
                        if possible_path.exists() and possible_path.is_file():
                            # 将图片复制到HTML的images目录
                            target_img_name = f"{md_file.stem}_{Path(img_src).name}"
                            target_img_path = task_dirs['images'] / target_img_name
                            
                            try:
                                shutil.copy2(possible_path, target_img_path)
                                # 更新图片src为相对路径（相对于HTML文件）
                                img['src'] = f"images/{target_img_name}"
                                found = True
                                logger.info(f"复制图片: {possible_path} -> {target_img_path}")
                                break
                            except Exception as e:
                                logger.warning(f"复制图片失败 {possible_path}: {e}")
                                continue
                    
                    if not found:
                        logger.warning(f"未找到图片: {img_src}")
                
                # 设置图片样式
                img['style'] = 'display: block; margin: 25px auto; max-width: 100%; height: auto; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'
        
        # 处理表格居中
        for table in processed_soup.find_all('table'):
            table['style'] = 'margin: 20px auto; width: 100%; border-collapse: collapse;'
        
        # 处理代码块的高亮
        for pre in processed_soup.find_all('pre'):
            pre['style'] = 'background: #f8f8f8; border-radius: 8px; padding: 20px; margin: 20px 0; overflow-x: auto; border: 1px solid #eaeaea;'
        
        # 创建内容包装器
        content_wrapper = soup.new_tag('div')
        content_wrapper['class'] = 'content-wrapper'
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
            'images_dir': str(task_dirs['images']),
            'task_dir': str(output_dir),
            'has_toc': bool(toc_content)
        }
    
    except Exception as e:
        logger.error(f"Markdown转HTML失败: {str(e)}", exc_info=True)
        return None