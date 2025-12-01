import email
from email import policy
from bs4 import BeautifulSoup
import chardet
import re

def convert_mhtml_with_chinese(mhtml_file, html_file):
    """
    处理中文编码的MHTML转换
    """
    try:
        # 先用二进制方式读取以检测编码
        with open(mhtml_file, 'rb') as f:
            raw_data = f.read()
        
        # 检测编码
        encoding_detected = chardet.detect(raw_data)
        file_encoding = encoding_detected['encoding'] or 'utf-8'
        print(f"检测到的编码: {file_encoding}, 置信度: {encoding_detected['confidence']}")
        
        # 用检测到的编码读取文件
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
            
            # 保存为UTF-8
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            print(f"转换成功: {mhtml_file} -> {html_file}")
        else:
            print("未找到HTML内容")
            
    except Exception as e:
        print(f"转换失败: {e}")

# 使用示例
convert_mhtml_with_chinese('example.mhtml', 'output.html')