import os
import sys
import shutil
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import math
from io import BytesIO

class HTMLToSegmentedImage:
    def __init__(self, chrome_driver_path=None):
        """初始化"""
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument('--lang=zh-CN')
        
        try:
            if chrome_driver_path:
                self.driver = webdriver.Chrome(executable_path=chrome_driver_path, options=self.chrome_options)
            else:
                self.driver = webdriver.Chrome(options=self.chrome_options)
        except Exception as e:
            print(f"ChromeDriver初始化失败: {e}")
            sys.exit(1)
    
    def html_to_long_image(self, html_file_path, output_path, wait_time=3):
        """将HTML文件转换为长图片"""
        try:
            html_url = f"file://{os.path.abspath(html_file_path)}"
            print(f"加载HTML: {html_url}")
            self.driver.get(html_url)
            self.driver.implicitly_wait(wait_time)
            
            total_width = self.driver.execute_script("return document.body.scrollWidth")
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            print(f"页面尺寸: {total_width} x {total_height}")
            
            self.driver.set_window_size(total_width, total_height)
            import time
            time.sleep(1)
            
            screenshot = self.driver.get_screenshot_as_png()
            image = Image.open(BytesIO(screenshot))
            image.save(output_path)
            print(f"长图片已保存: {output_path}")
            return image
            
        except Exception as e:
            print(f"HTML转图片失败: {e}")
            return None

    def add_watermark_with_control(self, image, watermark_text, output_path=None, 
                                 font_size=50, opacity=0.3, angle=30, 
                                 spacing_ratio=2.5, layers=1, 
                                 color=(255, 255, 255), shadow=False):
        """
        可控密度的水印函数
        """
        try:
            print("开始添加可控密度水印...")
            print(f"密度参数: 间距倍数={spacing_ratio}, 层数={layers}")
            
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            width, height = image.size
            watermark_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(watermark_layer)
            
            # 获取字体
            font = self._get_chinese_font(font_size)
            if font is None:
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()
            
            # 测量文字尺寸
            try:
                bbox = draw.textbbox((0, 0), watermark_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except:
                text_width = len(watermark_text) * font_size
                text_height = font_size
            
            print(f"水印文字尺寸: {text_width} x {text_height}")
            
            # 创建水印文字图片
            padding = 40
            text_img_size = (text_width + padding, text_height + padding)
            text_img = Image.new('RGBA', text_img_size, (0, 0, 0, 0))
            text_draw = ImageDraw.Draw(text_img)
            
            # 设置文字位置
            text_x = padding // 2
            text_y = padding // 2
            
            # 设置透明度
            alpha = int(255 * opacity)
            fill_color = (*color, alpha)
            
            # 添加阴影
            if shadow:
                shadow_alpha = int(255 * opacity * 0.5)
                shadow_color = (0, 0, 0, shadow_alpha)
                text_draw.text((text_x+2, text_y+2), watermark_text, font=font, fill=shadow_color)
            
            # 绘制文字
            text_draw.text((text_x, text_y), watermark_text, font=font, fill=fill_color)
            
            # 旋转文字
            rotated_text = text_img.rotate(angle, expand=True, resample=Image.BICUBIC, fillcolor=(0, 0, 0, 0))
            rot_width, rot_height = rotated_text.size
            
            # 计算间距
            base_spacing_x = int(rot_width * spacing_ratio)
            base_spacing_y = int(rot_height * spacing_ratio)
            
            print(f"实际间距: {base_spacing_x} x {base_spacing_y}")
            print(f"水印单元尺寸: {rot_width} x {rot_height}")
            
            # 第一层平铺
            for x in range(-rot_width, width + rot_width, base_spacing_x):
                for y in range(-rot_height, height + rot_height, base_spacing_y):
                    watermark_layer.paste(rotated_text, (x, y), rotated_text)
            
            # 第二层平铺（可选）
            if layers >= 2:
                offset_x = base_spacing_x // 2
                offset_y = base_spacing_y // 2
                for x in range(-rot_width + offset_x, width + rot_width, base_spacing_x):
                    for y in range(-rot_height + offset_y, height + rot_height, base_spacing_y):
                        watermark_layer.paste(rotated_text, (x, y), rotated_text)
            
            # 合并图层
            image_rgba = image.convert('RGBA')
            watermarked = Image.alpha_composite(image_rgba, watermark_layer)
            watermarked = watermarked.convert('RGB')
            
            if output_path:
                watermarked.save(output_path, quality=95)
                print(f"可控密度水印图片已保存: {output_path}")
            
            return watermarked
            
        except Exception as e:
            print(f"添加可控密度水印失败: {e}")
            import traceback
            traceback.print_exc()
            return image

    def add_sparse_watermark(self, image, watermark_text, output_path=None,
                           font_size=60, opacity=0.25, angle=45,
                           grid_columns=3, grid_rows=8):
        """
        网格布局水印
        """
        try:
            print("开始添加网格布局水印...")
            print(f"网格布局: {grid_columns}列 x {grid_rows}行")
            
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            width, height = image.size
            watermark_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(watermark_layer)
            
            # 获取字体
            font = self._get_chinese_font(font_size)
            if font is None:
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()
            
            # 测量文字尺寸
            try:
                bbox = draw.textbbox((0, 0), watermark_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except:
                text_width = len(watermark_text) * font_size
                text_height = font_size
            
            # 计算网格间距
            cell_width = width // grid_columns
            cell_height = height // grid_rows
            
            print(f"网格单元尺寸: {cell_width} x {cell_height}")
            
            # 设置透明度
            alpha = int(255 * opacity)
            fill_color = (255, 255, 255, alpha)
            
            # 在网格交叉点放置水印
            for col in range(grid_columns + 1):
                for row in range(grid_rows + 1):
                    x = col * cell_width
                    y = row * cell_height
                    
                    # 创建单个水印
                    text_img = Image.new('RGBA', (text_width + 20, text_height + 20), (0, 0, 0, 0))
                    text_draw = ImageDraw.Draw(text_img)
                    text_draw.text((10, 10), watermark_text, font=font, fill=fill_color)
                    
                    # 旋转
                    rotated_text = text_img.rotate(angle, expand=True, resample=Image.BICUBIC, fillcolor=(0, 0, 0, 0))
                    rot_width, rot_height = rotated_text.size
                    
                    # 放置在网格点（居中）
                    paste_x = x - rot_width // 2
                    paste_y = y - rot_height // 2
                    
                    watermark_layer.paste(rotated_text, (paste_x, paste_y), rotated_text)
            
            # 合并图层
            image_rgba = image.convert('RGBA')
            watermarked = Image.alpha_composite(image_rgba, watermark_layer)
            watermarked = watermarked.convert('RGB')
            
            if output_path:
                watermarked.save(output_path, quality=95)
                print(f"网格水印图片已保存: {output_path}")
            
            return watermarked
            
        except Exception as e:
            print(f"添加网格水印失败: {e}")
            return image

    def _get_chinese_font(self, font_size):
        """获取中文字体"""
        chinese_font_paths = [
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simsun.ttc",
            "/System/Library/Fonts/PingFang.ttc",
        ]
        
        for font_path in chinese_font_paths:
            try:
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, font_size)
            except:
                continue
        
        try:
            return ImageFont.load_default()
        except:
            return None

    def split_image(self, image, segment_height, output_dir, prefix="segment"):
        """切分图片"""
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            width, height = image.size
            segments = math.ceil(height / segment_height)
            segment_paths = []
            
            for i in range(segments):
                start_y = i * segment_height
                end_y = min((i + 1) * segment_height, height)
                segment = image.crop((0, start_y, width, end_y))
                segment_path = os.path.join(output_dir, f"{prefix}_{i+1:03d}.jpg")
                segment.save(segment_path, "JPEG", quality=95)
                segment_paths.append(segment_path)
            
            print(f"切分成 {segments} 段图片")
            return segment_paths
            
        except Exception as e:
            print(f"图片切分失败: {e}")
            return []

    def auto_process_batch(self, input_dir="input_html", output_base_dir="output", 
                          watermark_text="知识星球：羊头人的AI日志",
                          segment_height=1200, watermark_style="grid",
                          auto_cleanup=True, **kwargs):
        """
        自动化批量处理
        
        :param input_dir: HTML文件输入目录
        :param output_base_dir: 输出基础目录
        :param auto_cleanup: 是否自动清理输入文件
        :param **kwargs: 其他水印参数
        """
        print("=== 开始自动化批量处理 ===")
        
        # 确保输入目录存在
        if not os.path.exists(input_dir):
            print(f"输入目录不存在: {input_dir}")
            return False
        
        # 获取所有HTML文件
        html_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.html')]
        if not html_files:
            print(f"在 {input_dir} 目录中没有找到HTML文件")
            return False
        
        print(f"找到 {len(html_files)} 个HTML文件: {html_files}")
        
        results = {}
        
        for html_file in html_files:
            print(f"\n=== 处理文件: {html_file} ===")
            
            # 创建带时间戳的输出目录
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_base_name = os.path.splitext(html_file)[0]
            output_dir = os.path.join(output_base_dir, f"{file_base_name}_{timestamp}")
            
            # 处理HTML文件
            html_file_path = os.path.join(input_dir, html_file)
            result = self.process_html_with_density_control(
                html_file_path=html_file_path,
                output_dir=output_dir,
                watermark_text=watermark_text,
                segment_height=segment_height,
                watermark_style=watermark_style,
                **kwargs
            )
            
            if result:
                results[html_file] = result
                print(f"✓ 成功处理: {html_file}")
                
                # # 自动清理输入文件
                # if auto_cleanup:
                #     try:
                #         os.remove(html_file_path)
                #         print(f"✓ 已清理输入文件: {html_file}")
                #     except Exception as e:
                #         print(f"✗ 清理文件失败: {e}")
            else:
                print(f"✗ 处理失败: {html_file}")
        
        print(f"\n=== 批量处理完成 ===")
        print(f"成功处理: {len(results)}/{len(html_files)} 个文件")
        return results

    def process_html_with_density_control(self, html_file_path, output_dir, watermark_text,
                                        segment_height=1000, watermark_style="sparse", **kwargs):
        """
        带密度控制的处理流程
        """
        if not os.path.exists(html_file_path):
            print(f"HTML文件不存在: {html_file_path}")
            return False
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        try:
            # HTML转长图片
            long_image_path = os.path.join(output_dir, "long_image.png")
            image = self.html_to_long_image(html_file_path, long_image_path)
            
            if image is None:
                return False
            
            # 添加水印
            watermarked_path = os.path.join(output_dir, "watermarked_image.png")
            
            if watermark_style == "very_sparse":
                watermarked_image = self.add_watermark_with_control(
                    image, watermark_text, watermarked_path,
                    spacing_ratio=4.0, layers=1, **kwargs
                )
            elif watermark_style == "sparse":
                watermarked_image = self.add_watermark_with_control(
                    image, watermark_text, watermarked_path,
                    spacing_ratio=3.0, layers=1, **kwargs
                )
            elif watermark_style == "medium":
                watermarked_image = self.add_watermark_with_control(
                    image, watermark_text, watermarked_path,
                    spacing_ratio=2.5, layers=1, **kwargs
                )
            elif watermark_style == "grid":
                watermarked_image = self.add_sparse_watermark(
                    image, watermark_text, watermarked_path, **kwargs
                )
            else:
                watermarked_image = self.add_watermark_with_control(
                    image, watermark_text, watermarked_path, **kwargs
                )
            
            # 切分图片
            segments_dir = os.path.join(output_dir, "segments")
            segment_paths = self.split_image(watermarked_image, segment_height, segments_dir)
            
            print("处理完成!")
            return {
                'long_image': long_image_path,
                'watermarked_image': watermarked_path,
                'segments': segment_paths,
                'segment_count': len(segment_paths)
            }
            
        except Exception as e:
            print(f"处理过程出错: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def close(self):
        """关闭浏览器驱动"""
        if hasattr(self, 'driver'):
            self.driver.quit()

def setup_directories():
    """设置必要的目录结构"""
    directories = ['input_html', 'output']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"创建目录: {directory}")

def main():
    """主函数 - 自动化批量处理"""
    
    # 设置目录
    setup_directories()
    
    # 初始化处理器
    processor = HTMLToSegmentedImage()
    
    try:
        # 自动化批量处理
        results = processor.auto_process_batch(
            input_dir="input_html",           # HTML文件放在这个目录
            output_base_dir="output",         # 处理结果输出到这个目录
            watermark_text="知识星球：羊头人的AI日志",
            segment_height=1200,              # 每段图片高度
            watermark_style="grid",           # 水印样式: grid, sparse, medium, very_sparse
            auto_cleanup=True,                # 处理完成后自动删除输入HTML文件
            
            # 网格水印参数
            grid_columns=3,                   # 列数
            grid_rows=10,                     # 行数
            font_size=30,                     # 字体大小
            opacity=0.4,                      # 透明度
            angle=30                          # 旋转角度
        )
        
        if results:
            print("\n=== 处理结果汇总 ===")
            for file_name, result in results.items():
                print(f"📄 {file_name}: {result['segment_count']} 个分段")
        
    except Exception as e:
        print(f"处理过程中出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        processor.close()

if __name__ == "__main__":
    main()