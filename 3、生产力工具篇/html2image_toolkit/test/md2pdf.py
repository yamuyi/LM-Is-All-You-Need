# md2img_simple.py
import markdown
from PIL import Image, ImageDraw, ImageFont
import textwrap
import os

def markdown_to_image_simple(md_file, output_path, watermark="内部使用"):
    """
    简化的Markdown转图片（直接渲染，不经过PDF）
    """
    
    # 1. 读取文件，自动检测编码
    encodings = ['utf-8', 'gbk', 'utf-8-sig', 'latin-1']
    md_text = ""
    
    for encoding in encodings:
        try:
            with open(md_file, 'r', encoding=encoding) as f:
                md_text = f.read()
                break
        except UnicodeDecodeError:
            continue
    
    if not md_text:
        print("无法读取文件，请检查文件编码")
        return
    
    # 2. 创建图片
    img_width = 1000
    line_height = 40
    margin = 50
    
    # 计算图片高度（根据行数）
    lines = md_text.split('\n')
    img_height = margin * 2 + len(lines) * line_height
    
    # 创建白色背景图片
    img = Image.new('RGB', (img_width, img_height), color='white')
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # 3. 设置字体
    try:
        font = ImageFont.truetype("simhei.ttf", 24)  # 黑体
    except:
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
    
    # 4. 绘制文本
    y = margin
    for line in lines:
        if line.strip():  # 非空行
            # 文本换行
            wrapped = textwrap.wrap(line, width=80)
            for wrapped_line in wrapped:
                draw.text((margin, y), wrapped_line, fill=(0, 0, 0), font=font)
                y += line_height
        else:
            y += line_height  # 空行
    
    # 5. 添加水印
    try:
        watermark_font = ImageFont.truetype("simhei.ttf", 60)
    except:
        watermark_font = font
    
    # 平铺水印
    for i in range(-img_height, img_width + img_height, 300):
        for j in range(-img_width, img_height + img_width, 200):
            draw.text((i, j), watermark, 
                     fill=(220, 220, 220, 100),
                     font=watermark_font)
    
    # 6. 保存
    img.save(output_path, 'PNG', quality=95)
    print(f"✅ 成功生成: {output_path}")

# 使用
markdown_to_image_simple("input.md", "output.png", "机密 - 请勿外传")