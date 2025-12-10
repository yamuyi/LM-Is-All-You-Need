import requests
import json
from pathlib import Path
from typing import Optional, Tuple
from src.utils.log_utils import logger
from src.config import OLLAMA_CONFIG, MD_CLEAN_CONFIG

class MarkdownCleaner:
    """使用本地Ollama模型清理Markdown内容的头部和尾部"""
    
    def __init__(self):
        self.base_url = OLLAMA_CONFIG['base_url']
        self.model = OLLAMA_CONFIG['model']
        self.timeout = OLLAMA_CONFIG['timeout']
        self.max_chunk_size = 1500  # 留出空间给prompt
    
    def clean_markdown(self, md_content: str, file_path: Optional[Path] = None) -> Optional[str]:
        """
        只清理Markdown内容的头部和尾部，保持中间内容不变
        
        Args:
            md_content: Markdown内容
            file_path: 文件路径（用于日志）
            
        Returns:
            清理后的Markdown内容
        """
        try:
            # 分割内容为头部、主体和尾部
            header, body, footer = self._split_content(md_content)
            
            logger.info(f"内容分割完成 - 头部: {len(header)}字符, 主体: {len(body)}字符, 尾部: {len(footer)}字符")
            
            # 只清理头部和尾部
            cleaned_header = self._clean_content_part(header, "头部", file_path) if header else ""
            cleaned_footer = self._clean_content_part(footer, "尾部", file_path) if footer else ""
            
            # 重新组合内容
            cleaned_content_parts = []
            if cleaned_header:
                cleaned_content_parts.append(cleaned_header)
            if body:
                cleaned_content_parts.append(body)
            if cleaned_footer:
                cleaned_content_parts.append(cleaned_footer)
            
            final_content = "\n\n".join(cleaned_content_parts)
            
            # 检查是否有变化
            if final_content != md_content:
                logger.info(f"Markdown头尾清理完成: {file_path or '未知文件'}")
            else:
                logger.info(f"Markdown内容无变化: {file_path or '未知文件'}")
                
            return final_content
                
        except Exception as e:
            logger.error(f"Markdown清理过程中出错: {str(e)}", exc_info=True)
            return md_content
    
    def _split_content(self, content: str) -> Tuple[str, str, str]:
        """
        将内容分割为头部、主体和尾部
        
        Args:
            content: 原始内容
            
        Returns:
            (header, body, footer) 三元组
        """
        lines = content.split('\n')
        total_lines = len(lines)
        
        # 计算分割点（头部取前20%，尾部取后15%，可根据需要调整）
        header_end = max(10, int(total_lines * 0.2))  # 至少10行或20%
        footer_start = min(total_lines - 10, total_lines - int(total_lines * 0.15))  # 至少10行或15%
        
        # 确保footer_start在header_end之后
        footer_start = max(footer_start, header_end + 1)
        
        header_lines = lines[:header_end]
        body_lines = lines[header_end:footer_start]
        footer_lines = lines[footer_start:]
        
        header = '\n'.join(header_lines)
        body = '\n'.join(body_lines)
        footer = '\n'.join(footer_lines)
        
        return header, body, footer
    
    def _clean_content_part(self, content: str, part_name: str, file_path: Optional[Path] = None) -> str:
        """
        清理内容的特定部分（头部或尾部）
        
        Args:
            content: 要清理的内容
            part_name: 部分名称（用于日志）
            file_path: 文件路径
            
        Returns:
            清理后的内容
        """
        if not content or len(content.strip()) == 0:
            return content
            
        # 如果内容很短，直接返回（避免对很短的内容调用API）
        if len(content) < 100:
            logger.info(f"{part_name}内容过短，跳过清理: {file_path or '未知文件'}")
            return content
            
        prompt = self._build_clean_prompt(content, part_name)
        response = self._call_ollama(prompt)
        
        if response:
            cleaned_content = self._extract_cleaned_content(response)
            if cleaned_content and cleaned_content.strip() != content.strip():
                logger.info(f"{part_name}清理完成: {file_path or '未知文件'}")
                return cleaned_content
            else:
                logger.info(f"{part_name}无变化: {file_path or '未知文件'}")
        
        return content
    
    def _build_clean_prompt(self, content: str, part_name: str) -> str:
        """构建清理提示"""
        patterns = "、".join(MD_CLEAN_CONFIG['remove_patterns'])
        
        prompt = f"""请清理以下Markdown文档的{part_name}部分，要求：
        1. 移除所有无关内容，包括但不限于：{patterns}
        2. 保留核心的技术介绍、目录结构等实质性内容
        3. 移除作者个人介绍、平台推广、版权声明、联系方式等非核心信息
        4. 保持文档结构和格式的完整性
        5. 如果内容本身就是技术性的，没有无关内容，请原样返回

        请直接返回清理后的{part_name}内容，不要添加任何解释或说明。

        需要清理的{part_name}内容：
        {content}

        清理后的{part_name}内容："""
        
        return prompt
    
    def _call_ollama(self, prompt: str) -> Optional[str]:
        """调用Ollama API"""
        try:
            # 检查prompt长度，如果超长则截断
            if len(prompt) > 2048:
                logger.warning(f"Prompt长度{len(prompt)}超过限制，进行截断")
                # 计算保留的内容长度（留出空间给prompt模板）
                available_space = 1800 - len(prompt) + len(prompt.split('需要清理的')[1].split('清理后的')[0])
                content_to_keep = min(len(prompt.split('需要清理的')[1].split('清理后的')[0]), available_space)
                
                # 重建prompt，只保留部分内容
                prompt_parts = prompt.split('需要清理的')
                if len(prompt_parts) > 1:
                    content_part = prompt_parts[1].split('清理后的')[0]
                    # 只保留内容的开头部分
                    kept_content = content_part[:content_to_keep] + "\n\n[...内容截断...]"
                    prompt = prompt_parts[0] + "需要清理的" + kept_content + "清理后的" + prompt_parts[1].split('清理后的')[1]
            
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": OLLAMA_CONFIG['temperature'],
                    "num_predict": OLLAMA_CONFIG['max_tokens']
                }
            }
            
            response = requests.post(
                url, 
                json=payload, 
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"处理前：\n{prompt}\n处理后：\n{result}")
            return result.get('response', '').strip()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API请求失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Ollama API调用异常: {str(e)}")
            return None
    
    def _extract_cleaned_content(self, response: str) -> Optional[str]:
        """从Ollama响应中提取清理后的内容"""
        try:
            if response.startswith('{'):
                data = json.loads(response)
                return data.get('content', response)
            return response
        except:
            return response

# 单例实例
md_cleaner = MarkdownCleaner()

def clean_markdown_content(md_content: str, file_path: Optional[Path] = None) -> str:
    """清理Markdown内容的便捷函数"""
    return md_cleaner.clean_markdown(md_content, file_path)