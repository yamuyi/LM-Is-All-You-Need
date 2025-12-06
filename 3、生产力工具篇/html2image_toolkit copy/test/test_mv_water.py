import cv2
import numpy as np
import os
from pathlib import Path

def remove_watermark_image(image, region_ratio=0.2):
    """
    移除图片右下角的水印
    
    参数:
        image: 输入的OpenCV图像对象
        region_ratio: 右下角区域的比例，默认为0.3（即右下角30%×30%的区域）
    
    返回:
        处理后的图像
    """
    if image is None:
        raise ValueError("输入的图像为空")
    
    height, width = image.shape[:2]
    
    # 计算右下角区域的坐标
    region_height = int(height * region_ratio)
    region_width = int(width * region_ratio*2)
    
    # 右下角区域的坐标范围
    y_start = height - region_height
    x_start = width - region_width
    
    # 提取右下角区域
    roi = image[y_start:height, x_start:width]
    
    # 对右下角区域进行处理
    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # 使用阈值操作找到水印区域（可根据实际水印调整阈值）
    _, thresholded = cv2.threshold(gray_roi, 128, 255, cv2.THRESH_BINARY_INV)
    
    # 使用膨胀操作去除小孔洞
    kernel = np.ones((3, 3), np.uint8)
    dilated = cv2.dilate(thresholded, kernel, iterations=1)
    
    # 创建全白背景（与ROI尺寸相同）
    white_background = np.ones_like(roi) * 255
    
    # 处理ROI区域：水印区域保留原图，非水印区域填充白色
    result_roi = cv2.bitwise_and(roi, roi, mask=dilated)  # 水印区域保留原图
    result_roi += cv2.bitwise_and(white_background, white_background, mask=~dilated)  # 非水印区域填充白色
    
    # 将处理后的ROI放回原图
    result = image.copy()
    result[y_start:height, x_start:width] = result_roi
    
    return result



def batch_remove_watermark(input_folder, output_folder, region_ratio=0.3, 
                           extensions=('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
    """
    批量移除图片水印
    
    参数:
        input_folder: 输入图片文件夹路径
        output_folder: 输出图片文件夹路径
        region_ratio: 右下角区域的比例
        extensions: 支持的图片扩展名
    """
    # 创建输出文件夹
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 获取输入文件夹中的所有图片文件
    input_path = Path(input_folder)
    image_files = []
    
    for ext in extensions:
        image_files.extend(input_path.glob(f'*{ext}'))
        image_files.extend(input_path.glob(f'*{ext.upper()}'))
    
    print(f"找到 {len(image_files)} 张图片")
    
    processed_count = 0
    error_files = []
    
    for img_file in image_files:
        try:
            print(f"处理中: {img_file.name}")
            
            # 读取图片
            image = cv2.imread(str(img_file))
            if image is None:
                raise ValueError(f"无法读取图片：{img_file.name}")
            
            # 处理图片
            result = remove_watermark_image(image, region_ratio)
            
            # 构建输出路径
            output_file = output_path / img_file.name
            
            # 保存处理后的图片
            cv2.imwrite(str(output_file), result)
            
            print(f"  已保存: {output_file.name}")
            processed_count += 1
            
        except Exception as e:
            print(f"  处理失败 {img_file.name}: {str(e)}")
            error_files.append(img_file.name)
    
    # 输出处理总结
    print("\n" + "="*50)
    print("处理完成！")
    print(f"成功处理: {processed_count} 张图片")
    print(f"处理失败: {len(error_files)} 张图片")
    
    if error_files:
        print("失败的图片：")
        for error_file in error_files:
            print(f"  - {error_file}")

def process_single_image(input_path, output_path, region_ratio=0.3):
    """
    处理单张图片的便捷函数
    """
    # 创建输出文件夹
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"处理单张图片: {input_path}")
    
    # 读取图片
    image = cv2.imread(input_path)
    if image is None:
        raise ValueError(f"无法读取图片：{input_path}")
    
    # 处理图片
    result = remove_watermark_image(image, region_ratio)
    
    # 保存图片
    cv2.imwrite(output_path, result)
    print(f"已保存到: {output_path}")

# 使用示例
if __name__ == "__main__":
    # 方法1：批量处理整个文件夹
    print("方法1：批量处理整个文件夹")
    input_folder = "./input"  # 输入文件夹路径
    output_folder = "./output"  # 输出文件夹路径
    
    batch_remove_watermark(
        input_folder=input_folder,
        output_folder=output_folder,
        region_ratio=0.17,  # 可以根据需要调整比例
        extensions=('.jpg', '.jpeg', '.png')  # 指定要处理的图片格式
    )