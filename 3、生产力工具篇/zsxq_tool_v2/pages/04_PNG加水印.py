import streamlit as st
import base64
from io import BytesIO
from datetime import datetime
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageOps
import tempfile
import os
import requests
import re
import html
from urllib.parse import urlparse
import io

# 设置页面配置
st.set_page_config(
    page_title="Markdown转图片卡片生成器",
    page_icon="🖼️",
    layout="wide"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main > div {
        padding-top: 1rem;
    }
    .stButton > button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .preview-container {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 20px;
        background-color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap');
    * {
        font-family: 'Noto Sans SC', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# 初始化session state
if 'card_image' not in st.session_state:
    st.session_state.card_image = None
if 'last_watermark_text' not in st.session_state:
    st.session_state.last_watermark_text = ""
if 'temp_images' not in st.session_state:
    st.session_state.temp_images = {}

def get_font(font_path=None, size=16):
    """获取字体，优先使用用户上传的中文字体"""
    font_paths = []
    
    # 1. 如果用户上传了字体，使用上传的字体
    if font_path and os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size=size)
        except:
            pass
    
    # 2. 尝试常见的中文字体路径
    common_fonts = [
        # Windows 中文字体
        "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
        "C:/Windows/Fonts/simhei.ttf",  # 黑体
        "C:/Windows/Fonts/simkai.ttf",  # 楷体
        # macOS 中文字体
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        # Linux 中文字体
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    
    for font in common_fonts:
        if os.path.exists(font):
            try:
                return ImageFont.truetype(font, size=size)
            except:
                continue
    
    # 3. 如果都失败，使用默认字体（可能不支持中文）
    st.warning("未找到中文字体，中文可能显示为方框。请上传中文字体文件。")
    return ImageFont.load_default()

def download_image(url, max_size=(600, 400)):
    """下载并调整图片大小"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        img = Image.open(BytesIO(response.content))
        
        # 转换为RGB模式（如果是RGBA）
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 调整图片大小
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        return img
    except Exception as e:
        st.error(f"下载图片失败: {e}")
        return None

def extract_images_from_markdown(md_content):
    """从Markdown中提取图片链接"""
    # Markdown图片语法: ![alt](url)
    pattern = r'!\[.*?\]\((.*?)\)'
    return re.findall(pattern, md_content)

def replace_images_with_placeholders(md_content):
    """将图片替换为占位符"""
    pattern = r'(!\[.*?\]\()(.*?)(\))'
    def replace(match):
        return f"{match.group(1)}[图片]{match.group(3)}"
    return re.sub(pattern, replace, md_content)

def create_mac_window_header(draw, width, title="Markdown Card"):
    """创建Mac风格窗口头部"""
    # 绘制窗口背景
    draw.rectangle([(0, 0), (width, 30)], 
                  fill=(232, 232, 232), 
                  outline=(176, 176, 176))
    
    # 绘制窗口控制按钮
    button_colors = [(255, 95, 87), (255, 189, 46), (40, 202, 66)]
    for i, color in enumerate(button_colors):
        x = 15 + i * 20
        y = 9
        draw.ellipse([x, y, x+12, y+12], fill=color)
    
    return 30  # 返回头部高度

def wrap_text_chinese(text, font, max_width):
    """支持中文的文本换行"""
    lines = []
    current_line = ""
    
    for char in text:
        # 测试添加当前字符后的宽度
        test_line = current_line + char
        bbox = font.getbbox(test_line)
        text_width = bbox[2] - bbox[0]
        
        if text_width <= max_width or not current_line:
            current_line += char
        else:
            lines.append(current_line)
            current_line = char
    
    if current_line:
        lines.append(current_line)
    
    return lines

def create_card_image(md_content, config, uploaded_font=None):
    """创建卡片图片"""
    # 提取图片链接
    image_urls = extract_images_from_markdown(md_content)
    
    # 替换图片为占位符，避免干扰文本布局计算
    md_content_for_layout = replace_images_with_placeholders(md_content)
    
    # 创建图片
    width = config['card_width']
    # 初始高度，后面会根据内容调整
    height = min(2000, len(md_content.split('\n')) * 40 + 300)
    
    background_colors = {
        'light': (248, 249, 250),
        'dark': (33, 37, 41),
        'blue': (240, 247, 255),
        'green': (240, 252, 245),
        'pink': (255, 240, 246)
    }
    
    bg_color = background_colors.get(config['theme'], (248, 249, 250))
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # 获取字体
    title_font = get_font(uploaded_font, size=config['font_size'] + 4)
    content_font = get_font(uploaded_font, size=config['font_size'])
    watermark_font = get_font(uploaded_font, size=config['watermark_size'])
    
    # 初始化位置
    y_offset = 40
    
    # 绘制Mac窗口头部
    if config['show_mac_header']:
        header_height = create_mac_window_header(draw, width, config.get('window_title', 'Markdown Card'))
        y_offset = header_height + 40
    
    # 绘制标题区域
    title = f"{config['author']} 的卡片"
    title_bbox = title_font.getbbox(title)
    title_x = (width - (title_bbox[2] - title_bbox[0])) // 2
    draw.text((title_x, y_offset), title, fill=(0, 0, 0), font=title_font)
    y_offset += title_bbox[3] - title_bbox[1] + 30
    
    # 绘制日期
    if config['show_date']:
        date_text = config['date']
        date_bbox = content_font.getbbox(date_text)
        date_x = width - date_bbox[2] + date_bbox[0] - 40
        date_y = 60 if config['show_mac_header'] else 40
        draw.text((date_x, date_y), date_text, fill=(100, 100, 100), font=content_font)
    
    # 绘制分隔线
    draw.line([(40, y_offset - 10), (width - 40, y_offset - 10)], fill=(200, 200, 200), width=1)
    y_offset += 30
    
    # 解析并绘制Markdown内容
    content_x = 40
    max_line_width = width - 80
    
    # 按行处理
    lines = md_content.split('\n')
    current_font = content_font
    image_index = 0
    
    for i, line in enumerate(lines):
        if line.strip() == '':
            y_offset += 20
            continue
        
        # 检查是否是图片
        image_match = re.match(r'!\[(.*?)\]\((.*?)\)', line)
        if image_match:
            alt_text, image_url = image_match.groups()
            
            # 下载并插入图片
            if image_url.startswith('http'):
                with st.spinner(f"正在下载图片 {image_index + 1}/{len(image_urls)}..."):
                    image_data = download_image(image_url)
                    
                if image_data:
                    # 计算图片位置（居中）
                    img_width, img_height = image_data.size
                    img_x = (width - img_width) // 2
                    
                    # 确保图片不会超出当前图像边界
                    if y_offset + img_height + 20 < height:
                        img.paste(image_data, (img_x, y_offset))
                        
                        # 添加图片说明
                        if alt_text and alt_text != "图片":
                            caption_font = get_font(uploaded_font, size=config['font_size'] - 2)
                            caption_bbox = caption_font.getbbox(alt_text)
                            caption_x = (width - (caption_bbox[2] - caption_bbox[0])) // 2
                            draw.text((caption_x, y_offset + img_height + 5), 
                                     alt_text, fill=(150, 150, 150), font=caption_font)
                            y_offset += img_height + 30
                        else:
                            y_offset += img_height + 20
                    else:
                        # 图片太高，需要扩展图像
                        new_height = y_offset + img_height + 100
                        new_img = Image.new('RGB', (width, new_height), color=bg_color)
                        new_img.paste(img, (0, 0))
                        img = new_img
                        draw = ImageDraw.Draw(img)
                        img.paste(image_data, (img_x, y_offset))
                        y_offset += img_height + 20
                    
                    image_index += 1
                else:
                    # 图片下载失败，显示占位符
                    placeholder_width = min(200, max_line_width)
                    placeholder_height = 150
                    draw.rectangle([(content_x, y_offset), 
                                   (content_x + placeholder_width, y_offset + placeholder_height)], 
                                  fill=(230, 230, 230), outline=(200, 200, 200))
                    draw.text((content_x + 10, y_offset + 10), 
                             "图片加载失败", fill=(150, 150, 150), font=content_font)
                    y_offset += placeholder_height + 20
            continue
        
        # 处理标题
        current_font = content_font
        if line.startswith('# '):
            current_font = get_font(uploaded_font, size=config['font_size'] + 8)
            line = line[2:]
            y_offset += 10  # 标题前额外间距
        elif line.startswith('## '):
            current_font = get_font(uploaded_font, size=config['font_size'] + 4)
            line = line[3:]
            y_offset += 5  # 二级标题前额外间距
        elif line.startswith('### '):
            current_font = get_font(uploaded_font, size=config['font_size'] + 2)
            line = line[4:]
        
        # 处理列表项
        is_list_item = False
        if line.strip().startswith('- ') or line.strip().startswith('* '):
            is_list_item = True
            list_marker = "• "
            line = line.strip()[2:]
        
        # 文本换行
        wrapped_lines = wrap_text_chinese(line, current_font, max_line_width)
        
        for j, wrapped_line in enumerate(wrapped_lines):
            # 添加列表标记
            if is_list_item and j == 0:
                wrapped_line = list_marker + wrapped_line
            
            # 检查是否有足够空间
            line_bbox = current_font.getbbox(wrapped_line)
            line_height = line_bbox[3] - line_bbox[1]
            
            if y_offset + line_height + 10 >= height:
                # 扩展图像高度
                new_height = height + 200
                new_img = Image.new('RGB', (width, new_height), color=bg_color)
                new_img.paste(img, (0, 0))
                img = new_img
                draw = ImageDraw.Draw(img)
                height = new_height
            
            draw.text((content_x, y_offset), wrapped_line, fill=(0, 0, 0), font=current_font)
            y_offset += line_height + 5
        
        y_offset += 10
    
    # 裁剪图片到合适高度
    final_height = min(y_offset + 50, height)
    img = img.crop((0, 0, width, final_height))
    
    # 添加水印
    if config['watermark_text']:
        img = add_watermark(img, config['watermark_text'], config['watermark_color'], 
                           config['watermark_size'], config['watermark_density'], uploaded_font)
    
    return img

def add_watermark(image, text, color, size, density, uploaded_font=None):
    """添加水印到图片"""
    # 创建水印图片
    watermark = Image.new('RGBA', image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(watermark)
    
    font = get_font(uploaded_font, size=size)
    
    # 计算水印位置
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # 根据密度设置水印间距
    spacing = int(200 / density)
    
    # 在图片上重复添加水印
    for x in range(0, image.width, text_width + spacing):
        for y in range(0, image.height, text_height + spacing):
            # 设置透明度
            r, g, b = [int(color[i:i+2], 16) for i in (1, 3, 5)]
            draw.text((x, y), text, fill=(r, g, b, 80), font=font)
    
    # 合并原图和水印
    watermarked = Image.alpha_composite(image.convert('RGBA'), watermark)
    
    return watermarked.convert('RGB')

def get_image_download_link(img, filename):
    """生成图片下载链接"""
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    href = f'<a href="data:image/png;base64,{img_str}" download="{filename}">点击下载图片</a>'
    return href

# 主应用
st.title("📝 Markdown转图片卡片生成器")

# 侧边栏配置
with st.sidebar:
    st.header("⚙️ 配置")
    
    # 上传字体文件（用于中文显示）
    st.subheader("字体设置（解决中文显示问题）")
    uploaded_font = st.file_uploader("上传中文字体文件 (TTF/OTF)", type=['ttf', 'otf', 'ttc'])
    
    if uploaded_font:
        # 保存上传的字体到临时文件
        font_bytes = uploaded_font.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ttf') as tmp_font:
            tmp_font.write(font_bytes)
            font_path = tmp_font.name
        st.success("字体文件已上传！")
    else:
        font_path = None
        st.info("未上传字体文件，将尝试使用系统字体")
    
    st.divider()
    
    # 上传Markdown文件
    uploaded_file = st.file_uploader("上传Markdown文件", type=['md', 'txt', 'markdown'])
    
    # 卡片主题选择
    theme = st.selectbox(
        "卡片主题",
        ["light", "dark", "blue", "green", "pink"],
        index=0
    )
    
    # 作者昵称
    author = st.text_input("作者昵称", value="作者")
    
    # 日期显示
    show_date = st.checkbox("显示日期", value=True)
    date = st.date_input("选择日期", value=datetime.now().date())
    
    # 卡片宽度
    card_width = st.slider("卡片宽度 (px)", 400, 1200, 800, 50)
    
    # 字体大小
    font_size = st.slider("字体大小", 12, 24, 16)
    
    # Mac窗口头部
    show_mac_header = st.checkbox("显示Mac窗口头部", value=True)
    if show_mac_header:
        window_title = st.text_input("窗口标题", value="Markdown Card")
    
    # 水印设置
    st.divider()
    st.subheader("水印设置")
    
    watermark_text = st.text_input("水印文字", value="")
    watermark_color = st.color_picker("水印颜色", "#808080")
    watermark_size = st.slider("水印大小", 20, 60, 30)
    watermark_density = st.slider("水印密度", 1, 10, 5)
    
    # 导出按钮
    st.divider()
    export_button = st.button("🖼️ 导出图片", type="primary", use_container_width=True)

# 主内容区域
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📋 Markdown内容")
    
    # 默认Markdown内容（包含中文和图片示例）
    default_md = """# 欢迎使用Markdown卡片生成器

这是一个将Markdown转换为美观图片卡片的工具，支持**中文显示**和**图片插入**！

## 功能特性
- ✅ 支持多种主题
- ✅ 自定义卡片宽度和字体
- ✅ 添加水印保护
- ✅ 导出高质量图片
- ✅ 完美支持中文显示
- ✅ 支持网络图片插入

## 使用方法
1. 上传或编辑Markdown内容
2. 在左侧调整配置
3. 预览效果并导出

## 图片示例

![风景图片](https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=600)

> 提示：导出的图片可用于社交媒体分享、博客配图等场景。

## 测试中文显示
这是一段中文测试文本，用于验证中文显示是否正常。如果上传了中文字体文件，中文将会完美显示。

**加粗的中文** 和 *斜体的中文* 也可以正常显示。

- 列表项1：中文测试
- 列表项2：继续测试
- 列表项3：完成测试

---
感谢使用本工具！😊"""
    
    if uploaded_file is not None:
        try:
            md_content = uploaded_file.read().decode("utf-8")
        except UnicodeDecodeError:
            # 尝试其他编码
            uploaded_file.seek(0)
            md_content = uploaded_file.read().decode("gbk", errors='ignore')
    else:
        md_content = st.text_area("编辑Markdown内容", default_md, height=400)

with col2:
    st.header("👁️ 预览")
    
    # 配置参数
    config = {
        'theme': theme,
        'author': author,
        'show_date': show_date,
        'date': date.strftime("%Y年%m月%d日"),
        'card_width': card_width,
        'font_size': font_size,
        'show_mac_header': show_mac_header,
        'window_title': window_title if show_mac_header else 'Markdown Card',
        'watermark_text': watermark_text,
        'watermark_color': watermark_color,
        'watermark_size': watermark_size,
        'watermark_density': watermark_density
    }
    
    # 创建预览
    if st.button("🔄 更新预览", key="preview", use_container_width=True):
        with st.spinner("正在生成预览..."):
            preview_image = create_card_image(md_content, config, font_path)
            st.session_state.card_image = preview_image
    
    # 显示预览或默认图片
    if st.session_state.card_image:
        st.image(st.session_state.card_image, use_column_width=True, 
                caption="卡片预览", output_format="PNG")
    else:
        # 显示初始预览
        with st.spinner("生成初始预览..."):
            preview_image = create_card_image(md_content, config, font_path)
            st.session_state.card_image = preview_image
            st.image(preview_image, use_column_width=True, 
                    caption="卡片预览", output_format="PNG")

# 导出功能
if export_button:
    with st.spinner("正在生成高清图片..."):
        export_image = create_card_image(md_content, config, font_path)
        
        # 保存到临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            export_image.save(tmp_file, format='PNG', quality=95)
            tmp_file_path = tmp_file.name
        
        # 提供下载
        with open(tmp_file_path, "rb") as file:
            btn = st.download_button(
                label="📥 下载图片",
                data=file,
                file_name=f"markdown_card_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                mime="image/png",
                use_container_width=True
            )
        
        # 清理临时文件
        try:
            os.unlink(tmp_file_path)
            if font_path:
                os.unlink(font_path)
        except:
            pass

# 使用说明
with st.expander("📖 使用说明"):
    st.markdown("""
    ### 使用方法：
    1. **上传字体文件**（可选但推荐）：在侧边栏上传中文字体文件（如`.ttf`或`.otf`格式），解决中文显示为方框的问题
    2. **上传或编辑Markdown**：在左侧上传`.md`文件，或在文本框中直接编辑
    3. **自定义样式**：通过侧边栏调整卡片主题、尺寸、字体等参数
    4. **添加水印**：设置水印文字、颜色、大小和密度
    5. **预览和导出**：右侧实时预览，点击"导出图片"生成高清图片

    ### 支持的Markdown格式：
    - 标题 (#, ##, ###)
    - 列表 (-, *)
    - 引用块 (>)
    - 粗体 (**text**)、斜体 (*text*)
    - 图片：`![alt](图片URL)` - 支持网络图片
    - 分隔线 (---)

    ### 图片支持：
    - 支持网络图片URL
    - 图片会自动调整大小以适应卡片宽度
    - 支持图片说明文字
    - 注意：目前不支持本地图片文件，请使用网络图片链接

    ### 常见问题：
    1. **中文显示为方框？**
       - 上传中文字体文件（如微软雅黑、思源黑体等）
       - 或者使用支持中文的系统字体
    
    2. **图片不显示？**
       - 确保图片URL是正确的网络地址
       - 检查网络连接是否正常
       - 有些网站可能禁止图片外链

    3. **卡片高度不够？**
       - 应用会自动调整高度以适应内容
       - 如果内容过多，可能需要更宽的卡片
    """)

# 页脚
st.divider()
st.caption("✨ Markdown转图片卡片生成器 | 将Markdown转换为美观的分享图片")