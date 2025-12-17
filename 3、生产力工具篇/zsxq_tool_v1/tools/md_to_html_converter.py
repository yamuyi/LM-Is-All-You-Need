import streamlit as st
import markdown
from pathlib import Path
from bs4 import BeautifulSoup
import shutil
import uuid
import zipfile
import time
from datetime import datetime

def convert_md_to_html(md_content, filename, output_dir, use_extensions=True):
    """
    Markdown转HTML核心函数
    
    Args:
        md_content: Markdown内容字符串
        filename: 原始文件名
        output_dir: 输出目录
        use_extensions: 是否启用Markdown扩展
    
    Returns:
        dict: 处理结果信息
    """
    try:
        # 创建必要的目录结构
        html_dir = output_dir / "html"
        images_dir = html_dir / "images"
        html_dir.mkdir(parents=True, exist_ok=True)
        images_dir.mkdir(parents=True, exist_ok=True)
        
        # 输出HTML路径
        html_filename = f"{Path(filename).stem}.html"
        output_html_file = html_dir / html_filename
        
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
        title_tag.string = Path(filename).stem
        head_tag.append(title_tag)
        
        # 添加viewport标签
        viewport_tag = soup.new_tag('meta')
        viewport_tag['name'] = 'viewport'
        viewport_tag['content'] = 'width=device-width, initial-scale=1.0'
        head_tag.append(viewport_tag)
        
        # 添加CSS样式
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
            font-size: 16px;
            color: #333;
        }
        
        h1 {
            font-size: 28px;
            margin: 30px 0 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #eaeaea;
            font-weight: 700;
            color: #222;
        }
        
        h2 {
            font-size: 24px;
            margin: 28px 0 18px;
            padding-bottom: 8px;
            border-bottom: 2px solid #f0f0f0;
            font-weight: 600;
            color: #333;
        }
        
        h3 {
            font-size: 20px;
            margin: 24px 0 16px;
            font-weight: 600;
            color: #444;
        }
        
        h4 {
            font-size: 18px;
            margin: 20px 0 14px;
            font-weight: 600;
            color: #555;
        }
        
        h5, h6 {
            font-size: 16px;
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
        
        pre {
            background: #f8f8f8;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            overflow-x: auto;
            border: 1px solid #eaeaea;
            font-size: 14px;
        }
        
        code {
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
            background: #f5f5f5;
            padding: 3px 6px;
            border-radius: 4px;
            font-size: 14px;
            color: #d63384;
        }
        
        pre code {
            background: transparent;
            padding: 0;
            color: #333;
        }
        
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            font-size: 15px;
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
        
        ul, ol {
            margin: 16px 0;
            padding-left: 30px;
        }
        
        li {
            margin: 8px 0;
            line-height: 1.8;
        }
        
        blockquote {
            border-left: 4px solid #0070f3;
            margin: 20px 0;
            padding: 15px 20px;
            background-color: #f9f9f9;
            border-radius: 0 4px 4px 0;
            font-size: 15px;
        }
        
        blockquote p {
            margin: 0;
        }
        
        img {
            display: block;
            margin: 25px auto;
            max-width: 100%;
            height: auto;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
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
        
        hr {
            border: none;
            border-top: 2px solid #eaeaea;
            margin: 30px 0;
        }
        
        .footnote {
            font-size: 14px;
            color: #666;
        }
        
        .content-wrapper {
            max-width: 100%;
            overflow-wrap: break-word;
        }
        
        @media print {
            body {
                padding: 0;
                font-size: 12pt;
            }
            
            h1 { font-size: 24pt; }
            h2 { font-size: 20pt; }
            h3 { font-size: 16pt; }
            h4 { font-size: 14pt; }
            
            pre, code {
                font-size: 10pt;
            }
            
            table {
                font-size: 11pt;
            }
        }
        """
        style_tag.string = style_content
        head_tag.append(style_tag)
        
        # 处理HTML内容
        content_soup = BeautifulSoup(html_content, 'html.parser')
        html_str = str(content_soup)
        
        # 处理目录
        if '<p>[toc]</p>' in html_str and toc_content:
            toc_html = f'''
            <div class="toc-container">
                <div class="toc-title">📑 目录</div>
                <div class="toc">
                    {toc_content}
                </div>
            </div>
            '''
            html_str = html_str.replace('<p>[toc]</p>', toc_html)
        
        # 重新解析为BeautifulSoup对象
        processed_soup = BeautifulSoup(html_str, 'html.parser')
        
        # 处理图片标签
        for img in processed_soup.find_all('img'):
            img_src = img.get('src', '')
            if img_src:
                img['style'] = 'display: block; margin: 25px auto; max-width: 100%; height: auto; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'
        
        # 处理表格样式
        for table in processed_soup.find_all('table'):
            table['style'] = 'margin: 20px auto; width: 100%; border-collapse: collapse;'
        
        # 处理代码块样式
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
        
        # 保存HTML文件
        with open(output_html_file, 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        
        return {
            'success': True,
            'html_file': str(output_html_file),
            'html_dir': str(html_dir),
            'images_dir': str(images_dir),
            'filename': html_filename,
            'has_toc': bool(toc_content)
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def create_html_zip(result, output_dir):
    """创建HTML文件夹的ZIP包"""
    try:
        task_id = f"md_to_html_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        zip_filename = f"{task_id}.zip"
        zip_path = output_dir.parent / zip_filename
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 添加HTML目录中的所有文件
            html_dir = Path(result['html_dir'])
            for file_path in html_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(output_dir)
                    zipf.write(file_path, arcname=arcname)
        
        return {
            'success': True,
            'zip_path': str(zip_path),
            'zip_filename': zip_filename,
            'task_id': task_id
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# 明确定义 main() 函数
def main():
    """主函数 - 工具集成平台会调用这个函数"""
    # 设置页面配置
    st.set_page_config(
        page_title="Markdown转HTML工具",
        page_icon="📄",
        layout="wide"
    )
    
    # 创建临时目录
    TEMP_DIR = Path("temp/md_to_html")
    TEMP_DIR.mkdir(exist_ok=True, parents=True)
    
    st.title("📄 Markdown转HTML工具")
    st.markdown("""
    将Markdown文件转换为美观的HTML文档，支持目录生成、代码高亮、响应式设计等功能。
    
    **主要功能：**
    1. 上传Markdown文件
    2. 自动生成HTML文档
    3. 支持目录生成
    4. 代码语法高亮
    5. 响应式设计，适配移动端
    6. 生成可下载的ZIP包
    """)
    
    # 初始化session state
    if 'md_content' not in st.session_state:
        st.session_state.md_content = None
    if 'uploaded_filename' not in st.session_state:
        st.session_state.uploaded_filename = None
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 转换设置")
        
        use_extensions = st.checkbox("启用Markdown扩展", value=True, 
            help="启用额外功能如代码高亮、目录生成等")
        
        include_css = st.checkbox("包含CSS样式", value=True,
            help="在HTML中嵌入CSS样式")
        
        generate_toc = st.checkbox("自动生成目录", value=True,
            help="为文档自动生成目录导航")
        
        st.divider()
        st.header("📊 统计信息")
        if st.session_state.md_content:
            lines = len(st.session_state.md_content.split('\n'))
            words = len(st.session_state.md_content.split())
            chars = len(st.session_state.md_content)
            
            st.metric("行数", lines)
            st.metric("单词数", words)
            st.metric("字符数", chars)
    
    # 主界面
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("1. 上传Markdown文件")
        uploaded_file = st.file_uploader(
            "选择Markdown文件",
            type=['md', 'markdown', 'txt'],
            help="支持.md、.markdown、.txt格式"
        )
        
        if uploaded_file is not None:
            if (st.session_state.uploaded_filename != uploaded_file.name or 
                st.session_state.md_content is None):
                
                st.session_state.uploaded_filename = uploaded_file.name
                try:
                    content = uploaded_file.getvalue().decode('utf-8')
                except:
                    content = uploaded_file.getvalue().decode('gbk', errors='ignore')
                
                st.session_state.md_content = content
            
            # 显示文件信息
            file_info = {
                "文件名": uploaded_file.name,
                "大小": f"{uploaded_file.size / 1024:.1f} KB",
                "编码": "UTF-8"
            }
            
            with st.expander("📄 文件信息", expanded=False):
                for key, value in file_info.items():
                    st.write(f"**{key}**: {value}")
    
    with col2:
        st.subheader("2. 转换选项")
        
        if uploaded_file is not None:
            # 预览选项
            with st.expander("👁️ 预览原始内容", expanded=False):
                preview_lines = min(50, len(st.session_state.md_content.split('\n')))
                preview_content = '\n'.join(st.session_state.md_content.split('\n')[:preview_lines])
                if len(st.session_state.md_content.split('\n')) > preview_lines:
                    preview_content += "\n\n..."
                st.code(preview_content, language="markdown")
            
            # 转换按钮
            if st.button("🚀 开始转换", type="primary", use_container_width=True):
                with st.spinner("正在转换中..."):
                    # 创建临时输出目录
                    task_id = f"task_{uuid.uuid4().hex[:8]}"
                    task_dir = TEMP_DIR / task_id
                    task_dir.mkdir(exist_ok=True)
                    
                    # 执行转换
                    result = convert_md_to_html(
                        md_content=st.session_state.md_content,
                        filename=st.session_state.uploaded_filename,
                        output_dir=task_dir,
                        use_extensions=use_extensions
                    )
                    
                    if result['success']:
                        st.success("✅ 转换成功！")
                        
                        # 创建ZIP包
                        zip_result = create_html_zip(result, task_dir)
                        
                        if zip_result['success']:
                            # 显示结果
                            st.subheader("3. 转换结果")
                            
                            # 创建两列布局
                            result_col1, result_col2 = st.columns([1, 1])
                            
                            with result_col1:
                                st.metric("输出文件", result['filename'])
                                st.metric("目录生成", "✅" if result['has_toc'] else "❌")
                                
                                # 预览HTML
                                with st.expander("👀 预览HTML", expanded=False):
                                    try:
                                        with open(result['html_file'], 'r', encoding='utf-8') as f:
                                            html_content = f.read()
                                        preview_length = min(2000, len(html_content))
                                        html_preview = html_content[:preview_length]
                                        if len(html_content) > preview_length:
                                            html_preview += "..."
                                        st.code(html_preview, language="html")
                                    except Exception as e:
                                        st.warning(f"无法预览HTML内容: {e}")
                            
                            with result_col2:
                                # 文件结构
                                st.info("📁 文件结构:")
                                st.code(f"""
{task_id}/
├── html/
│   ├── {result['filename']}
│   └── images/
│       └── (图片文件夹)
└── {zip_result['zip_filename']}
                                """.strip())
                            
                            # 下载按钮
                            st.divider()
                            
                            col_btn1, col_btn2 = st.columns([1, 1])
                            
                            with col_btn1:
                                # 下载HTML文件
                                with open(result['html_file'], 'rb') as f:
                                    html_data = f.read()
                                
                                st.download_button(
                                    label="⬇️ 下载HTML文件",
                                    data=html_data,
                                    file_name=result['filename'],
                                    mime="text/html",
                                    use_container_width=True
                                )
                            
                            with col_btn2:
                                # 下载ZIP包
                                with open(zip_result['zip_path'], 'rb') as f:
                                    zip_data = f.read()
                                
                                st.download_button(
                                    label="📦 下载完整ZIP包",
                                    data=zip_data,
                                    file_name=zip_result['zip_filename'],
                                    mime="application/zip",
                                    use_container_width=True
                                )
                            
                            # 清理旧文件
                            try:
                                # 清理24小时前的临时文件
                                now = time.time()
                                for file_item in TEMP_DIR.glob("task_*"):
                                    if file_item.is_dir() and (now - file_item.stat().st_mtime) > 86400:
                                        shutil.rmtree(file_item)
                                for file_item in TEMP_DIR.glob("*.zip"):
                                    if (now - file_item.stat().st_mtime) > 86400:
                                        file_item.unlink()
                            except Exception as e:
                                # 忽略清理错误
                                pass
                        else:
                            st.error(f"创建ZIP包失败: {zip_result['error']}")
                    else:
                        st.error(f"转换失败: {result['error']}")
        else:
            st.info("👆 请先上传Markdown文件")
    
    # 使用说明
    with st.expander("📚 使用说明", expanded=False):
        st.markdown("""
        ### 功能介绍
        
        **支持的Markdown语法：**
        - 标题（H1-H6）
        - 粗体、斜体、删除线
        - 列表（有序/无序）
        - 代码块（支持语法高亮）
        - 表格
        - 引用块
        - 水平线
        - 图片
        - 链接
        
        **扩展功能：**
        1. **目录生成**：在文档中插入 `[toc]` 会自动生成目录
        2. **代码高亮**：自动识别代码语言并进行高亮
        3. **响应式设计**：适配电脑、平板和手机
        4. **打印优化**：支持打印时的样式优化
        
        ### 输出说明
        
        转换后会生成：
        - **HTML文件**：完整的网页文档
        - **ZIP包**：包含HTML文件和images文件夹
        
        ### 注意事项
        
        1. 图片处理：目前工具会保持图片的原始链接，如需本地化图片请先使用图片本地化工具
        2. 大文件处理：建议处理文件大小不超过10MB
        3. 编码支持：默认使用UTF-8编码，如有乱码问题请尝试GBK编码
        """)

# 如果单独运行这个工具
if __name__ == "__main__":
    main()