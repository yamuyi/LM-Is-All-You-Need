import streamlit as st
import re
import requests
import uuid
import zipfile
import shutil
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime

# 页面配置
st.set_page_config(
    page_title="Markdown图片本地化",
    page_icon="📸",
    layout="wide"
)

def extract_image_urls(markdown_content):
    """从Markdown内容中提取所有图片URL"""
    img_pattern = r'!\[.*?\]\((http[s]?://.*?)\)'
    img_urls = re.findall(img_pattern, markdown_content)
    
    html_img_pattern = r'<img[^>]+src="(http[s]?://[^">]+)"'
    html_img_urls = re.findall(html_img_pattern, markdown_content)
    
    all_urls = img_urls + html_img_urls
    return list(set(all_urls))

def download_image(url, download_dir):
    """下载图片并保存到指定目录"""
    try:
        parsed_url = urlparse(url)
        filename = parsed_url.path.split('/')[-1]
        
        if not '.' in filename or len(filename.split('.')[-1]) > 5:
            filename = f"{uuid.uuid4().hex[:8]}.jpg"
        
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
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        return filename, filepath
    
    except Exception as e:
        st.warning(f"下载图片失败: {url}, 错误: {str(e)}")
        return None, None

# def replace_image_urls(markdown_content, url_map):
#     """替换Markdown内容中的远程URL为本地相对路径"""
#     modified_content = markdown_content
    
#     for url, local_path in url_map.items():
#         escaped_url = re.escape(url)
#         pattern = rf'!\[(.*?)\]\({escaped_url}\)'
#         modified_content = re.sub(pattern, f'![\\1]({local_path})', modified_content)
        
#         html_pattern = rf'<img([^>]+)src="{escaped_url}"'
#         modified_content = re.sub(html_pattern, f'<img\\1src="{local_path}"', modified_content)
    
#     return modified_content

def replace_image_urls(markdown_content, url_map):
    """替换Markdown内容中的远程URL为本地相对路径 - 简单可靠的版本"""
    if not url_map:
        return markdown_content
    
    # 使用简单的字符串替换，避免正则表达式带来的格式问题
    modified_content = markdown_content
    
    # 按URL长度倒序替换，避免部分替换问题
    sorted_urls = sorted(url_map.items(), key=lambda x: len(x[0]), reverse=True)
    
    for url, local_path in sorted_urls:
        # 直接替换Markdown格式的图片
        modified_content = modified_content.replace(f'({url})', f'({local_path})')
        
        # 替换可能的HTML格式图片
        modified_content = modified_content.replace(f'src="{url}"', f'src="{local_path}"')
        modified_content = modified_content.replace(f"src='{url}'", f"src='{local_path}'")
    
    return modified_content

def create_zip_file(markdown_content, original_filename, url_map, download_images_dir):
    """创建包含Markdown文件和图片的ZIP包"""
    task_id = f"md_images_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    task_dir = download_images_dir.parent / task_id
    task_images_dir = task_dir / "images"
    task_dir.mkdir(exist_ok=True)
    task_images_dir.mkdir(exist_ok=True)
    
    try:
        downloaded_images = []
        for url, local_path in url_map.items():
            if local_path.startswith("images/"):
                filename = local_path[7:]
            else:
                filename = local_path
            
            original_path = download_images_dir / filename
            if original_path.exists():
                target_path = task_images_dir / filename
                shutil.copy2(original_path, target_path)
                downloaded_images.append(filename)
        
        if '.' in original_filename:
            name_parts = original_filename.rsplit('.', 1)
            new_filename = f"{name_parts[0]}_local.{name_parts[1]}"
        else:
            new_filename = f"{original_filename}_local.md"
        
        md_filepath = task_dir / new_filename
        
        with open(md_filepath, 'wb') as f:
            f.write(markdown_content.encode('utf-8'))
        
        zip_path = download_images_dir.parent / f"{task_id}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(md_filepath, arcname=new_filename)
            
            for image_file in task_images_dir.rglob("*"):
                if image_file.is_file():
                    arcname = image_file.relative_to(task_dir)
                    zipf.write(image_file, arcname=arcname)
        
        return zip_path, task_id, len(downloaded_images)
    
    except Exception as e:
        st.error(f"创建ZIP文件时出错: {str(e)}")
        raise
    finally:
        if task_dir.exists():
            shutil.rmtree(task_dir)

# def main():
#     # 页面标题和返回按钮
#     col1, col2 = st.columns([4, 1])
#     with col1:
#         st.title("📸 Markdown图片本地化工具")
#     with col2:
#         if st.button("🏠 返回门户", use_container_width=True):
#             st.switch_page("portal.py")
    
#     st.markdown("""
#     ### 功能说明
#     将Markdown文件中的远程图片下载到本地，并生成包含Markdown文件和图片的ZIP包。
    
#     **使用步骤：**
#     1. 上传Markdown文件
#     2. 系统自动分析远程图片链接
#     3. 选择要下载的图片数量
#     4. 开始处理并下载ZIP包
#     """)
    
#     # 创建临时目录
#     session_id = str(uuid.uuid4().hex[:8])
#     TEMP_DIR = Path("temp") / f"markdown_images_{session_id}"
#     IMAGES_DIR = TEMP_DIR / "images"
#     TEMP_DIR.mkdir(exist_ok=True, parents=True)
#     IMAGES_DIR.mkdir(exist_ok=True)
    
#     # 文件上传
#     uploaded_file = st.file_uploader(
#         "📤 上传Markdown文件", 
#         type=['md', 'markdown', 'txt'],
#         help="支持.md、.markdown或.txt格式的文件"
#     )
    
#     if uploaded_file is not None:
#         # 读取文件内容
#         try:
#             content = uploaded_file.getvalue().decode('utf-8')
#         except:
#             content = uploaded_file.getvalue().decode('gbk', errors='ignore')
        
#         # 提取图片URL
#         image_urls = extract_image_urls(content)
        
#         if not image_urls:
#             st.info("⚠️ 未在文件中发现远程图片链接")
            
#             # 预览内容
#             with st.expander("📝 预览内容"):
#                 st.code(content[:1000], language="markdown")
#         else:
#             st.success(f"✅ 发现 {len(image_urls)} 个远程图片链接")
            
#             # 显示图片列表
#             with st.expander("🔗 查看图片链接"):
#                 for i, url in enumerate(image_urls[:10], 1):
#                     st.write(f"{i}. {url[:80]}...")
#                 if len(image_urls) > 10:
#                     st.write(f"... 还有 {len(image_urls) - 10} 个图片")
            
#             # 下载选项
#             col1, col2 = st.columns(2)
#             with col1:
#                 max_images = st.slider("下载图片数量", 1, len(image_urls), min(10, len(image_urls)))
#             with col2:
#                 download_all = st.checkbox("下载所有图片", value=True)
            
#             # 开始处理按钮
#             if st.button("🚀 开始处理", type="primary", use_container_width=True):
#                 with st.spinner("正在处理中..."):
#                     progress_bar = st.progress(0)
#                     status_text = st.empty()
#                     url_map = {}
#                     successful_downloads = 0
                    
#                     urls_to_download = image_urls if download_all else image_urls[:max_images]
                    
#                     # 清空图片目录
#                     for file in IMAGES_DIR.glob("*"):
#                         try:
#                             file.unlink()
#                         except:
#                             pass
                    
#                     for i, url in enumerate(urls_to_download):
#                         status_text.text(f"正在下载图片 {i+1}/{len(urls_to_download)}...")
#                         filename, filepath = download_image(url, IMAGES_DIR)
#                         if filename:
#                             url_map[url] = f"images/{filename}"
#                             successful_downloads += 1
#                         progress_bar.progress((i + 1) / len(urls_to_download))
                    
#                     # 替换图片链接
#                     status_text.text("正在替换图片链接...")
#                     modified_content = replace_image_urls(content, url_map)
                    
                    

#                     # 创建ZIP文件
#                     status_text.text("正在创建ZIP文件...")
#                     try:
#                         zip_path, task_id, zip_image_count = create_zip_file(
#                             modified_content, 
#                             uploaded_file.name, 
#                             url_map,
#                             IMAGES_DIR
#                         )
                        
#                         progress_bar.progress(1.0)
#                         status_text.text("处理完成！")
                        
#                         if zip_path.exists():
#                             with open(zip_path, 'rb') as f:
#                                 zip_data = f.read()
                            
#                             # 显示结果
#                             st.success(f"✅ 处理完成！成功下载 {successful_downloads} 张图片")
                            
#                             # 对比预览
#                             col_preview1, col_preview2 = st.columns(2)
#                             with col_preview1:
#                                 with st.expander("原始内容片段"):
#                                     st.code(content[:500], language="markdown")
#                             with col_preview2:
#                                 with st.expander("修改后内容片段"):
#                                     st.code(modified_content[:500], language="markdown")
                            
#                             # 下载按钮
#                             st.download_button(
#                                 label="⬇️ 下载ZIP文件",
#                                 data=zip_data,
#                                 file_name=f"{task_id}.zip",
#                                 mime="application/zip",
#                                 use_container_width=True,
#                                 type="primary"
#                             )
                            
#                             # 文件结构
#                             with st.expander("📁 文件结构"):
#                                 st.code(f"""
# {uploaded_file.name.split('.')[0]}_local.md
# └── images/
#     └── 包含 {zip_image_count} 张图片
#                                 """)
#                         else:
#                             st.error("❌ ZIP文件创建失败")
                    
#                     except Exception as e:
#                         st.error(f"处理失败: {str(e)}")
    
#     else:
#         st.info("👆 请上传一个Markdown文件开始处理")
        
#         # 示例
#         with st.expander("📋 查看示例"):
#             st.markdown("""
#             ```markdown
#             # 示例文档
            
#             这是一张远程图片：
            
#             ![示例图片](https://example.com/image.jpg)
            
#             处理后会变成：
            
#             ![示例图片](images/image.jpg)
#             ```
#             """)

def main():
    # 页面标题和返回按钮
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("📸 Markdown图片本地化工具")
    with col2:
        if st.button("🏠 返回门户", use_container_width=True):
            st.switch_page("portal.py")
    
    st.markdown("""
    ### 功能说明
    将Markdown文件中的远程图片下载到本地，并生成包含Markdown文件和图片的ZIP包。
    
    **使用步骤：**
    1. 上传Markdown文件
    2. 系统自动分析远程图片链接
    3. 选择要下载的图片数量
    4. 开始处理并下载ZIP包
    """)
    
    # 创建临时目录
    session_id = str(uuid.uuid4().hex[:8])
    TEMP_DIR = Path("temp") / f"markdown_images_{session_id}"
    IMAGES_DIR = TEMP_DIR / "images"
    MD_FILE_DIR = TEMP_DIR  # Markdown文件也放在temp目录下
    TEMP_DIR.mkdir(exist_ok=True, parents=True)
    IMAGES_DIR.mkdir(exist_ok=True)
    
    # 文件上传
    uploaded_file = st.file_uploader(
        "📤 上传Markdown文件", 
        type=['md', 'markdown', 'txt'],
        help="支持.md、.markdown或.txt格式的文件"
    )
    
    if uploaded_file is not None:
        # 读取文件内容
        try:
            content = uploaded_file.getvalue().decode('utf-8')
        except:
            content = uploaded_file.getvalue().decode('gbk', errors='ignore')
        
        # 提取图片URL
        image_urls = extract_image_urls(content)
        
        if not image_urls:
            st.info("⚠️ 未在文件中发现远程图片链接")
            
            # 预览内容
            with st.expander("📝 预览内容"):
                st.code(content[:1000], language="markdown")
        else:
            st.success(f"✅ 发现 {len(image_urls)} 个远程图片链接")
            
            # 显示图片列表
            with st.expander("🔗 查看图片链接"):
                for i, url in enumerate(image_urls[:10], 1):
                    st.write(f"{i}. {url[:80]}...")
                if len(image_urls) > 10:
                    st.write(f"... 还有 {len(image_urls) - 10} 个图片")
            
            # 下载选项
            col1, col2 = st.columns(2)
            with col1:
                max_images = st.slider("下载图片数量", 1, len(image_urls), min(10, len(image_urls)))
            with col2:
                download_all = st.checkbox("下载所有图片", value=True)
            
            # 开始处理按钮
            if st.button("🚀 开始处理", type="primary", use_container_width=True):
                with st.spinner("正在处理中..."):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    url_map = {}
                    successful_downloads = 0
                    
                    urls_to_download = image_urls if download_all else image_urls[:max_images]
                    
                    # 清空图片目录
                    for file in IMAGES_DIR.glob("*"):
                        try:
                            file.unlink()
                        except:
                            pass
                    
                    for i, url in enumerate(urls_to_download):
                        status_text.text(f"正在下载图片 {i+1}/{len(urls_to_download)}...")
                        filename, filepath = download_image(url, IMAGES_DIR)
                        if filename:
                            url_map[url] = f"images/{filename}"
                            successful_downloads += 1
                        progress_bar.progress((i + 1) / len(urls_to_download))
                    
                    # 替换图片链接
                    status_text.text("正在替换图片链接...")
                    modified_content = replace_image_urls(content, url_map)
                    
                    # 保存单独的Markdown文件到temp目录
                    md_filename = f"{uploaded_file.name.split('.')[0]}_local.md"
                    md_filepath = MD_FILE_DIR / md_filename
                    
                    try:
                        with open(md_filepath, 'w', encoding='utf-8') as f:
                            f.write(modified_content)
                        st.success(f"✅ Markdown文件已保存: `{md_filepath}`")
                    except Exception as e:
                        st.warning(f"保存单独的Markdown文件时出错: {str(e)}")
                    
                    # 创建ZIP文件
                    status_text.text("正在创建ZIP文件...")
                    try:
                        zip_path, task_id, zip_image_count = create_zip_file(
                            modified_content, 
                            uploaded_file.name, 
                            url_map,
                            IMAGES_DIR
                        )
                        
                        progress_bar.progress(1.0)
                        status_text.text("处理完成！")
                        
                        if zip_path.exists():
                            with open(zip_path, 'rb') as f:
                                zip_data = f.read()
                            
                            # 显示结果
                            st.success(f"✅ 处理完成！成功下载 {successful_downloads} 张图片")
                            
                            # 对比预览
                            col_preview1, col_preview2 = st.columns(2)
                            with col_preview1:
                                with st.expander("原始内容片段"):
                                    st.code(content[:500], language="markdown")
                            with col_preview2:
                                with st.expander("修改后内容片段"):
                                    st.code(modified_content[:500], language="markdown")
                            
                            # 显示文件结构
                            with st.expander("📁 文件结构"):
                                st.code(f"""
temp/
├── {md_filename}            # 修改后的Markdown文件
├── images/
│   └── 包含 {zip_image_count} 张图片
└── {task_id}.zip          # ZIP压缩包
                                """)
                            
                            # 下载选项
                            col_dl1, col_dl2 = st.columns(2)
                            with col_dl1:
                                # ZIP下载按钮
                                st.download_button(
                                    label="⬇️ 下载ZIP文件",
                                    data=zip_data,
                                    file_name=f"{task_id}.zip",
                                    mime="application/zip",
                                    use_container_width=True,
                                    type="primary"
                                )
                            
                            with col_dl2:
                                # 单独的Markdown文件下载按钮
                                with open(md_filepath, 'rb') as f:
                                    md_data = f.read()
                                st.download_button(
                                    label="📄 仅下载Markdown文件",
                                    data=md_data,
                                    file_name=md_filename,
                                    mime="text/markdown",
                                    use_container_width=True
                                )
                            
                            # 显示保存路径
                            st.info(f"""
                            **文件保存位置：**
                            - ZIP文件: `{zip_path}`
                            - Markdown文件: `{md_filepath}`
                            - 图片文件夹: `{IMAGES_DIR}`
                            """)
                        else:
                            st.error("❌ ZIP文件创建失败")
                    
                    except Exception as e:
                        st.error(f"处理失败: {str(e)}")
    
    else:
        st.info("👆 请上传一个Markdown文件开始处理")
        
        # 示例
        with st.expander("📋 查看示例"):
            st.markdown("""
            ```markdown
            # 示例文档
            
            这是一张远程图片：
            
            ![示例图片](https://example.com/image.jpg)
            
            处理后会变成：
            
            ![示例图片](images/image.jpg)
            ```
            """)


if __name__ == "__main__":
    main()