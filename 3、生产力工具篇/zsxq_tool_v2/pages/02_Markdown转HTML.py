import streamlit as st
import markdown
from pathlib import Path
from bs4 import BeautifulSoup
import uuid
import zipfile
from datetime import datetime

# 页面配置
st.set_page_config(
    page_title="Markdown转HTML",
    page_icon="📄",
    layout="wide"
)

def main():
    # 页面标题和返回按钮
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("📄 Markdown转HTML工具")
    with col2:
        if st.button("🏠 返回门户", use_container_width=True):
            st.switch_page("portal.py")
    
    st.markdown("""
    ### 功能说明
    将Markdown文件转换为美观的HTML文档，支持目录生成、代码高亮、响应式设计。
    
    **使用步骤：**
    1. 上传Markdown文件
    2. 设置转换选项
    3. 开始转换
    4. 下载HTML文件或完整ZIP包
    """)
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 转换设置")
        use_extensions = st.checkbox("启用Markdown扩展", value=True, 
                                    help="启用代码高亮、目录等扩展功能")
        generate_toc = st.checkbox("自动生成目录", value=True,
                                  help="为文档自动生成目录导航")
        include_css = st.checkbox("包含CSS样式", value=True,
                                 help="在HTML中嵌入现代化的CSS样式")
    
    # 文件上传
    uploaded_file = st.file_uploader(
        "📤 上传Markdown文件",
        type=['md', 'markdown', 'txt'],
        help="支持.md、.markdown、.txt格式"
    )
    
    if uploaded_file is not None:
        # 读取文件内容
        try:
            content = uploaded_file.getvalue().decode('utf-8')
        except:
            content = uploaded_file.getvalue().decode('gbk', errors='ignore')
        
        # 显示文件信息
        with st.expander("📄 文件信息", expanded=False):
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.metric("文件名", uploaded_file.name)
                st.metric("文件大小", f"{uploaded_file.size / 1024:.1f} KB")
            with col_info2:
                st.metric("行数", len(content.split('\n')))
                st.metric("字符数", len(content))
        
        # 预览
        with st.expander("👁️ 预览内容", expanded=False):
            st.code(content[:1000] + ("..." if len(content) > 1000 else ""), language="markdown")
        
        # 转换按钮
        if st.button("🚀 开始转换", type="primary", use_container_width=True):
            with st.spinner("正在转换中..."):
                try:
                    # 创建临时目录
                    task_id = f"md_to_html_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
                    temp_dir = Path("temp") / task_id
                    html_dir = temp_dir / "html"
                    html_dir.mkdir(parents=True, exist_ok=True)
                    
                    # 配置Markdown扩展
                    extensions = []
                    if use_extensions:
                        extensions = [
                            'markdown.extensions.extra',
                            'markdown.extensions.codehilite',
                            'markdown.extensions.toc',
                            'markdown.extensions.fenced_code'
                        ]
                    
                    # Markdown转HTML
                    md_processor = markdown.Markdown(extensions=extensions)
                    html_content = md_processor.convert(content)
                    
                    # 获取目录
                    toc_content = md_processor.toc if hasattr(md_processor, 'toc') else ""
                    
                    # 创建完整的HTML文档
                    soup = BeautifulSoup('', 'html.parser')
                    html_tag = soup.new_tag('html')
                    html_tag['lang'] = 'zh-CN'
                    
                    # head部分
                    head_tag = soup.new_tag('head')
                    meta_charset = soup.new_tag('meta', charset='utf-8')
                    head_tag.append(meta_charset)
                    
                    title_tag = soup.new_tag('title')
                    title_tag.string = Path(uploaded_file.name).stem
                    head_tag.append(title_tag)
                    
                    viewport_tag = soup.new_tag('meta', name='viewport', 
                                                content='width=device-width, initial-scale=1.0')
                    head_tag.append(viewport_tag)
                    
                    if include_css:
                        style_tag = soup.new_tag('style')
                        style_content = """
                        * {
                            box-sizing: border-box;
                            margin: 0;
                            padding: 0;
                        }
                        body { 
                            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
                            max-width: 800px;
                            margin: 0 auto;
                            padding: 40px;
                            line-height: 1.6;
                            color: #333;
                            background: #fff;
                        }
                        h1 { 
                            font-size: 2em; 
                            margin: 1em 0 0.5em;
                            padding-bottom: 0.3em;
                            border-bottom: 2px solid #eee;
                        }
                        h2 { 
                            font-size: 1.5em; 
                            margin: 1em 0 0.5em;
                            padding-bottom: 0.3em;
                            border-bottom: 1px solid #eee;
                        }
                        h3 { font-size: 1.25em; margin: 1em 0 0.5em; }
                        p { margin: 1em 0; }
                        pre { 
                            background: #f6f8fa; 
                            padding: 1em; 
                            border-radius: 6px; 
                            overflow-x: auto;
                            font-size: 0.9em;
                        }
                        code { 
                            background: #f6f8fa; 
                            padding: 0.2em 0.4em; 
                            border-radius: 3px;
                            font-family: 'SFMono-Regular', Consolas, monospace;
                        }
                        pre code { background: transparent; padding: 0; }
                        .toc { 
                            background: #f8f9fa; 
                            padding: 1em; 
                            border-radius: 8px; 
                            margin: 1.5em 0;
                            border: 1px solid #e1e4e8;
                        }
                        .toc-title { 
                            font-weight: 600; 
                            margin-bottom: 0.5em;
                            color: #24292e;
                        }
                        blockquote {
                            border-left: 4px solid #ddd;
                            padding: 0 1em;
                            color: #666;
                            margin: 1em 0;
                        }
                        table {
                            border-collapse: collapse;
                            width: 100%;
                            margin: 1em 0;
                        }
                        th, td {
                            border: 1px solid #ddd;
                            padding: 0.5em;
                            text-align: left;
                        }
                        th {
                            background: #f8f9fa;
                            font-weight: 600;
                        }
                        img {
                            max-width: 100%;
                            height: auto;
                            display: block;
                            margin: 1em auto;
                        }
                        @media (max-width: 600px) {
                            body { padding: 20px; }
                        }
                        """
                        style_tag.string = style_content
                        head_tag.append(style_tag)
                    
                    # body部分
                    body_tag = soup.new_tag('body')
                    
                    # 添加目录
                    if generate_toc and toc_content:
                        toc_div = soup.new_tag('div', **{'class': 'toc'})
                        toc_title = soup.new_tag('div', **{'class': 'toc-title'})
                        toc_title.string = "📑 目录"
                        toc_div.append(toc_title)
                        toc_content_soup = BeautifulSoup(toc_content, 'html.parser')
                        toc_div.append(toc_content_soup)
                        body_tag.append(toc_div)
                    
                    # 添加内容
                    content_div = soup.new_tag('div')
                    content_soup = BeautifulSoup(html_content, 'html.parser')
                    content_div.append(content_soup)
                    body_tag.append(content_div)
                    
                    # 组装文档
                    html_tag.append(head_tag)
                    html_tag.append(body_tag)
                    soup.append(html_tag)
                    
                    # 保存HTML文件
                    html_filename = f"{Path(uploaded_file.name).stem}.html"
                    html_filepath = html_dir / html_filename
                    
                    with open(html_filepath, 'w', encoding='utf-8') as f:
                        f.write(soup.prettify())
                    
                    # 创建ZIP包
                    zip_filename = f"{task_id}.zip"
                    zip_path = temp_dir.parent / zip_filename
                    
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        zipf.write(html_filepath, arcname=html_filename)
                    
                    st.success("✅ 转换成功！")
                    
                    # 显示结果统计
                    col_stat1, col_stat2, col_stat3 = st.columns(3)
                    with col_stat1:
                        st.metric("输出文件", html_filename)
                    with col_stat2:
                        st.metric("HTML大小", f"{html_filepath.stat().st_size / 1024:.1f} KB")
                    with col_stat3:
                        st.metric("目录生成", "✅" if toc_content else "❌")
                    
                    # 提供下载
                    st.subheader("📥 下载选项")
                    col_dl1, col_dl2 = st.columns(2)
                    
                    with col_dl1:
                        with open(html_filepath, 'rb') as f:
                            html_data = f.read()
                        
                        st.download_button(
                            label="⬇️ 下载HTML文件",
                            data=html_data,
                            file_name=html_filename,
                            mime="text/html",
                            use_container_width=True,
                            type="primary"
                        )
                    
                    with col_dl2:
                        with open(zip_path, 'rb') as f:
                            zip_data = f.read()
                        
                        st.download_button(
                            label="📦 下载完整ZIP包",
                            data=zip_data,
                            file_name=zip_filename,
                            mime="application/zip",
                            use_container_width=True
                        )
                    
                    # 预览HTML
                    with st.expander("👀 预览HTML效果", expanded=False):
                        st.components.v1.html(soup.prettify(), height=400, scrolling=True)
                    
                    # HTML源码预览
                    with st.expander("📄 查看HTML源码"):
                        st.code(soup.prettify()[:1500], language="html")
                
                except Exception as e:
                    st.error(f"转换失败: {str(e)}")
    
    else:
        st.info("👆 请上传一个Markdown文件开始处理")
        
        # 示例
        with st.expander("📋 查看示例"):
            st.markdown("""
            ```markdown
            # 示例标题
            
            这是一个段落。
            
            ## 二级标题
            
            - 列表项1
            - 列表项2
            
            ```python
            print("Hello World!")
            ```
            """)

if __name__ == "__main__":
    main()