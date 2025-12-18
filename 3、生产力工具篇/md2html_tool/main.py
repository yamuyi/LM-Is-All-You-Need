import streamlit as st
import os
import re
import requests
import markdown
from pathlib import Path
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import uuid
from datetime import datetime
import base64

# 设置页面配置
st.set_page_config(
    page_title="MD转HTML转换器",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 应用标题和描述
st.title("📄 Markdown 转 HTML 转换器")
st.markdown("将Markdown文档转换为HTML，并可选择下载远程网站的代码到本地")

# 创建必要的目录
os.makedirs("downloads", exist_ok=True)
os.makedirs("temp", exist_ok=True)

# 侧边栏配置
with st.sidebar:
    st.header("配置选项")
    
    # 转换选项
    st.subheader("Markdown转换选项")
    extensions = st.multiselect(
        "Markdown扩展",
        options=["extra", "codehilite", "fenced_code", "tables", "toc"],
        default=["extra", "fenced_code", "tables"]
    )
    
    # 远程资源下载选项
    st.subheader("远程资源下载选项")
    download_images = st.checkbox("下载远程图片", value=True)
    download_css = st.checkbox("下载CSS文件", value=False)
    download_js = st.checkbox("下载JavaScript文件", value=False)
    
    # 资源重命名选项
    rename_resources = st.checkbox("重命名下载的资源文件", value=True)
    
    # 清理选项
    if st.button("清理临时文件"):
        for folder in ["downloads", "temp"]:
            for file in os.listdir(folder):
                file_path = os.path.join(folder, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    st.error(f"删除 {file_path} 时出错: {e}")
        st.success("临时文件已清理!")
    
    st.divider()
    st.markdown("### 使用说明")
    st.markdown("""
    1. 在左侧输入或上传Markdown文档
    2. 配置转换选项
    3. 点击"转换Markdown为HTML"按钮
    4. 预览HTML结果或下载文件
    5. 如需下载远程资源，请确保选中相应选项
    """)

# 初始化session状态
if 'converted_html' not in st.session_state:
    st.session_state.converted_html = ""
if 'original_md' not in st.session_state:
    st.session_state.original_md = ""
if 'resource_map' not in st.session_state:
    st.session_state.resource_map = {}

# 下载远程资源的函数
def download_resource(url, resource_type="image", rename=False):
    """下载远程资源到本地"""
    try:
        # 检查URL是否有效
        if not url or not url.startswith(('http://', 'https://')):
            return None
        
        # 生成文件名
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        
        # 如果路径没有扩展名或需要重命名
        if not filename or '.' not in filename or rename:
            ext = ""
            if resource_type == "image":
                # 尝试从Content-Type获取扩展名
                try:
                    head_response = requests.head(url, timeout=5)
                    content_type = head_response.headers.get('Content-Type', '')
                    if 'image/jpeg' in content_type:
                        ext = '.jpg'
                    elif 'image/png' in content_type:
                        ext = '.png'
                    elif 'image/gif' in content_type:
                        ext = '.gif'
                    elif 'image/svg' in content_type or 'svg' in content_type:
                        ext = '.svg'
                    elif 'image/webp' in content_type:
                        ext = '.webp'
                except:
                    pass
            
            # 如果无法确定扩展名，使用默认值
            if not ext:
                if resource_type == "image":
                    ext = '.jpg'
                elif resource_type == "css":
                    ext = '.css'
                elif resource_type == "js":
                    ext = '.js'
            
            # 生成唯一文件名
            unique_id = str(uuid.uuid4())[:8]
            filename = f"{resource_type}_{unique_id}{ext}"
        
        # 创建资源目录
        resource_dir = os.path.join("downloads", resource_type + "s")
        os.makedirs(resource_dir, exist_ok=True)
        
        # 完整的文件路径
        filepath = os.path.join(resource_dir, filename)
        
        # 下载文件
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # 保存文件
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        # 返回相对路径
        return f"./downloads/{resource_type}s/{filename}"
    
    except Exception as e:
        st.warning(f"无法下载资源 {url}: {e}")
        return None

# 提取和替换远程资源的函数
def process_remote_resources(markdown_text, html_content, download_images=True, 
                            download_css=False, download_js=False, rename=False):
    """处理Markdown和HTML中的远程资源"""
    
    resource_map = {}
    processed_html = html_content
    
    # 1. 处理Markdown中的图片链接
    if download_images:
        # 正则表达式匹配Markdown图片语法
        md_image_pattern = r'!\[.*?\]\((http[s]?://.*?)\)'
        matches = re.findall(md_image_pattern, markdown_text)
        
        for img_url in matches:
            local_path = download_resource(img_url, "image", rename)
            if local_path:
                resource_map[img_url] = local_path
                # 替换Markdown中的URL
                markdown_text = markdown_text.replace(img_url, local_path)
    
    # 2. 处理HTML中的资源
    soup = BeautifulSoup(processed_html, 'html.parser')
    
    # 处理HTML中的图片
    if download_images:
        for img_tag in soup.find_all('img'):
            img_url = img_tag.get('src', '')
            if img_url.startswith('http'):
                local_path = download_resource(img_url, "image", rename)
                if local_path:
                    resource_map[img_url] = local_path
                    img_tag['src'] = local_path
    
    # 处理HTML中的CSS链接
    if download_css:
        for link_tag in soup.find_all('link', rel='stylesheet'):
            css_url = link_tag.get('href', '')
            if css_url.startswith('http'):
                local_path = download_resource(css_url, "css", rename)
                if local_path:
                    resource_map[css_url] = local_path
                    link_tag['href'] = local_path
    
    # 处理HTML中的JavaScript
    if download_js:
        for script_tag in soup.find_all('script'):
            js_url = script_tag.get('src', '')
            if js_url and js_url.startswith('http'):
                local_path = download_resource(js_url, "js", rename)
                if local_path:
                    resource_map[js_url] = local_path
                    script_tag['src'] = local_path
    
    # 更新处理后的HTML
    processed_html = str(soup)
    
    return markdown_text, processed_html, resource_map

# 主应用区域
tab1, tab2, tab3 = st.tabs(["输入Markdown", "转换结果", "下载资源"])

with tab1:
    # Markdown输入选项
    input_method = st.radio("输入方式", ["直接输入", "上传文件", "从URL加载"], horizontal=True)
    
    md_content = ""
    
    if input_method == "直接输入":
        md_content = st.text_area(
            "输入Markdown内容",
            height=400,
            placeholder="在这里输入Markdown内容...",
            value=st.session_state.original_md if st.session_state.original_md else ""
        )
    
    elif input_method == "上传文件":
        uploaded_file = st.file_uploader("上传Markdown文件", type=['md', 'markdown', 'txt'])
        if uploaded_file is not None:
            md_content = uploaded_file.getvalue().decode("utf-8")
    
    else:  # 从URL加载
        url = st.text_input("输入Markdown文件的URL", placeholder="https://example.com/document.md")
        if url:
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                md_content = response.text
                st.success("成功从URL加载Markdown内容")
            except Exception as e:
                st.error(f"无法从URL加载内容: {e}")
    
    # 保存到session状态
    if md_content:
        st.session_state.original_md = md_content
    
    # 显示原始内容预览
    if md_content:
        with st.expander("预览原始Markdown"):
            st.markdown(md_content)

with tab2:
    if st.button("转换Markdown为HTML", type="primary", use_container_width=True):
        if not st.session_state.original_md:
            st.warning("请输入Markdown内容")
        else:
            with st.spinner("正在转换Markdown..."):
                # 转换Markdown为HTML
                md_extensions = extensions if extensions else ["extra", "fenced_code", "tables"]
                html_content = markdown.markdown(st.session_state.original_md, extensions=md_extensions)
                
                # 处理远程资源
                processed_md, processed_html, resource_map = process_remote_resources(
                    st.session_state.original_md, 
                    html_content, 
                    download_images, 
                    download_css, 
                    download_js,
                    rename_resources
                )
                
                # 保存到session状态
                st.session_state.converted_html = processed_html
                st.session_state.resource_map = resource_map
                st.session_state.processed_md = processed_md
                
                st.success("转换完成!")
    
    # 显示转换结果
    if st.session_state.converted_html:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("HTML源代码")
            st.code(st.session_state.converted_html, language="html")
            
            # 添加HTML下载按钮
            html_b64 = base64.b64encode(st.session_state.converted_html.encode()).decode()
            html_filename = f"converted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            st.download_button(
                label="下载HTML文件",
                data=st.session_state.converted_html,
                file_name=html_filename,
                mime="text/html",
                use_container_width=True
            )
        
        with col2:
            st.subheader("HTML预览")
            st.components.v1.html(
                f"""
                <div style="border: 1px solid #ddd; padding: 20px; border-radius: 5px; max-height: 500px; overflow-y: auto;">
                {st.session_state.converted_html}
                </div>
                """,
                height=550,
                scrolling=True
            )
        
        # 显示处理后的Markdown
        with st.expander("查看处理后的Markdown（已替换资源链接）"):
            st.code(st.session_state.processed_md, language="markdown")

with tab3:
    st.header("下载的资源文件")
    
    if st.session_state.resource_map:
        st.info(f"已下载 {len(st.session_state.resource_map)} 个资源文件")
        
        # 按类型分类显示资源
        image_resources = {k:v for k,v in st.session_state.resource_map.items() if "images" in v}
        css_resources = {k:v for k,v in st.session_state.resource_map.items() if "css" in v}
        js_resources = {k:v for k,v in st.session_state.resource_map.items() if "js" in v}
        
        if image_resources:
            st.subheader("图片资源")
            cols = st.columns(3)
            for idx, (original, local) in enumerate(image_resources.items()):
                col_idx = idx % 3
                with cols[col_idx]:
                    try:
                        # 尝试显示图片
                        st.image(local, caption=os.path.basename(local), use_column_width=True)
                        st.caption(f"原始URL: {original[:50]}...")
                    except:
                        st.info(f"无法预览: {os.path.basename(local)}")
        
        if css_resources:
            st.subheader("CSS文件")
            for original, local in css_resources.items():
                with st.expander(f"CSS: {os.path.basename(local)}"):
                    st.code(f"原始URL: {original}")
                    try:
                        with open(local, 'r', encoding='utf-8') as f:
                            st.code(f.read(), language="css")
                    except:
                        st.info("无法读取文件内容")
        
        if js_resources:
            st.subheader("JavaScript文件")
            for original, local in js_resources.items():
                with st.expander(f"JS: {os.path.basename(local)}"):
                    st.code(f"原始URL: {original}")
                    try:
                        with open(local, 'r', encoding='utf-8') as f:
                            st.code(f.read(), language="javascript")     
                    except:
                        st.info("无法读取文件内容")
        
        # 显示资源映射表
        with st.expander("查看资源映射表"):
            import pandas as pd
            df = pd.DataFrame({
                "原始URL": list(st.session_state.resource_map.keys()),
                "本地路径": list(st.session_state.resource_map.values())
            })
            st.dataframe(df, use_container_width=True)
    else:
        st.info("尚未下载任何资源文件。请先转换包含远程资源的Markdown文档。")

# 页脚
st.divider()
st.caption("MD转HTML转换器 | 支持远程资源下载到本地")