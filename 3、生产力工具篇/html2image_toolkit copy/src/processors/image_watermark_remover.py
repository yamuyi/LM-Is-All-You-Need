import cv2
import numpy as np
from pathlib import Path
from src.utils.log_utils import logger

class ImageWatermarkRemover:
    """图片水印去除器"""
    
    def remove_watermark_from_image(self, image_path: Path) -> bool:
        """
        从单张图片中去除水印
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            是否成功去除水印
        """
        try:
            # 读取图片
            img = cv2.imread(str(image_path))
            if img is None:
                logger.error(f"无法读取图片: {image_path}")
                return False
            
            # 转换为灰度图
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 使用图像修复技术去除水印
            # 这里使用简单的阈值和修复方法，可以根据实际水印特点调整
            _, mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
            
            # 膨胀操作增强掩码
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.dilate(mask, kernel, iterations=1)
            
            # 使用图像修复
            result = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)
            
            # 保存结果
            cv2.imwrite(str(image_path), result)
            logger.info(f"水印去除完成: {image_path}")
            return True
            
        except Exception as e:
            logger.error(f"图片水印去除失败 {image_path}: {str(e)}")
            return False
    
    def remove_watermarks_from_md_images(self, md_file: Path, images_dir: Path) -> bool:
        """
        从Markdown文件相关的图片中去除水印
        
        Args:
            md_file: Markdown文件路径
            images_dir: 图片目录路径
            
        Returns:
            是否成功处理所有图片
        """
        try:
            # 读取Markdown文件内容
            content = md_file.read_text(encoding='utf-8')
            
            # 查找所有图片引用
            import re
            image_pattern = r'!\[.*?\]\((.*?)\)'
            image_matches = re.findall(image_pattern, content)
            
            success_count = 0
            total_count = len(image_matches)
            
            for image_ref in image_matches:
                image_path = images_dir / Path(image_ref).name
                if image_path.exists():
                    if self.remove_watermark_from_image(image_path):
                        success_count += 1
            
            logger.info(f"图片水印去除完成: {success_count}/{total_count} 张图片")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Markdown图片水印去除失败 {md_file}: {str(e)}")
            return False

# 单例实例
watermark_remover = ImageWatermarkRemover()