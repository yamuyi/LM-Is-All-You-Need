import os
from pathlib import Path
from datetime import datetime

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"

# 基础目录结构
INPUT_DIR = DATA_DIR / "input"
PROCESSING_DIR = DATA_DIR / "processing"  # 新增：处理中目录
OUTPUT_DIR = DATA_DIR / "output"

# 输入目录细分
MHTML_INPUT_DIR = INPUT_DIR / "mhtml"
HTML_INPUT_DIR = INPUT_DIR / "html"
MD_INPUT_DIR = INPUT_DIR / "md"

# 处理目录（存放正在处理的文件）
PROCESSING_TEMP_DIR = PROCESSING_DIR / "temp"  # 临时处理目录

# 输出目录（最终结果）
FINAL_OUTPUT_DIR = OUTPUT_DIR / "final"

# 按任务组织输出的函数
def get_task_output_dir(task_name: str, create: bool = True) -> Path:
    """
    获取任务输出目录
    
    Args:
        task_name: 任务名称/标识符（通常使用输入文件名）
        create: 是否创建目录
    
    Returns:
        Path: 任务输出目录路径
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    task_dir = FINAL_OUTPUT_DIR / f"{task_name}_{timestamp}"
    
    if create:
        task_dir.mkdir(parents=True, exist_ok=True)
    
    return task_dir

def get_task_subdirs(task_dir: Path) -> dict:
    """
    获取任务目录下的标准子目录结构
    
    Returns:
        dict: 子目录路径字典
    """
    return {
        'html': task_dir / "html",
        'markdown': task_dir / "markdown",
        'images': task_dir / "markdown" / "images",  # 图片放在markdown目录下
        'working_md': task_dir / "working_md",  # 手动编辑的markdown
        'segmented': task_dir / "segmented",
        'temp': task_dir / ".temp",  # 临时文件
    }

# 其余配置保持不变...
OLLAMA_CONFIG = {
    'base_url': 'http://localhost:11434',
    'model': 'qwen3:8b',
    'timeout': 120,
    'temperature': 0.1,
    'max_tokens': 8192
}

MD_CLEAN_CONFIG = {
    'remove_patterns': [
        '作者介绍', '作者简介', '关于作者',
        '知乎', '知识星球', '公众号', '微信公众号',
        '版权声明', '转载声明', '免责声明',
        '平台介绍', '来源', '原文链接'
    ],
    'keep_essential': True
}

# 水印默认配置
DEFAULT_WATERMARK = {
    "text": "知识星球：羊头人的AI日志",
    "style": "grid",
    "font_size": 30,
    "opacity": 0.4,
    "angle": 30,
    "segment_height": 1200,
    "grid_columns": 3,
    "grid_rows": 10
}

# 图片下载配置
IMAGE_DOWNLOAD_CONFIG = {
    "timeout": 30,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# 初始化目录
def create_directories():
    """创建所有必要的目录"""
    # 基础目录
    base_dirs = [
        INPUT_DIR, PROCESSING_DIR, OUTPUT_DIR, FINAL_OUTPUT_DIR,
        MHTML_INPUT_DIR, HTML_INPUT_DIR, MD_INPUT_DIR,
        PROCESSING_TEMP_DIR
    ]
    
    for dir_path in base_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    logger = get_logger()
    logger.info("目录结构初始化完成")

# 延迟导入以避免循环依赖
def get_logger():
    from src.utils.log_utils import logger
    return logger

# 初始化
create_directories()