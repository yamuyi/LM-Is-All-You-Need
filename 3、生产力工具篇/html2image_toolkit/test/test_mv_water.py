# # import numpy as np
# # import cv2

# # def remove_watermark(image_path, region_ratio=0.3, gray_threshold_range=(180, 240)):
# #     """
# #     移除右下角灰色水印
    
# #     参数:
# #     - image_path: 图像路径
# #     - region_ratio: 检测区域的宽度/高度比例（默认为右下角30%区域）
# #     - gray_threshold_range: 灰度值范围，用于检测灰色水印像素
# #     """
# #     # 读取图像
# #     image = cv2.imread(image_path)
# #     if image is None:
# #         print(f"无法读取图像: {image_path}")
# #         return None
    
# #     # 显示原始图像
# #     cv2.imshow('Original Image', image)
# #     cv2.waitKey(1)
    
# #     # 转换为灰度图像用于检测灰色像素
# #     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
# #     # 获取图像尺寸
# #     height, width = image.shape[:2]
    
# #     # 计算右下角区域的范围
# #     start_y = int(height * (1 - region_ratio))
# #     start_x = int(width * (1 - region_ratio))
    
# #     # 创建水印区域的掩码
# #     watermark_mask = np.zeros((height, width), dtype=np.uint8)
    
# #     # 在右下角区域检测灰色像素
# #     # 灰色像素的特点是R、G、B三个通道的值比较接近
# #     roi = image[start_y:height, start_x:width]
# #     gray_roi = gray[start_y:height, start_x:width]
    
# #     # 方法1: 使用灰度值范围检测
# #     mask_gray = cv2.inRange(gray_roi, gray_threshold_range[0], gray_threshold_range[1])
    
# #     # 方法2: 检测RGB通道值接近的像素（灰色特征）
# #     # 计算RGB通道之间的最大差值
# #     b, g, r = cv2.split(roi)
# #     diff_rg = cv2.absdiff(r, g)
# #     diff_gb = cv2.absdiff(g, b)
# #     diff_br = cv2.absdiff(b, r)
    
# #     # 合并差异，找到RGB值接近的像素
# #     diff_combined = cv2.add(diff_rg, diff_gb)
# #     diff_combined = cv2.add(diff_combined, diff_br)
    
# #     # 设置阈值，RGB差值小于30的被认为是灰色
# #     mask_gray_feature = cv2.inRange(diff_combined, 0, 30)
    
# #     # 结合两种检测方法
# #     combined_mask = cv2.bitwise_and(mask_gray, mask_gray_feature)
    
# #     # 将掩码应用到完整图像
# #     watermark_mask[start_y:height, start_x:width] = combined_mask
    
# #     # 创建结果图像
# #     result = image.copy()
    
# #     # 方法1: 直接替换为白色
# #     result[watermark_mask == 255] = [255, 255, 255]
    
# #     # 方法2: 使用周围像素进行修复（更自然）
# #     # kernel = np.ones((3, 3), np.uint8)
# #     # dilated_mask = cv2.dilate(watermark_mask, kernel, iterations=1)
# #     # inpainted = cv2.inpaint(result, dilated_mask, 3, cv2.INPAINT_TELEA)
    
# #     # 显示结果
# #     cv2.imshow('Watermark Mask', watermark_mask)
# #     cv2.imshow('Result Image', result)
    
# #     # 等待按键
# #     print("按任意键继续...")
# #     cv2.waitKey(0)
# #     cv2.destroyAllWindows()
    
# #     return result

# # def remove_watermark_with_adaptive_threshold(image_path, region_ratio=0.3):
# #     """
# #     使用自适应阈值移除右下角水印
# #     """
# #     # 读取图像
# #     image = cv2.imread(image_path)
# #     if image is None:
# #         print(f"无法读取图像: {image_path}")
# #         return None
    
# #     # 获取图像尺寸
# #     height, width = image.shape[:2]
    
# #     # 计算右下角区域
# #     start_y = int(height * (1 - region_ratio))
# #     start_x = int(width * (1 - region_ratio))
    
# #     # 提取右下角区域
# #     roi = image[start_y:height, start_x:width]
# #     roi_hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    
# #     # 分离HSV通道
# #     h, s, v = cv2.split(roi_hsv)
    
# #     # 检测低饱和度的像素（灰色特征）
# #     # 灰色像素通常饱和度较低
# #     _, low_sat_mask = cv2.threshold(s, 40, 255, cv2.THRESH_BINARY_INV)
    
# #     # 检测亮度适中的像素
# #     _, brightness_mask = cv2.threshold(v, 150, 255, cv2.THRESH_BINARY)
    
# #     # 结合两个条件
# #     gray_mask = cv2.bitwise_and(low_sat_mask, brightness_mask)
    
# #     # 形态学操作，去除噪声
# #     kernel = np.ones((2, 2), np.uint8)
# #     gray_mask = cv2.morphologyEx(gray_mask, cv2.MORPH_OPEN, kernel)
# #     gray_mask = cv2.morphologyEx(gray_mask, cv2.MORPH_CLOSE, kernel)
    
# #     # 创建完整图像掩码
# #     full_mask = np.zeros((height, width), dtype=np.uint8)
# #     full_mask[start_y:height, start_x:width] = gray_mask
    
# #     # 应用图像修复
# #     result = cv2.inpaint(image, full_mask, 3, cv2.INPAINT_TELEA)
    
# #     # 显示结果
# #     cv2.imshow('Original Image', image)
# #     cv2.imshow('Detected Watermark', full_mask)
# #     cv2.imshow('Inpainted Image', result)
    
# #     cv2.waitKey(0)
# #     cv2.destroyAllWindows()
    
# #     return result

# # # 使用示例
# # if __name__ == "__main__":
# #     # 方法1: 基于灰度值检测
# #     print("使用方法1: 基于灰度值检测")
# #     # result1 = remove_watermark('./input/f291f37d3bc9a960465dfb0a63365cda.jpg', region_ratio=0.3)
# #     result1 = remove_watermark('./input/e313778daa5a29dca473260c1ea46661.jpg', region_ratio=0.3)
    
# #     # 如果需要保存结果
# #     if result1 is not None:
# #         cv2.imwrite('result_without_watermark1.jpg', result1)
# #         print("结果已保存为 'result_without_watermark1.jpg'")
    

# import numpy as np
# import cv2

# def remove_watermark_improved(image_path, region_ratio=0.3, gray_threshold_range=(180, 240), 
#                               use_inpainting=True, blend_edges=True):
#     """
#     改进的水印去除方法，优化边界处理
    
#     参数:
#     - image_path: 图像路径
#     - region_ratio: 检测区域的宽度/高度比例
#     - gray_threshold_range: 灰度值范围
#     - use_inpainting: 是否使用图像修复技术
#     - blend_edges: 是否对边缘进行融合
#     """
#     # 读取图像
#     image = cv2.imread(image_path)
#     if image is None:
#         print(f"无法读取图像: {image_path}")
#         return None
    
#     # 创建原始图像的备份
#     original = image.copy()
    
#     # 转换为灰度图像
#     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
#     # 获取图像尺寸
#     height, width = image.shape[:2]
    
#     # 计算右下角区域的范围
#     start_y = int(height * (1 - region_ratio))
#     start_x = int(width * (1 - region_ratio))
    
#     # 1. 创建更精确的水印检测掩码
#     watermark_mask = np.zeros((height, width), dtype=np.uint8)
    
#     # 提取右下角区域
#     roi = image[start_y:height, start_x:width]
#     gray_roi = gray[start_y:height, start_x:width]
    
#     # 方法A: 使用自适应阈值检测灰色区域
#     gray_thresh = cv2.adaptiveThreshold(gray_roi, 255, 
#                                         cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
#                                         cv2.THRESH_BINARY, 11, 2)
    
#     # 方法B: 检测RGB通道接近的像素（灰色特征）
#     b, g, r = cv2.split(roi)
#     diff_rg = cv2.absdiff(r, g)
#     diff_gb = cv2.absdiff(g, b)
#     diff_br = cv2.absdiff(b, r)
    
#     diff_combined = cv2.add(diff_rg, diff_gb)
#     diff_combined = cv2.add(diff_combined, diff_br)
    
#     # 使用更保守的阈值检测灰色像素
#     _, mask_gray_feature = cv2.threshold(diff_combined, 40, 255, cv2.THRESH_BINARY_INV)
    
#     # 方法C: 结合亮度和对比度信息
#     # 计算局部对比度
#     kernel_size = 5
#     blurred = cv2.GaussianBlur(gray_roi, (kernel_size, kernel_size), 0)
#     local_contrast = cv2.absdiff(gray_roi, blurred)
    
#     # 低对比度且亮度适中的区域可能是水印
#     _, low_contrast_mask = cv2.threshold(local_contrast, 15, 255, cv2.THRESH_BINARY_INV)
#     _, brightness_mask = cv2.threshold(gray_roi, gray_threshold_range[0], gray_threshold_range[1], cv2.THRESH_BINARY)
    
#     # 结合多个条件
#     condition1 = cv2.bitwise_and(mask_gray_feature, low_contrast_mask)
#     condition2 = cv2.bitwise_and(condition1, brightness_mask)
    
#     # 使用形态学操作优化掩码边界
#     kernel = np.ones((3, 3), np.uint8)
#     refined_mask = cv2.morphologyEx(condition2, cv2.MORPH_CLOSE, kernel)
#     refined_mask = cv2.morphologyEx(refined_mask, cv2.MORPH_OPEN, kernel)
    
#     # 2. 边缘检测和羽化处理
#     if blend_edges:
#         # 创建边缘羽化效果
#         edges = cv2.Canny(refined_mask, 50, 150)
        
#         # 对边缘进行膨胀
#         kernel_edge = np.ones((2, 2), np.uint8)
#         edges_dilated = cv2.dilate(edges, kernel_edge, iterations=1)
        
#         # 创建羽化掩码
#         feather_mask = np.zeros_like(refined_mask, dtype=np.float32)
#         feather_mask[refined_mask == 255] = 1.0
        
#         # 边缘区域设置渐变透明度
#         edges_indices = edges_dilated == 255
#         if np.any(edges_indices):
#             # 计算到最近的非边缘像素的距离
#             from scipy import ndimage
#             distance = ndimage.distance_transform_edt(~edges_indices)
            
#             # 创建渐变（距离越大，透明度越低）
#             max_dist = np.max(distance)
#             if max_dist > 0:
#                 feather_edges = 1.0 - (distance / max_dist * 0.3)  # 边缘渐变30%
#                 feather_mask[edges_indices] = feather_edges[edges_indices]
    
#     # 将处理后的掩码放回完整图像
#     watermark_mask[start_y:height, start_x:width] = refined_mask
    
#     # 3. 根据选项选择修复方法
#     result = original.copy()
    
#     if use_inpainting:
#         # 方法1: 使用OpenCV的图像修复（telea算法）
#         # 稍微扩大掩码以包括更多边界区域
#         kernel_inpaint = np.ones((2, 2), np.uint8)
#         inpaint_mask = cv2.dilate(watermark_mask, kernel_inpaint, iterations=1)
        
#         # 应用图像修复
#         inpainted = cv2.inpaint(original, inpaint_mask, 3, cv2.INPAINT_TELEA)
#         result = inpainted
        
#     else:
#         # 方法2: 使用局部平均颜色替换（更自然）
#         # 创建背景估计
#         background = original.copy()
        
#         # 使用中值滤波估计背景
#         kernel_size_bg = 7
#         for c in range(3):
#             channel = original[:, :, c].copy()
#             channel[watermark_mask == 255] = 0
#             background_channel = cv2.medianBlur(channel, kernel_size_bg)
#             background[:, :, c] = background_channel
        
#         # 如果需要边缘融合
#         if blend_edges and 'feather_mask' in locals():
#             # 将羽化掩码扩展到全图
#             full_feather_mask = np.zeros((height, width), dtype=np.float32)
#             full_feather_mask[start_y:height, start_x:width] = feather_mask
            
#             # 应用羽化混合
#             result = result.astype(np.float32)
#             background = background.astype(np.float32)
            
#             for c in range(3):
#                 # 创建混合层
#                 blend = result[:, :, c] * (1 - full_feather_mask) + background[:, :, c] * full_feather_mask
#                 result[:, :, c] = blend
            
#             result = result.astype(np.uint8)
#         else:
#             # 直接替换
#             result[watermark_mask == 255] = background[watermark_mask == 255]
    
#     # 4. 边界后处理
#     # 应用轻微的高斯模糊使边界更自然
#     if blend_edges:
#         # 只在边界区域应用模糊
#         kernel_blur = np.ones((3, 3), np.uint8)
#         boundary_mask = cv2.dilate(watermark_mask, kernel_blur, iterations=1)
#         boundary_mask = boundary_mask - cv2.erode(watermark_mask, kernel_blur, iterations=1)
        
#         if np.any(boundary_mask == 255):
#             # 提取边界区域
#             boundary_indices = boundary_mask == 255
            
#             # 对边界应用轻微高斯模糊
#             blurred_result = cv2.GaussianBlur(result, (3, 3), 0.5)
            
#             # 只替换边界区域
#             for c in range(3):
#                 channel = result[:, :, c]
#                 blurred_channel = blurred_result[:, :, c]
#                 channel[boundary_indices] = blurred_channel[boundary_indices]
#                 result[:, :, c] = channel
    
#     # 5. 显示结果对比
#     cv2.imshow('1. Original Image', original)
#     cv2.imshow('2. Watermark Mask', watermark_mask * 255)
    
#     if blend_edges and 'full_feather_mask' in locals():
#         cv2.imshow('3. Feather Mask', (full_feather_mask * 255).astype(np.uint8))
    
#     cv2.imshow('4. Result Image', result)
    
#     # 创建对比图
#     comparison = np.hstack([
#         cv2.resize(original[start_y:height, start_x:width], (300, 300)),
#         cv2.resize(result[start_y:height, start_x:width], (300, 300))
#     ])
#     cv2.imshow('5. ROI Comparison (Before/After)', comparison)
    
#     print("按任意键继续...")
#     cv2.waitKey(0)
#     cv2.destroyAllWindows()
    
#     return result, watermark_mask


# def remove_watermark_simple_but_effective(image_path, region_ratio=0.3):
#     """
#     简单但有效的版本，适合快速处理
#     """
#     image = cv2.imread(image_path)
#     if image is None:
#         return None
    
#     original = image.copy()
#     height, width = image.shape[:2]
    
#     # 计算右下角区域
#     start_y = int(height * (1 - region_ratio))
#     start_x = int(width * (1 - region_ratio))
    
#     roi = original[start_y:height, start_x:width]
    
#     # 转换为HSV空间
#     hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
#     h, s, v = cv2.split(hsv)
    
#     # 检测灰色区域（低饱和度）
#     _, sat_mask = cv2.threshold(s, 50, 255, cv2.THRESH_BINARY_INV)
    
#     # 检测适当亮度范围
#     _, val_mask = cv2.threshold(v, 180, 240, cv2.THRESH_BINARY)
    
#     # 结合条件
#     gray_mask = cv2.bitwise_and(sat_mask, val_mask)
    
#     # 形态学处理
#     kernel = np.ones((3, 3), np.uint8)
#     gray_mask = cv2.morphologyEx(gray_mask, cv2.MORPH_CLOSE, kernel)
#     gray_mask = cv2.morphologyEx(gray_mask, cv2.MORPH_OPEN, kernel)
    
#     # 创建完整掩码
#     full_mask = np.zeros((height, width), dtype=np.uint8)
#     full_mask[start_y:height, start_x:width] = gray_mask
    
#     # 方法1: 使用邻域平均颜色替换
#     result = original.copy()
    
#     # 对每个水印像素，使用周围非水印像素的平均颜色
#     for y in range(max(0, start_y-1), min(height, start_y + int(height*region_ratio) + 1)):
#         for x in range(max(0, start_x-1), min(width, start_x + int(width*region_ratio) + 1)):
#             if full_mask[y, x] == 255:
#                 # 获取3x3邻域
#                 y_min = max(0, y-1)
#                 y_max = min(height, y+2)
#                 x_min = max(0, x-1)
#                 x_max = min(width, x+2)
                
#                 # 计算邻域中非水印像素的平均颜色
#                 neighbor_roi = original[y_min:y_max, x_min:x_max]
#                 mask_roi = full_mask[y_min:y_max, x_min:x_max]
                
#                 if np.any(mask_roi == 0):  # 如果有非水印像素
#                     # 计算非水印像素的平均值
#                     non_watermark_pixels = neighbor_roi[mask_roi == 0]
#                     if len(non_watermark_pixels) > 0:
#                         avg_color = np.mean(non_watermark_pixels, axis=0)
#                         result[y, x] = avg_color
    
#     return result


# # 使用示例
# if __name__ == "__main__":
#     print("改进的水印去除方法")
    
# #     # result1 = remove_watermark('./input/f291f37d3bc9a960465dfb0a63365cda.jpg', region_ratio=0.3)
# #     result1 = remove_watermark('./input/e313778daa5a29dca473260c1ea46661.jpg', region_ratio=0.3)

#     # 方法1: 完整版本
#     result1, mask1 = remove_watermark_improved(
#         './input/f291f37d3bc9a960465dfb0a63365cda.jpg',
#         region_ratio=0.3,
#         gray_threshold_range=(170, 230),  # 根据水印深浅调整
#         use_inpainting=True,
#         blend_edges=True
#     )
    
#     if result1 is not None:
#         cv2.imwrite('result_improved.jpg', result1)
#         cv2.imwrite('watermark_mask.jpg', mask1 * 255)
#         print("结果已保存为 'result_improved.jpg'")
    
#     print("\n简单有效版本")
#     # 方法2: 简单版本
#     result2 = remove_watermark_simple_but_effective('./input/f291f37d3bc9a960465dfb0a63365cda.jpg', region_ratio=0.3)
    
#     if result2 is not None:
#         cv2.imshow('Simple Result', result2)
#         cv2.waitKey(0)
#         cv2.destroyAllWindows()
#         cv2.imwrite('result_simple.jpg', result2)
#         print("结果已保存为 'result_simple.jpg'")

import cv2
import numpy as np
from PIL import Image
import os
 
dir = os.getcwd()
# path = "./input/f291f37d3bc9a960465dfb0a63365cda.jpg"
path = "./input/image.png"
newPath = "./output/f291f37d3bc9a960465dfb0a63365cda.jpg"
img = cv2.imread(path, 1)
hight, width, depth = img.shape[0:3]
 
# 截取
cropped = img[int(hight * 0.8):hight, int(width * 0.7):width]  # 裁剪坐标为[y0:y1, x0:x1]
cv2.imwrite(newPath, cropped)
imgSY = cv2.imread(newPath, 1)
 
# 图片二值化处理，把[200,200,200]-[250,250,250]以外的颜色变成0
thresh = cv2.inRange(imgSY, np.array([200, 200, 200]), np.array([250, 250, 250]))
# 创建形状和尺寸的结构元素
kernel = np.ones((3, 3), np.uint8)
# 扩展待修复区域
hi_mask = cv2.dilate(thresh, kernel, iterations=10)
specular = cv2.inpaint(imgSY, hi_mask, 5, flags=cv2.INPAINT_TELEA)
cv2.imwrite(newPath, specular)
 
# 覆盖图片
imgSY = Image.open(newPath)
img = Image.open(path)
img.paste(imgSY, (int(width * 0.7), int(hight * 0.8), width, hight))
img.save(newPath)