# import markdown
# from pathlib import Path
# from bs4 import BeautifulSoup
# from src.utils.log_utils import logger
# from src.utils.file_utils import get_output_path

# def convert_md_to_html(
#     md_file: str | Path,
#     output_html_file: str | Path | None = None,
#     use_extensions: bool = True
# ) -> Path | None:
#     """
#     Markdown转HTML（支持扩展语法和美化）
#     :param md_file: Markdown文件路径
#     :param output_html_file: 输出HTML路径（None时自动生成）
#     :param use_extensions: 是否启用Markdown扩展
#     :return: 输出HTML路径
#     """
#     md_file = Path(md_file)
#     if not md_file.exists():
#         logger.error(f"Markdown文件不存在: {md_file}")
#         return None
    
#     # 自动生成输出路径
#     if output_html_file is None:
#         from src.config import HTML_OUTPUT_DIR
#         output_html_file = get_output_path(md_file, HTML_OUTPUT_DIR, ".html")
#     else:
#         output_html_file = Path(output_html_file)
    
#     try:
#         # 读取Markdown内容
#         with open(md_file, 'r', encoding='utf-8') as f:
#             md_content = f.read()
        
#         # 配置Markdown扩展
#         extensions = []
#         if use_extensions:
#             extensions = [
#                 'extra',          # 基础扩展（表格、代码块等）
#                 'codehilite',     # 代码高亮
#                 'toc',            # 目录生成
#                 'sane_lists',     # 列表优化
#                 'smarty',         # 智能标点
#                 'fenced_code'     # 围栏代码块
#             ]
        
#         # Markdown转HTML
#         html_content = markdown.markdown(md_content, extensions=extensions)
        
#         # 美化HTML（添加基础样式）
#         soup = BeautifulSoup(html_content, 'html.parser')
#         html_tag = soup.new_tag('html', lang='zh-CN')
#         head_tag = soup.new_tag('head')
#         body_tag = soup.new_tag('body')
        
#         # 添加基础样式（优化显示效果）
#         style_tag = soup.new_tag('style')
#         style_content = """
#         body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; line-height: 1.6; }
#         h1, h2, h3, h4 { margin-top: 24px; margin-bottom: 16px; color: #2d3748; }
#         img { max-width: 100%; height: auto; border-radius: 4px; margin: 16px 0; }
#         code { background-color: #f7fafc; padding: 2px 4px; border-radius: 4px; font-family: monospace; }
#         pre { background-color: #f7fafc; padding: 16px; border-radius: 4px; overflow-x: auto; }
#         table { border-collapse: collapse; width: 100%; margin: 16px 0; }
#         th, td { border: 1px solid #e2e8f0; padding: 8px 12px; text-align: left; }
#         th { background-color: #f7fafc; }
#         """
#         style_tag.string = style_content
        
#         # 组装HTML结构
#         head_tag.append(style_tag)
#         head_tag.append(soup.new_tag('meta', charset='utf-8'))
#         head_tag.append(soup.new_tag('title', string=md_file.stem))
#         body_tag.append(soup)
#         html_tag.append(head_tag)
#         html_tag.append(body_tag)
        
#         # 保存HTML
#         with open(output_html_file, 'w', encoding='utf-8') as f:
#             f.write(soup.prettify())
        
#         logger.success(f"Markdown转HTML成功: {md_file} -> {output_html_file}")
#         return output_html_file
    
#     except Exception as e:
#         logger.error(f"Markdown转HTML失败: {str(e)}", exc_info=True)
#         return None


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
                'extra',          # 基础扩展（表格、代码块等）
                'codehilite',     # 代码高亮
                'toc',            # 目录生成
                'sane_lists',     # 列表优化
                'smarty',         # 智能标点
                'fenced_code'     # 围栏代码块
            ]
        
        # Markdown转HTML
        html_content = markdown.markdown(md_content, extensions=extensions)
        
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
        
        # 优化CSS样式 - 减少边距，优化图片和表格显示
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
        h1, h2, h3, h4, h5, h6 { 
            margin: 20px 0 10px 0;
            color: #2d3748;
            line-height: 1.3;
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
        """
        style_tag.string = style_content
        head_tag.append(style_tag)
        
        # 将转换的HTML内容添加到body
        content_soup = BeautifulSoup(html_content, 'html.parser')
        
        # 进一步处理内容，确保图片和表格居中
        for img in content_soup.find_all('img'):
            img['style'] = 'display: block; margin: 15px auto; max-width: 100%; height: auto;'
        
        for table in content_soup.find_all('table'):
            table['style'] = 'margin: 15px auto;'
        
        body_tag.append(content_soup)
        
        # 组装完整HTML文档
        html_tag.append(head_tag)
        html_tag.append(body_tag)
        soup.append(html_tag)
        
        # 保存HTML
        with open(output_html_file, 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        
        logger.success(f"Markdown转HTML成功: {md_file} -> {output_html_file}")
        return output_html_file
    
    except Exception as e:
        logger.error(f"Markdown转HTML失败: {str(e)}", exc_info=True)
        return None
# def convert_md_to_html(
#     md_file: str | Path,
#     output_html_file: str | Path | None = None,
#     use_extensions: bool = True
# ) -> Path | None:
#     """
#     Markdown转HTML（支持扩展语法和美化）
#     :param md_file: Markdown文件路径
#     :param output_html_file: 输出HTML路径（None时自动生成）
#     :param use_extensions: 是否启用Markdown扩展
#     :return: 输出HTML路径
#     """
#     md_file = Path(md_file)
#     if not md_file.exists():
#         logger.error(f"Markdown文件不存在: {md_file}")
#         return None
    
#     # 自动生成输出路径
#     if output_html_file is None:
#         from src.config import HTML_OUTPUT_DIR
#         output_html_file = get_output_path(md_file, HTML_OUTPUT_DIR, ".html")
#     else:
#         output_html_file = Path(output_html_file)
    
#     try:
#         # 读取Markdown内容
#         with open(md_file, 'r', encoding='utf-8') as f:
#             md_content = f.read()
        
#         # 配置Markdown扩展
#         extensions = []
#         if use_extensions:
#             extensions = [
#                 'extra',          # 基础扩展（表格、代码块等）
#                 'codehilite',     # 代码高亮
#                 'toc',            # 目录生成
#                 'sane_lists',     # 列表优化
#                 'smarty',         # 智能标点
#                 'fenced_code'     # 围栏代码块
#             ]
        
#         # Markdown转HTML
#         html_content = markdown.markdown(md_content, extensions=extensions)
        
#         # 创建完整的HTML文档
#         soup = BeautifulSoup('', 'html.parser')
        
#         # 创建HTML结构
#         html_tag = soup.new_tag('html', lang='zh-CN')
#         head_tag = soup.new_tag('head')
#         body_tag = soup.new_tag('body')
        
#         # 添加meta和title
#         head_tag.append(soup.new_tag('meta', charset='utf-8'))
#         title_tag = soup.new_tag('title')
#         title_tag.string = md_file.stem
#         head_tag.append(title_tag)
        
#         # 添加基础样式（优化显示效果）
#         style_tag = soup.new_tag('style')
#         style_content = """
#         body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; line-height: 1.6; }
#         h1, h2, h3, h4 { margin-top: 24px; margin-bottom: 16px; color: #2d3748; }
#         img { max-width: 100%; height: auto; border-radius: 4px; margin: 16px 0; }
#         code { background-color: #f7fafc; padding: 2px 4px; border-radius: 4px; font-family: monospace; }
#         pre { background-color: #f7fafc; padding: 16px; border-radius: 4px; overflow-x: auto; }
#         table { border-collapse: collapse; width: 100%; margin: 16px 0; }
#         th, td { border: 1px solid #e2e8f0; padding: 8px 12px; text-align: left; }
#         th { background-color: #f7fafc; }
#         """
#         style_tag.string = style_content
#         head_tag.append(style_tag)
        
#         # 将转换的HTML内容添加到body
#         content_soup = BeautifulSoup(html_content, 'html.parser')
#         body_tag.append(content_soup)
        
#         # 组装完整HTML文档
#         html_tag.append(head_tag)
#         html_tag.append(body_tag)
#         soup.append(html_tag)
        
#         # 保存HTML
#         with open(output_html_file, 'w', encoding='utf-8') as f:
#             f.write(soup.prettify())
        
#         logger.success(f"Markdown转HTML成功: {md_file} -> {output_html_file}")
#         return output_html_file
    
#     except Exception as e:
#         logger.error(f"Markdown转HTML失败: {str(e)}", exc_info=True)
#         return None