from pathlib import Path
from src.utils.log_utils import logger
import os

def get_file_extension(file_path: str | Path) -> str:
    """获取文件扩展名（含.）"""
    return Path(file_path).suffix.lower()

def get_file_name_without_ext(file_path: str | Path) -> str:
    """获取无扩展名的文件名"""
    return Path(file_path).stem

def get_output_path(
    input_path: str | Path,
    output_dir: str | Path,
    output_ext: str
) -> Path:
    """生成输出文件路径（保持原文件名，更换扩展名）"""
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_filename = input_path.stem + output_ext
    return output_dir / output_filename

def list_files_in_dir(
    dir_path: str | Path,
    extensions: list[str] | None = None
) -> list[Path]:
    """列出目录下指定扩展名的文件"""
    dir_path = Path(dir_path)
    if not dir_path.exists():
        logger.warning(f"目录不存在: {dir_path}")
        return []
    
    files = []
    for file in dir_path.glob("*"):
        if file.is_file():
            if extensions is None or file.suffix.lower() in extensions:
                files.append(file)
    
    logger.info(f"在 {dir_path} 找到 {len(files)} 个文件")
    return files