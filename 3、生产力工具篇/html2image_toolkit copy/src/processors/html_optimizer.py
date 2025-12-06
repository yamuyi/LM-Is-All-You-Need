from bs4 import BeautifulSoup
from pathlib import Path
from src.utils.log_utils import logger

def optimize_html_for_screenshot(html_file: str | Path) -> Path:
    """
    优化HTML文件用于截图，减少边距，优化布局
    """
    html_file = Path(html_file)
    if not html_file.exists():
        logger.error(f"HTML文件不存在: {html_file}")
        return html_file
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # 优化body样式
        body = soup.find('body')
        if body:
            # 移除或减少内边距
            if body.get('style'):
                # 移除原有的padding和margin
                style = body['style']
                style = style.replace('padding: 20px', 'padding: 10px')
                style = style.replace('margin: 0 auto', 'margin: 0 auto')
                if 'padding' not in style:
                    body['style'] = style + '; padding: 10px;'
            else:
                body['style'] = 'padding: 10px; margin: 0 auto;'
        
        # 确保所有图片居中显示
        for img in soup.find_all('img'):
            if not img.get('style'):
                img['style'] = 'display: block; margin: 10px auto; max-width: 95%;'
            else:
                style = img['style']
                if 'margin' not in style:
                    img['style'] = style + '; margin: 10px auto;'
                if 'display' not in style:
                    img['style'] = style + '; display: block;'
        
        # 确保所有表格居中显示
        for table in soup.find_all('table'):
            if not table.get('style'):
                table['style'] = 'margin: 10px auto;'
            else:
                style = table['style']
                if 'margin' not in style:
                    table['style'] = style + '; margin: 10px auto;'
        
        # 优化标题边距
        for i in range(1, 7):
            for header in soup.find_all(f'h{i}'):
                if not header.get('style'):
                    header['style'] = 'margin: 15px 0 8px 0;'
        
        # 保存优化后的HTML
        optimized_file = html_file.parent / f"{html_file.stem}_optimized.html"
        with open(optimized_file, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        logger.info(f"HTML优化完成: {optimized_file}")
        return optimized_file
    
    except Exception as e:
        logger.error(f"HTML优化失败: {str(e)}")
        return html_file