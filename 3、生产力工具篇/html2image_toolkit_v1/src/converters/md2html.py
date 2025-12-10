import markdown
from pathlib import Path
from bs4 import BeautifulSoup
from src.utils.log_utils import logger
from src.utils.file_utils import get_output_path

def convert_md_to_html(
    md_file: str | Path,
    output_html_file: str | Path | None = None,
    use_extensions: bool = True
) -> Path | None:
    """
    Markdown转HTML（支持扩展语法和美化）
    :param md_file: Markdown文件路径
    :param output_html_file: 输出HTML路径（None时自动生成）
    :param use_extensions: 是否启用Markdown扩展
    :return: 输出HTML路径
    """
    md_file = Path(md_file)
    if not md_file.exists():
        logger.error(f"Markdown文件不存在: {md_file}")
        return None
    
    # 自动生成输出路径
    if output_html_file is None:
        from src.config import HTML_OUTPUT_DIR
        output_html_file = get_output_path(md_file, HTML_OUTPUT_DIR, ".html")
    else:
        output_html_file = Path(output_html_file)
    
    try:
        # 读取Markdown内容
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # 配置Markdown扩展
        extensions = []
        if use_extensions:
            extensions = [
                'markdown.extensions.extra',          # 基础扩展
                'markdown.extensions.codehilite',     # 代码高亮
                'markdown.extensions.toc',            # 目录生成
                'markdown.extensions.sane_lists',     # 列表优化
                'markdown.extensions.smarty',         # 智能标点
                'markdown.extensions.fenced_code'     # 围栏代码块
            ]
        
        # Markdown转HTML
        md_processor = markdown.Markdown(extensions=extensions)
        html_content = md_processor.convert(md_content)
        
        # 获取目录内容（如果有的话）
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
        
        # 优化CSS样式 - 包括目录样式
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
        
        /* 目录样式 */
        .toc-container {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            max-width: 800px;
        }
        .toc-title {
            font-size: 1.2em;
            font-weight: bold;
            color: #2d3748;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #4299e1;
        }
        .toc ul {
            list-style-type: none;
            padding-left: 0;
        }
        .toc li {
            margin: 8px 0;
            line-height: 1.4;
        }
        .toc a {
            color: #4a5568;
            text-decoration: none;
            transition: color 0.2s;
            display: inline-block;
            padding: 2px 0;
        }
        .toc a:hover {
            color: #4299e1;
            text-decoration: underline;
        }
        .toc ul ul {
            padding-left: 20px;
            margin-top: 5px;
        }
        .toc ul ul li {
            font-size: 0.9em;
        }
        
        h1, h2, h3, h4, h5, h6 { 
            margin: 20px 0 10px 0;
            color: #2d3748;
            line-height: 1.3;
            scroll-margin-top: 20px;
        }
        h1 { font-size: 1.8em; margin-top: 10px; }
        h2 { font-size: 1.5em; }
        h3 { font-size: 1.3em; }
        
        p { 
            margin: 12px 0;
            text-align: justify;
        }
        
        /* 图片样式优化 */
        img { 
            display: block;
            max-width: 100%;
            height: auto;
            margin: 15px auto;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        /* 表格样式优化 */
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px auto;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            font-size: 0.9em;
        }
        th, td { 
            border: 1px solid #e2e8f0; 
            padding: 8px 12px; 
            text-align: left;
        }
        th { 
            background-color: #f8fafc;
            font-weight: 600;
        }
        tr:nth-child(even) {
            background-color: #f8fafc;
        }
        
        /* 代码块样式 */
        code { 
            background-color: #f7fafc; 
            padding: 2px 6px;
            border-radius: 3px; 
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9em;
        }
        pre { 
            background-color: #f7fafc; 
            padding: 16px; 
            border-radius: 6px; 
            overflow-x: auto;
            margin: 15px 0;
            border-left: 4px solid #4299e1;
        }
        pre code {
            background: none;
            padding: 0;
        }
        
        /* 列表样式 */
        ul, ol {
            margin: 12px 0;
            padding-left: 24px;
        }
        li {
            margin: 4px 0;
        }
        
        /* 引用样式 */
        blockquote {
            border-left: 4px solid #e2e8f0;
            padding: 12px 20px;
            margin: 15px 0;
            background-color: #f8fafc;
            color: #4a5568;
        }
        
        /* 链接样式 */
        a {
            color: #4299e1;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        
        /* 水平线 */
        hr {
            border: none;
            border-top: 1px solid #e2e8f0;
            margin: 20px 0;
        }
        
        /* 添加一些间距和样式优化 */
        .content-wrapper {
            width: 100%;
        }
        """
        style_tag.string = style_content
        head_tag.append(style_tag)
        
        # 处理HTML内容，替换[toc]标记
        content_soup = BeautifulSoup(html_content, 'html.parser')
        
        # 创建内容包装器
        content_wrapper = soup.new_tag('div', **{'class': 'content-wrapper'})
        
        # 方法1：直接在HTML字符串中替换[toc]标记
        # 更简单直接的方法：在转换后的HTML中查找并替换[toc]相关元素
        html_str = str(content_soup)
        
        # 查找可能的[toc]段落（Markdown转换后可能会变成<p>[toc]</p>）
        if '<p>[toc]</p>' in html_str and toc_content:
            # 创建目录HTML
            toc_html = f'''
            <div class="toc-container">
                <div class="toc-title">目录</div>
                {toc_content}
            </div>
            '''
            # 替换[toc]标记
            html_str = html_str.replace('<p>[toc]</p>', toc_html)
        
        # 将处理后的HTML字符串重新解析为BeautifulSoup对象
        processed_soup = BeautifulSoup(html_str, 'html.parser')
        
        # 处理图片和表格居中
        for img in processed_soup.find_all('img'):
            img['style'] = 'display: block; margin: 15px auto; max-width: 100%; height: auto;'
        
        for table in processed_soup.find_all('table'):
            table['style'] = 'margin: 15px auto;'
        
        # 将处理后的内容添加到内容包装器
        for element in processed_soup.children:
            content_wrapper.append(element)
        
        # 将内容包装器添加到body
        body_tag.append(content_wrapper)
        
        # 组装完整HTML文档
        html_tag.append(head_tag)
        html_tag.append(body_tag)
        soup.append(html_tag)
        
        # 保存HTML
        with open(output_html_file, 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        
        logger.success(f"Markdown转HTML成功: {md_file} -> {output_html_file}")
        if toc_content:
            logger.info(f"已生成目录")
        return output_html_file
    
    except Exception as e:
        logger.error(f"Markdown转HTML失败: {str(e)}", exc_info=True)
        return None