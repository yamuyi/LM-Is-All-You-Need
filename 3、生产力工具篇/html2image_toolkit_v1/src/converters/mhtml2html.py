import email
from email import policy
from bs4 import BeautifulSoup
import chardet
from pathlib import Path
from src.utils.log_utils import logger
from src.utils.file_utils import get_output_path

def convert_mhtml_to_html(
    mhtml_file: str | Path,
    output_html_file: str | Path | None = None
) -> Path | None:
    """
    处理中文编码的MHTML转换为HTML
    :param mhtml_file: MHTML文件路径
    :param output_html_file: 输出HTML路径（None时自动生成）
    :return: 输出HTML路径
    """
    mhtml_file = Path(mhtml_file)
    import pdb
    # pdb.set_trace()
    if not mhtml_file.exists():
        logger.error(f"MHTML文件不存在: {mhtml_file}")
        return None
    
    # 自动生成输出路径
    if output_html_file is None:
        from src.config import HTML_OUTPUT_DIR
        output_html_file = get_output_path(mhtml_file, HTML_OUTPUT_DIR, ".html")
    else:
        output_html_file = Path(output_html_file)
    # pdb.set_trace()
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
                print(f"HTML内容编码: {html_encoding}")
                
                html_content = payload.decode(html_encoding, errors='replace')
                break
        
        if html_content:
            # 使用BeautifulSoup处理，确保指定编码
            soup = BeautifulSoup(html_content, 'html.parser', from_encoding='utf-8')
            
            # 确保HTML有正确的meta charset
            if soup.find('meta', {'charset': True}) is None:
                meta_charset = soup.new_tag('meta', charset='utf-8')
                soup.head.insert(0, meta_charset) if soup.head else soup.html.insert(0, meta_charset)
            
        
            # 保存HTML
            with open(output_html_file, 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
        
            logger.success(f"MHTML转HTML成功: {mhtml_file} -> {output_html_file}")
            return output_html_file
        else:
            print("未找到HTML内容")
    
    except Exception as e:
        logger.error(f"MHTML转HTML失败: {str(e)}", exc_info=True)
        return None

