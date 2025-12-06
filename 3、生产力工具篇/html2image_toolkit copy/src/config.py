import os
from pathlib import Path

# 项目根目录 - 修复：正确的层级
ROOT_DIR = Path(__file__).parent.parent

# 数据目录配置
DATA_DIR = ROOT_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"

# 细分输入目录
MHTML_INPUT_DIR = INPUT_DIR / "mhtml"
HTML_INPUT_DIR = INPUT_DIR / "html"
MD_INPUT_DIR = INPUT_DIR / "md"

# 细分输出目录
HTML_OUTPUT_DIR = OUTPUT_DIR / "html"
MD_OUTPUT_DIR = OUTPUT_DIR / "md"
IMAGE_OUTPUT_DIR = OUTPUT_DIR / "images"
SEGMENTED_OUTPUT_DIR = OUTPUT_DIR / "segmented"

# Ollama 配置
OLLAMA_CONFIG = {
    'base_url': 'http://localhost:11434',
    'model': 'qwen3:8b',  # 或其他您使用的模型
    'timeout': 120,
    'temperature': 0.1,
    'max_tokens': 8192
}

# Markdown 清理配置
MD_CLEAN_CONFIG = {
    'remove_patterns': [
        '作者介绍', '作者简介', '关于作者',
        '知乎', '知识星球', '公众号', '微信公众号',
        '版权声明', '转载声明', '免责声明',
        '平台介绍', '来源', '原文链接'
    ],
    'keep_essential': True
}

# 确保目录存在
def create_directories():
    dirs = [
        MHTML_INPUT_DIR, HTML_INPUT_DIR, MD_INPUT_DIR,
        HTML_OUTPUT_DIR, MD_OUTPUT_DIR, IMAGE_OUTPUT_DIR,
        SEGMENTED_OUTPUT_DIR
    ]
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)

# 水印默认配置
DEFAULT_WATERMARK = {
    "text": "知识星球：羊头人的AI日志",
    "style": "grid",  # grid/sparse/medium/very_sparse
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

WORKING_DIR = DATA_DIR / "working"  # 新增：工作目录（手动编辑用）
# # 新增：工作目录细分
WORKING_MD_DIR = WORKING_DIR / "md"  # 手动编辑后的Markdown存放目录

# # 确保目录存在（新增WORKING相关目录）
def create_directories():
    dirs = [
        # 原有目录
        MHTML_INPUT_DIR, HTML_INPUT_DIR, MD_INPUT_DIR,
        HTML_OUTPUT_DIR, MD_OUTPUT_DIR, IMAGE_OUTPUT_DIR,
        SEGMENTED_OUTPUT_DIR,
        # 新增工作目录
        WORKING_DIR, WORKING_MD_DIR
    ]
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)

# 其余配置（水印、图片下载）不变...

# 初始化目录
create_directories()