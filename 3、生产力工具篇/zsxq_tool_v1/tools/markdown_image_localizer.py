import streamlit as st
import os
import re
import requests
import uuid
import zipfile
import shutil
from pathlib import Path
from urllib.parse import urlparse
import time
from datetime import datetime

def extract_image_urls(markdown_content):
    """从Markdown内容中提取所有图片URL"""
    # 匹配Markdown图片语法 ![alt](url)
    img_pattern = r'!\[.*?\]\((http[s]?://.*?)\)'
    img_urls = re.findall(img_pattern, markdown_content)
    
    # 匹配HTML img标签
    html_img_pattern = r'<img[^>]+src="(http[s]?://[^">]+)"'
    html_img_urls = re.findall(html_img_pattern, markdown_content)
    
    # 合并所有图片URL
    all_urls = img_urls + html_img_urls
    return list(set(all_urls))  # 去重

def download_image(url, download_dir):
    """下载图片并保存到指定目录"""
    try:
        # 解析URL获取文件名
        parsed_url = urlparse(url)
        filename = parsed_url.path.split('/')[-1]
        
        # 如果没有扩展名或扩展名不常见，添加.jpg扩展名
        if not '.' in filename or len(filename.split('.')[-1]) > 5:
            filename = f"{uuid.uuid4().hex[:8]}.jpg"
        
        # 确保文件名唯一
        counter = 1
        original_name = filename
        while (download_dir / filename).exists():
            name_parts = original_name.rsplit('.', 1)
            if len(name_parts) == 2:
                filename = f"{name_parts[0]}_{counter}.{name_parts[1]}"
            else:
                filename = f"{original_name}_{counter}"
            counter += 1
        
        filepath = download_dir / filename
        
        # 下载图片
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 检查内容类型是否为图片
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            st.warning(f"URL {url} 的内容类型不是图片: {content_type}")
            # 但仍然尝试保存，因为有些图片服务器可能没有正确设置content-type
        
        # 保存图片
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        return filename, filepath
    
    except Exception as e:
        st.warning(f"下载图片失败: {url}, 错误: {str(e)}")
        return None, None

def replace_image_urls(markdown_content, url_map):
    """替换Markdown内容中的远程URL为本地相对路径"""
    # 创建修改后的内容
    modified_content = markdown_content
    
    # 替换Markdown图片语法
    for url, local_path in url_map.items():
        # 转义URL中的特殊字符用于正则匹配
        escaped_url = re.escape(url)
        # 替换Markdown格式的图片
        pattern = rf'!\[(.*?)\]\({escaped_url}\)'
        modified_content = re.sub(pattern, f'![\\1]({local_path})', modified_content)
        
        # 替换HTML格式的图片
        html_pattern = rf'<img([^>]+)src="{escaped_url}"'
        modified_content = re.sub(html_pattern, f'<img\\1src="{local_path}"', modified_content)
    
    return modified_content

def create_zip_file(markdown_content, original_filename, url_map, download_images_dir, original_content=None):
    """创建包含Markdown文件和图片的ZIP包"""
    # 生成唯一的任务ID
    task_id = f"md_images_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    task_dir = download_images_dir.parent / task_id  # 使用同一个父目录
    task_images_dir = task_dir / "images"
    task_dir.mkdir(exist_ok=True)
    task_images_dir.mkdir(exist_ok=True)
    
    try:
        # 复制所有下载的图片到任务目录
        downloaded_images = []
        for url, local_path in url_map.items():
            # 从local_path中提取文件名（去掉"images/"前缀）
            if local_path.startswith("images/"):
                filename = local_path[7:]  # 去掉"images/"前缀
            else:
                filename = local_path
            
            # 查找图片文件
            original_path = download_images_dir / filename
            if original_path.exists():
                target_path = task_images_dir / filename
                shutil.copy2(original_path, target_path)
                downloaded_images.append(filename)
            else:
                # 尝试不同的路径
                st.warning(f"图片文件不存在: {original_path}")
                # 尝试在下载目录中查找
                for file in download_images_dir.glob("*"):
                    if file.name == filename:
                        shutil.copy2(file, target_path)
                        downloaded_images.append(filename)
                        break
                else:
                    st.error(f"无法找到图片文件: {filename}")
        
        # 生成新的Markdown文件名
        if '.' in original_filename:
            name_parts = original_filename.rsplit('.', 1)
            new_filename = f"{name_parts[0]}_local.{name_parts[1]}"
        else:
            new_filename = f"{original_filename}_local.md"
        
        # 保存修改后的Markdown文件
        md_filepath = task_dir / new_filename
        
        if original_content is not None:
            final_content = markdown_content
        else:
            final_content = markdown_content
        
        # 使用二进制模式写入，保持原始换行符
        with open(md_filepath, 'wb') as f:
            f.write(final_content.encode('utf-8'))
        
        # 创建ZIP文件
        zip_path = download_images_dir.parent / f"{task_id}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 添加Markdown文件（在ZIP的根目录）
            zipf.write(md_filepath, arcname=new_filename)
            
            # 添加图片文件夹中的所有图片
            for image_file in task_images_dir.rglob("*"):
                if image_file.is_file():
                    # 保持images文件夹结构
                    arcname = image_file.relative_to(task_dir)
                    zipf.write(image_file, arcname=arcname)
        
        return zip_path, task_id, len(downloaded_images)
    
    except Exception as e:
        st.error(f"创建ZIP文件时出错: {str(e)}")
        raise
    finally:
        # 清理任务目录
        if task_dir.exists():
            shutil.rmtree(task_dir)

def cleanup_old_files(temp_dir, max_age_hours=24):
    """清理旧文件"""
    now = time.time()
    for file in temp_dir.glob("*.zip"):
        if now - file.stat().st_mtime > max_age_hours * 3600:
            try:
                file.unlink()
            except:
                pass

def main():
    """主函数 - 工具集成平台会调用这个函数"""
    # 设置页面配置
    st.set_page_config(
        page_title="Markdown图片本地化工具",
        page_icon="📸",
        layout="wide"
    )
    
    # 创建临时目录 - 为每个会话创建唯一的目录
    session_id = str(uuid.uuid4().hex[:8])
    TEMP_DIR = Path("temp") / f"markdown_images_{session_id}"
    IMAGES_DIR = TEMP_DIR / "images"
    TEMP_DIR.mkdir(exist_ok=True, parents=True)
    IMAGES_DIR.mkdir(exist_ok=True)
    
    # 清理旧文件
    cleanup_old_files(TEMP_DIR.parent)
    
    # 初始化session state
    if 'original_content' not in st.session_state:
        st.session_state.original_content = None
    if 'image_urls' not in st.session_state:
        st.session_state.image_urls = None
    if 'uploaded_file_name' not in st.session_state:
        st.session_state.uploaded_file_name = None
    if 'temp_dir' not in st.session_state:
        st.session_state.temp_dir = TEMP_DIR
    if 'images_dir' not in st.session_state:
        st.session_state.images_dir = IMAGES_DIR
    
    st.title("📸 Markdown图片本地化工具")
    st.markdown("""
    这个工具可以帮助您将Markdown文件中的远程图片下载到本地，并生成一个包含Markdown文件和图片文件夹的ZIP包。
    
    **主要功能：**
    1. 上传Markdown文件
    2. 自动检测并下载远程图片
    3. 将图片链接替换为本地相对路径
    4. 下载包含Markdown文件和图片的ZIP包
    """)
    
    # 文件上传
    uploaded_file = st.file_uploader(
        "上传Markdown文件", 
        type=['md', 'markdown', 'txt'],
        help="支持.md、.markdown或.txt格式的文件"
    )
    
    if uploaded_file is not None:
        # 检查文件是否变化
        if (st.session_state.uploaded_file_name != uploaded_file.name or 
            st.session_state.original_content is None):
            
            st.session_state.uploaded_file_name = uploaded_file.name
            
            try:
                content = uploaded_file.getvalue().decode('utf-8')
            except:
                content = uploaded_file.getvalue().decode('gbk', errors='ignore')
            
            st.session_state.original_content = content
            
            with st.spinner("正在分析Markdown文件..."):
                image_urls = extract_image_urls(content)
                st.session_state.image_urls = image_urls
        else:
            content = st.session_state.original_content
            image_urls = st.session_state.image_urls
        
        # 显示文件信息
        file_details = {
            "文件名": uploaded_file.name,
            "文件大小": f"{uploaded_file.size / 1024:.2f} KB",
            "文件类型": uploaded_file.type
        }
        
        with st.expander("📄 文件详情", expanded=False):
            st.write(file_details)
        
        if not image_urls:
            st.info("⚠️ 未在文件中发现远程图片链接")
            
            with st.expander("📝 预览原始内容"):
                preview_content = content[:2000].replace('\n', '⏎\n')
                st.code(preview_content, language="markdown")
        else:
            st.success(f"✅ 发现 {len(image_urls)} 个远程图片链接")
            
            with st.expander("🔗 查看图片链接", expanded=False):
                for i, url in enumerate(image_urls, 1):
                    st.write(f"{i}. {url}")
            
            # 图片下载选项
            st.subheader("📥 下载选项")
            col1, col2 = st.columns(2)
            
            with col1:
                max_images = st.number_input(
                    "最大下载图片数",
                    min_value=1,
                    max_value=len(image_urls),
                    value=min(10, len(image_urls)),
                    help="限制下载的图片数量"
                )
            
            with col2:
                download_all = st.checkbox("下载所有图片", value=True)
            
            # 开始处理按钮
            if st.button("🚀 开始处理", type="primary", use_container_width=True):
                with st.spinner("正在处理中，请稍候..."):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    url_map = {}
                    successful_downloads = 0
                    
                    urls_to_download = image_urls if download_all else image_urls[:max_images]
                    
                    # 清空图片目录，确保每次都是新的
                    for file in IMAGES_DIR.glob("*"):
                        try:
                            file.unlink()
                        except:
                            pass
                    
                    for i, url in enumerate(urls_to_download):
                        status_text.text(f"正在下载图片 {i+1}/{len(urls_to_download)}: {url[:50]}...")
                        filename, filepath = download_image(url, IMAGES_DIR)
                        
                        if filename:
                            url_map[url] = f"images/{filename}"
                            successful_downloads += 1
                        
                        progress_bar.progress((i + 1) / len(urls_to_download))
                    
                    status_text.text("正在替换图片链接...")
                    
                    # 替换Markdown内容中的图片链接
                    modified_content = replace_image_urls(st.session_state.original_content, url_map)
                    
                    # 创建ZIP文件
                    status_text.text("正在创建ZIP文件...")
                    try:
                        zip_path, task_id, zip_image_count = create_zip_file(
                            modified_content, 
                            uploaded_file.name, 
                            url_map,
                            IMAGES_DIR,  # 传递图片目录
                            st.session_state.original_content
                        )
                    except Exception as e:
                        st.error(f"创建ZIP文件失败: {str(e)}")
                        progress_bar.empty()
                        status_text.text("处理失败！")
                        return
                    
                    progress_bar.progress(1.0)
                    status_text.text("处理完成！")
                    
                    # 显示结果
                    st.success(f"✅ 处理完成！成功下载 {successful_downloads}/{len(urls_to_download)} 张图片，ZIP包中包含 {zip_image_count} 张图片")
                    
                    # 创建两列布局
                    col1_result, col2_result = st.columns(2)
                    
                    with col1_result:
                        # 预览修改后的内容
                        with st.expander("📝 预览修改前后的对比", expanded=False):
                            tab1, tab2 = st.tabs(["原始内容", "修改后内容"])
                            
                            with tab1:
                                st.code(st.session_state.original_content[:1500], language="markdown")
                            
                            with tab2:
                                st.code(modified_content[:1500], language="markdown")
                    
                    with col2_result:
                        # 显示统计信息
                        st.metric("原始图片数", len(image_urls))
                        st.metric("下载图片数", successful_downloads)
                        st.metric("ZIP中图片数", zip_image_count)
                    
                    # 下载按钮
                    if zip_path.exists():
                        with open(zip_path, 'rb') as f:
                            zip_data = f.read()
                        
                        st.download_button(
                            label="⬇️ 下载ZIP文件",
                            data=zip_data,
                            file_name=f"{task_id}.zip",
                            mime="application/zip",
                            use_container_width=True,
                            help="ZIP文件包含Markdown文件和images文件夹"
                        )
                        
                        # 显示ZIP文件内容结构
                        with st.expander("📁 ZIP文件结构", expanded=False):
                            # 获取前几个图片文件名
                            image_files = list(url_map.values())[:3]
                            image_names = [img.split('/')[-1] for img in image_files]
                            
                            zip_structure = f"""
{uploaded_file.name.split('.')[0]}_local.md
└── images/
    ├── {', '.join(image_names)}
    {'...' if len(url_map) > 3 else ''}
                            """
                            st.code(zip_structure.strip())
                        
                        # 添加测试下载按钮
                        with st.expander("🔧 测试下载", expanded=False):
                            st.caption("测试ZIP文件内容")
                            test_col1, test_col2 = st.columns(2)
                            with test_col1:
                                if st.button("查看测试内容"):
                                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                                        # 读取修改后的markdown文件
                                        zip_files = zip_ref.namelist()
                                        md_files = [f for f in zip_files if f.endswith('.md')]
                                        if md_files:
                                            md_content = zip_ref.read(md_files[0]).decode('utf-8')
                                            st.text_area("ZIP中的Markdown内容", md_content[:500], height=200)
                            with test_col2:
                                if st.button("检查images文件夹"):
                                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                                        image_files = [name for name in zip_ref.namelist() if name.startswith('images/') and not name.endswith('/')]
                                        st.write(f"Images文件夹中的文件数: {len(image_files)}")
                                        for img in image_files[:5]:
                                            st.write(f"- {img}")
                    else:
                        st.error("❌ ZIP文件创建失败，请重试")
            
            # 侧边栏显示预览
            with st.sidebar:
                st.subheader("图片预览")
                if len(image_urls) > 0:
                    try:
                        # 尝试获取第一张图片的预览
                        preview_url = image_urls[0]
                        st.caption(f"预览: {preview_url[:50]}...")
                        
                        # 设置超时，防止卡顿
                        response = requests.get(preview_url, timeout=5)
                        if response.status_code == 200 and response.headers.get('content-type', '').startswith('image/'):
                            st.image(response.content, caption="第一张图片预览", use_column_width=True)
                        else:
                            st.warning("无法预览图片（可能不是有效的图片URL）")
                    except Exception as e:
                        st.warning(f"无法加载图片预览: {str(e)}")
        
        # 使用指南
        with st.expander("📚 使用指南", expanded=False):
            st.markdown("""
            ### 如何使用这个工具：
            
            1. **上传文件**：点击"Browse files"上传你的Markdown文件
            2. **自动分析**：系统会自动分析文件中的远程图片链接
            3. **设置选项**：选择要下载的图片数量（默认下载所有图片）
            4. **开始处理**：点击"开始处理"按钮
            5. **下载结果**：处理完成后，点击"下载ZIP文件"按钮
            
            ### 输出文件结构：
            ```
            下载的ZIP文件解压后：
            ├── yourfile_local.md     # 修改后的Markdown文件
            └── images/               # 图片文件夹
                ├── image1.jpg
                ├── image2.png
                └── ...
            ```
            
            ### 支持的文件格式：
            - Markdown文件 (.md, .markdown)
            - 文本文件 (.txt)
            - 支持HTTP/HTTPS图片链接
            """)
    
    else:
        # 清空session state
        st.session_state.original_content = None
        st.session_state.image_urls = None
        st.session_state.uploaded_file_name = None
        
        # 示例展示
        st.info("👆 请上传一个Markdown文件开始处理")
        
        with st.expander("📋 查看示例", expanded=False):
            st.markdown("""
            ### 示例Markdown内容：
            ```markdown
            # 示例文档
            
            这是一张远程图片：
            
            ![示例图片](https://example.com/image.jpg)
            
            <img src="https://example.com/another.png" width="300">
            
            ### 处理后会变成：
            
            ![示例图片](images/image.jpg)
            
            <img src="images/another.png" width="300">
            ```
            """)

# 如果单独运行这个工具
if __name__ == "__main__":
    main()