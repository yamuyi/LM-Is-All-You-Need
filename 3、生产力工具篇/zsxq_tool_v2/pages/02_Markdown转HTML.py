import streamlit as st
import markdown
from pathlib import Path
from bs4 import BeautifulSoup
import uuid
import zipfile
from datetime import datetime
import tempfile
import os
import base64
from io import BytesIO

# 新增导入 - 用于PDF和图片处理
import xhtml2pdf.pisa as pisa  # HTML转PDF[citation:5]
from spire.pdf import *  # PDF水印处理[citation:2]
from spire.pdf.common import *
from pdf2image import convert_from_path  # PDF转PNG[citation:3][citation:8]
from PIL import Image, ImageDraw, ImageFont
import math

# 页面配置
st.set_page_config(
    page_title="Markdown转HTML/PDF/图片工具",
    page_icon="📄",
    layout="wide"
)

def html_to_pdf(html_content, output_path, pdf_settings=None):
    """将HTML转换为PDF文件[citation:5]"""
    try:
        with open(output_path, "wb") as pdf_file:
            # 使用xhtml2pdf将HTML转换为PDF
            pisa_status = pisa.CreatePDF(
                html_content,
                dest=pdf_file,
                encoding='utf-8'
            )
        
        if pisa_status.err:
            st.error(f"PDF转换错误: {pisa_status.err}")
            return False
        return True
    except Exception as e:
        st.error(f"PDF转换失败: {str(e)}")
        return False

def add_watermark_to_pdf(input_pdf, output_pdf, watermark_config):
    """为PDF添加水印[citation:2]"""
    try:
        # 创建PdfDocument对象
        doc = PdfDocument()
        
        # 加载PDF文档
        doc.LoadFromFile(input_pdf)
        
        # 创建水印字体
        font_size = watermark_config.get('size', 48)
        font = PdfTrueTypeFont("Arial", font_size, 0, True)
        
        # 获取水印文本
        text = watermark_config.get('text', '')
        if not text:
            return False
        
        # 测量文本尺寸
        text_width = font.MeasureString(text).Width
        text_height = font.MeasureString(text).Height
        
        # 水印颜色
        color_hex = watermark_config.get('color', '#808080')
        color_rgb = tuple(int(color_hex[i:i+2], 16) for i in (1, 3, 5))
        color = PdfRGBColor(color_rgb[0]/255, color_rgb[1]/255, color_rgb[2]/255)
        
        # 水印密度设置
        density = watermark_config.get('density', 5)
        spacing = 200 / density  # 密度越大，间距越小
        
        # 遍历每一页添加水印
        for i in range(doc.Pages.Count):
            page = doc.Pages.get_Item(i)
            
            # 保存当前画布状态
            state = page.Canvas.Save()
            
            # 设置水印透明度
            page.Canvas.SetTransparency(0.3)
            
            # 根据密度重复添加水印
            page_width = page.Canvas.Size.Width
            page_height = page.Canvas.Size.Height
            
            # 计算需要添加的水印数量
            cols = int(page_width / (text_width + spacing)) + 1
            rows = int(page_height / (text_height + spacing)) + 1
            
            for col in range(cols):
                for row in range(rows):
                    x = col * (text_width + spacing)
                    y = row * (text_height + spacing)
                    
                    # 保存状态
                    page_state = page.Canvas.Save()
                    
                    # 移动到水印位置
                    page.Canvas.TranslateTransform(x, y)
                    
                    # 旋转角度
                    page.Canvas.RotateTransform(-45.0)
                    
                    # 绘制水印
                    page.Canvas.DrawString(text, font, PdfSolidBrush(color), 
                                          PointF(-text_width/2, -text_height/2))
                    
                    # 恢复状态
                    page.Canvas.Restore(page_state)
            
            # 恢复原始状态
            page.Canvas.Restore(state)
        
        # 保存加水印后的PDF
        doc.SaveToFile(output_pdf)
        doc.Close()
        return True
        
    except Exception as e:
        st.error(f"添加水印失败: {str(e)}")
        return False

def pdf_to_png(pdf_path, output_dir, dpi=150):
    """将PDF转换为PNG图片（每页一张）[citation:3][citation:8]"""
    try:
        # 使用pdf2image将PDF转换为图片列表
        images = convert_from_path(pdf_path, dpi=dpi)
        
        # 保存每张图片
        image_paths = []
        for i, image in enumerate(images):
            image_path = os.path.join(output_dir, f"page_{i+1:03d}.png")
            image.save(image_path, "PNG")
            image_paths.append(image_path)
        
        return image_paths
    except Exception as e:
        st.error(f"PDF转PNG失败: {str(e)}")
        return []

def create_zip_file(files, zip_path):
    """创建包含多个文件的ZIP包"""
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in files:
                zipf.write(file, os.path.basename(file))
        return True
    except Exception as e:
        st.error(f"创建ZIP包失败: {str(e)}")
        return False

def main():
    # 页面标题和返回按钮
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("📄 Markdown转HTML/PDF/图片工具")
    with col2:
        if st.button("🏠 返回门户", use_container_width=True):
            st.switch_page("portal.py")
    
    st.markdown("""
    ### 功能说明
    将Markdown文件转换为美观的HTML文档、PDF文件或PNG图片，支持多种格式输出。
    
    **新增功能：**
    1. HTML转PDF - 将生成的HTML转换为PDF文档
    2. PDF加水印 - 为PDF添加可自定义的水印
    3. PDF转PNG - 将PDF自动切分成多个PNG图片
    
    **使用步骤：**
    1. 上传Markdown文件
    2. 设置转换选项
    3. 开始转换
    4. 下载所需格式文件
    """)
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 转换设置")
        
        # Markdown转换设置
        use_extensions = st.checkbox("启用Markdown扩展", value=True, 
                                    help="启用代码高亮、目录等扩展功能")
        generate_toc = st.checkbox("自动生成目录", value=True,
                                  help="为文档自动生成目录导航")
        include_css = st.checkbox("包含CSS样式", value=True,
                                 help="在HTML中嵌入现代化的CSS样式")
        
        st.divider()
        st.header("📄 PDF转换设置")
        
        # PDF转换设置
        generate_pdf = st.checkbox("生成PDF文件", value=False,
                                  help="将HTML转换为PDF格式")
        
        if generate_pdf:
            # 水印设置
            add_watermark = st.checkbox("添加PDF水印", value=False,
                                       help="为PDF文件添加水印")
            
            if add_watermark:
                watermark_text = st.text_input("水印文字", value="机密文件",
                                              help="水印显示的文字内容")
                watermark_color = st.color_picker("水印颜色", "#808080",
                                                 help="水印文字的颜色")
                watermark_size = st.slider("水印大小", 20, 100, 48,
                                          help="水印文字的大小")
                watermark_density = st.slider("水印密度", 1, 10, 5,
                                            help="水印的密集程度，值越大越密集")
            
            # PNG转换设置
            convert_to_png = st.checkbox("PDF转PNG图片", value=False,
                                        help="将PDF转换为PNG图片格式")
            
            if convert_to_png:
                png_dpi = st.slider("图片DPI", 72, 300, 150,
                                   help="PNG图片的分辨率，值越高越清晰")
    
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
                    task_id = f"md_conversion_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
                    temp_dir = Path("temp") / task_id
                    temp_dir.mkdir(parents=True, exist_ok=True)
                    
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
                            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Microsoft YaHei", sans-serif; 
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
                    html_filepath = temp_dir / html_filename
                    
                    with open(html_filepath, 'w', encoding='utf-8') as f:
                        f.write(soup.prettify())
                    
                    st.success("✅ HTML转换成功！")
                    
                    # 结果统计和文件列表
                    all_files = [html_filepath]
                    
                    # 显示HTML结果统计
                    col_stat1, col_stat2, col_stat3 = st.columns(3)
                    with col_stat1:
                        st.metric("输出文件", html_filename)
                    with col_stat2:
                        st.metric("HTML大小", f"{html_filepath.stat().st_size / 1024:.1f} KB")
                    with col_stat3:
                        st.metric("目录生成", "✅" if toc_content else "❌")
                    
                    # PDF转换
                    pdf_filepath = None
                    if generate_pdf:
                        st.subheader("📄 PDF转换")
                        
                        # 生成PDF文件名
                        pdf_filename = f"{Path(uploaded_file.name).stem}.pdf"
                        pdf_filepath = temp_dir / pdf_filename
                        
                        # 将HTML转换为PDF[citation:5]
                        with st.spinner("正在生成PDF文件..."):
                            if html_to_pdf(soup.prettify(), pdf_filepath):
                                pdf_size = pdf_filepath.stat().st_size / 1024
                                st.success(f"✅ PDF生成成功！文件大小: {pdf_size:.1f} KB")
                                all_files.append(pdf_filepath)
                                
                                # PDF加水印
                                if add_watermark:
                                    watermark_config = {
                                        'text': watermark_text,
                                        'color': watermark_color,
                                        'size': watermark_size,
                                        'density': watermark_density
                                    }
                                    
                                    watermarked_pdf = temp_dir / f"watermarked_{pdf_filename}"
                                    with st.spinner("正在添加水印..."):
                                        if add_watermark_to_pdf(str(pdf_filepath), str(watermarked_pdf), watermark_config):
                                            watermarked_size = watermarked_pdf.stat().st_size / 1024
                                            st.success(f"✅ 水印添加成功！文件大小: {watermarked_size:.1f} KB")
                                            all_files.append(watermarked_pdf)
                                            pdf_filepath = watermarked_pdf  # 后续使用加水印的PDF
                                
                                # PDF转PNG[citation:3][citation:8]
                                if convert_to_png:
                                    st.subheader("🖼️ PDF转PNG")
                                    
                                    # 创建PNG输出目录
                                    png_dir = temp_dir / "png_images"
                                    png_dir.mkdir(exist_ok=True)
                                    
                                    with st.spinner("正在转换PDF为PNG图片..."):
                                        png_files = pdf_to_png(str(pdf_filepath), str(png_dir), png_dpi)
                                        
                                        if png_files:
                                            st.success(f"✅ 转换成功！生成 {len(png_files)} 张PNG图片")
                                            
                                            # 显示图片预览
                                            cols = st.columns(min(3, len(png_files)))
                                            for idx, png_file in enumerate(png_files[:3]):  # 最多显示3张预览
                                                with cols[idx % 3]:
                                                    st.image(png_file, caption=f"第{idx+1}页", use_column_width=True)
                                            
                                            # 将所有PNG文件添加到文件列表
                                            all_files.extend(png_files)
                    
                    # 提供下载
                    st.subheader("📥 下载选项")
                    
                    # 创建下载列
                    num_columns = min(4, len(all_files))
                    cols = st.columns(num_columns)
                    
                    for idx, file_path in enumerate(all_files):
                        with cols[idx % num_columns]:
                            file_name = os.path.basename(file_path)
                            file_size = os.path.getsize(file_path) / 1024
                            
                            with open(file_path, 'rb') as f:
                                file_data = f.read()
                            
                            # 确定MIME类型
                            if file_name.endswith('.html'):
                                mime_type = "text/html"
                                label = "⬇️ HTML"
                            elif file_name.endswith('.pdf'):
                                mime_type = "application/pdf"
                                label = "⬇️ PDF"
                            elif file_name.endswith('.png'):
                                mime_type = "image/png"
                                label = "🖼️ PNG"
                            else:
                                mime_type = "application/octet-stream"
                                label = "⬇️ 文件"
                            
                            st.download_button(
                                label=f"{label} ({file_name})",
                                data=file_data,
                                file_name=file_name,
                                mime=mime_type,
                                help=f"大小: {file_size:.1f} KB",
                                use_container_width=True
                            )
                    
                    # 创建完整ZIP包
                    st.subheader("📦 打包下载")
                    zip_filename = f"{task_id}.zip"
                    zip_path = temp_dir.parent / zip_filename
                    
                    if create_zip_file(all_files, zip_path):
                        with open(zip_path, 'rb') as f:
                            zip_data = f.read()
                        
                        st.download_button(
                            label="📦 下载完整ZIP包",
                            data=zip_data,
                            file_name=zip_filename,
                            mime="application/zip",
                            use_container_width=True,
                            type="primary"
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
            
        # 新增功能说明
        with st.expander("🆕 新增功能说明"):
            st.markdown("""
            ### 新增功能详细说明
            
            **1. HTML转PDF功能**
            - 使用xhtml2pdf库实现HTML到PDF的转换[citation:5]
            - 保持HTML的样式和布局
            - 支持中文字符显示
            
            **2. PDF加水印功能**[citation:2]
            - 支持自定义水印文字
            - 可设置水印颜色、大小和透明度
            - 可调节水印密度（密集程度）
            - 水印倾斜45度显示，覆盖整个页面
            
            **3. PDF转PNG功能**[citation:3][citation:8]
            - 自动将PDF每页转换为单独的PNG图片
            - 可调节输出图片的DPI（分辨率）
            - 支持批量处理多页PDF
            - 保持原始PDF的清晰度
            
            **安装所需依赖：**
            ```bash
            pip install xhtml2pdf spire.pdf pdf2image pillow
            ```
            
            **注意：**
            - pdf2image需要系统安装poppler或ImageMagick
            - 在Linux上: `sudo apt-get install poppler-utils`
            - 在macOS上: `brew install poppler`
            - 在Windows上: 从http://blog.alivate.com.au/poppler-windows/ 下载poppler
            """)

if __name__ == "__main__":
    main()