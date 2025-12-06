import email
from email import policy
from bs4 import BeautifulSoup
import chardet
from pathlib import Path
from src.utils.log_utils import logger

def convert_mhtml_to_html(
    mhtml_file: str | Path,
    output_dir: Path,
    task_name: str = None
) -> dict | None:
    """
    处理中文编码的MHTML转换为HTML，保存到任务目录
    
    Args:
        mhtml_file: MHTML文件路径
        output_dir: 输出目录（任务目录）
        task_name: 任务名称
    
    Returns:
        dict: 处理结果信息
    """
    mhtml_file = Path(mhtml_file)
    if not mhtml_file.exists():
        logger.error(f"MHTML文件不存在: {mhtml_file}")
        return None
    
    # 创建任务子目录
    task_dirs = {
        'html': output_dir / "html",
        'temp': output_dir / ".temp"
    }
    
    for dir_path in task_dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # 输出HTML路径
    output_html_file = task_dirs['html'] / f"{mhtml_file.stem}.html"
    
    try:
        # 二进制读取检测编码
        with open(mhtml_file, 'rb') as f:
            raw_data = f.read()
        
        # 检测文件编码
        encoding_detected = chardet.detect(raw_data)
        file_encoding = encoding_detected['encoding'] or 'utf-8'
        logger.info(f"检测到MHTML文件编码: {file_encoding} (置信度: {encoding_detected['confidence']:.2f})")
        
        # 解码文件内容
        mhtml_content = raw_data.decode(file_encoding, errors='replace')
        
        # 解析MHTML
        msg = email.message_from_string(mhtml_content, policy=policy.default)
        
        html_content = None
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == 'text/html':
                # 获取HTML内容并处理编码
                payload = part.get_payload(decode=True)
                
                # 检测HTML内容的编码
                html_encoding_detected = chardet.detect(payload)
                html_encoding = html_encoding_detected['encoding'] or 'utf-8'
                logger.info(f"HTML内容编码: {html_encoding}")
                
                html_content = payload.decode(html_encoding, errors='replace')
                break
        
        if html_content:
            # 使用BeautifulSoup处理
            soup = BeautifulSoup(html_content, 'html.parser', from_encoding='utf-8')
            
            # 确保HTML有正确的meta charset
            if soup.find('meta', {'charset': True}) is None:
                meta_charset = soup.new_tag('meta', charset='utf-8')
                if soup.head:
                    soup.head.insert(0, meta_charset)
                else:
                    soup.html.insert(0, meta_charset)
            
            # 保存HTML
            with open(output_html_file, 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
        
            logger.success(f"MHTML转HTML成功: {mhtml_file} -> {output_html_file}")
            
            return {
                'input_file': str(mhtml_file),
                'output_html': str(output_html_file),
                'html_dir': str(task_dirs['html']),
                'task_dir': str(output_dir)
            }
        else:
            logger.error("未找到HTML内容")
            return None
    
    except Exception as e:
        logger.error(f"MHTML转HTML失败: {str(e)}", exc_info=True)
        return None