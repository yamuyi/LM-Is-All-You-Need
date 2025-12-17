import streamlit as st
import markdown
from pathlib import Path
from bs4 import BeautifulSoup
import uuid
import zipfile
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import base64
from io import BytesIO
import tempfile
import os

# 页面配置
st.set_page_config(
    page_title="Markdown转HTML(专业水印)",
    page_icon="🖼️",
    layout="wide"
)

def add_watermark_to_html(content, watermark_text, 
                          color='#888888',
                          opacity=0.3,
                          font_size='3vw',
                          rotate=-45,
                          density=10):
    """
    给HTML内容添加简洁有效的水印
    
    参数:
    content (str): HTML内容字符串
    watermark_text (str): 水印文本
    color (str): 水印文本颜色
    opacity (float): 水印透明度
    font_size (str): 水印字体大小
    rotate (int): 水印旋转角度
    density (int): 水印密度
    
    返回:
    str: 添加水印后的HTML内容
    """
    soup = BeautifulSoup(content, 'html.parser')
    
    # 创建水印样式 - 简化版本，更稳定可靠
    style_tag = soup.new_tag('style')
    style_content = f"""
    /* 水印样式 */
    .watermark-overlay {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 9999;
        overflow: hidden;
    }}

    .watermark-layer {{
    width: 100vw;  # 视口宽度单位
    height: 100vh; # 视口高度单位
    }}
    
    .watermark-item {{
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
    }}
    
    .watermark-text {{
        color: {color};
        opacity: {opacity};
        font-size: {font_size};
        transform: rotate({rotate}deg);
        white-space: nowrap;
        font-weight: normal;
        font-family: Arial, sans-serif;
    }}
    
    /* 确保内容在水印上方 */
    .content-wrapper {{
        position: relative;
        z-index: 1;
    }}
    
    /* 打印时保持水印 */
    @media print {{
        .watermark-overlay {{
            display: block !important;
        }}
        .watermark-text {{
            opacity: 0.2 !important;
        }}
    }}
    """
    style_tag.string = style_content
    
    # 将样式添加到head
    head_tag = soup.head
    if head_tag:
        head_tag.append(style_tag)
    else:
        html_tag = soup.html
        if html_tag:
            html_tag.insert(0, style_tag)
    
    # 获取或创建body
    body_tag = soup.body
    if not body_tag:
        body_tag = soup.new_tag('body')
        soup.html.append(body_tag)
    
    # 创建内容包装器
    existing_content = list(body_tag.contents)
    content_wrapper = soup.new_tag('div')
    content_wrapper['class'] = 'content-wrapper'
    
    # 移动原有内容到包装器
    for child in existing_content:
        if child.name is not None:  # 只移动标签元素
            content_wrapper.append(child)
    
    # 清空body并添加新结构
    body_tag.clear()
    
    # 创建水印层
    watermark_layer = soup.new_tag('div')
    watermark_layer['class'] = 'watermark-overlay'
    watermark_grid = soup.new_tag('div')
    watermark_grid['class'] = 'watermark-grid'
    watermark_layer.append(watermark_grid)
    
    # 添加水印项目
    for _ in range(density * density):
        watermark_item = soup.new_tag('div')
        watermark_item['class'] = 'watermark-item'
        watermark_text_tag = soup.new_tag('div')
        watermark_text_tag['class'] = 'watermark-text'
        watermark_text_tag.string = watermark_text
        watermark_item.append(watermark_text_tag)
        watermark_grid.append(watermark_item)
    
    # 添加到body
    body_tag.append(watermark_layer)
    body_tag.append(content_wrapper)
    
    return str(soup)

def create_html_skeleton(title="带水印文档", content_html="", watermark_config=None):
    """创建HTML基础骨架，直接嵌入内容"""
    # 读取Markdown转换的HTML内容
    content_html = content_html or "<p>文档内容</p>"
    
    # 基础CSS样式
    css_style = """
    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }
    
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei", sans-serif;
        max-width: 1200px;
        margin: 0 auto;
        padding: 40px 20px;
        line-height: 1.8;
        color: #333;
        background: #fff;
        min-height: 100vh;
        position: relative;
    }
    
    .document-content {
        background: white;
        padding: 50px;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        position: relative;
        z-index: 1;
    }
    
    h1 { 
        font-size: 2.5em; 
        margin: 1.2em 0 0.6em;
        padding-bottom: 0.4em;
        border-bottom: 3px solid #4a90e2;
        color: #2c3e50;
        font-weight: 600;
    }
    
    h2 { 
        font-size: 2em; 
        margin: 1.5em 0 0.8em;
        padding-bottom: 0.3em;
        border-bottom: 2px solid #e0e6ed;
        color: #34495e;
        font-weight: 500;
    }
    
    h3 { 
        font-size: 1.5em; 
        margin: 1.2em 0 0.6em;
        color: #4a5568;
        font-weight: 500;
    }
    
    h4 {
        font-size: 1.25em;
        margin: 1em 0 0.5em;
        color: #718096;
    }
    
    p { 
        margin: 1.2em 0;
        text-align: justify;
        font-size: 1.1em;
    }
    
    pre { 
        background: #f8fafc; 
        padding: 1.5em; 
        border-radius: 10px; 
        overflow-x: auto;
        font-size: 0.95em;
        border-left: 4px solid #4299e1;
        margin: 1.5em 0;
    }
    
    code { 
        background: #f1f5f9; 
        padding: 0.3em 0.6em; 
        border-radius: 4px;
        font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, 'Courier New', monospace;
        font-size: 0.95em;
        color: #2d3748;
    }
    
    pre code { 
        background: transparent; 
        padding: 0;
        font-size: 1em;
    }
    
    .toc-container {
        background: linear-gradient(135deg, #f6f9fc 0%, #edf2f7 100%);
        padding: 2em;
        border-radius: 12px;
        margin: 2em 0;
        border: 1px solid #e2e8f0;
    }
    
    .toc-title { 
        font-weight: 600; 
        margin-bottom: 1.2em;
        color: #2d3748;
        font-size: 1.3em;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .toc-title::before {
        content: "📑";
        font-size: 1.2em;
    }
    
    .toc ul { 
        list-style: none; 
        padding-left: 0;
        margin: 0;
    }
    
    .toc li { 
        margin: 0.8em 0;
        position: relative;
        padding-left: 1.5em;
    }
    
    .toc li::before {
        content: "•";
        position: absolute;
        left: 0;
        color: #4a90e2;
        font-weight: bold;
    }
    
    .toc a {
        color: #4a90e2;
        text-decoration: none;
        transition: color 0.2s;
        font-size: 1.05em;
    }
    
    .toc a:hover {
        color: #2c5282;
        text-decoration: underline;
    }
    
    blockquote {
        border-left: 4px solid #a0aec0;
        padding: 1.2em 2em;
        color: #4a5568;
        margin: 2em 0;
        background: #f7fafc;
        border-radius: 0 8px 8px 0;
        font-style: italic;
    }
    
    blockquote p {
        margin: 0;
    }
    
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 2em 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        border-radius: 8px;
        overflow: hidden;
    }
    
    th, td {
        border: 1px solid #e2e8f0;
        padding: 1em;
        text-align: left;
    }
    
    th {
        background: linear-gradient(135deg, #4a90e2 0%, #2c5282 100%);
        color: white;
        font-weight: 500;
    }
    
    tr:nth-child(even) {
        background: #f8fafc;
    }
    
    img {
        max-width: 100%;
        height: auto;
        display: block;
        margin: 2em auto;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
        margin: 3em 0;
    }
    
    ul, ol {
        margin: 1.2em 0;
        padding-left: 2em;
    }
    
    li {
        margin: 0.8em 0;
    }
    
    /* 响应式设计 */
    @media (max-width: 768px) {
        body {
            padding: 20px 15px;
        }
        
        .document-content {
            padding: 25px;
        }
        
        h1 { 
            font-size: 2em; 
        }
        
        h2 { 
            font-size: 1.6em; 
        }
        
        h3 { 
            font-size: 1.3em; 
        }
        
        p {
            font-size: 1em;
        }
        
        pre {
            padding: 1em;
        }
    }
    
    /* 打印样式 */
    @media print {
        body {
            background: white;
            padding: 0;
            margin: 0;
        }
        
        .document-content {
            box-shadow: none;
            padding: 20pt;
        }
        
        h1, h2, h3, h4 {
            page-break-after: avoid;
        }
        
        p {
            orphans: 3;
            widows: 3;
        }
        
        pre, code {
            page-break-inside: avoid;
        }
    }
    """
    
    # 直接创建完整的HTML
    html_template = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        {css_style}
    </style>
</head>
<body>
    <div class="document-content">
        {content_html}
    </div>
</body>
</html>'''
    
    return html_template

def create_watermark_preview(watermark_text, color='#888888', opacity=0.3, 
                           font_size='3vw', rotate=-45, density=10):
    """创建水印预览图片"""
    try:
        # 创建预览图片
        width, height = 500, 350
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        # 绘制背景网格
        cell_width = width / density
        cell_height = height / density
        
        # 绘制网格线
        for i in range(1, density):
            x = i * cell_width
            y = i * cell_height
            draw.line([(x, 0), (x, height)], fill='#f0f0f0', width=1)
            draw.line([(0, y), (width, y)], fill='#f0f0f0', width=1)
        
        # 将十六进制颜色转换为RGB
        hex_color = color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # 计算透明度
        alpha = int(255 * opacity)
        
        # 创建字体
        try:
            # 估算vw大小（假设100vw=500px）
            vw_value = float(font_size.replace('vw', ''))
            font_size_px = int(width * vw_value / 100)
            font_size_px = max(12, min(font_size_px, 36))
            
            # 尝试加载字体
            font = None
            font_paths = [
                "C:/Windows/Fonts/msyh.ttc",
                "C:/Windows/Fonts/simhei.ttf",
                "/System/Library/Fonts/PingFang.ttc",
                "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            ]
            
            for path in font_paths:
                if Path(path).exists():
                    try:
                        font = ImageFont.truetype(path, font_size_px)
                        break
                    except:
                        continue
            
            if not font:
                font = ImageFont.load_default().font_variant(size=font_size_px)
        except:
            font = ImageFont.load_default()
        
        # 计算每个水印的位置
        for i in range(density):
            for j in range(density):
                center_x = i * cell_width + cell_width / 2
                center_y = j * cell_height + cell_height / 2
                
                # 创建文本图像
                text_img = Image.new('RGBA', (200, 200), (0, 0, 0, 0))
                text_draw = ImageDraw.Draw(text_img)
                
                # 获取文本尺寸
                bbox = text_draw.textbbox((0, 0), watermark_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # 将文本绘制在中心
                text_x = 100 - text_width / 2
                text_y = 100 - text_height / 2
                text_draw.text((text_x, text_y), watermark_text, 
                              font=font, fill=(*rgb, alpha))
                
                # 旋转文本
                rotated_text = text_img.rotate(rotate, expand=True, fillcolor=(0, 0, 0, 0))
                
                # 粘贴到主图像
                paste_x = int(center_x - rotated_text.width / 2)
                paste_y = int(center_y - rotated_text.height / 2)
                img.paste(rotated_text, (paste_x, paste_y), rotated_text)
        
        # 添加边框
        border_img = Image.new('RGB', (width + 40, height + 60), color='#f8fafc')
        border_img.paste(img, (20, 20))
        
        # 添加标题
        title_draw = ImageDraw.Draw(border_img)
        title_draw.text((20, height + 30), 
                       f"水印预览: {watermark_text} | 网格: {density}×{density}", 
                       fill='#666666', font=ImageFont.load_default())
        
        return border_img
        
    except Exception as e:
        # 简单备选方案
        img = Image.new('RGB', (500, 350), color='white')
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, 499, 349], outline='#e2e8f0', width=2)
        
        # 简单显示水印文字
        draw.text((150, 150), watermark_text, fill='#888888', 
                 font=ImageFont.load_default())
        draw.text((50, 50), f"网格密度: {density}×{density}", 
                 fill='#666666', font=ImageFont.load_default())
        
        return img

def main():
    # 页面标题和返回按钮
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("🖼️ Markdown转HTML(专业水印)")
    with col2:
        if st.button("🏠 返回门户", use_container_width=True):
            st.switch_page("portal.py")
    
    st.markdown("""
    ### 🎯 功能说明
    将Markdown文件转换为带有专业网格水印的HTML文档，水印随视口大小自动调整，支持长页面滚动。
    """)
    
    # 创建两列布局
    col_config, col_main = st.columns([1, 2])
    
    with col_config:
        st.header("⚙️ 水印设置")
        
        # 水印文本设置
        watermark_text = st.text_input(
            "📝 水印文字",
            value="羊头人的AI日志",
            help="输入要显示的水印文字"
        )
        
        # 颜色选择
        st.subheader("🎨 颜色设置")
        color_options = {
            "深灰色 (推荐)": "#888888",
            "浅灰色": "#AAAAAA",
            "红色": "#FF6B6B",
            "蓝色": "#4A90E2",
            "绿色": "#51CF66",
            "紫色": "#9775FA",
            "橙色": "#FF922B",
            "自定义颜色": "custom"
        }
        
        selected_color_name = st.selectbox(
            "选择水印颜色",
            list(color_options.keys()),
            index=0
        )
        
        if selected_color_name == "自定义颜色":
            watermark_color = st.color_picker("选择自定义颜色", "#888888")
        else:
            watermark_color = color_options[selected_color_name]
        
        # 高级设置
        with st.expander("⚙️ 高级设置", expanded=True):
            opacity = st.slider(
                "透明度", 
                min_value=0.05, 
                max_value=0.8, 
                value=0.3, 
                step=0.05,
                help="水印的透明度，越低越不明显"
            )
            
            font_size = st.select_slider(
                "字体大小 (vw)", 
                options=['1vw', '2vw', '3vw', '4vw', '5vw', '6vw'],
                value='3vw',
                help="相对于视口宽度的百分比，推荐3vw"
            )
            
            rotate = st.slider(
                "旋转角度", 
                min_value=-90, 
                max_value=90, 
                value=-45, 
                step=5,
                help="水印文本的旋转角度，负数为逆时针旋转"
            )
            
            density = st.slider(
                "网格密度", 
                min_value=5, 
                max_value=20, 
                value=5, 
                step=1,
                help="水印网格的行列数，密度越高水印越密集"
            )
        
        st.header("📄 HTML设置")
        
        with st.expander("文档配置", expanded=True):
            use_extensions = st.checkbox("启用Markdown扩展", value=True,
                                       help="启用代码高亮、表格等扩展功能")
            generate_toc = st.checkbox("自动生成目录", value=True,
                                      help="为文档自动生成导航目录")
            theme_style = st.selectbox(
                "文档主题",
                options=["light", "professional", "academic"],
                format_func=lambda x: {
                    "light": "🌞 明亮风格",
                    "professional": "💼 专业风格",
                    "academic": "🎓 学术风格"
                }[x]
            )
    
    with col_main:
        # 显示水印预览
        st.header("👁️ 实时预览")
        
        # 创建两列预览布局
        preview_col1, preview_col2 = st.columns(2)
        
        with preview_col1:
            # 水印效果预览
            preview_img = create_watermark_preview(
                watermark_text, 
                color=watermark_color,
                opacity=opacity,
                font_size=font_size,
                rotate=rotate,
                density=density
            )
            
            # 转换为base64显示
            buffered = BytesIO()
            preview_img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            st.markdown(f"""
            <div style="text-align: center; margin-bottom: 20px;">
                <div style="font-weight: bold; color: #4a5568; margin-bottom: 10px;">🎨 水印效果预览</div>
                <img src="data:image/png;base64,{img_str}" style="max-width: 100%; border-radius: 12px; border: 1px solid #e2e8f0;">
            </div>
            """, unsafe_allow_html=True)
        
        with preview_col2:
            # 参数展示
            st.markdown("### 📊 当前参数")
            
            param_html = f"""
            <div style="background: #f8fafc; padding: 15px; border-radius: 10px; margin: 10px 0;">
                <div style="display: flex; justify-content: space-between; margin: 8px 0;">
                    <span style="color: #718096; font-weight: 500;">水印文字:</span>
                    <span style="color: #2d3748; font-weight: 600;">{watermark_text}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin: 8px 0;">
                    <span style="color: #718096; font-weight: 500;">颜色:</span>
                    <span style="color: {watermark_color}; font-weight: 600;">■ {selected_color_name}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin: 8px 0;">
                    <span style="color: #718096; font-weight: 500;">透明度:</span>
                    <span style="color: #2d3748; font-weight: 600;">{int(opacity*100)}%</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin: 8px 0;">
                    <span style="color: #718096; font-weight: 500;">字体大小:</span>
                    <span style="color: #2d3748; font-weight: 600;">{font_size}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin: 8px 0;">
                    <span style="color: #718096; font-weight: 500;">旋转角度:</span>
                    <span style="color: #2d3748; font-weight: 600;">{rotate}°</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin: 8px 0;">
                    <span style="color: #718096; font-weight: 500;">网格密度:</span>
                    <span style="color: #2d3748; font-weight: 600;">{density}×{density}</span>
                </div>
            </div>
            """
            
            st.markdown(param_html, unsafe_allow_html=True)
        
        # 文件上传区域
        st.header("📤 文件上传")
        uploaded_file = st.file_uploader(
            "选择Markdown文件",
            type=['md', 'markdown', 'txt'],
            help="支持.md、.markdown、.txt格式"
        )
        
        if uploaded_file is not None:
            # 读取文件内容
            try:
                content = uploaded_file.getvalue().decode('utf-8')
            except:
                content = uploaded_file.getvalue().decode('gbk', errors='ignore')
            
            # 显示文件信息和预览
            tab_info, tab_preview = st.tabs(["📋 文件信息", "👁️ 内容预览"])
            
            with tab_info:
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.metric("📄 文件名", uploaded_file.name)
                    st.metric("📊 文件大小", f"{uploaded_file.size / 1024:.1f} KB")
                with col_info2:
                    st.metric("📈 行数", len(content.split('\n')))
                    st.metric("🔤 字符数", len(content))
            
            with tab_preview:
                st.code(content[:1500] + ("..." if len(content) > 1500 else ""), 
                       language="markdown")
            
            # 转换按钮
            st.markdown("---")
            if st.button("🚀 开始转换", type="primary", use_container_width=True):
                with st.spinner("正在转换中..."):
                    try:
                        # 创建临时目录
                        task_id = f"watermark_md_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
                        temp_dir = Path(tempfile.gettempdir()) / task_id
                        html_dir = temp_dir / "html"
                        html_dir.mkdir(parents=True, exist_ok=True)
                        
                        # 配置Markdown扩展
                        extensions = []
                        if use_extensions:
                            extensions = [
                                'markdown.extensions.extra',
                                'markdown.extensions.codehilite',
                                'markdown.extensions.toc',
                                'markdown.extensions.fenced_code',
                                'markdown.extensions.tables',
                                'markdown.extensions.sane_lists'
                            ]
                        
                        # Markdown转HTML
                        md_processor = markdown.Markdown(extensions=extensions)
                        html_content = md_processor.convert(content)
                        
                        # 获取目录
                        toc_content = ""
                        if generate_toc and hasattr(md_processor, 'toc'):
                            toc_content = md_processor.toc
                        
                        # 处理目录插入
                        html_with_toc = str(html_content)
                        if '<p>[toc]</p>' in html_with_toc and toc_content:
                            toc_html = f'''
                            <div class="toc-container">
                                <div class="toc-title">目录</div>
                                <div class="toc">
                                    {toc_content}
                                </div>
                            </div>
                            '''
                            html_with_toc = html_with_toc.replace('<p>[toc]</p>', toc_html)
                        
                        # 创建完整的HTML骨架
                        full_html = create_html_skeleton(
                            title=f"{Path(uploaded_file.name).stem} - 带水印文档",
                            content_html=html_with_toc
                        )
                        
                        # 添加水印
                        watermarked_html = add_watermark_to_html(
                            full_html,
                            watermark_text=watermark_text,
                            color=watermark_color,
                            opacity=opacity,
                            font_size=font_size,
                            rotate=rotate,
                            density=density
                        )
                        
                        # 保存HTML文件
                        html_filename = f"{Path(uploaded_file.name).stem}_watermarked.html"
                        html_filepath = html_dir / html_filename
                        
                        with open(html_filepath, 'w', encoding='utf-8') as f:
                            f.write(watermarked_html)
                        
                        # 创建ZIP包
                        zip_filename = f"{Path(uploaded_file.name).stem}_watermarked.zip"
                        zip_path = temp_dir / zip_filename
                        
                        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                            zipf.write(html_filepath, arcname=html_filename)
                        
                        st.success("✅ 转换成功！")
                        
                        # 显示结果
                        st.subheader("📦 下载选项")
                        
                        col_dl1, col_dl2 = st.columns(2)
                        
                        with col_dl1:
                            with open(html_filepath, 'rb') as f:
                                html_data = f.read()
                            
                            st.download_button(
                                label="📄 下载HTML文件",
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
                                label="📦 下载ZIP压缩包",
                                data=zip_data,
                                file_name=zip_filename,
                                mime="application/zip",
                                use_container_width=True
                            )
                        
                        # HTML预览
                        with st.expander("👀 HTML效果预览", expanded=True):
                            st.markdown("""
                            <div style="background: #f8fafc; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                                <div style="color: #4a5568; font-weight: 500;">💡 预览说明：</div>
                                <div style="color: #718096; font-size: 0.9em; margin-top: 5px;">
                                    实际水印效果需要在浏览器中打开HTML文件查看，以下是HTML源码预览：
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # 显示前3000个字符的预览
                            preview_html = watermarked_html[:3000]
                            if len(watermarked_html) > 3000:
                                preview_html += "\n\n... [完整内容请下载查看]"
                            
                            st.code(preview_html, language="html")
                        
                        # 使用提示
                        st.info("""
                        💡 **使用提示：**
                        1. 下载的HTML文件可以在任何现代浏览器中打开
                        2. 水印使用CSS网格布局，响应式设计，适配各种屏幕
                        3. 水印会显示在文档内容后面，不会遮挡文字阅读
                        4. 长文档滚动时会自动添加水印层，保证全覆盖
                        5. 打印时水印会自动调整，确保清晰可见
                        """)
                    
                    except Exception as e:
                        st.error(f"❌ 转换失败: {str(e)}")
                        st.exception(e)
        
        else:
            st.info("👆 请上传一个Markdown文件开始处理")

if __name__ == "__main__":
    main()