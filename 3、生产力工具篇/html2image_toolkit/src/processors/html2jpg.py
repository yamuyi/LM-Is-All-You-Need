import os
import sys
import math
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from io import BytesIO
from src.utils.log_utils import logger
from src.config import DEFAULT_WATERMARK

class HTMLToSegmentedImage:
    def __init__(self):
        """初始化（自动管理ChromeDriver）"""
        self.chrome_options = self._init_chrome_options()
        self.driver = self._init_driver()
    
    def _init_chrome_options(self) -> Options:
        """初始化Chrome选项"""
        options = Options()
        options.add_argument('--headless=new')  # 新版无头模式
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--lang=zh-CN')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        return options
    
    def _init_driver(self) -> webdriver.Chrome:
        """初始化ChromeDriver（自动下载对应版本）"""
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=self.chrome_options)
            logger.info("ChromeDriver初始化成功")
            return driver
        except Exception as e:
            logger.error(f"ChromeDriver初始化失败: {str(e)}", exc_info=True)
            sys.exit(1)
    
    def html_to_long_image(self, html_file_path: str | Path, output_path: str | Path) -> Image.Image | None:
        """HTML转长图片"""
        html_file_path = Path(html_file_path)
        output_path = Path(output_path)
        
        if not html_file_path.exists():
            logger.error(f"HTML文件不存在: {html_file_path}")
            return None
        
        try:
            # 确保输出目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            html_url = f"file://{html_file_path.absolute()}"
            logger.info(f"加载HTML文件: {html_url}")
            
            # 设置初始窗口大小
            self.driver.set_window_size(1200, 800)
            self.driver.get(html_url)
            
            # 等待页面完全加载
            self.driver.implicitly_wait(10)
            import time
            time.sleep(3)  # 额外等待时间确保所有资源加载
            
            # 获取准确的高度
            total_height = self._get_accurate_page_height()
            total_width = self._get_accurate_page_width()
            
            logger.info(f"计算后页面尺寸: {total_width} x {total_height}")
            
            if total_height <= 0 or total_width <= 0:
                logger.error("无法获取有效的页面尺寸")
                return None
                
            # 限制最大宽度，避免过宽
            max_content_width = 1000
            if total_width > max_content_width:
                total_width = max_content_width
                # 通过JavaScript设置页面最大宽度
                self.driver.execute_script(f"""
                    var body = document.body;
                    var html = document.documentElement;
                    body.style.maxWidth = '{max_content_width}px';
                    body.style.margin = '0 auto';
                    body.style.padding = '20px';
                    html.style.maxWidth = '{max_content_width}px';
                    
                    // 确保所有元素居中
                    var allElements = document.querySelectorAll('*');
                    for (var i = 0; i < allElements.length; i++) {{
                        var element = allElements[i];
                        if (element.tagName === 'IMG' || element.tagName === 'TABLE') {{
                            element.style.display = 'block';
                            element.style.margin = '0 auto';
                        }}
                    }}
                """)
                # 重新计算高度
                time.sleep(2)
                total_height = self._get_accurate_page_height()
            
            # 设置浏览器窗口大小
            self.driver.set_window_size(total_width + 100, min(total_height + 100, 32767))
            
            # 再次等待渲染
            time.sleep(2)
            
            # 使用Selenium的完整页面截图
            screenshot = self.driver.get_screenshot_as_png()
            image = Image.open(BytesIO(screenshot))
            
            # 验证截图是否完整
            if image.height < total_height * 0.8:  # 如果截图高度远小于页面高度
                logger.warning(f"截图可能不完整: 截图高度={image.height}, 页面高度={total_height}")
                # 尝试滚动截图方式
                image = self._take_scrolling_screenshot(total_height)
            
            image.save(output_path, quality=95)
            logger.info(f"长图片保存成功: {output_path}, 尺寸: {image.size}")
            return image
        
        except Exception as e:
            logger.error(f"HTML转长图片失败: {str(e)}", exc_info=True)
            return None

    def _get_accurate_page_height(self) -> int:
        """获取准确的页面高度"""
        try:
            # 尝试多种方法获取高度
            heights = []
            
            # 方法1: body scrollHeight
            body_height = self.driver.execute_script("return document.body.scrollHeight")
            heights.append(body_height)
            
            # 方法2: documentElement scrollHeight
            doc_height = self.driver.execute_script("return document.documentElement.scrollHeight")
            heights.append(doc_height)
            
            # 方法3: 取body和documentElement的最大值
            max_height = self.driver.execute_script(
                "return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight, "
                "document.body.offsetHeight, document.documentElement.offsetHeight, "
                "document.body.clientHeight, document.documentElement.clientHeight)"
            )
            heights.append(max_height)
            
            # 方法4: 获取所有元素的最大底部位置
            max_bottom = self.driver.execute_script("""
                var all = document.querySelectorAll('*');
                var max = 0;
                for (var i = 0; i < all.length; i++) {
                    var rect = all[i].getBoundingClientRect();
                    var bottom = rect.bottom + window.pageYOffset;
                    if (bottom > max) max = bottom;
                }
                return max;
            """)
            heights.append(max_bottom)
            
            # 返回最大值
            accurate_height = max(heights) + 20
            logger.debug(f"高度计算: 最终={accurate_height}")
            
            return accurate_height
            
        except Exception as e:
            logger.warning(f"获取页面高度时出错: {e}, 使用备用方法")
            return self.driver.execute_script("return document.body.scrollHeight")

    def _get_accurate_page_width(self) -> int:
        """获取准确的页面宽度"""
        try:
            widths = []
            
            # 多种方法获取宽度
            body_width = self.driver.execute_script("return document.body.scrollWidth")
            doc_width = self.driver.execute_script("return document.documentElement.scrollWidth")
            max_width = self.driver.execute_script(
                "return Math.max(document.body.scrollWidth, document.documentElement.scrollWidth)"
            )
            
            widths.extend([body_width, doc_width, max_width])
            return max(widths)
            
        except Exception as e:
            logger.warning(f"获取页面宽度时出错: {e}")
            return 1200  # 默认宽度

    def _take_scrolling_screenshot(self, total_height: int) -> Image.Image:
        """使用滚动方式截图（备用方法）"""
        try:
            logger.info("使用滚动截图方式")
            
            viewport_height = self.driver.execute_script("return window.innerHeight")
            slices = []
            offset = 0
            
            while offset < total_height:
                # 滚动到当前位置
                self.driver.execute_script(f"window.scrollTo(0, {offset});")
                import time
                time.sleep(0.5)  # 等待滚动完成
                
                # 截取当前视图
                screenshot = self.driver.get_screenshot_as_png()
                slice_img = Image.open(BytesIO(screenshot))
                slices.append(slice_img)
                
                offset += viewport_height
            
            # 合并所有切片
            if slices:
                total_width = slices[0].width
                combined_image = Image.new('RGB', (total_width, total_height))
                y_offset = 0
                
                for slice_img in slices:
                    combined_image.paste(slice_img, (0, y_offset))
                    y_offset += slice_img.height
                    # 如果已经达到总高度，停止粘贴
                    if y_offset >= total_height:
                        break
                
                return combined_image
            else:
                raise Exception("无法获取任何截图切片")
                
        except Exception as e:
            logger.error(f"滚动截图失败: {e}")
            raise

    def add_watermark(self, image: Image.Image, watermark_text: str, **kwargs) -> Image.Image:
        """统一水印接口（支持多种样式）"""
        # 合并默认参数和传入参数
        style = kwargs.get('style', DEFAULT_WATERMARK['style'])
        
        # 基础参数
        base_params = {
            'font_size': kwargs.get('font_size', DEFAULT_WATERMARK['font_size']),
            'opacity': kwargs.get('opacity', DEFAULT_WATERMARK['opacity']),
            'angle': kwargs.get('angle', DEFAULT_WATERMARK['angle'])
        }
        
        if style == "grid":
            return self._add_grid_watermark(image, watermark_text, **base_params, **kwargs)
        else:
            return self._add_density_controlled_watermark(image, watermark_text, **base_params, **kwargs)
    
    def _add_density_controlled_watermark(self, image: Image.Image, watermark_text: str, **kwargs) -> Image.Image:
        """密度可控水印"""
        font_size = kwargs.get('font_size', 30)
        opacity = kwargs.get('opacity', 0.4)
        angle = kwargs.get('angle', 30)
        spacing_ratio = kwargs.get('spacing_ratio', 2.5)
        layers = kwargs.get('layers', 1)
        
        try:
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            width, height = image.size
            watermark_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(watermark_layer)
            
            # 获取字体
            font = self._get_chinese_font(font_size)
            
            # 测量文字尺寸
            bbox = draw.textbbox((0, 0), watermark_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # 创建旋转文字
            text_img = Image.new('RGBA', (text_width + 40, text_height + 40), (0, 0, 0, 0))
            text_draw = ImageDraw.Draw(text_img)
            fill_color = (255, 255, 255, int(255 * opacity))
            text_draw.text((20, 20), watermark_text, font=font, fill=fill_color)
            
            rotated_text = text_img.rotate(
                angle, 
                expand=True, 
                resample=Image.BICUBIC, 
                fillcolor=(0, 0, 0, 0)
            )
            rot_width, rot_height = rotated_text.size
            
            # 计算间距
            spacing_x = int(rot_width * spacing_ratio)
            spacing_y = int(rot_height * spacing_ratio)
            
            # 平铺水印
            for x in range(-rot_width, width + rot_width, spacing_x):
                for y in range(-rot_height, height + rot_height, spacing_y):
                    watermark_layer.paste(rotated_text, (x, y), rotated_text)
            
            # 第二层（可选）
            if layers >= 2:
                for x in range(-rot_width + spacing_x//2, width + rot_width, spacing_x):
                    for y in range(-rot_height + spacing_y//2, height + rot_height, spacing_y):
                        watermark_layer.paste(rotated_text, (x, y), rotated_text)
            
            # 合并图层
            image_rgba = image.convert('RGBA')
            return Image.alpha_composite(image_rgba, watermark_layer).convert('RGB')
        
        except Exception as e:
            logger.error(f"添加密度可控水印失败: {str(e)}", exc_info=True)
            return image
    
    def _add_grid_watermark(self, image: Image.Image, watermark_text: str, **kwargs) -> Image.Image:
        """网格布局水印"""
        font_size = kwargs.get('font_size', 30)
        opacity = kwargs.get('opacity', 0.4)
        angle = kwargs.get('angle', 30)
        grid_columns = kwargs.get('grid_columns', 3)
        grid_rows = kwargs.get('grid_rows', 10)
        
        try:
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            width, height = image.size
            watermark_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(watermark_layer)
            
            # 获取字体
            font = self._get_chinese_font(font_size)
            
            # 测量文字尺寸
            bbox = draw.textbbox((0, 0), watermark_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # 计算网格间距
            cell_width = width // grid_columns
            cell_height = height // grid_rows
            
            # 水印样式
            fill_color = (255, 255, 255, int(255 * opacity))
            
            # 网格布局放置水印
            for col in range(grid_columns + 1):
                for row in range(grid_rows + 1):
                    x = col * cell_width
                    y = row * cell_height
                    
                    # 创建旋转文字
                    text_img = Image.new('RGBA', (text_width + 20, text_height + 20), (0, 0, 0, 0))
                    text_draw = ImageDraw.Draw(text_img)
                    text_draw.text((10, 10), watermark_text, font=font, fill=fill_color)
                    
                    rotated_text = text_img.rotate(
                        angle,
                        expand=True,
                        resample=Image.BICUBIC,
                        fillcolor=(0, 0, 0, 0)
                    )
                    rot_width, rot_height = rotated_text.size
                    
                    # 居中放置
                    paste_x = x - rot_width // 2
                    paste_y = y - rot_height // 2
                    watermark_layer.paste(rotated_text, (paste_x, paste_y), rotated_text)
            
            # 合并图层
            image_rgba = image.convert('RGBA')
            return Image.alpha_composite(image_rgba, watermark_layer).convert('RGB')
        
        except Exception as e:
            logger.error(f"添加网格水印失败: {str(e)}", exc_info=True)
            return image
    
    def _get_chinese_font(self, font_size: int) -> ImageFont.FreeTypeFont:
        """获取系统中文字体（跨平台支持）"""
        font_paths = [
            # Windows
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simsun.ttc",
            # macOS
            "/System/Library/Fonts/PingFang.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
            # Linux
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        ]
        
        for path in font_paths:
            if Path(path).exists():
                try:
                    return ImageFont.truetype(path, font_size)
                except:
                    continue
        
        # fallback字体
        try:
            return ImageFont.truetype("arial.ttf", font_size)
        except:
            logger.warning("未找到合适字体，使用默认字体")
            return ImageFont.load_default()
    
    def split_image(self, image: Image.Image, segment_height: int, output_dir: str | Path, prefix: str = "segment") -> list[Path]:
        """切分图片为指定高度的片段"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        width, height = image.size
        segments_count = math.ceil(height / segment_height)
        segment_paths = []
        
        try:
            for i in range(segments_count):
                start_y = i * segment_height
                end_y = min((i + 1) * segment_height, height)
                segment = image.crop((0, start_y, width, end_y))
                
                segment_path = output_dir / f"{prefix}_{i+1:03d}.jpg"
                segment.save(segment_path, "JPEG", quality=95)
                segment_paths.append(segment_path)
            
            logger.info(f"图片切分完成: {segments_count} 个片段，保存至 {output_dir}")
            return segment_paths
        except Exception as e:
            logger.error(f"图片切分失败: {str(e)}", exc_info=True)
            return []


    def process_html(self, html_file: str | Path, output_dir: Path, **kwargs) -> dict | None:
        """
        完整处理流程：HTML -> 长图片 -> 加水印 -> 切分
        
        Args:
            html_file: HTML文件路径
            output_dir: 输出目录（任务目录）
            **kwargs: 水印参数
        
        Returns:
            dict: 处理结果信息
        """
        html_file = Path(html_file)
        if not html_file.exists():
            logger.error(f"HTML文件不存在: {html_file}")
            return None
        
        # 创建任务子目录
        task_dirs = {
            'segmented': output_dir / "segmented",
            'temp': output_dir / ".temp"
        }
        
        for dir_path in task_dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # 1. HTML转长图片
            long_image_path = task_dirs['segmented'] / "long_image.png"
            long_image = self.html_to_long_image(html_file, long_image_path)
            if not long_image:
                return None
            
            # 2. 加水印
            watermarked_path = task_dirs['segmented'] / "watermarked_image.png"
            watermarked_image = self.add_watermark(
                long_image,
                watermark_text=kwargs.get('watermark_text', DEFAULT_WATERMARK['text']),
                **{k: v for k, v in kwargs.items() if k != 'watermark_text'}
            )
            watermarked_image.save(watermarked_path, quality=95)
            logger.info(f"水印图片保存成功: {watermarked_path}")
            
            # 3. 切分图片
            segment_height = kwargs.get('segment_height', DEFAULT_WATERMARK['segment_height'])
            segments_dir = task_dirs['segmented'] / "segments"
            segments_dir.mkdir(exist_ok=True)
            
            segment_paths = self.split_image(watermarked_image, segment_height, segments_dir)
            
            return {
                'input_file': str(html_file),
                'long_image': str(long_image_path),
                'watermarked_image': str(watermarked_path),
                'segments_dir': str(segments_dir),
                'segment_count': len(segment_paths),
                'segments': [str(p) for p in segment_paths],
                'task_dir': str(output_dir)
            }
        except Exception as e:
            logger.error(f"HTML处理流程失败: {str(e)}", exc_info=True)
            return None
    def close(self):
        """关闭ChromeDriver"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            logger.info("ChromeDriver已关闭")